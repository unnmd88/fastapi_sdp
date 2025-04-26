from core.drivers import AsyncClientHTTP

HTTP_CLIENT_SESSIONS: dict[int, AsyncClientHTTP | None] = {0: None}
SWARCO_SSH_CONNECTIONS = {}