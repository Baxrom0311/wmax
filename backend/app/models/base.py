from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def __init__(self, **kwargs):
        mapped = set(self.__mapper__.attrs.keys())
        for key, value in kwargs.items():
            setattr(self, key, value)
