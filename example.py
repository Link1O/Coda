from Coda.core.http import WebSocket_Handler
from Coda.core.handler_base import handler_base
from Coda.core.embed_base import embed_base
from ..core.constants import *
import asyncio
bot = WebSocket_Handler("MTE2NjAxMzg5MTQ0MTA4NjU0Ng.GFIIMz.yXhdqlj1g-jmopbzhwHNF1IAFTK3Gj1NgY6SPk", intents=intents_base.ALL, prefix="h!", debug=True)
async def main(): await bot.connect()
@bot.command("do")
async def cmd(handler: handler_base, value):
    print(value)
    await handler.reply("...")
@bot.on_ready
async def ss():
    print("hello")
    await bot.change_presence(presence_status_base.DND, "hello", type=presence_type_base.PLAYING)
loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()
