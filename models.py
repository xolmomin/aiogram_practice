import enum
from datetime import datetime

from sqlalchemy import Enum, create_engine, select as sqlalchemy_select, \
    update as sqlalchemy_update, delete as sqlalchemy_delete, Integer, String, ForeignKey, BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, sessionmaker, declared_attr, Mapped, mapped_column, relationship

from config import settings


class Base(DeclarativeBase):
    @declared_attr
    def __tablename__(self):
        _name = self.__name__
        new_name = _name[0]
        for i in _name[1:]:
            if i.isupper():
                new_name += '_'
            new_name += i

        if new_name.endswith('y'):
            new_name = new_name[:-1] + 'ies'
        else:
            new_name = new_name + 's'
        return new_name.lower()


class Database:

    def __init__(self):
        self._engine = None
        self._session = None

    def init(self):
        self._engine = create_engine(settings.postgresql_url)
        self._session = sessionmaker(self._engine, expire_on_commit=False)()

    def __getattr__(self, item):
        return getattr(self._session, item)

    def create_all(self):
        Base.metadata.create_all(self._engine)

    def drop_all(self):
        Base.metadata.drop_all(self._engine)


db = Database()
db.init()


class AbstractClass:
    @classmethod
    def commit(cls):
        try:
            db.commit()
        except Exception as e:
            db.rollback()

    @classmethod
    def create(cls, **kwargs):
        _obj = cls(**kwargs)
        db.add(_obj)
        cls.commit()
        return _obj

    @classmethod
    def get_all(cls):
        query = sqlalchemy_select(cls).order_by(cls.id.desc())
        db.expire_all()
        results = db.execute(query)
        return results.scalars()

    @classmethod
    def first(cls):
        query = sqlalchemy_select(cls).order_by(cls.id.desc())
        db.expire_all()
        results = db.execute(query)
        return results.scalar()

    @classmethod
    def get(cls, _id):
        query = sqlalchemy_select(cls).where(cls.id == _id)
        db.expire_all()
        results = db.execute(query)
        return results.scalar()

    @classmethod
    def update(cls, _id, **kwargs):
        query = sqlalchemy_update(cls).where(cls.id == _id).values(**kwargs).returning(cls)
        new_obj = db.execute(query)
        cls.commit()
        db.expire_all()
        return new_obj.scalar()

    @classmethod
    def delete(cls, _id):
        query = sqlalchemy_delete(cls).where(cls.id == _id).returning(cls)
        new_obj = db.execute(query)
        cls.commit()
        db.expire_all()
        return new_obj.scalar()

    @classmethod
    def truncate(cls):
        query = sqlalchemy_delete(cls).returning(cls)
        new_obj = db.execute(query)
        cls.commit()
        return new_obj.scalars()

    # 🔹 New filter method
    @classmethod
    def filter(cls, *conditions, **kwargs):
        """
        Filter records by conditions or keyword arguments.
        Example:
            User.filter(User.age > 21, is_active=True)

            # Get all active users
            users = User.filter(is_active=True)

            # Get users older than 30
            users = User.filter(User.age > 30)

            # Combine both
            users = User.filter(User.age > 30, is_active=True)
        """
        query = sqlalchemy_select(cls)

        # Handle explicit conditions (like User.age > 21)
        if conditions:
            for cond in conditions:
                query = query.where(cond)

        # Handle keyword filters (like is_active=True)
        for key, value in kwargs.items():
            if hasattr(cls, key):
                query = query.where(getattr(cls, key) == value)

        db.expire_all()
        results = db.execute(query)
        return results.scalars()


class Model(AbstractClass, Base):
    __abstract__ = True


class Channel(Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    chat_id: Mapped[str] = mapped_column(String(255))
    link: Mapped[str] = mapped_column(String(255), unique=True)


class Region(Model):  # Viloyat
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    districts: Mapped[list['District']] = relationship('District', back_populates='region')


class District(Model):  # Tuman
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    region_id: Mapped[int] = mapped_column(ForeignKey('regions.id', ondelete='CASCADE'))
    region: Mapped['Region'] = relationship('Region', back_populates='districts')

    @classmethod
    def get_by_region_id(cls, _id):
        query = sqlalchemy_select(cls).where(cls.region_id == _id)
        db.expire_all()
        results = db.execute(query)
        return results.scalars()


class User(Model):
    class Type(enum.Enum):
        ADMIN = 'admin'
        USER = 'user'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    type: Mapped[Type] = mapped_column(Enum(Type), server_default=Type.USER.name)
    username: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @classmethod
    def get_or_create(cls, **kwargs) -> tuple['User', bool]:
        user = cls.get(kwargs.get('id'))
        if user is None:
            user = cls.create(**kwargs)
            return user, True
        return user, False

    @property
    def is_admin(self) -> bool:
        return self.type == self.Type.ADMIN
