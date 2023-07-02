import asyncio
import logging

from uuid import uuid4

from nats import connect
from nats.js.client import JetStreamContext
from nats.js.object_store import ObjectStore
from nats.errors import TimeoutError

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.types import BufferedInputFile

from bot.config_reader import Settings


logging.basicConfig(level=logging.INFO)


async def worker(bot: Bot, js: JetStreamContext, storage: ObjectStore):
    sub = await js.subscribe("bot.photo.converter.out")
    while True:
        try:
            msg = await sub.next_msg()
            logging.info(f"msg from worker, {msg}")
            storage_info = await storage.get(name=msg.headers["uid_key"])
            await bot.send_photo(
                chat_id=int(msg.headers["user_id"]),
                photo=BufferedInputFile(storage_info.data, filename="filename.jpg")
            )
            await msg.ack()
        except TimeoutError:
            logging.info("bot timeout")


async def get_photo(m: Message, bot: Bot, storage: ObjectStore, js: JetStreamContext):
    file = await bot.download(m.photo[-1])
    uid_key = uuid4().hex
    await storage.put(
        name=uid_key,
        data=file.read(),
    )
    await js.publish(
        subject="bot.photo.converter.in",
        headers={"user_id": str(m.from_user.id), "uid_key": uid_key}
    )


async def main() -> None:
    config = Settings()
    bot = Bot(config.bot_token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher()

    nc = await connect()
    js = nc.jetstream()

    # await js.create_object_store("photos")
    # await js.create_object_store("ready_photos")

    storage = await js.object_store("photos")
    storage_ready = await js.object_store("ready_photos")
    dp.message.register(get_photo, F.photo)
    await asyncio.gather(
        worker(bot, js, storage_ready),
        dp.start_polling(bot, storage=storage, js=js)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
