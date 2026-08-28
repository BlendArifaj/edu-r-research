from contextvars import ContextVar

inbound_authorization: ContextVar[str] = ContextVar("inbound_authorization", default="")
