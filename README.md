## Configurin Nats
You must create the first stream for the worker with this subject `bot.photo.converter.in`

And one more for a bot with such a subject
`bot.photo.converter.out`

To do that you can use that repository

And two ObjectStorages `photo`, `ready_photos`

https://github.com/Vermilonik/HowCreateStreamAndConsumerNats


# Start

Run Bot `python -m bot`

Run Worker `python bot\photo_handler.py`