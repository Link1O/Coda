from Coda.core.http import WebSocket_Handler
from Coda.core.handler_base import handler_base
from Coda.core.embed_base import embed_base
from Coda.core.constants import *
import asyncio
bot = WebSocket_Handler("your-token", intents=intents_base.ALL, prefix="h!", debug=True)
async def main(): await bot.connect()
@bot.command("say")
async def cmd(handler: handler_base, value):
    await handler.reply(value)
@bot.on_ready
async def on_ready_event():
    await bot.change_presence(presence_status_base.DND, "hello", type=presence_type_base.PLAYING)
loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()
