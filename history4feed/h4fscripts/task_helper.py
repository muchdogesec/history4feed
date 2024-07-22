import time
from celery import shared_task
import celery
from celery.result import ResultSet

from ..app import models
from django.conf import settings
from . import h4f, wayback_helpers, logger, exceptions
from datetime import datetime
from django.conf import settings

def new_job(feed: models.Feed):
    job_obj = models.Job.objects.create(
        feed=feed,
        earliest_item_requested=feed.latest_item_pubdate or settings.EARLIEST_SEARCH_DATE,
        latest_item_requested=datetime.now(),
    )
    # earliest_entry = feed.latest_item_pubdate or settings.EARLIEST_SEARCH_DATE
    start_job.s(job_obj.pk).apply_async(countdown=5)
    return job_obj

@shared_task
def start_job(job_id):
    job = models.Job.objects.get(pk=job_id)
    feed = job.feed
    job.state = models.JobState.RUNNING
    job.save()
    try:
        urls = wayback_helpers.get_wayback_urls(feed.url, job.earliest_item_requested, job.latest_item_requested)
        retrieve_posts_from_link.apply_async((job_id, urls), link=collect_and_schedule_removal.s(job_id))
    except BaseException as e:
        job.state = models.JobState.FAILED
        job.info = str(e)
        job.save()



@shared_task
def retrieve_posts_from_link(job_id, urls):
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
        full_text_chain = celery.chain([retrieve_full_text.s(job_id, post.id) for post in posts])
        chains.append(full_text_chain.apply_async(args=(None,)))

    for k, v in parsed_feed.items():
        setattr(feed, k, v)
    feed.save()
    fulltext_result_set = ResultSet(chains)
    while not fulltext_result_set.ready():
        time.sleep(10)
    logger.info(f"JOB with id `{job_id}` completed")


@shared_task
def collect_and_schedule_removal(sender, job_id):
    logger.print(f"===> {sender=}, {job_id=} ")
    job = models.Job.objects.get(pk=job_id)
    job.state = models.JobState.SUCCESS
    job.save()

def retrieve_posts_from_url(url, db_feed: models.Feed, job_id: str):
    back_off_seconds = settings.WAYBACK_SLEEP_SECONDS
    all_posts = []
    error = None
    parsed_feed = {}
    for i in range(settings.REQUEST_RETRY_COUNT):
        if i != 0:
            time.sleep(back_off_seconds)
        try:
            data, content_type, url = h4f.fetch_page_with_retries(url)
            parsed_feed = h4f.parse_feed_from_content(data, url)
            if parsed_feed['feed_type'] == models.FeedType.ATOM:
                posts = h4f.parse_posts_from_atom_feed(data)
            elif parsed_feed['feed_type'] == models.FeedType.RSS:
                posts = h4f.parse_posts_from_rss_feed(data)
            else:
                raise exceptions.UnknownFeedtypeException("unknown feed type `{}` at {}".format(parsed_feed['feed_type'], url))
            for post_dict in posts.values():
                categories = post_dict.categories
                del post_dict.categories
                post, created = models.Post.objects.get_or_create(defaults=post_dict.__dict__, feed=db_feed, link=post_dict.link, job_id=job_id)
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
    return parsed_feed, all_posts, error
        
@shared_task(bind=True)
def retrieve_full_text(self, _, job_id, post_id):
    fulltext_job = models.FulltextJob.objects.create(
            job_id=job_id,
            post_id=post_id,
    )
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

