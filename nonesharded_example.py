from Coda import Client, Intents, Event, PresenceStatus, Interaction
import asyncio

client = Client(
    "YOUR_TOKEN",
    intents=Intents.ALL,
    prefix="!",
    debug=True,
)


async def main():
    await client.register()

    @client.event(Event.READY)
    async def on_ready_event():
        await client.change_presence(
            status=PresenceStatus.DND, value=f"running an unsharded Client!"
        )

    @client.slash_command()
    async def hello(ctx: Interaction):
        await ctx.reply("Hello, world")

    await client.connect()


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()
