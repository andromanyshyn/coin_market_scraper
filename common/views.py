class BaseWebSocket:
    def __init__(self, name: str, db: dict, uri: str):
        self.name = name
        self.uri = uri
        self.db = db