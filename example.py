from Coda import *
import asyncio
shard_manager = ShardManager(
    "MTE1NTkwMTM1NDAzMjc1ODk0Nw.G4TCrP.KL-Kj7VwwiI7LfeLlAU4vbLgLF_2E6lJ7B9IuE", # your token, should look like this (this token is just a place holder!)
    intents=intents_base.ALL,
    prefix="h!",
    shard_count=3,
    debug=True
)
async def main():
    await shard_manager.register()
    def bind_handlers(shard):
        @shard.on_ready
        async def on_ready_event():
            print(shard.shard_id)
            await shard.change_presence(presence_status_base.DND, f"shard no: {shard.shard_id}")
        @shard.command("shrd")
        async def shrd(ctx: handler_base):
            await ctx.reply(content=str(shard.shard_id))
    for shard in shard_manager.shards:
        bind_handlers(shard)
    await shard_manager.connect()
loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()
