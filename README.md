# coda

Coda is a straightforward and efficient framework for creating Discord Clients and managing webhooks using Python. It is made for developers seeking a quick and user-friendly solution that conserves memory and maintains performance.

## Features 

- **Built In Command And *Component Handler***: Quickly set up and organize your bot commands and components without the need to install external library's.
- **Fast JSON Processing**: Utilizes [orjson](https://github.com/ijl/orjson) for speedy JSON encoding and decoding.
- **Low Memory Usage**: Designed to use minimal memory.
- **Speedy**: Ensure your Client runs smoothly, even on limited resources.

## Installation  

### Requirements  

- **Python 3.10+**: Ensure you have Python version 3.10 or higher installed.  
- **Discord Bot Token**: Obtain your bot’s token from the [Discord Developer Portal](https://discord.com/developers/applications).  

### Steps 

#### method 1 (pip)

*soon*
#### method 2 ( For Rolling Releases )

```bash
pip install git+https://github.com/Link1O/Coda.git 
```

## Quick Start  

To get your bot operational quickly:

1. Create a Python file, for example, `main.py`, and set up your bot: 

    ```python
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
                presence_status_base.DND, f"running a none-sharded Client!"
            )

        @client.command()
        async def hello(ctx: base_handler):
            await ctx.reply("hello, world")

        await client.connect()


    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
    ``` 

2. Start your Client:

    ```bash
    python main.py
    ```  

Your Client will now reply to `!hello` with "Hello, world!"  

Coda, a simple framework for your simple needs.

> **Note:** with the current incomplete state of the framework, it is recommended to only use it for low traffic purposes (eg: a custom Client for your own server)

### Citation
Langa, Ł., & contributors to Black. *Black: The uncompromising Python code formatter* [Computer software]. https://github.com/psf/black