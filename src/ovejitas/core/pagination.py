from typing import Generic, Self, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    has_next: bool


class Page(BaseModel, Generic[T]):
    data: list[T]
    meta: PageMeta

    @classmethod
    def build(cls, items: list[T], total: int, params: PageParams) -> Self:
        return cls(
            data=items,
            meta=PageMeta(
                page=params.page,
                page_size=params.page_size,
                total=total,
                has_next=(params.page * params.page_size) < total,
            ),
        )
