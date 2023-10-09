class CryptoBaseException(Exception):
    message: str = ''

    def __init__(self, *args: object, msg: str = '') -> None:
        self.message = msg or self.message
        super().__init__(*args)

    def __str__(self) -> str:
        return self.message + f'Details: {self.args}'


class WebsocketConnectionError(CryptoBaseException):
    message = 'Connection Error. '


class WebsocketMessageSendingError(CryptoBaseException):
    message = 'Error sending message. '
