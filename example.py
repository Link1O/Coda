from Coda.core.http import ShardManager
from Coda.core.handler_base import handler_base
from Coda.core.constants import *
import asyncio

shard_manager = ShardManager("your-token", intents=intents_base.ALL, prefix="h!", shard_count=2, debug=True)

async def main():
    await shard_manager.start()

# Bind commands and events to all shards
for shard in shard_manager.shards:
    @shard.command("say")
    async def cmd(handler: handler_base, value):
        await handler.reply(value)

    @shard.on_ready
    async def on_ready_event():
        await shard.change_presence(presence_status_base.DND, f"Shard {shard.shard_id}", type=presence_type_base.PLAYING)

loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()
