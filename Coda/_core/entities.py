from typing import Union, List, Dict, Any, Optional
from aiohttp import ClientSession
from .constants import __base_url__, AllowedMentions
from .embed_base import Embed
from .payloads import MessagePayload
from .components import ActionRow
from .exceptions import *
from .http import _request
from .models import ObjectBuilder, Poll


class Guild:
    """
    Represents a shorthand Discord Guild object.
    """

    def __init__(self, **kwargs) -> None:
        self.id = kwargs["id"]


class Channel(ObjectBuilder):
    """
    Represents a Discord Channel.
    """

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
        """
        Retrieve a specific message from this channel by ID.
        """
        data = await _request(
            self._session,
            "GET",
            f"{__base_url__}channels/{self.id}/messages/{message_id}",
            headers={"Authorization": self.kwargs["auth"]},
        )
        return Message(
            tree=data,
            session=self._session,
            auth=self._auth,
            channel=self,
        )

    async def send(
        self,
        content: str = None,
        embeds: List[Embed] = None,
        sticker_ids: List[str] = None,
        poll: Poll = None,
        allowed_mentions: AllowedMentions = None,
        reference_message_id: str = None,
        components: List[ActionRow] = None,
    ):
        """
        Send a message to this channel.
        """
        if not any([content, embeds, sticker_ids, poll, components]):
            raise ValueError("No arguments provided")
        payload = MessagePayload(
            content=content,
            embeds=embeds,
            sticker_ids=sticker_ids,
            poll=poll,
            allowed_mentions=allowed_mentions,
            reference_message_id=reference_message_id,
            components=components,
        ).payload_tree
        data = await _request(
            self._session,
            "POST",
            f"{__base_url__}channels/{self.id}/messages",
            json=payload,
        )
        return Message(
            tree=data,
            session=self._session,
            auth=self._auth,
            channel=self,
        )

    async def delete(self):
        """
        Delete this channel.
        """
        await _request(self._session, "DELETE", f"{__base_url__}channels/{self.id}")
        return True

    async def get_pins(self, before: str = None, limit: int = None):
        """
        Retrieve all pinned messages in the channel.

        This method fetches a list of messages that have been pinned in the current channel.
        The Discord API limits pinned messages to a maximum of 50 per channel.
        """
        data = await _request(
            self._session,
            "GET",
            f"{__base_url__}channels/{self.id}/pins",
            json={"before": before, "limit": limit},
        )
        return [
            Message(tree=pin, session=self._session, auth=self._auth, channel=self)
            for pin in data
        ]


class Author:
    """
    Represents a Discord User/Author object.
    """

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


