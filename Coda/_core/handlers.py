from .constants import __base_url__
from .embed_base import embed_base
from .exceptions import *
from typing import Union, List, Dict, Any, Optional
from aiohttp import ClientSession
import orjson


__status_codes__ = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    429: TooManyRequests,
}


async def _handle_status_code(res):
    if res in __status_codes__:
        raise __status_codes__[res](f"discord API returned {res}")


class base_handler:
    def __init__(self, **kwargs) -> None:
        self._session = kwargs["session"]
        self.content: str = kwargs["content"]
        self.id = kwargs["id"]
        self._auth = kwargs["auth"]
        self.guild = guild_handler_base(
            session=self._session, id=kwargs["guild_id"], auth=self._auth
        )
        self.channel_id = kwargs["channel_id"]
    async def reply(
        self,
        content: str = None,
        embed: dict = None,
        embeds: list = None,
        poll: dict = None,
    ):
        if not any([content, embed, embeds, poll]):
            raise Exception("no argument passed")
        embeds_payload = []
        if embed:
            embeds_payload.append(embed.tree)
        if embeds:
            embeds_payload.extend([embed_item.tree for embed_item in embeds])
        payload = {
            "content": content or None,
            "embeds": embeds_payload,
            "message_reference": {
                "guild_id": self.guild.id,
                "message_id": self.id,
            },
        }
        async with self._session.post(
            f"{__base_url__}channels/{self.channel_id}/messages",
            json=payload,
            headers={"Authorization": self._auth, "Content-Type": "application/json"},
        ) as response:
            await _handle_status_code(response.status)
            data = await response.json(loads=orjson.loads)
            return massage(
                tree=data, session=self._session, auth=self._auth, channel=self.channel_id
            )


class discord_object:
    def __init__(self, data: Dict[str, Any]):
        self.update(data)

    def update(self, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, discord_object(value))
            else:
                setattr(self, key, value)

    def __repr__(self):
        return f"<discord_object {self.__dict__}>"


class author_object:
    id: str
    username: str
    avatar: Optional[str]
    discriminator: str
    public_flags: int
    flags: int
    bot: bool
    banner: Optional[str]
    accent_color: Optional[int]
    global_name: Optional[str]
    avatar_decoration_data: Optional[Any]
    collectibles: Optional[Any]
    display_name_styles: Optional[Any]
    banner_color: Optional[int]
    clan: Optional[Any]
    primary_guild: Optional[Any]


