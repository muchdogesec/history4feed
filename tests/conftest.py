from datetime import UTC, datetime
import uuid
import pytest
from history4feed.app.models import Feed, Job, Post


@pytest.fixture
def feeds():
    return [
        Feed.objects.create(
            url="https://example.com/rss1.xml",
            title="Test Feed 1",
            feed_type="atom",
            description="some description",
            id=uuid.UUID("6ca6ce37-1c69-4a81-8490-89c91b57e557"),
        ),
        Feed.objects.create(
            url="https://example.com/rss2.xml",
            title="Test Feed 2",
            feed_type="rss",
            description="descr-iption",
            id=uuid.UUID("0dfccb58-158c-4436-b338-163e3662943c"),
        ),
        Feed.objects.create(
            url="https://example.com/rss3.xml",
            title="Some other feed 3",
            feed_type="skeleton",
        ),
    ]


@pytest.fixture
def feed(feeds) -> Feed:
    return feeds[0]


@pytest.fixture
def feed_posts(feed):
    p1 = Post.objects.create(
        feed=feed,
        title="First post",
        pubdate=datetime.now(UTC),
        link="https://example.net/post1",
        id=uuid.UUID("561ed102-7584-4b7d-a302-43d4bca5605b"),
    )
    p2 = Post.objects.create(
        feed=feed,
        title="Second post",
        pubdate=datetime.now(UTC),
        link="https://example.net/post2",
    )
    return feed, (p1, p2)


@pytest.fixture
def jobs(feeds):
    return [
        Job.objects.create(feed=feeds[0], id="8ff3672d-067b-40af-9065-e801061f5593"),
        Job.objects.create(feed=feeds[1], id="e9794a6c-388e-4bd5-bf29-6bc01aebb8bb"),
    ]



@pytest.fixture(scope='session')
def api_schema():
    import schemathesis
    from history4feed.asgi import application
    yield schemathesis.openapi.from_asgi("/api/schema/?format=json", application)