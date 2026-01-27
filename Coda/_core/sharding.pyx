# shard_manager.pyx
# cython: language_level=3
import asyncio
from aiohttp import ClientSession
from colorama import Fore
from typing import Union, Iterable
from ._core.ws import FetchClientData, WebSocket

cdef class ShardedClient:
    cdef public str prefix, _auth
    cdef public object intents, shards, session
    cdef public int shard_count
    cdef public bint _debug
    cdef public bint _compress

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
        if not self.session:
            self.session = ClientSession(raise_for_status=True, headers={
                    "authorization": self._auth,
                    "content-type": "application/json",  
                })
        gatway_data, client_info = await FetchClientData(self.session, self._auth)
        for shard_id in range(self.shard_count):
            shard = WebSocket(
                intents=self.intents,
                prefix=self.prefix,
                debug=self._debug,
                compress=self._compress,
                _gateway_data=gatway_data,
                _client_info=client_info,
                _shard_id=shard_id,
                _shard_count=self.shard_count,
                session=self.session,
                auth=self._auth,
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
        if self.session is not None:
            await self.session.close()
        print(f"coda: {Fore.RED}All shards stopped.{Fore.RESET}")