class massage(discord_object):
    id: str
    channel_id: str
    guild_id: str
    content: str
    author: author_object
    timestamp: str
    edited_timestamp: Optional[str]
    tts: bool
    mention_everyone: bool
    mentions: List[Dict[str, Any]]
    mention_roles: List[str]
    attachments: List[Dict[str, Any]]
    embeds: List[Dict[str, Any]]
    reactions: Optional[List[Dict[str, Any]]]
    pinned: bool
    webhook_id: Optional[str]
    type: int
    _session: ClientSession
    _auth: str

    def __init__(self, tree, session: ClientSession, auth, channel):
        super().__init__(tree)
        self._session = session
        self._auth = auth
        self.channel = channel
        self.pinned = None
        self.reactions = None

    async def edit(
        self, new_content: str = None, embed: dict = None, embeds: list = None
    ):
        if not any([new_content, embed, embeds]):
            raise Exception("no argument passed")

        embeds_payload = []
        if embed:
            embeds_payload.append(embed.tree)
        if embeds:
            embeds_payload.extend([embed_item.tree for embed_item in embeds])

        payload = {"content": new_content or self.content, "embeds": embeds_payload}

        async with self._session.patch(
            f"{__base_url__}channels/{self.channel_id}/messages/{self.id}",
            json=payload,
            headers={"Authorization": self._auth, "Content-Type": "application/json"},
        ) as response:
            await _handle_status_code(response.status)
            data = await response.json(loads=orjson.loads)
            self.update(data)
            return self

    async def delete(self):
        async with self._session.delete(
            f"{__base_url__}channels/{self.channel_id}/messages/{self.id}",
            headers={"Authorization": self._auth},
        ) as response:
            await _handle_status_code(response.status)
            return True

    async def pin(self):
        async with self._session.put(
            f"{__base_url__}channels/{self.channel_id}/pins/{self.id}",
            headers={"Authorization": self._auth},
        ) as response:
            await _handle_status_code(response.status)
            self.pinned = True
            return self

    async def unpin(self):
        async with self._session.delete(
            f"{__base_url__}channels/{self.channel_id}/pins/{self.id}",
            headers={"Authorization": self._auth},
        ) as response:
            await _handle_status_code(response.status)
            self.pinned = False
            return self

    async def get_channel_pins(self):
        async with self._session.get(
            f"{__base_url__}channels/{self.channel_id}/pins",
            headers={"Authorization": self._auth},
        ) as response:
            await _handle_status_code(response.status)
            data = await response.json(loads=orjson.loads)
            return [
                massage(
                    tree=msg,
                    session=self._session,
                    auth=self._auth,
                    channel=self.channel,
                )
                for msg in data
            ]

    async def react(self, emoji: str):
        async with self._session.put(
            f"{__base_url__}channels/{self.channel_id}/messages/{self.id}/reactions/{emoji}/@me",
            headers={"Authorization": self._auth},
        ) as response:
            await _handle_status_code(response.status)
            return self

    async def delete_reaction(self, emoji: str, user_id: Optional[str] = None):
        user_segment = f"/{user_id}" if user_id else ""
        async with self._session.delete(
            f"{__base_url__}channels/{self.channel_id}/messages/{self.id}/reactions/{emoji}{user_segment}",
            headers={"Authorization": self._auth},
        ) as response:
            await _handle_status_code(response.status)
            return self

    async def delete_all_reactions(self):
        async with self._session.delete(
            f"{__base_url__}channels/{self.channel_id}/messages/{self.id}/reactions",
            headers={"Authorization": self._auth},
        ) as response:
            await _handle_status_code(response.status)
            self.reactions = []
            return self

    async def get_reactions(self, emoji: str):
        async with self._session.get(
            f"{__base_url__}channels/{self.channel_id}/messages/{self.id}/reactions/{emoji}",
            headers={"Authorization": self._auth},
        ) as response:
            await _handle_status_code(response.status)
            self.reactions = await response.json(loads=orjson.loads)
            return self.reactions


class channel_base_handler(discord_object):
    id: str
    type: int
    last_message_id: str
    flags: int
    guild_id: str
    name: str
    parent_id: Optional[str]
    rate_limit_per_user: int
    topic: Optional[str]
    position: int
    permission_overwrites: List
    nsfw: bool
    def __init__(self, tree, **kwargs) -> None:
        super().__init__(tree)
        self.id = kwargs["id"]
        self._session = kwargs["session"]
        self._auth = kwargs["auth"]
        self.kwargs = kwargs

    async def get_message(self, message_id):
        async with self._session.get(
            f"{__base_url__}channels/{self.id}/messages/{message_id}",
            headers={"Authorization": self.kwargs["auth"]}
        ) as response:
            data = await response.json(loads=orjson.loads)
            return massage(
                tree=data,
                session=self._session,
                auth=self._auth,
                channel=self,
            )

    async def send(
        self,
        content: str = None,
        embed: Union[embed_base, dict] = None,
        embeds: list = None,
        poll: dict = None,
    ):
        if not any([content, embed, embeds, poll]):
            raise Exception("no argument passed")
        payload = {
            "content": content or None,
            "embeds": (
                [embed.tree]
                if embed
                else [] + [embed_item.tree for embed_item in embeds] if embeds else []
            ),
        }
        async with self._session.post(
            f"{__base_url__}channels/{self.id}/messages",
            json=payload,
            headers={
                "Authorization": self._auth,
                "Content-Type": "application/json",
            },
        ) as response:
            data = await response.json(loads=orjson.loads)
            return massage(
                tree=data,
                session=self._session,
                auth=self._auth,
                channel=self,
            )

    async def delete(self):
        async with self._session.delete(
            f"{__base_url__}channels/{self.id}",
        ) as response:
            await _handle_status_code(response.status)
            return True
    
class guild_handler_base:
    def __init__(self, **kwargs) -> None:
        self.id = kwargs["id"]
