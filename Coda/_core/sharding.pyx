# shard_manager.pyx
# cython: language_level=3
import asyncio
from aiohttp import ClientSession
from colorama import Fore
from typing import Union, Iterable
from ._core.ws import WebSocket_Handler

cdef class ShardManager:
    cdef public str token, prefix
    cdef public object intents, shards, _session
    cdef public int shard_count
    cdef public bint _debug
    cdef public bint _compress

    def __init__(self, token: str, intents: Union[Iterable, int], prefix: str, shard_count: int, debug: bool = False, compress: bool = True):
        self.token = token
        self.intents = intents
        self.prefix = prefix
        self.shard_count = shard_count
        self._debug = debug
        self._compress = compress
        self.shards = []
        self._session = None

    async def register(self):
        if self._session is None:
            self._session = ClientSession(raise_for_status=True)
        for shard_id in range(self.shard_count):
            shard = WebSocket_Handler(
                token=self.token,
                intents=self.intents,
                prefix=self.prefix,
                debug=self._debug,
                compress=self._compress,
                _shard_id=shard_id,
                _shard_count=self.shard_count,
                _session=self._session
            )
            self.shards.append(shard)

    async def connect(self, grace_period: int = 3):
        for shard in self.shards:
            asyncio.create_task(shard.connect())
            await asyncio.sleep(grace_period)
    async def stop_shard(self, shard: WebSocket_Handler):
        shard._keep_alive_task.cancel()
        await shard.ws.close()
    async def stop_shards(self, shards: list[WebSocket_Handler]):
        for shard in shards:
            shard._keep_alive_task.cancel()
            await shard.ws.close()
    async def stop(self):
        for shard in self.shards:
            if shard.ws is not None:
                await shard.ws.close()
        if self._session is not None:
            await self._session.close()
        print(f"coda: {Fore.RED}All shards stopped.{Fore.RESET}")