from sqlalchemy.orm import declarative_base


class BaseMixin:
    ...


Base = declarative_base(cls=BaseMixin)
