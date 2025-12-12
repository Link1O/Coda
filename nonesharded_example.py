from Coda import *
import asyncio

client = Client(
    "YOUR_TOKEN",
    intents=intents_base.ALL,
    prefix="!",
    debug=True,
)


async def main():
    await client.setup()

    @client.on_ready
    async def on_ready_event():
        await client.change_presence(
            presence_status_base.DND, f"running an unsharded Client!"
        )

    @client.command()
    async def hello(ctx: base_handler):
        await ctx.reply("Hello, world")

    await client.connect()


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()
