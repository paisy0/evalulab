class EvalLabError(Exception):
    pass


class ConfigurationError(EvalLabError):
    pass


class ConnectionFailed(EvalLabError):
    def __init__(self, db_type: str, host: str, port: int | None, reason: str):
        self.db_type = db_type
        self.host = host
        self.port = port
        target = f"{host}:{port}" if port is not None else host
        super().__init__(
            f"{db_type} connection failed -> {target}. "
            f"Check .env values. Reason: {reason}"
        )


class QueryFailed(EvalLabError):
    def __init__(self, query_preview: str, reason: str):
        self.query_preview = query_preview
        super().__init__(f"Query failed: {reason}\n  -> {query_preview}")


class NotConnected(EvalLabError):
    def __init__(self):
        super().__init__(
            "Not connected. Use `with get_loader('<db_type>') as db:` "
            "or call .connect() first."
        )


class UnknownLoader(EvalLabError):
    def __init__(self, db_type: str, available: list[str]):
        self.db_type = db_type
        super().__init__(
            f"Unknown db_type '{db_type}'. Pick one: {available}"
        )


class UnknownEvalType(EvalLabError):
    def __init__(self, eval_type: str):
        self.eval_type = eval_type
        super().__init__(f"Unknown eval type: {eval_type}")
