class history4feedException(Exception):
    pass
class UnknownFeedtypeException(history4feedException):
    pass
class ParseArgumentException(history4feedException):
    pass
class FetchRedirect(history4feedException):
    pass

class ScrapflyError(Exception):
    pass