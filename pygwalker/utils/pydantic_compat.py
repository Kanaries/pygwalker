from typing import Any, Type, TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)
PYDANTIC_V2 = hasattr(BaseModel, "model_validate")


def model_dump(model: BaseModel, **kwargs) -> dict:
    if PYDANTIC_V2:
        return model.model_dump(**kwargs)
    return model.dict(**kwargs)


def model_validate(model_cls: Type[ModelT], data: Any) -> ModelT:
    if PYDANTIC_V2:
        return model_cls.model_validate(data)
    return model_cls.parse_obj(data)
