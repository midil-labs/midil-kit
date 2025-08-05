from enum import StrEnum
from pydantic import BaseModel, ConfigDict


class Extra(StrEnum):
    FORBID = "forbid"
    IGNORE = "ignore"
    ALLOW = "allow"


class ForbidExtraFieldsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if getattr(cls, "model_config", {}).get("extra") != "forbid":
            raise TypeError(f"{cls.__name__}: 'extra' must be 'forbid'")


class AllowExtraFieldsModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    def __init_subclass__(cls, **kwargs):
        BaseModel.__init_subclass__(**kwargs)
        if getattr(cls, "model_config", {}).get("extra") != Extra.ALLOW:
            raise TypeError("extra must be 'allow' in all subclasses")


class IgnoreExtraFieldsModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    def __init_subclass__(cls, **kwargs):
        BaseModel.__init_subclass__(**kwargs)
        if getattr(cls, "model_config", {}).get("extra") != Extra.IGNORE:
            raise TypeError("extra must be 'ignore' in all subclasses")
