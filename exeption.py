class EndpoionNotResponse(Exception):
    """Ошибка, Эндпоинт не отвечает."""

    pass


class APINotResponse(Exception):
    """Ошибка, API не отвечает."""

    pass


class KeyNotInList(Exception):
    """Ошибка, ключа нет в списке."""

    pass


class KeyNotExists(Exception):
    """Ошибка, ключа не существует."""

    pass


class KeyNotRegister(Exception):
    """Ошибка, ключ не зарегестрирован."""

    pass


class StatusKeyNotExists(Exception):
    """Ошибка, ключа 'status' нет в homework."""

    pass
