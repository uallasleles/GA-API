import hashlib
import hmac
import time


class SignedSession:
    """Cookie de sessao assinado (HMAC-SHA256), sem estado no servidor."""

    def __init__(self, secret: str, max_age_seconds: int):
        self.secret = secret
        self.max_age_seconds = max_age_seconds

    def issue(self) -> str:
        issued_at = str(int(time.time()))
        mac = hmac.new(self.secret.encode(), issued_at.encode(), hashlib.sha256).hexdigest()
        return f"{issued_at}.{mac}"

    def verify(self, token: str | None) -> bool:
        if not token:
            return False
        try:
            issued_at, mac = token.rsplit(".", 1)
        except ValueError:
            return False
        expected = hmac.new(self.secret.encode(), issued_at.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(mac, expected):
            return False
        try:
            return (time.time() - int(issued_at)) < self.max_age_seconds
        except ValueError:
            return False
