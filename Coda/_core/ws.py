import asyncio
import threading
from aiohttp import ClientSession, ClientConnectionError, WSMsgType
import zlib
import orjson
from os import name as _os_name
from colorama import Fore
from typing import Union, Iterable, NoReturn
from datetime import datetime, UTC
from .constants import __base_url__, intents_base
from .handlers import base_handler, channel_base_handler, _handle_status_code
from ..type_errors import UnSufficientArguments


class Reloop(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class HeartBeats_Handler:
    def __init__(self) -> None: ...


async def _fetch_gateway_and_bot_info(session: ClientSession, token: str):
    resp1, resp2 = await asyncio.gather(
        session.get(f"{__base_url__}gateway"),
        session.get(
            f"{__base_url__}users/@me", headers={"Authorization": f"Bot {token}"}
        ),
    )
    async with resp1:
        data1 = await resp1.json(loads=orjson.loads)
    async with resp2:
        data2 = await resp2.json(loads=orjson.loads)
    return data1, data2


class ShardedClient:
    """
    WARNING:
    This is the python fallback for the Cython sharding implementation, it is recommended to only use this when faced with compatibillity issues or if it is
    general preference because it's most likely few features behind.
    """

    def __init__(
        self,
        token: str,
        intents: Union[Iterable[intents_base], int],
        prefix: str,
        shard_count: int,
        debug: bool = False,
        compress: bool = True,
        session: ClientSession = None,
    ):
        self.token = token
        self.intents = intents
        self.prefix = prefix
        self.shard_count = shard_count
        self._debug = debug
        self._compress = compress
        self.session = session
        self.shards = []

    async def register(self):
        print(
            f"{Fore.RED}the python fallback for the Cython sharding implementation is being run.{Fore.RESET}"
        )
        if not self.session:
            self.session = ClientSession(raise_for_status=True)
        gatway_data, bot_info = await _fetch_gateway_and_bot_info(
            self.session, self.token
        )
        for shard_id in range(self.shard_count):
            shard = WebSocket_Handler(
                token=self.token,
                intents=self.intents,
                prefix=self.prefix,
                debug=self._debug,
                compress=self._compress,
                _gatway_data=gatway_data,
                _bot_info=bot_info,
                _shard_id=shard_id,
                _shard_count=self.shard_count,
                session=self.session,
            )
            self.shards.append(shard)

    async def connect(self, grace_period: int = 3):
        for shard in self.shards:
            asyncio.create_task(shard.connect())
            await asyncio.sleep(grace_period)

    async def stop(self):
        for shard in self.shards:
            if shard.ws:
                await shard.ws.close()
        await self.session.close()
        print(f"coda: {Fore.RED}All shards stopped.{Fore.RESET}")


class WebhookHandler:
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
        if not any([content, username, avatar_url, embed, embeds]):
            raise Exception("no argument passed")
        payload = {}
        if content:
            payload["content"] = content
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url
        if embeds:
            payload["embeds"] = embeds

        async with self.session.post(
            self.webhook_url, json=payload
        ) as response:
            await _handle_status_code(response.status)
            return await response.json(loads=orjson.loads)

    async def info(self):
        async with self.session.get(self.webhook_url) as response:
            await _handle_status_code(response.status)
            return await response.json(loads=orjson.loads)

    async def delete_message(self, message_id: int):
        async with self.session.delete(f"{self.webhook_url}/messages/{message_id}") as response:
            await _handle_status_code(response.status)
            return True


class WebSocket_Handler:

    def __init__(
        self,
        token: str,
        intents: Union[Iterable[intents_base], int],
        prefix: str,
        debug: bool = False,
        compress: bool = True,
        session=None,
        _gatway_data: dict = None,
        _bot_info: dict = None,
        _shard_id: int = 0,
        _shard_count: int = 1,
    ) -> None:
        self._auth = f"Bot {token}"
        if isinstance(intents, Iterable):
            self.intents = sum(intent.value for intent in intents)
        else:
            self.intents = intents.value
        self.prefix = prefix
        self._debug = debug
        self.decompresser = zlib.decompressobj() if compress else None
        self.session = session
        if _gatway_data:
            self.gateway_url = _gatway_data["url"]
        else:
            self.gateway_url = None
        if _bot_info:
            self.id = _bot_info["id"]
            self.user_name = _bot_info["username"]
            self.bio = _bot_info.get("bio", "")
        else:
            self.id = None
            self.user_name = None
            self.bio = ""
        self.shard_id = _shard_id
        self.shard_count = _shard_count
        self.ws = None
        self._events_tree = {}
        self._command_tree = {}

    async def _create_ws_connection(self):
        self.ws = (
            await self.session.ws_connect(
                f"{self.gateway_url}/?v=10&encoding=json&compress=zlib-stream",
                max_msg_size=0,
            )
            if self.decompresser
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
                            "os": _os_name,
                            "browser": "coda",
                            "device": "coda",
                        },
                    },
                }
            )
        )

    async def connect(self) -> Union[None, NoReturn]:
        await self._create_ws_connection()
        await self._identify()
        print(
            f"coda: {Fore.GREEN}Shard {self.shard_id}/{self.shard_count}{Fore.RESET} connected to the{Fore.GREEN} gateway successfully{Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]"
        )
        if "on_setup" in self._events_tree:
            await self._trigger(self._events_tree["on_setup"])
        await self._ws_loop()

    async def _reconnect_to_ws(self) -> None:
        self._keep_alive_task.cancel()
        await self.ws.close()
        await self._create_ws_connection()
        print(
            f"coda: {Fore.LIGHTGREEN_EX}Shard {self.shard_id}/{self.shard_count} reconnected{Fore.RESET} to the{Fore.GREEN} gateway successfully{Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]"
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
            f"coda: {Fore.LIGHTGREEN_EX}Shard {self.shard_id}/{self.shard_count} resumed connection{Fore.RESET} to the{Fore.GREEN} gateway successfully{Fore.RESET} [{datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}]"
        )

    async def _ws_loop(self) -> None:
        async for msg in self.ws:
            try:
                if msg.type == WSMsgType.BINARY:
                    data: dict = orjson.loads(self.decompresser.decompress(msg.data))
                elif msg.type == WSMsgType.TEXT:
                    data: dict = orjson.loads(msg.data)  # if you request no compression
                elif msg.type == WSMsgType.ERROR:
                    print(
                        f"coda: {Fore.RED}Shard {self.shard_id}/{self.shard_count} websocket error: {msg.data}{Fore.RESET}"
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
                                base_handler(
                                    session=self.session,
                                    auth=self._auth,
                                    content=data["d"]["content"],
                                    id=data["d"]["id"],
                                    guild_id=data["d"]["guild_id"],
                                    channel_id=data["d"]["channel_id"],
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
                                    await self._trigger(
                                        command_data["coro"],
                                        base_handler(
                                            session=self.session,
                                            auth=self._auth,
                                            content=data["d"]["content"],
                                            id=data["d"]["id"],
                                            guild_id=data["d"]["guild_id"],
                                            channel_id=data["d"]["channel_id"]
                                        ),
                                        *args,
                                    )
                                else:
                                    raise UnSufficientArguments(
                                        f"coda: not enough arguments passed. Required: {req_arg_count}"
                                        if prov_args_count_len < req_arg_count
                                        else f"coda: arguments limit exceeded. Max: {max_arg_count}"
                                    )
                    if data["t"] == "MESSAGE_DELETE":
                        if "on_message_delete" in self._events_tree:
                            await self._trigger("")
                elif data["op"] == 7:  # Reconnect & resume
                    await self._reconnect_to_ws()
                    await self._resume()
                    print(
                        f"coda: {Fore.GREEN}Shard {self.shard_id}/{self.shard_count} reconnected & resumed{Fore.RESET} to the {Fore.GREEN} gateway successfully {Fore.RESET} [{datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}]"
                    )
                    self.decompresser = zlib.decompressobj()
                    asyncio.create_task(self._ws_loop())
                    return
                elif data["op"] == 9:  # invalid session
                    print(
                        f"coda: {Fore.YELLOW}Shard {self.shard_id}/{self.shard_count} invalid session"
                    )
                    if data["d"]:
                        await self._resume()
                    else:
                        await self._reconnect_to_ws()
                        await self._identify()
                        self.decompresser = zlib.decompressobj()
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
                            f"coda [debug]:{Fore.LIGHTCYAN_EX} Shard {self.shard_id}/{self.shard_count} heartbeat{Fore.RESET} was{Fore.GREEN} successful {Fore.RESET} [{datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}]"
                        )
                else:
                    print(
                        f"coda: {Fore.RED}Shard {self.shard_id}/{self.shard_count} unhandled operation code. ({data["op"]}){Fore.RESET}"
                    )
            except ClientConnectionError:
                print(
                    f"coda: {Fore.RED}Shard {self.shard_id}/{self.shard_count} connection lost!{Fore.RESET} [{datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}]"
                )
                break
            except Exception as e:
                print(
                    f"coda: {Fore.RED}Shard {self.shard_id}/{self.shard_count} unexpected error: {e}{Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]"
                )

    async def _keep_alive(self, heartbeat_interval: int) -> None:
        while True:
            await asyncio.sleep(heartbeat_interval)
            await self.ws.send_bytes(orjson.dumps({"op": 1, "d": self._last_sequence}))
            if self._debug:
                print(
                    f"coda [debug]: Shard {self.shard_id}/{self.shard_count} Heartbeat{Fore.LIGHTCYAN_EX} sent{Fore.RESET}"
                )

    async def change_presence(
        self, status: str, value: str = None, type: int = 0, **kwargs
    ):
        await self.ws.send_bytes(
            orjson.dumps(
                {
                    "op": 3,
                    "d": {
                        "status": status,
                        "afk": False,
                        "since": None,
                        "activities": [
                            {"name": value, "type": type, "url": kwargs.get("url")}
                        ],
                    },
                }
            )
        )

    async def get_webhook(self, webhook_url: str) -> WebhookHandler:
        return WebhookHandler(self.session, webhook_url)
    
    async def get_channel(self, channel_id: int):
        async with self.session.get(
            f"{__base_url__}channels/{channel_id}",
            headers={"Authorization": self._auth}
            ) as response:
            await _handle_status_code(response.status)
            data = await response.json(loads=orjson.loads)
            return channel_base_handler(
                tree=data, session=self.session, id=data["id"], auth=self._auth
            )

    def on_setup(self, coro: callable):
        self._events_tree["on_setup"] = coro

    def on_ready(self, coro: callable):
        self._events_tree["on_ready"] = coro

    def on_message(self, coro: callable):
        self._events_tree["on_message"] = coro

    def on_message_delete(self, coro: callable):
        self._events_tree["on_message_delete"] = coro

    def command(self, name: str = None):
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

        return wrapper

    async def _trigger(self, target: callable, *args):
        asyncio.create_task(target(*args))


class Client(WebSocket_Handler):
    """
    A simple Discord client without sharding.
    """

    def __init__(
        self,
        token: str,
        intents: Union[Iterable[intents_base], int],
        prefix: str = "",
        debug: bool = False,
        compress: bool = True,
        session: ClientSession = None,
    ):
        self.token = token
        super().__init__(
            token=token,
            intents=intents,
            prefix=prefix,
            debug=debug,
            compress=compress,
            session=session,
            _gatway_data=None,
            _bot_info=None,
            _shard_id=0,
            _shard_count=1,
        )
        self.session = session

    async def setup(self):
        if self.session is None:
            self.session = ClientSession(raise_for_status=True)

        gateway_data, bot_info = await _fetch_gateway_and_bot_info(
            self.session, self.token
        )
        self.gateway_url = gateway_data["url"]
        self.id = bot_info["id"]
        self.user_name = bot_info["username"]
        self.bio = bot_info.get("bio", "")

    async def connect_client(self):
        await self.setup()
        await self.connect()

    async def stop_client(self):
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
        print(f"coda: {Fore.RED}Client stopped.{Fore.RESET}")
