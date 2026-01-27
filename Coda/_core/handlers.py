import re
from .constants import __base_url__, AllowedMentions, PollLayoutStyle, InteractionResponseType, ApplicationCommandOptionType, InteractionType, ComponentType
from .embed_base import Embed
from .poll_base import Poll
from .payloads import MessagePayload, InteractionPayload
from .components_base import ActionRow, Button
from .exceptions import *
from typing import Union, List, Dict, Any, Optional
from aiohttp import ClientSession
import orjson
import asyncio
from colorama import Fore
from datetime import datetime, UTC

__status_codes__ = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    429: TooManyRequests,
}

class Bucket:
    """
    Represents a Discord rate limit bucket for a specific route.
    
    Tracks the 'remaining' requests, 'limit', and the 'reset' time based on 
    Discord's X-RateLimit headers.
    """
    def __init__(self):
        self.lock = asyncio.Lock()
        self.remaining = 1
        self.limit = 1
        self.reset_at = 0

    async def wait(self):
        """
        Wait until a slot is available in this bucket.
        Handles both immediate slot consumption and sleeping until reset.
        """
        async with self.lock:
            while True:
                now = datetime.now(UTC).timestamp()
                if self.remaining > 0:
                    self.remaining -= 1
                    return
                
                if now >= self.reset_at:
                    self.remaining = self.limit - 1
                    return
                
                wait_time = self.reset_at - now
                if wait_time > 0:
                    print(f"Coda: {Fore.CYAN}Rate limit bucket full. Waiting {wait_time:.2f}s{Fore.RESET}")
                    await asyncio.sleep(wait_time)
                else:
                    self.remaining = self.limit - 1
                    return

    def update(self, headers: dict):
        """
        Update bucket state from Discord's response headers.
        """
        self.limit = int(headers.get("X-RateLimit-Limit", self.limit))
        self.remaining = int(headers.get("X-RateLimit-Remaining", 0))
        reset_after = float(headers.get("X-RateLimit-Reset-After", 0))
        self.reset_at = datetime.now(UTC).timestamp() + reset_after

class RateLimiter:
    """
    Global manager for rate limit buckets and global backoff.
    """
    def __init__(self):
        self.buckets: Dict[str, Bucket] = {}
        self.global_wait_until = 0

    async def wait_global(self):
        """
        Proactively wait if a global rate limit backoff is active.
        """
        now = datetime.now(UTC).timestamp()
        if now < self.global_wait_until:
            wait_time = self.global_wait_until - now
            print(f"Coda: {Fore.RED}Global backoff active. Waiting {wait_time:.2f}s{Fore.RESET}")
            await asyncio.sleep(wait_time)

    def set_global_backoff(self, retry_after: float):
        """
        Set a global backoff period across all requests.
        """
        self.global_wait_until = datetime.now(UTC).timestamp() + retry_after

    def get_bucket(self, method: str, url: str) -> Bucket:
        """
        Identify and return the rate limit bucket for a specific endpoint.
        Uses regex to normalize paths (e.g., grouping all message deletions).
        """
        path = url.split(__base_url__)[-1]
        route = re.sub(r'messages/\d+', 'messages/:id', path)
        route = re.sub(r'reactions/[^/]+', 'reactions/:emoji', route)
        key = f"{method} {route}"
        
        if key not in self.buckets:
            self.buckets[key] = Bucket()
        return self.buckets[key]

_rate_limiter = RateLimiter()


async def _request(session: ClientSession, method: str, url: str, **kwargs) -> Any:
    """
    Centralized HTTP request handler for the Discord API.
    Handles proactive rate limiting, global backoffs, and error code mapping.
    """
    bucket = _rate_limiter.get_bucket(method, url)
    
    while True:
        await _rate_limiter.wait_global()
        await bucket.wait()
        
        async with session.request(method, url, **kwargs) as response:
            # Update bucket from headers
            bucket.update(response.headers)
            
            if response.status == 429:
                data = await response.json(loads=orjson.loads)
                retry_after = data.get("retry_after", 1)
                is_global = data.get("global", False)
                
                if is_global:
                     _rate_limiter.set_global_backoff(retry_after)
                     print(f"Coda: {Fore.RED}GLOBAL Rate limit hit. Retrying in {retry_after}s{Fore.RESET}")
                else:
                     print(f"Coda: {Fore.YELLOW}Bucket Rate limit hit ({method} {url}). Retrying in {retry_after}s{Fore.RESET}")
                     await asyncio.sleep(retry_after)
                continue

            if response.status in __status_codes__:
                raise __status_codes__[response.status](f"discord API returned {response.status}")
            
            if response.status == 204:
                return None
            
            try:
                return await response.json(loads=orjson.loads)
            except:
                return await response.text()


