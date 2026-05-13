class history4feedException(Exception):
    pass


class UnknownFeedtypeException(history4feedException):
    pass


class ParseArgumentException(history4feedException):
    pass


class FetchRedirect(history4feedException):
    pass


class ScrapflyError(Exception):
    def __str__(self):
        return f"ScrapflyError({super().__str__()})"
