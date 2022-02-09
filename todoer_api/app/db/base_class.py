import typing as t

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, DateTime

class_registry: t.Dict = {}


@as_declarative(class_registry=class_registry)
class Base:
    """
    Is the Base class for the ORM declarative mapping, adds __tablename__.

    Often done as: Base = declarative_base()
    """

    id: t.Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