class ObjectBuilder:
    """
    A utility class that converts dictionaries into objects with dot-notation access.
    Automatically recurses into nested dictionaries.
    """
    def __init__(self, data: Dict[str, Any]):
        self.update(data)

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update the object attributes from a dictionary.
        """
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, ObjectBuilder(value))
            else:
                setattr(self, key, value)

    def __repr__(self):
        return f"<ObjectBuilder {self.__dict__}>"


class PollMedia:
    text: str
    emoji: Optional[Any]


class PollAnswers:
    text: str
    emoji: Optional[Any]


class PollAnswerCount:
    id: int
    count: int
    me_voted: bool


class PollResults:
    is_finalized: bool
    answer_counts: PollAnswerCount


class Poll(ObjectBuilder):
    """
    Represents a Discord Poll object
    """
    question: str
    answers: PollAnswers
    expiry: str
    allow_multiselect: bool
    layout_type: PollLayoutStyle
    results:  PollResults


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
        self.pinned = None
        self.reactions = None
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
        if not any([content, embeds, sticker_ids, poll, components]):
            raise ValueError("No arguments provided")
            
        # If we have an interaction token, we can use it to reply as a follow-up
        if hasattr(self, "_interaction_token") and self._interaction_token and hasattr(self, "_application_id") and self._application_id:
             payload = InteractionPayload(
                content=content,
                embeds=embeds,
                poll=poll,
                components=components
            ).payload_tree
            
             data = await _request(
                 self._session,
                 "POST",
                 f"{__base_url__}webhooks/{self._application_id}/{self._interaction_token}",
                 json=payload
             )
             return Message(data, self._session, self._auth, self.channel, 
                            interaction_token=self._interaction_token, 
                            application_id=self._application_id)

        # Standard message reply
        payload = MessagePayload(
            content=content,
            embeds=embeds,
            sticker_ids=sticker_ids,
            poll=poll,
            allowed_mentions=allowed_mentions,
            reference_message_id=self.id,
            components=components
        ).payload_tree
        
        data = await _request(
            self._session, 
            "POST", 
            f"{__base_url__}channels/{self.channel.id}/messages",
            json=payload
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
        
        if hasattr(self, "_interaction_token") and self._interaction_token and hasattr(self, "_application_id") and self._application_id:
            data = await _request(
                self._session,
                "PATCH",
                f"{__base_url__}webhooks/{self._application_id}/{self._interaction_token}/messages/{self.id}",
                json=payload
            )
        else:
            data = await _request(
                self._session,
                "PATCH",
                f"{__base_url__}channels/{self.channel.id}/messages/{self.id}",
                json=payload
            )
        
        self.update(data)
        return self

    async def delete(self):
        """
        Delete this message.

        """
        if hasattr(self, "_interaction_token") and self._interaction_token and hasattr(self, "_application_id") and self._application_id:
            await _request(
                self._session,
                "DELETE",
                f"{__base_url__}webhooks/{self._application_id}/{self._interaction_token}/messages/{self.id}"
            )
        else:
            await _request(
                 self._session,
                 "DELETE",
                 f"{__base_url__}channels/{self.channel.id}/messages/{self.id}"
            )
        return True

    async def pin(self):
        """
        Pin this message.
        """
        await _request(
            self._session,
            "PUT",
            f"{__base_url__}channels/{self.channel.id}/pins/{self.id}"
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
            f"{__base_url__}channels/{self.channel.id}/pins/{self.id}"
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
            f"{__base_url__}channels/{self.channel.id}/messages/{self.id}/reactions/{emoji}/@me"
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
             f"{__base_url__}channels/{self.channel.id}/messages/{self.id}/reactions/{emoji}{user_segment}"
        )
        return self

    async def delete_all_reactions(self):
        """
        Delete all reactions from this message.
        """
        await _request(
            self._session,
            "DELETE",
            f"{__base_url__}channels/{self.channel.id}/messages/{self.id}/reactions"
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
            f"{__base_url__}channels/{self.channel.id}/messages/{self.id}/reactions/{emoji}"
        )
        return self.reactions


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
            headers={"Authorization": self.kwargs["auth"]}
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
            json=payload
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
        await _request(
            self._session,
            "DELETE",
            f"{__base_url__}channels/{self.id}"
        )
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
            json={"before": before, "limit": limit}
        )
        return [Message(tree=pin, session=self._session, auth=self._auth, channel=self) for pin in data]
class Guild:
    """
    Represents a shorthand Discord Guild object.
    """
    def __init__(self, **kwargs) -> None:
        self.id = kwargs["id"]

class Option:
    """
    Represents an option for a slash command.
    """
    def __init__(self, name: str, description: str, type: ApplicationCommandOptionType, required: bool = False):
        self.name = name
        self.description = description
        self.type = type.value
        self.required = required

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "required": self.required
        }

class Interaction:
    """
    Represents a Discord Interaction (Slash Command, Component Click, Modal Submit).
    """
    def __init__(self, session: ClientSession, data: Dict[str, Any], auth: str):
        self._session = session
        self._auth = auth
        self.id = data["id"]
        self.application_id = data["application_id"]
        self.token = data["token"]
        self.type = data["type"]
        self.data = data.get("data", {})
        self.guild_id = data.get("guild_id")
        self.channel_id = data.get("channel_id")
        
        member_data = data.get("member")
        user_data = member_data.get("user") if member_data else data.get("user")
        
        self.user_id = user_data["id"] if user_data else None
        self.username = user_data["username"] if user_data else None
        
        # Construct simple objects for easy access
        if self.channel_id:
             self.channel = Channel(
                tree={"id": self.channel_id},
                session=self._session,
                id=self.channel_id,
                auth=self._auth
            )
        
        if self.guild_id:
             self.guild = Guild(
                id=self.guild_id
            )
            
        # Link message if it exists (for component interactions)
        message_data = data.get("message")
        if message_data:
            self.message = Message(
                tree=message_data, 
                session=self._session, 
                auth=self._auth, 
                channel=self.channel,
                interaction_token=self.token,
                application_id=self.application_id
            )
        else:
            self.message = None

        # Parse data based on interaction type
        self.values = []
        if self.type == InteractionType.MESSAGE_COMPONENT.value:
            self.values = self.data.get("values", [])
        elif self.type == InteractionType.MODAL_SUBMIT.value:
             # Modals send data in nested components (ActionRows -> TextInputs)
             self.values = {}
             for row in self.data.get("components", []):
                 for comp in row.get("components", []):
                     if comp.get("type") == ComponentType.TEXT_INPUT.value:
                         self.values[comp["custom_id"]] = comp["value"]

    async def respond(self, content: str = None, embeds: list = None, ephemeral: bool = False, components: List[ActionRow] = None):
        """
        Respond to the interaction with a message.
        """
        payload = InteractionPayload(
            type=InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            content=content,
            embeds=embeds,
            ephemeral=ephemeral,
            components=components
        ).payload_tree
            
        await _request(
             self._session,
             "POST",
             f"{__base_url__}interactions/{self.id}/{self.token}/callback",
             json=payload
        )

        if not ephemeral:
             data = await _request(
                 self._session,
                 "GET",
                 f"{__base_url__}webhooks/{self.application_id}/{self.token}/messages/@original"
             )
             return Message(data, self._session, self._auth, self.channel, 
                            interaction_token=self.token, 
                            application_id=self.application_id)

    async def modal_response(self, title: str, custom_id: str, components: List[ActionRow]):
        """
        Respond to the interaction with a modal.
        """
        payload = {
            "type": InteractionResponseType.MODAL.value,
            "data": {
                "title": title,
                "custom_id": custom_id,
                "components": [c.tree for c in components]
            }
        }
        await _request(
            self._session,
            "POST",
            f"{__base_url__}interactions/{self.id}/{self.token}/callback",
            json=payload
        )

    async def defer(self, ephemeral: bool = False):
        """
        Defer the interaction (show 'Bot is thinking...').
        Typically used when processing will take longer than 3 seconds.
        """
        payload = InteractionPayload(
            type=InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
            ephemeral=ephemeral
        ).payload_tree

        await _request(
            self._session,
            "POST",
            f"{__base_url__}interactions/{self.id}/{self.token}/callback",
             json=payload
        )

    async def follow_up(self, content: str = None, embeds: list = None, ephemeral: bool = False, components: List[ActionRow] = None):
        """
        Send a follow-up message.
        """
        payload = InteractionPayload(
            content=content,
            embeds=embeds,
            ephemeral=ephemeral,
            components=components
        ).payload_tree

        data = await _request(
            self._session,
            "POST",
            f"{__base_url__}webhooks/{self.application_id}/{self.token}",
            json=payload
        )
        return Message(data, self._session, self._auth, self.channel, 
                       interaction_token=self.token, 
                       application_id=self.application_id)

    async def edit_response(self, content: str = None, embeds: list = None, message_id: str = "@original"):
        """
        Edit the original interaction response or a follow-up message.
        """
        payload = InteractionPayload(
            content=content,
            embeds=embeds
        ).payload_tree

        data = await _request(
            self._session, 
            "PATCH",
            f"{__base_url__}webhooks/{self.application_id}/{self.token}/messages/{message_id}",
            json=payload
        )
        return Message(data, self._session, self._auth, self.channel, 
                       interaction_token=self.token, 
                       application_id=self.application_id)

    async def delete_response(self, message_id: str = "@original"):
        """
        Delete the original response or a specific follow-up message.
        """
        await _request(
            self._session,
            "DELETE",
            f"{__base_url__}webhooks/{self.application_id}/{self.token}/messages/{message_id}"
        )
