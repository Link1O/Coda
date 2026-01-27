# Coda
High-performance, lightweight Python framework for Discord.

## Features
- **Proactive Rate Limiting**: Uses bucket tracking to prevent 429s.
- **Interaction-Aware Messages**: Unified `Message` class with automatic interaction follow-up logic.
- **Full Interaction Support**: Built-in handlers for slash commands, buttons, select menus, and modals.
- **Internal Cache**: Optimized channel and guild caching.
- **Performance**: Low memory footprint and `orjson` integration.

## Install
`pip install git+https://github.com/Link1O/Coda.git`

## Quick Start
```python
from Coda import Client, Intents, PresenceStatus, Interaction
import asyncio

client = Client(
    "YOUR_TOKEN",
    intents=Intents.ALL,
    prefix="!",
    debug=True,
)


async def main():
    await client.register()

    @client.on_ready
    async def on_ready_event():
        await client.change_presence(
            status=PresenceStatus.DND,
            value=f"running an unsharded Client!"
        )

    @client.slash_command()
    async def hello(ctx: Interaction):
        await ctx.reply("Hello, world")

    await client.connect()


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()

```

### Citation
Langa, Ł., & contributors to Black. *Black: The uncompromising Python code formatter* [Computer software]. https://github.com/psf/black