import time
from celery import shared_task, Task as CeleryTask
import celery
from celery.result import ResultSet, AsyncResult
import redis

from history4feed.h4fscripts.sitemap_helpers import fetch_posts_links_with_serper

from ..app import models
from . import h4f, wayback_helpers, logger, exceptions
from datetime import UTC, datetime
from history4feed.app.settings import history4feed_server_settings as settings

from urllib.parse import urlparse
from contextlib import contextmanager
from django.core.cache import cache
from rest_framework.exceptions import APIException, Throttled
from django.db import transaction

LOCK_EXPIRE = 60 * 60

def get_lock_id(feed: models.Feed):
    lock_id = f"feed-lock-{feed.id}"
    logger.debug("using lock id %s", lock_id)
    return lock_id

def queue_lock(feed: models.Feed, job=None):
    lock_value = dict(feed_id=str(feed.id))
    if job:
        lock_value["job_id"] = str(job.id)
        
    status = cache.add(get_lock_id(feed), lock_value, timeout=LOCK_EXPIRE)
    return status


@transaction.atomic()
def new_job(feed: models.Feed, include_remote_blogs):
    job_obj = models.Job.objects.create(
        feed=feed,
        earliest_item_requested=feed.latest_item_pubdate or settings.EARLIEST_SEARCH_DATE,
        latest_item_requested=datetime.now(UTC),
        include_remote_blogs=include_remote_blogs,
    )
    if not queue_lock(feed, job_obj):
        raise Throttled(detail={"message": "A job is already running for this feed", **cache.get(get_lock_id(feed))})

    (start_job.s(job_obj.pk) | retrieve_posts_from_links.s(job_obj.pk) | wait_for_all_with_retry.s() | collect_and_schedule_removal.si(job_obj.pk)).apply_async(countdown=5, link_error=error_handler.s(job_obj.pk))
    return job_obj

def new_patch_posts_job(feed: models.Feed, posts: list[models.Post], include_remote_blogs=True):
    job_obj = models.Job.objects.create(
        feed=feed,
        state=models.JobState.PENDING,
        include_remote_blogs=include_remote_blogs,
    )
    ft_jobs = [models.FulltextJob.objects.create(
        job_id=job_obj.id,
        post_id=post.id,
        link=post.link,
    ) for post in posts]
    chain = celery.chain([retrieve_full_text.si(ft_job.pk) for ft_job in ft_jobs])
    ( start_post_job.si(job_obj.id) | chain | collect_and_schedule_removal.si(job_obj.pk)).apply_async(link_error=error_handler.s(job_obj.pk), countdown=5)
    return job_obj

@shared_task(bind=True, default_retry_delay=10)
def start_post_job(self: CeleryTask, job_id):
    job = models.Job.objects.get(pk=job_id)
    if job.is_cancelled():
        job.info = "job cancelled while in queue"
        job.save(update_fields=['info'])
        return False
    if not queue_lock(job.feed, job):
        return self.retry(max_retries=360)
    job.update_state(models.JobState.RUNNING)
    return True

@shared_task
def start_job(job_id):
    job = models.Job.objects.get(pk=job_id)
    feed = job.feed
    job.update_state(models.JobState.RUNNING)
    try:
        if feed.feed_type == models.FeedType.SEARCH_INDEX:
            return [feed.url]
        return wayback_helpers.get_wayback_urls(feed.url, job.earliest_item_requested, job.latest_item_requested)
    except BaseException as e:
        job.update_state(models.JobState.FAILED)
        job.info = str(e)
        job.save(update_fields=['info'])
        return []

@shared_task(bind=True, default_retry_delay=10)
def wait_for_all_with_retry(self, result_ids):
    if not result_ids:
        return []
    result_set = ResultSet([AsyncResult(task_id) for task_id in result_ids])
    if not result_set.ready():
        return self.retry(max_retries=360)
    return result_ids

@shared_task
def retrieve_posts_from_links(urls, job_id):
    if not urls:
        return []
    full_text_chain = models.Job.objects.get(pk=job_id)
    feed = full_text_chain.feed
    chains = []
    parsed_feed = {}
    job = models.Job.objects.get(id=job_id)
    for index, url in enumerate(urls):
        if job.is_cancelled():
            break
        error = None
        if feed.feed_type == models.FeedType.SEARCH_INDEX:
            posts = retrieve_posts_from_serper(feed, job, url)
        else:
            parsed_feed, posts, error = retrieve_posts_from_url(url, feed, job)
        if error:
            logger.exception(error)
            continue
        if not posts:
            logger.warning('no new post in `%s`', url)
            continue

        full_text_chain = create_fulltexts_task_chain(job_id, posts)
        chains.append(full_text_chain.apply_async())

    if parsed_feed:
        feed.set_description(parsed_feed['description'])
        feed.set_title(parsed_feed['title'])
    feed.freshness = job.run_datetime
    
    feed.save()
    logger.info("====\n"*5)
    return [result.id for result in chains]

