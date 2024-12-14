# coda

Coda is a straightforward and efficient framework for creating Discord bots and managing webhooks using Python. It made for developers seeking a quick and user-friendly solution that conserves memory and maintains performance.

## Features 

- **Built In Command And Component Handler**: Quickly set up and organize your bot commands and components without the need to install external library's.
- **Fast JSON Processing**: Utilizes [orjson](https://github.com/ijl/orjson) for speedy JSON encoding and decoding.
- **Minimal Memory Usage**: Designed to use less RAM compared to other Python-based Discord frameworks.
- **Optimized for speed**: Ensure your bot runs smoothly and responsively, even on limited resources.

## Installation  

### Requirements  

- **Python 3.8+**: Ensure you have Python version 3.8 or higher installed.  
- **Discord Bot Token**: Obtain your bot’s token from the [Discord Developer Portal](https://discord.com/developers/applications).  

### Steps 

#### method 1


#### method 2 ( For Rolling Releases )

```bash
pip install git+https://github.com/Link1O/Coda.git 
```

## Quick Start  

To get your bot operational quickly:

1. Create a Python file, for example, `main.py`, and set up your bot: 

    ```python
    from coda import Client

    bot = Client(prefix="!", token="your-discord-bot-token")

    @bot.command()
    async def hello(ctx):
        await ctx.send("Hello, world!")

    bot.run()
    ``` 

2. Start your bot:

    ```bash
    python main.py
    ```  

Your bot will now reply to `!hello` with "Hello, world!"  

Coda simplifies the process—create fast, lightweight bots with minimal effort.