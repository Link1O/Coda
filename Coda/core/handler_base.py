from .embed_base import embed_base
from typing import Union, Iterable
__base_url__ = "https://discord.com/api/"
class handler_base:
    def __init__(self, session, data_tree, **kwargs) -> None:
        self._session = session
        self.content: str = data_tree["content"]
        self.id = data_tree["id"]
        self._auth = kwargs["auth"]
        self.guild = guild_handler_base(session=self._session, id=data_tree["guild_id"], auth=self._auth)
        self.channel = channel_handler_base(session=session, id=data_tree["channel_id"], auth=self._auth)
    async def reply(self, content: str = None, embed: dict = None, embeds: list = None):
        if not any([content, embed, embeds]):
            raise Exception("no argument passed")
        payload = {
            "content": content or None,
            "embeds": ([embed.tree] if embed else [] + [embed_item.tree for embed_item in embeds] if embeds else []),
            "message_reference": {
                "guild_id": self.guild.id,
                "message_id": self.id
            }
        }
        await self._session.post(f"{__base_url__}channels/{self.channel.id}/messages", json=payload, headers={
            "Authorization": self._auth,
            "Content-Type": "application/json"
        })
class none_responsive_handler_base(handler_base):
    async def send(self, *args, **kwargs):
        raise AttributeError("cannot interact with a deleted message.")
    async def reply(self, *args, **kwargs):
        raise AttributeError("cannot interact with a deleted message.")
class channel_handler_base:
    def __init__(self, **kwargs) -> None:
        self.id = kwargs["id"]
        self._session = kwargs["session"]
        self.kwargs = kwargs
    async def send(self, content: str = None, embed: Union[embed_base, dict] = None, embeds: list = None):
        if not any([content, embed, embeds]):
            raise Exception("no argument passed")
        payload = {
            "content": content or None,
            "embeds": ([embed.tree] if embed else [] + [embed_item.tree for embed_item in embeds] if embeds else [])
        }
        await self._session.post(f"{__base_url__}channels/{self.id}/messages", json=payload, headers={
            "Authorization": self.kwargs["auth"],
            "Content-Type": "application/json"
        })
class guild_handler_base:
    def __init__(self, **kwargs) -> None:
        self.id = kwargs["id"]