def create_fulltexts_task_chain(job_id, posts):
    chain_tasks = []
    for post in posts:
        ftjob_entry = models.FulltextJob.objects.create(
                job_id=job_id,
                post_id=post.id,
                link=post.link,
            )
        chain_tasks.append(retrieve_full_text.si(ftjob_entry.pk))
    return celery.chain(chain_tasks)

def retrieve_posts_from_serper(feed, job, url):
    start_time = feed.freshness or settings.EARLIEST_SEARCH_DATE
    if not start_time.tzinfo:
        start_time = start_time.replace(tzinfo=UTC)
    crawled_posts = fetch_posts_links_with_serper(url, from_time=start_time, to_time=job.run_datetime)
    posts = []
    for post_dict in crawled_posts.values():
        if post := add_post_to_db(feed, job, post_dict):
            posts.append(post)
    return posts

class JobCancelled(Exception):
    pass

@shared_task(bind=True)
def collect_and_schedule_removal(sender, job_id):
    logger.print(f"===> {sender=}, {job_id=} ")
    job = models.Job.objects.get(pk=job_id)
    remove_lock(job)
    if job.state == models.JobState.RUNNING:
        job.update_state(models.JobState.SUCCESS)

def remove_lock(job):
    if cache.delete(get_lock_id(job.feed)):
        logger.debug("lock deleted")
    else:
        logger.debug("Failed to remove lock")

def retrieve_posts_from_url(url, db_feed: models.Feed, job: models.Job):
    back_off_seconds = settings.WAYBACK_SLEEP_SECONDS
    all_posts: list[models.Post] = []
    error = None
    parsed_feed = {}
    for i in range(settings.REQUEST_RETRY_COUNT):
        if i != 0:
            time.sleep(back_off_seconds)
        try:
            if job.is_cancelled():
                raise JobCancelled("job was terminated by user")
            data, content_type, url = h4f.fetch_page_with_retries(url)
            parsed_feed = h4f.parse_feed_from_content(data, url)
            match parsed_feed['feed_type']:
                case models.FeedType.ATOM:
                    posts = h4f.parse_posts_from_atom_feed(url, data)
                case models.FeedType.RSS:
                    posts = h4f.parse_posts_from_rss_feed(url, data)
                case _:
                    raise exceptions.UnknownFeedtypeException("unknown feed type `{}` at {}".format(parsed_feed['feed_type'], url))
            for post_dict in posts.values():
                # make sure that post and feed share the same domain
                post = add_post_to_db(db_feed, job, post_dict)
                if not post:
                    continue
                all_posts.append(post)
            db_feed.save()
            logger.info(f"saved {len(posts)} posts for {url}")
            break
        except ConnectionError as e:
            logger.error(e, exc_info=True)
            error = e
            logger.info(f"job with url {url} ran into an issue {e}, backing off for {back_off_seconds} seconds")
            back_off_seconds *= 1.2
        except BaseException as e:
            logger.error(e, exc_info=True)
            error = e
            break
    return parsed_feed, all_posts, error

def add_post_to_db(db_feed: models.Feed, job: models.Job, post_dict: h4f.PostDict):
    # make sure that post and feed share the same domain
    if job.should_skip_post(post_dict.link):
        models.FulltextJob.objects.create(
                job_id=job.id,
                status=models.FullTextState.SKIPPED,
                link=post_dict.link,
        )
        return None
    categories = post_dict.categories
    del post_dict.categories
    post, created = models.Post.objects.get_or_create(defaults=post_dict.__dict__, feed=db_feed, link=post_dict.link)
    if not created or post.deleted_manually:
        return None

    post.save()
    post.add_categories(categories)
    return post
        
@shared_task()
def retrieve_full_text(ftjob_pk):
    fulltext_job = models.FulltextJob.objects.get(pk=ftjob_pk)
    try:
        if fulltext_job.is_cancelled():
            raise JobCancelled()
        else:
            fulltext_job.post.description, fulltext_job.post.content_type = h4f.get_full_text(fulltext_job.post.link)
            fulltext_job.status = models.FullTextState.RETRIEVED
            fulltext_job.error_str = ""
            fulltext_job.post.is_full_text = True
    except JobCancelled:
        fulltext_job.status = models.FullTextState.CANCELLED
        fulltext_job.error_str = "job cancelled while retrieving fulltext"
    except BaseException as e:
        fulltext_job.error_str = str(e)
        fulltext_job.status = models.FullTextState.FAILED
    fulltext_job.save()
    fulltext_job.post.save()



from celery import signals
@signals.worker_ready.connect
def mark_old_jobs_as_failed(**kwargs):
    models.Job.objects.filter(state__in=[models.JobState.PENDING, models.JobState.RUNNING]).update(state=models.JobState.CANCELLED, info="job cancelled automatically on server startup")

@shared_task
def error_handler(request, exc: Exception, traceback, job_id):
    job = models.Job.objects.get(pk=job_id)
    job.update_state(models.JobState.FAILED)
    job.info = f"job failed: {exc}"
    job.save(update_fields=['info'])
    remove_lock(job)
    logger.error('Job {3} with task_id {0} raised exception: {1!r}\n{2!r}'.format(
          request.id, exc, traceback, job_id))