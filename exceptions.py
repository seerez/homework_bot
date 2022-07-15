class HomeworksIsNotList(Exception):
    """Класс исключения."""

    pass


class MessageIsNotSent(Exception):
    """Исключение при отправке сообщения."""

    pass


class ResponseError(Exception):
    """Ошибка при запросе."""

    pass


class ResponseNotAnswered(Exception):
    """Ошибка при обращении к API(статус !=200)."""

    pass


class ErrorAccessingJson(Exception):
    """Ошибка при форматировании данных в формат json."""

    pass


class ErrorAccessingName(Exception):
    """Ошибка при обращении к homework_name."""

    pass


class ErrorAccessingStatus(Exception):
    """Ошибка при обращении к status."""

    pass
