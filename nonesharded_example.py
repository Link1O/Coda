from Coda import Client, Intents, Event, PresenceStatus, Interaction
import asyncio
from dotenv import load_dotenv
from os import environ

load_dotenv()

client = Client(
    str(environ.get("TOKEN")),
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
        message = await ctx.respond("Hello, world")
        await message.author.test()

    await client.connect()


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()
