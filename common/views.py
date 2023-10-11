class BaseWebSocketMixin:
    def __init__(self, name: str, db: dict, uri):
        self.name = name
        self.uri = uri
        self.db = db