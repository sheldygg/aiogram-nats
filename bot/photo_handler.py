import asyncio
import logging

from io import BytesIO
from uuid import uuid4
from PIL import Image, ImageDraw, ImageFont

from nats import connect
from nats.errors import TimeoutError


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


async def main():
    nc = await connect()
    js = nc.jetstream()
    sub = await js.subscribe("bot.photo.converter.in")
    storage = await js.object_store("photos")
    second_storage = await js.object_store("ready_photos")
    while True:
        try:
            msg = await sub.next_msg()
            logging.info(f"msg from bot, {msg}")
            storage_info = await storage.get(name=msg.headers["uid_key"])
            processed_photo = process_photo(storage_info.data)
            uid_key = uuid4().hex
            await asyncio.sleep(5)
            headers = {"uid_key": uid_key, "user_id": msg.headers["user_id"]}
            await second_storage.put(
                name=uid_key,
                data=processed_photo,
            )
            await js.publish("bot.photo.converter.out", headers=headers)
            await msg.ack()
            logging.info("ask")
        except TimeoutError:
            logging.info("worker timeout")


asyncio.run(main())
