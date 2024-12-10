import asyncio
import threading
from aiohttp import ClientSession, ClientConnectionError
import zlib
import orjson
# from inspect import signature
from os import name as _os_name
from colorama import Fore
from typing import (
    Union,
    Iterable,
    NoReturn
)
from datetime import datetime, UTC
# import time
from .constants import intents_base
from .handler_base import handler_base
from ..type_errors import UnSufficientArguments
__base_url__ = "https://discord.com/api/"


class Reloop(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class HeartBeats_Handler:
    def __init__(self) -> None:
        ...


class WebSocket_Handler:

    def __init__(self, token: str, intents: Union[Iterable[intents_base], int], prefix: str, debug: bool = False, **kwargs) -> None:
        if isinstance(intents, Iterable):
            self.intents = sum(intent.value for intent in intents)
        else:
            self.intents = intents.value
        self.decompresser = zlib.decompressobj()
        self._auth = f"Bot {token}"
        self.prefix = prefix
        self._debug = debug
        self._session = None
        self.ws = None
        self._events_tree = {}
        self._command_tree = {}

    async def _initialize(self):
        self._session = ClientSession(raise_for_status=True)

    async def _create_ws_connection(self):
        await self._fetch_gateway_url()
        self.ws = await self._session.ws_connect(f"{self.gateway_url}/?v=10&encoding=json&compress=zlib-stream")

    async def _identify(self):
        await self.ws.send_bytes(orjson.dumps({
            "op": 2,
            "d": {
                "token": self._auth,
                "intents": self.intents,
                "properties": {
                    "os": _os_name,
                    "browser": "Dissonance",
                    "device": "Dissonance"
                }
            }
        }))
    
    async def connect(self) -> Union[None, NoReturn]:
        await self._initialize()
        await self._create_ws_connection()
        await self._identify()
        print(f"dissonance: {Fore.GREEN}connected{Fore.RESET} to the{Fore.GREEN} gateway successfully{Fore.RESET} [{datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}]")
        await self._cache_client_info()
        if "on_setup" in self._events_tree:
            await self._trigger(self._events_tree["setup"])
        await self._ws_loop()

    async def _reconnect_to_ws(self) -> None:
        self._keep_alive_task.cancel()
        await self.ws.close()
        await self._create_ws_connection()
        print(f"dissonance: {Fore.LIGHTGREEN_EX}reconnected{Fore.RESET} to the{Fore.GREEN} gateway successfully{Fore.RESET} [{datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}]")

    async def _resume(self) -> None:
        await self.ws.send_bytes(orjson.dumps({
            "op": 6,
            "d": {
                "token": self._auth,
                "session_id": self._session_id,
                "seq": self._last_sequence
            }
        }))
        print(f"dissonance: {Fore.LIGHTGREEN_EX}resumed connection{Fore.RESET} to the{Fore.GREEN} gateway successfully{Fore.RESET} [{datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}]")

    async def _ws_loop(self) -> None:
        async for msg in self.ws:
            try:
                data: dict = orjson.loads(self.decompresser.decompress(msg.data))
                if data["op"] == 0: # Dispatch
                    self._last_sequence = data['s']
                    if data["t"] == "READY":
                        self._resume_gateway_url = data["d"]["resume_gateway_url"]
                        self._session_id = data["d"]["session_id"]
                        if "on_ready" in self._events_tree:
                            await self._trigger(self._events_tree["on_ready"])
                    if data["t"] == "MESSAGE_CREATE":
                        if "on_message" in self._events_tree:
                            await self._trigger(self._events_tree["on_message"], handler_base(session=self._session, auth=self._auth, data_tree=data["d"]))
                        if self._command_tree:
                            content = data.get("d", {}).get("content")
                            args = content.split(" ")
                            command_data = self._command_tree.get(args[0])
                            if command_data:
                                req_arg_count = command_data["required_arguments_count"] - 1
                                max_arg_count = command_data["arguments_sum"] - 1
                                prov_args_count_len = len(args) - 1
                                if prov_args_count_len in range(req_arg_count, max_arg_count + 1):
                                    await self._trigger(command_data["coro"], handler_base(session=self._session, auth=self._auth, data_tree=data["d"]), *args[1:])
                                else:
                                    raise UnSufficientArguments(f"dissonance: not enough arguments passed. Required arguments count: {req_arg_count}"
                                    if prov_args_count_len < req_arg_count
                                    else f"dissonance: arguments limit exceeded. Arguments limit: {max_arg_count}")
                    if data["t"] == "MESSAGE_DELETE":
                        if "on_message_delete" in self._events_tree:
                            await self._trigger("")
                elif data["op"] == 7: # Reconnect & resume
                    await self._reconnect_to_ws()
                    await self._resume()
                    print(f"dissonance: {Fore.GREEN}reconnected & resumed{Fore.RESET} to the {Fore.GREEN} gateway successfully {Fore.RESET} [{datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}]")
                    self.decompresser = zlib.decompressobj()
                    asyncio.create_task(self._ws_loop())
                    return
                elif data["op"] == 9: # invalid session
                    print(f"dissonance: {Fore.YELLOW}invalid session")
                    if data["d"]:
                        await self._resume()
                    else:
                        await self._reconnect_to_ws()
                        await self._identify()
                        self.decompresser = zlib.decompressobj()
                        asyncio.create_task(self._ws_loop())
                        return
                elif data["op"] == 10:  # Hello
                    self._keep_alive_task = asyncio.create_task(self._keep_alive(data.get("d", {}).get("heartbeat_interval") / 1000))
                elif data["op"] == 11:
                    if self._debug:
                        print(f"dissonance [debug]:{Fore.LIGHTCYAN_EX} heartbeat{Fore.RESET} was{Fore.GREEN} successful {Fore.RESET} [{datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}]")  
                else:
                    print(f"dissonance: {Fore.RED}unhandled operation code. ({data["op"]}){Fore.RESET}")
            except ClientConnectionError:
                print(f"dissonance: {Fore.RED}connection lost!{Fore.RESET} [{datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}]")
                break
            except Exception as e:
                print(f"dissonance: {Fore.RED}unexpected error: {e}{Fore.RESET} [{datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]")
 
    async def _keep_alive(self, heartbeat_interval: int) -> None:
        while True:
            await asyncio.sleep(heartbeat_interval)
            await self.ws.send_bytes(orjson.dumps({
                "op": 1,
                "d": self._last_sequence
            }))
            if self._debug:
                print(f"dissonance [debug]: Heartbeat{Fore.LIGHTCYAN_EX} sent{Fore.RESET}")

    async def _fetch_gateway_url(self):
        response = await self._session.get("https://discord.com/api/gateway")
        data = await response.json(loads=orjson.loads)
        self.gateway_url = data["url"]

    async def _cache_client_info(self):
        response = await self._session.get("https://discord.com/api/users/@me", headers={
            "Authorization": self._auth
        })
        data = await response.json(loads=orjson.loads)
        self.id = data["id"]
        self.user_name = data["username"]
        self.bio = data["bio"]

    async def change_presence(self, status: str, value: str = None, type: int = 0, **kwargs):
        await self.ws.send_bytes(orjson.dumps({
            "op": 3,
            "d": {
                "status": status,
                "afk": False,
                "since": None,
                "activities": [
                    {
                        "name": value,
                        "type": type,
                        "url": kwargs.get("url")
                    }
                ]
            }
        }))

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
                "arguments_sum": required_arguments_count + num_defaults
            }
        return wrapper

    async def _trigger(self, target: callable, *args):
        asyncio.create_task(target(*args))