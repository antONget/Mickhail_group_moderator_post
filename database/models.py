from sqlalchemy import String, Integer, BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine


# Создаем асинхронный движок
engine = create_async_engine("sqlite+aiosqlite:///database/db.sqlite3", echo=False)
# Настраиваем фабрику сессий
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class ChatAction(Base):
    __tablename__ = 'chat_actions'
    tg_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    type: Mapped[str] = mapped_column(String(50))
    added = mapped_column(DateTime)


class ChatUser(Base):
    __tablename__ = 'chat_users'
    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(200))
    last_name: Mapped[str] = mapped_column(String(200))
    user_name: Mapped[str] = mapped_column(String(100))
    reputation: Mapped[int] = mapped_column(BigInteger)
    total_help: Mapped[int] = mapped_column(BigInteger)
    mutes: Mapped[int] = mapped_column(BigInteger)
    last_rep_boost = mapped_column(DateTime)
    last_help_boost = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30))


class Group(Base):
    __tablename__ = 'group'
    tg_id: Mapped[int] = mapped_column(primary_key=True)
    peer_id: Mapped[int] = mapped_column(Integer)
    type_group: Mapped[str] = mapped_column(String)
    peer_id_test: Mapped[int] = mapped_column(Integer)


class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    type_order: Mapped[str] = mapped_column(String)
    create_tg_id: Mapped[int] = mapped_column(BigInteger)
    description: Mapped[str] = mapped_column(String)
    photo: Mapped[str] = mapped_column(String)
    info: Mapped[str] = mapped_column(String)
    chat_message: Mapped[str] = mapped_column(String, default="0")
    time_publish: Mapped[str] = mapped_column(String, default="0")
    status: Mapped[str] = mapped_column(String)


class User(Base):
    __tablename__ = 'users'
    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(100))


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
