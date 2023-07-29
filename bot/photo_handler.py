import asyncio
import logging
from functools import partial
from io import BytesIO
from uuid import uuid4

from nats import connect
from nats.aio.msg import Msg
from nats.js.client import JetStreamContext
from nats.js.object_store import ObjectStore
from PIL import Image, ImageDraw, ImageFont


def process_photo(image_bytes: bytes):
    image = Image.open(BytesIO(image_bytes))
    d1 = ImageDraw.Draw(image)
    font = ImageFont.truetype("roboto.ttf", 40)
    d1.text(xy=(10, 10), text="XYI", font=font, fill=(255, 0, 0))
    buff = BytesIO()
    image.save(buff, format="JPEG")
    buff.seek(0)
    return buff.read()


logging.basicConfig(level=logging.INFO)


async def worker(
    msg: Msg, storage: ObjectStore, second_storage: ObjectStore, js: JetStreamContext
):
    logging.info(f"msg from bot, {msg}")
    storage_info = await storage.get(name=msg.headers["uid_key"])
    processed_photo = process_photo(storage_info.data)
    await storage.delete(name=msg.headers["uid_key"])
    uid_key = uuid4().hex
    await asyncio.sleep(5)
    headers = {
        "uid_key": uid_key,
        "user_id": msg.headers["user_id"],
        "Nats-Msg-Id": uid_key,
    }
    await second_storage.put(
        name=uid_key,
        data=processed_photo,
    )
    await js.publish("bot.photo.converter.out", headers=headers)
    await msg.ack()


async def main():
    nc = await connect()
    js = nc.jetstream()
    storage = await js.object_store("photos")
    second_storage = await js.object_store("ready_photos")
    sub = await js.subscribe(
        "bot.photo.converter.in",
        cb=partial(worker, storage=storage, second_storage=second_storage, js=js),
    )
    try:
        await asyncio.Event().wait()
    finally:
        await sub.unsubscribe()


asyncio.run(main())
