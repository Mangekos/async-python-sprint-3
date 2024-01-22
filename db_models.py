from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_async_engine("sqlite+aiosqlite:///chat.db")
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


Base = declarative_base()


class Messages(Base):
    __tablename__ = "messages"
    id = Column(Integer(), primary_key=True)
    sender = Column(String(200))
    receiver = Column(String(200))
    message = Column(String())
    timestamp = Column(Integer())


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer(), primary_key=True)
    nickname = Column(String(200), unique=True)
    password = Column(String(200))


class Warnings(Base):
    __tablename__ = "warnings"
    id = Column(Integer(), primary_key=True)
    sender = Column(String(200))
    receiver = Column(String(200))
    timestamp = Column(Integer())
