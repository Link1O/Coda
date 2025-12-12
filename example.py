from Coda import ShardedClient, intents_base, presence_status_base, base_handler
import asyncio

sharded_client = ShardedClient(
    "YOUR_TOKEN",
    intents=intents_base.ALL,
    prefix="s!",
    shard_count=2,
    debug=True,
)


async def main():
    await sharded_client.register()

    def bind_handlers(shard):
        @shard.on_ready
        async def on_ready_event():
            print(shard.shard_id)
            await shard.change_presence(
                presence_status_base.DND, f"shard no: {shard.shard_id}"
            )

        @shard.command()
        async def shrd(ctx: base_handler):
            await ctx.reply(f"currently on shard no: {str(shard.shard_id)}")
    for shard in sharded_client.shards:
        bind_handlers(shard)
    await sharded_client.connect()


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()
