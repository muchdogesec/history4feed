import time
from celery import shared_task
import celery
from celery.result import ResultSet, AsyncResult

from ..app import models
from django.conf import settings
from . import h4f, wayback_helpers, logger, exceptions
from datetime import datetime
from django.conf import settings

from urllib.parse import urlparse

def new_job(feed: models.Feed):
    job_obj = models.Job.objects.create(
        feed=feed,
        earliest_item_requested=feed.latest_item_pubdate or settings.EARLIEST_SEARCH_DATE,
        latest_item_requested=datetime.now(),
    )
    # earliest_entry = feed.latest_item_pubdate or settings.EARLIEST_SEARCH_DATE
    (start_job.s(job_obj.pk)| retrieve_posts_from_links.s(job_obj.pk) | wait_for_all_with_retry.s() | collect_and_schedule_removal.si(job_obj.pk)).apply_async(countdown=5)
    return job_obj

@shared_task
def start_job(job_id):
    job = models.Job.objects.get(pk=job_id)
    feed = job.feed
    job.state = models.JobState.RUNNING
    job.save()
    try:
        return wayback_helpers.get_wayback_urls(feed.url, job.earliest_item_requested, job.latest_item_requested)
    except BaseException as e:
        job.state = models.JobState.FAILED
        job.info = str(e)
        job.save()
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
    for index, url in enumerate(urls):
        parsed_feed, posts, error = retrieve_posts_from_url(url, feed, job_id)
        if error:
            continue
        if not posts:
            continue

        chain_tasks = []
        for post in posts:
            ftjob_entry = models.FulltextJob.objects.create(
                job_id=job_id,
                post_id=post.id,
                link=post.link,
            )
            chain_tasks.append(retrieve_full_text.si(ftjob_entry.pk))
        full_text_chain = celery.chain(chain_tasks)
        chains.append(full_text_chain.apply_async())

    for k, v in parsed_feed.items():
        setattr(feed, k, v)
    feed.save()
    logger.info("====\n"*20)
    return [result.id for result in chains]


@shared_task(bind=True)
def collect_and_schedule_removal(sender, job_id):
    logger.print(f"===> {sender=}, {job_id=} ")
    job = models.Job.objects.get(pk=job_id)
    if job.state == models.JobState.RUNNING:
        job.state = models.JobState.SUCCESS
        job.save()

def retrieve_posts_from_url(url, db_feed: models.Feed, job_id: str):
    back_off_seconds = settings.WAYBACK_SLEEP_SECONDS
    all_posts: list[models.Post] = []
    error = None
    parsed_feed = {}
    for i in range(settings.REQUEST_RETRY_COUNT):
        if i != 0:
            time.sleep(back_off_seconds)
        try:
            data, content_type, url = h4f.fetch_page_with_retries(url)
            parsed_feed = h4f.parse_feed_from_content(data, url)
            if parsed_feed['feed_type'] == models.FeedType.ATOM:
                posts = h4f.parse_posts_from_atom_feed(url, data)
            elif parsed_feed['feed_type'] == models.FeedType.RSS:
                posts = h4f.parse_posts_from_rss_feed(url, data)
            else:
                raise exceptions.UnknownFeedtypeException("unknown feed type `{}` at {}".format(parsed_feed['feed_type'], url))
            for post_dict in posts.values():
                # make sure that post and feed share the same domain
                if db_feed.should_skip_post(post_dict.link):
                    models.FulltextJob.objects.create(
                            job_id=job_id,
                            status=models.FullTextState.SKIPPED,
                            link=post_dict.link,
                    )
                    continue
                categories = post_dict.categories
                del post_dict.categories
                post, created = models.Post.objects.get_or_create(defaults={**post_dict.__dict__, "job_id":job_id}, feed=db_feed, link=post_dict.link)
                if not created:
                    continue
                db_feed.earliest_item_pubdate = min(db_feed.earliest_item_pubdate or post.pubdate, post.pubdate)
                db_feed.latest_item_pubdate   = max(db_feed.latest_item_pubdate   or post.pubdate, post.pubdate)
                post.save()
                post.add_categories(categories)
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
        
@shared_task(bind=True)
def retrieve_full_text(self, ftjob_pk):
    fulltext_job = models.FulltextJob.objects.get(pk=ftjob_pk)
    try:
        if not fulltext_job.post.is_full_text:
            fulltext_job.post.description, fulltext_job.post.content_type = h4f.get_full_text(fulltext_job.post.link)
        fulltext_job.status = models.FullTextState.RETRIEVED
        fulltext_job.error_str = ""
        fulltext_job.post.is_full_text = True
    except BaseException as e:
        fulltext_job.error_str = str(e)
        fulltext_job.status = models.FullTextState.FAILED
    fulltext_job.save()
    fulltext_job.post.save()
    logger.print(f"{self}")



def is_remote_post(url1, url2):
    uri1 = urlparse(url1)
    uri2 = urlparse(url2)
    return uri1.hostname != uri2.hostname