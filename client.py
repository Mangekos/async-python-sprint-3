import asyncio
import time
from typing import AsyncGenerator, Coroutine

from sqlalchemy import select

from db_models import Messages, Warnings, async_session
from my_logger import logger


class Client:
    """
    Class of client connections
    """

    def __init__(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        self.reader = reader
        self.writer = writer
        self.nickname = None
        self.last_message_time = 0
        self.banned_until = 0
        self.warnings = 0
        self.peername = writer.get_extra_info("peername")

    async def send(self, message: str) -> Coroutine:
        """
        Send message to self
        """
        if self.banned_until > time.time():
            await asyncio.sleep(self.banned_until - time.time())
            self.banned_until = 0
        if not self.banned_until:
            self.writer.write(message.encode() + b"\n")
            await self.writer.drain()

    async def send_history(
        self, message_expiry: int, message_limit: int
    ) -> Coroutine:
        """
        Send history of last messages
        """
        timestamp_limit = int(time.time()) - message_expiry
        async with async_session() as session:
            result = await session.execute(
                select(Messages)
                .where(
                    (Messages.timestamp > timestamp_limit)
                    & (
                        (Messages.receiver.is_(None))
                        | (Messages.receiver == self.nickname)
                        | (Messages.sender == self.nickname)
                    )
                )
                .order_by(Messages.timestamp.desc())
                .limit(message_limit)
            )
            history = result.fetchall()

        if history:
            history.reverse()
            await self.send("История последних сообщений:")
            for message_obj in history:
                message = message_obj[0]
                if message.receiver:
                    await self.send(
                        f"{message.sender} для "
                        f"{message.receiver}: "
                        f"{message.message}"
                    )
                else:
                    await self.send(f"{message.sender}: {message.message}")

    async def load_user_info(self, nickname: str) -> Coroutine:
        """
        Load users warning info
        """
        async with async_session() as session:
            result = await session.execute(
                select(Messages).where(
                    (Messages.receiver == nickname)
                    & (Messages.sender.is_(None))
                )
            )
            self.warnings = len(result.fetchall())

    async def already_voted(self, sender_nickname: str, duration: int) -> bool:
        """
        Check if sender already voted for ban in duration sec time
        """
        timestamp_limit = int(time.time()) - duration
        async with async_session() as session:
            result = await session.execute(
                select(Messages).where(
                    (Messages.sender == sender_nickname)
                    & (Messages.receiver == self.nickname)
                    & (Messages.timestamp > timestamp_limit)
                )
            )
            result = result.fetchone()
        return result is not None

    async def read_messages(self) -> AsyncGenerator:
        """
        Asynchronously reads messages and yields them.
        """
        try:
            current_message = ""
            while True:
                char = await self.reader.read(1)
                if not char:
                    continue
                char = char.decode()
                if char == "\n":
                    message = current_message.strip()
                    current_message = ""
                    if message:
                        self.last_message_time = int(time.time())
                        yield message
                else:
                    current_message += char
        except asyncio.CancelledError as err:
            logger.error(f"Connection cancelled \n{err}")

    async def add_warning(self, sender_nickname: str) -> Coroutine:
        """
        Add warning for a receiver
        """
        timestamp = int(time.time())
        async with async_session() as session:
            async with session.begin():
                warnings = Warnings(
                    sender=sender_nickname,
                    receiver=self.nickname,
                    timestamp=timestamp,
                )
                session.add(warnings)
                await session.commit()
        self.warnings += 1
