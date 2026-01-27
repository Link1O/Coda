import asyncio
from aiohttp import ClientSession, ClientConnectionError, WSMsgType
import zlib
import orjson
from os import name as os_name
from colorama import Fore
from typing import Union, Iterable, List, NoReturn
from datetime import datetime, UTC
from .constants import __base_url__, PresenceStatus, PresenceType, Intents, InteractionType
from .entities import Channel, Message
from .interactions import Interaction
from .models import Guild, Option, Poll
from .http import _request
from .exceptions import UnSufficientArguments


class Reloop(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class HeartBeatsHandler:
    def __init__(self) -> None: ...


async def FetchClientData(session: ClientSession, auth: str):
    data1, data2 = await asyncio.gather(
        _request(session, "GET", f"{__base_url__}gateway"),
        _request(session, "GET", f"{__base_url__}users/@me", headers={"Authorization": auth})
    )
    return data1, data2


class ShardedClient:
    """
    WARNING:
    This is the python fallback for the Cython sharding implementation, it is recommended to only use this when faced with compatibility issues or if it is
    general preference because it's most likely few features behind.
    """

    def __init__(
        self,
        token: str,
        intents: Union[Iterable[Intents], int],
        prefix: str,
        shard_count: int,
        debug: bool = False,
        compress: bool = True,
        session: ClientSession = None,
    ):
        self.intents = intents
        self.prefix = prefix
        self.shard_count = shard_count
        self._debug = debug
        self._compress = compress
        self.session = session
        self.shards = []
        self._auth = f"Bot {token}"

    async def register(self):
        """
        Initialize the shards based on the provided shard count.
        Fetches gateway and client info before spawning WebSocket instances.
        """
        print(
            f"{Fore.RED}The python fallback for the Cython sharding implementation is being run.{Fore.RESET}"
        )
        if not self.session:
            self.session = ClientSession(headers={
                    "authorization": self._auth,
                    "content-type": "application/json",  
                })
        gateway_data, client_info = await FetchClientData(
            self.session, self._auth
        )
        for shard_id in range(self.shard_count):
            shard = WebSocket(
                intents=self.intents,
                prefix=self.prefix,
                debug=self._debug,
                compress=self._compress,
                _gateway_data=gateway_data,
                _client_info=client_info,
                _shard_id=shard_id,
                _shard_count=self.shard_count,
                session=self.session,
                auth=self._auth,
            )
            self.shards.append(shard)

    async def connect(self, grace_period: int = 3):
        """
        Start the connection loop for all registered shards.
        
        Args:
            grace_period (int): Seconds to wait between starting each shard to avoid identify 429s.
        """
        for shard in self.shards:
            asyncio.create_task(shard.connect())
            await asyncio.sleep(grace_period)

    async def stop(self):
        """
        Stop all shards and close the HTTP session.
        """
        for shard in self.shards:
            if shard.ws:
                await shard.ws.close()
        await self.session.close()
        print(f"Coda: {Fore.RED}All shards stopped.{Fore.RESET}")


class Webhook:
    """
    Represents a Discord Webhook.
    Provides methods for sending messages, getting info, and deleting messages via a webhook URL.
    """
    def __init__(self, session: ClientSession, webhook_url: str):
        self.session = session
        self.webhook_url = webhook_url

    async def send(
        self,
        content: str = None,
        username: str = None,
        avatar_url: str = None,
        embed: dict = None,
        embeds: list = None,
    ):
        """
        Send a message via the webhook.
        """
        if not any([content, username, avatar_url, embed, embeds]):
            raise Exception("No argument passed")
        payload = {}
        if content:
            payload["content"] = content
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url
        if embeds:
            payload["embeds"] = embeds

        return await _request(self.session, "POST", self.webhook_url, json=payload)

    async def info(self):
        return await _request(self.session, "GET", self.webhook_url)

    async def delete_message(self, message_id: int):
        await _request(self.session, "DELETE", f"{self.webhook_url}/messages/{message_id}")
        return True


class WebSocket:
    """
    Represents a single shard connection to the Discord Gateway.
    Handles events, heartbeats, and command dispatching.
    """
    def __init__(
        self,
        intents: Union[Iterable[Intents], int],
        prefix: str,
        debug: bool = False,
        compress: bool = True,
        session=None,
        _gateway_data: dict = None,
        _client_info: dict = None,
        _shard_id: int = 0,
        _shard_count: int = 1,
        **kwargs,
    ) -> None:
        if isinstance(intents, Iterable):
            self.intents = sum(intent.value for intent in intents)
        else:
            self.intents = intents.value
        self.prefix = prefix
        self._debug = debug
        self.decompressor = zlib.decompressobj() if compress else None
        self.session = session
        if _gateway_data:
            self.gateway_url = _gateway_data["url"]
        else:
            self.gateway_url = None
        if _client_info:
            self.id = _client_info["id"]
            self.user_name = _client_info["username"]
            self.bio = _client_info.get("bio", "")
        else:
            self.id = None
            self.user_name = None
            self.bio = ""
        self.shard_id = _shard_id
        self.shard_count = _shard_count
        self.kwargs = kwargs
        self._auth = kwargs.get("auth", None)
        self.ws = None
        self._events_tree = {}
        self._command_tree = {}
        self._slash_commands_tree = {}
        self._polls_tree = {}
        self._component_handlers = {}
        self._modal_handlers = {}
        self._channels = {}
        self._guilds = {}

    async def _create_ws_connection(self):
        self.ws = (
            await self.session.ws_connect(
                f"{self.gateway_url}/?v=10&encoding=json&compress=zlib-stream",
                max_msg_size=0,
            )
            if self.decompressor
            else await self.session.ws_connect(
                f"{self.gateway_url}/?v=10&encoding=json", max_msg_size=0
            )
        )

    async def _identify(self):
        await self.ws.send_bytes(
            orjson.dumps(
                {
                    "op": 2,
                    "d": {
                        "token": self._auth,
                        "intents": self.intents,
                        "shard": [self.shard_id, self.shard_count],
                        "properties": {
                            "os": os_name,
                            "browser": "Coda",
                            "device": "Coda",
                        },
                    },
                }
            )
        )

    async def connect(self, sync_app_commands: bool = True) -> Union[None, NoReturn]:
        await self._create_ws_connection()
        await self._identify()
        if sync_app_commands:
            await self.sync_commands()
        print(
            f"Coda: {Fore.GREEN}Shard {self.shard_id}/{self.shard_count}{Fore.RESET} connected to the {Fore.GREEN}gateway successfully{Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]"
        )
        if "on_setup" in self._events_tree:
            await self._trigger(self._events_tree["on_setup"])
        await self._ws_loop()

    async def _reconnect_to_ws(self) -> None:
        self._keep_alive_task.cancel()
        await self.ws.close()
        await self._create_ws_connection()
        print(
            f"Coda: {Fore.LIGHTGREEN_EX}Shard {self.shard_id}/{self.shard_count} reconnected{Fore.RESET} to the {Fore.GREEN}gateway successfully{Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]"
        )

    async def _resume(self) -> None:
        await self.ws.send_bytes(
            orjson.dumps(
                {
                    "op": 6,
                    "d": {
                        "token": self._auth,
                        "session_id": self.session_id,
                        "seq": self._last_sequence,
                    },
                }
            )
        )
        print(
            f"Coda: {Fore.LIGHTGREEN_EX}Shard {self.shard_id}/{self.shard_count} resumed connection{Fore.RESET} to the {Fore.GREEN}gateway successfully{Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]"
        )

    async def _ws_loop(self) -> None:
        async for msg in self.ws:
            try:
                if msg.type == WSMsgType.BINARY:
                    data: dict = orjson.loads(self.decompressor.decompress(msg.data))
                elif msg.type == WSMsgType.TEXT:
                    data: dict = orjson.loads(msg.data)  # No compression
                elif msg.type == WSMsgType.ERROR:
                    print(
                        f"Coda: {Fore.RED}Shard {self.shard_id}/{self.shard_count} websocket error: {msg.data}{Fore.RESET}"
                    )
                    break
                if data["op"] == 0:  # Dispatch
                    self._last_sequence = data["s"]
                    if data["t"] == "READY":
                        self._resume_gateway_url = data["d"]["resume_gateway_url"]
                        self.session_id = data["d"]["session_id"]
                        if "on_ready" in self._events_tree:
                            await self._trigger(self._events_tree["on_ready"])
                    if data["t"] == "MESSAGE_CREATE":
                        if "on_message" in self._events_tree:
                            await self._trigger(
                                self._events_tree["on_message"],
                                Message(
                                    tree=data["d"],
                                    session=self.session,
                                    auth=self._auth,
                                    channel=Channel(
                                        tree={"id": data["d"]["channel_id"]},
                                        session=self.session,
                                        id=data["d"]["channel_id"],
                                        auth=self._auth
                                    )
                                ),
                            )
                        if self._command_tree:
                            content = data.get("d", {}).get("content")
                            if not content:
                                return
                            cmd, *rest = content.split(" ", 1)
                            command_data = self._command_tree.get(cmd)
                            if command_data:
                                args = rest[0].split(" ") if rest else []
                                req_arg_count = (
                                    command_data["required_arguments_count"] - 1
                                )
                                max_arg_count = command_data["arguments_sum"] - 1
                                prov_args_count_len = len(args)
                                if prov_args_count_len in range(
                                    req_arg_count, max_arg_count + 1
                                ):
                                    channel = await self.get_channel(data["d"]["channel_id"])
                                    await self._trigger(
                                        command_data["coro"],
                                        Message(
                                            tree=data["d"],
                                            session=self.session,
                                            auth=self._auth,
                                            channel=channel
                                        ),
                                        *args,
                                    )
                                else:
                                    raise UnSufficientArguments(
                                        f"Coda: Not enough arguments passed. Required: {req_arg_count}"
                                        if prov_args_count_len < req_arg_count
                                        else f"Coda: Arguments limit exceeded. Max: {max_arg_count}"
                                    )
                    if data["t"] == "INTERACTION_CREATE":
                        if data["d"]["type"] == InteractionType.APPLICATION_COMMAND.value:
                            interaction = Interaction(self.session, data["d"], self._auth)
                            cmd_name = interaction.data.get("name")
                            if cmd_name in self._slash_commands_tree:
                                kwargs = {}
                                if "options" in interaction.data:
                                    for option in interaction.data["options"]:
                                        kwargs[option["name"]] = option["value"]
                                        
                                await self._trigger(
                                    self._slash_commands_tree[cmd_name]["coro"],
                                    interaction,
                                    **kwargs
                                )
                        elif data["d"]["type"] == InteractionType.MESSAGE_COMPONENT.value:
                            interaction = Interaction(self.session, data["d"], self._auth)
                            custom_id = interaction.data.get("custom_id")
                            if custom_id in self._component_handlers:
                                await self._trigger(
                                    self._component_handlers[custom_id],
                                    interaction
                                )
                        elif data["d"]["type"] == InteractionType.MODAL_SUBMIT.value:
                            interaction = Interaction(self.session, data["d"], self._auth)
                            custom_id = interaction.data.get("custom_id")
                            if custom_id in self._modal_handlers:
                                await self._trigger(
                                    self._modal_handlers[custom_id],
                                    interaction
                                )
                    
                    if data["t"] == "MESSAGE_UPDATE":
                        poll = Poll(data["d"].get("poll"))
                        if self._polls_tree.get(poll.question):
                            if poll and poll.results.is_finalized:
                                channel = self.get_channel(data["d"]["channel_id"])
                                await self._trigger(
                                    self._polls_tree[poll.question],
                                    poll,
                                    Message(
                                        tree=data["d"],
                                        session=self.session,
                                        auth=self._auth,
                                        channel=channel
                                    )
                                )
                    if data["t"] == "MESSAGE_DELETE":
                        if "on_message_delete" in self._events_tree:
                            await self._trigger("")
                    if data["t"] in ("GUILD_CREATE", "GUILD_UPDATE"):
                        guild_data = data["d"]
                        self._guilds[guild_data["id"]] = Guild(id=guild_data["id"])
                        if "channels" in guild_data:
                            for c in guild_data["channels"]:
                                self._channels[c["id"]] = Channel(tree=c, session=self.session, id=c["id"], auth=self._auth)
                    if data["t"] in ("CHANNEL_CREATE", "CHANNEL_UPDATE"):
                        c = data["d"]
                        self._channels[c["id"]] = Channel(tree=c, session=self.session, id=c["id"], auth=self._auth)
                elif data["op"] == 7:  # Reconnect & resume
                    await self._reconnect_to_ws()
                    await self._resume()
                    print(
                        f"Coda: {Fore.GREEN}Shard {self.shard_id}/{self.shard_count} reconnected & resumed{Fore.RESET} to the {Fore.GREEN}gateway successfully {Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]"
                    )
                    self.decompressor = zlib.decompressobj()
                    asyncio.create_task(self._ws_loop())
                    return
                elif data["op"] == 9:  # Invalid session
                    print(
                        f"Coda: {Fore.YELLOW}Shard {self.shard_id}/{self.shard_count} invalid session"
                    )
                    if data["d"]:
                        await self._resume()
                    else:
                        await self._reconnect_to_ws()
                        await self._identify()
                        self.decompressor = zlib.decompressobj()
                        asyncio.create_task(self._ws_loop())
                        return
                elif data["op"] == 10:  # Hello
                    self._keep_alive_task = asyncio.create_task(
                        self._keep_alive(
                            data.get("d", {}).get("heartbeat_interval") / 1000
                        )
                    )
                elif data["op"] == 11:
                    if self._debug:
                        print(
                            f"Coda [debug]:{Fore.LIGHTCYAN_EX} Shard {self.shard_id}/{self.shard_count} heartbeat{Fore.RESET} was{Fore.GREEN} successful {Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]"
                        )
                else:
                    print(
                        f"Coda: {Fore.RED}Shard {self.shard_id}/{self.shard_count} unhandled operation code. ({data['op']}){Fore.RESET}"
                    )
            except ClientConnectionError:
                print(
                    f"Coda: {Fore.RED}Shard {self.shard_id}/{self.shard_count} connection unsuccessful!{Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]"
                )
                break
                
            except Exception as e:
                print(
                    f"Coda: {Fore.RED}Shard {self.shard_id}/{self.shard_count} unexpected error: {e}{Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]"
                )

    async def _keep_alive(self, heartbeat_interval: int) -> None:
        while True:
            await asyncio.sleep(heartbeat_interval)
            await self.ws.send_bytes(orjson.dumps({"op": 1, "d": self._last_sequence}))
            if self._debug:
                print(
                    f"Coda [debug]: Shard {self.shard_id}/{self.shard_count} Heartbeat{Fore.LIGHTCYAN_EX} sent{Fore.RESET}"
                )

    async def change_presence(
        self, status: PresenceStatus, type: PresenceType = PresenceType.PLAYING, value: str = None, **kwargs
    ):
        """
        Change the bot's presence (status and activity).
        """
        await self.ws.send_bytes(
            orjson.dumps(
                {
                    "op": 3,
                    "d": {
                        "status": status.value,
                        "afk": False,
                        "since": None,
                        "activities": [
                            {"name": value, "type": type.value, "url": kwargs.get("url")}
                        ],
                    },
                }
            )
        )

    async def get_webhook(self, webhook_url: str) -> Webhook:
        return Webhook(self.session, webhook_url)
    
    async def get_channel(self, channel_id: int):
        """
        Retrieve a channel by ID. Checks the local cache first.
        """
        if channel_id in self._channels:
            return self._channels[channel_id]
            
        data = await _request(
            self.session,
            "GET",
            f"{__base_url__}channels/{channel_id}",
            headers={"Authorization": self._auth}
        )
        channel = Channel(
            tree=data, session=self.session, id=data["id"], auth=self._auth
        )
        self._channels[channel_id] = channel
        return channel

    def on_setup(self, coro: callable):
        """
        Decorator to register a setup event handler.
        """
        self._events_tree["on_setup"] = coro
        return coro

    def on_ready(self, coro: callable):
        """
        Decorator to register a ready event handler.
        """
        self._events_tree["on_ready"] = coro
        return coro

    def on_message(self, coro: callable):
        """
        Decorator to register a message event handler.
        """
        self._events_tree["on_message"] = coro
        return coro
    def on_message_delete(self, coro: callable):
        """
        Decorator to register a message delete event handler.
        """
        self._events_tree["on_message_delete"] = coro
        return coro

    def on_poll_end(self, poll_question: str = None):
        """
        Decorator to register a poll end event handler.
        """
        def wrapper(coro: callable):
            poll_question_ = poll_question or coro.__name__
            self._polls_tree[poll_question_] = coro
            return coro
        return wrapper

    def command(self, name: str = None):
        """
        Decorator to register a prefix-based command.
        """
        def wrapper(coro: callable):
            func_name = name or coro.__name__
            num_defaults = len(coro.__defaults__) if coro.__defaults__ else 0
            required_arguments_count = coro.__code__.co_argcount - num_defaults
            self._command_tree[self.prefix + func_name] = {
                "coro": coro,
                "required_arguments_count": required_arguments_count,
                "default_arguments_count": num_defaults,
                "arguments_sum": required_arguments_count + num_defaults,
            }
            return coro

        return wrapper

    def slash_command(self, name: str = None, description: str = "No description provided", options: List[Option] = None):
        """
        Decorator to register a slash (application) command.
        
        Note: These must be synced with Discord using `.sync_commands()`.
        """
        def wrapper(coro: callable):
            cmd_name = name or coro.__name__
            processed_options = []
            if options:
                for opt in options:
                    processed_options.append(opt.to_dict())
            
            self._slash_commands_tree[cmd_name] = {
                "coro": coro,
                "description": description,
                "name": cmd_name,
                "options": processed_options
            }
            return coro
        return wrapper

    def component(self, custom_id: str):
        """
        Decorator to register a handler for a specific message component (Button, Select).
        """
        def wrapper(coro: callable):
            self._component_handlers[custom_id] = coro
            return coro
        return wrapper

    def on_modal_submit(self, custom_id: str):
        """
        Decorator to register a handler for a specific modal submission.
        """
        def wrapper(coro: callable):
            self._modal_handlers[custom_id] = coro
            return coro
        return wrapper

    async def sync_commands(self):
        """
        Bulk overwrite global application commands with the local registration tree.
        """
        if not self._slash_commands_tree:
            return

        url = f"{__base_url__}applications/{self.id}/commands"
        
        # Prepare the payload list for all commands
        commands_payload = [
            {
                "name": data["name"],
                "description": data["description"],
                "type": 1,  # Chat Input
                "options": data["options"]
            }
            for data in self._slash_commands_tree.values()
        ]

        # Use PUT to bulk overwrite commands (Sync)
        resp = await _request(
            self.session,
            "PUT",
            url,
            json=commands_payload,
            headers={"Authorization": self._auth}
        )
        if resp:
            print(f"Coda: {Fore.GREEN}Successfully synced {len(commands_payload)} slash commands.{Fore.RESET}")


    async def _trigger(self, target: callable, *args, **kwargs):
        asyncio.create_task(target(*args, **kwargs))


class Client(WebSocket):
    """
    A simple Discord client without sharding.
    """

    def __init__(
        self,
        token: str,
        intents: Union[Iterable[Intents], int],
        prefix: str = "",
        debug: bool = False,
        compress: bool = True,
        session: ClientSession = None,
    ):
        self.session = session
        self._auth = f"Bot {token}"
        super().__init__(
            token=token,
            intents=intents,
            prefix=prefix,
            debug=debug,
            compress=compress,
            session=session,
            _gateway_data=None,
            _client_info=None,
            _shard_id=0,
            _shard_count=1,
            auth=self._auth,
        )

    async def register(self):
        self.session = ClientSession(headers={
                "authorization": self._auth,
                "content-type": "application/json",  
            })

        gateway_data, client_info = await FetchClientData(
            self.session, self._auth
        )
        self.gateway_url = gateway_data["url"]
        self.id = client_info["id"]
        self.user_name = client_info["username"]
        self.bio = client_info.get("bio", "")

    async def connect_client(self):
        await self.setup()
        await self.connect()

    async def stop_client(self):
        await self.ws.close()
        await self.session.close()
        print(f"coda: {Fore.RED}Client stopped.{Fore.RESET}")
