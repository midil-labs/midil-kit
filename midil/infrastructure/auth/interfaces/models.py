from pydantic import BaseModel, PrivateAttr, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone, timedelta
from dateutil import parser


class ExpirableTokenMixin(BaseModel):
    _time_buffer: timedelta = PrivateAttr(default_factory=lambda: timedelta(minutes=5))
    token: str

    def expires_at(self) -> Optional[datetime]:
        raise NotImplementedError("Subclasses must implement expires_at()")

    @property
    def expired(self) -> bool:
        dt = self.expires_at()
        return datetime.now(timezone.utc) >= (dt - self._time_buffer) if dt else False


class AuthNToken(ExpirableTokenMixin):
    expires_at_iso: Optional[str] = None

    def expires_at(self) -> Optional[datetime]:
        return parser.parse(self.expires_at_iso) if self.expires_at_iso else None


class AuthNHeaders(BaseModel):
    authorization: str = Field(alias="Authorization")
    accept: str = Field(alias="Accept", default="application/json")
    content_type: str = Field(alias="Content-Type", default="application/json")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class AuthZTokenClaims(ExpirableTokenMixin):
    sub: str
    exp: int  # epoch

    def expires_at(self) -> datetime:
        return datetime.fromtimestamp(self.exp, tz=timezone.utc)
