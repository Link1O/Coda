class UnSufficientArguments(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class BadRequest(Exception):
    def __init__(self, message="BAD REQUEST"):
        super().__init__(message)


class Unauthorized(Exception):
    def __init__(self, message="UNAUTHORIZED"):
        super().__init__(message)


class Forbidden(Exception):
    def __init__(self, message="FORBIDDEN"):
        super().__init__(message)


class NotFound(Exception):
    def __init__(self, message="NOT FOUND"):
        super().__init__(message)


class TooManyRequests(Exception):
    def __init__(self, message="TOO MANY REQUESTS"):
        super().__init__(message)