class Message(ObjectBuilder):
    """
    Represents a Discord Message.

    This class is 'Interaction-Aware', meaning if it was created as a
    response to an interaction, it stores the interaction context to
    allow seamless follow-ups via `.reply()`.
    """

    id: str
    channel_id: str
    guild_id: str
    content: str
    author: Author
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

    def __init__(self, tree, session: ClientSession, auth, channel, **kwargs):
        super().__init__(tree)
        self._session = session
        self._auth = auth
        self.channel = channel
        self._interaction_token = kwargs.get("interaction_token")
        self._application_id = kwargs.get("application_id")

    async def reply(
        self,
        content: str = None,
        embeds: List[Embed] = None,
        sticker_ids: List[str] = None,
        poll: Poll = None,
        allowed_mentions: Union[AllowedMentions, Dict] = None,
        components: List[ActionRow] = None,
    ):
        """
        Reply to this message.

        If this message is an interaction, it will
        automatically be sent as an interaction follow-up. Otherwise,
        it sends a standard message reply.
        """
        from .payloads import (
            InteractionPayload,
        )  # Local import to avoid circular dependency

        if not any([content, embeds, sticker_ids, poll, components]):
            raise ValueError("No arguments provided")

        # If we have an interaction token, we can use it to reply as a follow-up
        if (
            hasattr(self, "_interaction_token")
            and self._interaction_token
            and hasattr(self, "_application_id")
            and self._application_id
        ):
            payload = InteractionPayload(
                content=content, embeds=embeds, poll=poll, components=components
            ).payload_tree

            data = await _request(
                self._session,
                "POST",
                f"{__base_url__}webhooks/{self._application_id}/{self._interaction_token}",
                json=payload,
            )
            return Message(
                data,
                self._session,
                self._auth,
                self.channel,
                interaction_token=self._interaction_token,
                application_id=self._application_id,
            )

        # Standard message reply
        payload = MessagePayload(
            content=content,
            embeds=embeds,
            sticker_ids=sticker_ids,
            poll=poll,
            allowed_mentions=allowed_mentions,
            reference_message_id=self.id,
            components=components,
        ).payload_tree

        data = await _request(
            self._session,
            "POST",
            f"{__base_url__}channels/{self.channel.id}/messages",
            json=payload,
        )
        return Message(
            tree=data, session=self._session, auth=self._auth, channel=self.channel
        )

    async def edit(
        self, new_content: str = None, embed: dict = None, embeds: list = None
    ):
        """
        Edit this message.
        """
        if not any([new_content, embed, embeds]):
            raise ValueError("No arguments provided")

        embeds_payload = []
        if embed:
            embeds_payload.append(embed.tree)
        if embeds:
            embeds_payload.extend([embed_item.tree for embed_item in embeds])

        payload = {"content": new_content or self.content, "embeds": embeds_payload}

        if (
            hasattr(self, "_interaction_token")
            and self._interaction_token
            and hasattr(self, "_application_id")
            and self._application_id
        ):
            data = await _request(
                self._session,
                "PATCH",
                f"{__base_url__}webhooks/{self._application_id}/{self._interaction_token}/messages/{self.id}",
                json=payload,
            )
        else:
            data = await _request(
                self._session,
                "PATCH",
                f"{__base_url__}channels/{self.channel.id}/messages/{self.id}",
                json=payload,
            )

        self.update(data)
        return self

    async def delete(self):
        """
        Delete this message.

        """
        if (
            hasattr(self, "_interaction_token")
            and self._interaction_token
            and hasattr(self, "_application_id")
            and self._application_id
        ):
            await _request(
                self._session,
                "DELETE",
                f"{__base_url__}webhooks/{self._application_id}/{self._interaction_token}/messages/{self.id}",
            )
        else:
            await _request(
                self._session,
                "DELETE",
                f"{__base_url__}channels/{self.channel.id}/messages/{self.id}",
            )
        return True

    async def pin(self):
        """
        Pin this message.
        """
        await _request(
            self._session,
            "PUT",
            f"{__base_url__}channels/{self.channel.id}/pins/{self.id}",
        )
        self.pinned = True
        return self

    async def unpin(self):
        """
        Unpin this message.
        """
        await _request(
            self._session,
            "DELETE",
            f"{__base_url__}channels/{self.channel.id}/pins/{self.id}",
        )
        self.pinned = False
        return self

    async def react(self, emoji: str):
        """
        Add a reaction to this message.
        """
        await _request(
            self._session,
            "PUT",
            f"{__base_url__}channels/{self.channel.id}/messages/{self.id}/reactions/{emoji}/@me",
        )
        return self

    async def delete_reaction(self, emoji: str, user_id: Optional[str] = None):
        """
        Delete a reaction from this message.
        """
        user_segment = f"/{user_id}" if user_id else ""
        await _request(
            self._session,
            "DELETE",
            f"{__base_url__}channels/{self.channel.id}/messages/{self.id}/reactions/{emoji}{user_segment}",
        )
        return self

    async def delete_all_reactions(self):
        """
        Delete all reactions from this message.
        """
        await _request(
            self._session,
            "DELETE",
            f"{__base_url__}channels/{self.channel.id}/messages/{self.id}/reactions",
        )
        self.reactions = []
        return self

    async def get_reactions(self, emoji: str):
        """
        Get all users who reacted with a specific emoji.
        """
        self.reactions = await _request(
            self._session,
            "GET",
            f"{__base_url__}channels/{self.channel.id}/messages/{self.id}/reactions/{emoji}",
        )
        return self.reactions
