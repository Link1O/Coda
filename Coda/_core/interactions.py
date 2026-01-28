from typing import Any, Dict, List, Optional
from aiohttp import ClientSession
from .constants import (
    __base_url__,
    InteractionResponseType,
    InteractionType,
    ApplicationCommandOptionType,
    ComponentType,
)
from .payloads import InteractionPayload
from .entities import Guild, Channel, Message
from .components import ActionRow
from .http import _request


class Option:
    """
    Represents an option for a slash command.
    """

    def __init__(
        self,
        name: str,
        description: str,
        type: ApplicationCommandOptionType,
        required: bool = False,
    ):
        self.name = name
        self.description = description
        self.type = type.value
        self.required = required

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "required": self.required,
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
                auth=self._auth,
            )

        if self.guild_id:
            self.guild = Guild(id=self.guild_id)

        # Link message if it exists (for component interactions)
        message_data = data.get("message")
        if message_data:
            self.message = Message(
                tree=message_data,
                session=self._session,
                auth=self._auth,
                channel=self.channel,
                interaction_token=self.token,
                application_id=self.application_id,
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

    async def respond(
        self,
        content: str = None,
        embeds: list = None,
        ephemeral: bool = False,
        components: List[ActionRow] = None,
    ):
        """
        Respond to the interaction with a message.
        """
        from .entities import Message  # Local import

        payload = InteractionPayload(
            type=InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            content=content,
            embeds=embeds,
            ephemeral=ephemeral,
            components=components,
        ).payload_tree

        await _request(
            self._session,
            "POST",
            f"{__base_url__}interactions/{self.id}/{self.token}/callback",
            json=payload,
        )

        if not ephemeral:
            data = await _request(
                self._session,
                "GET",
                f"{__base_url__}webhooks/{self.application_id}/{self.token}/messages/@original",
            )
            return Message(
                data,
                self._session,
                self._auth,
                self.channel,
                interaction_token=self.token,
                application_id=self.application_id,
            )

    async def modal_response(
        self, title: str, custom_id: str, components: List[ActionRow]
    ):
        """
        Respond to the interaction with a modal.
        """
        payload = {
            "type": InteractionResponseType.MODAL.value,
            "data": {
                "title": title,
                "custom_id": custom_id,
                "components": [c.tree for c in components],
            },
        }
        await _request(
            self._session,
            "POST",
            f"{__base_url__}interactions/{self.id}/{self.token}/callback",
            json=payload,
        )

    async def defer(self, ephemeral: bool = False):
        """
        Defer the interaction (show 'Bot is thinking...').
        Typically used when processing will take longer than 3 seconds.
        """
        payload = InteractionPayload(
            type=InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
            ephemeral=ephemeral,
        ).payload_tree

        await _request(
            self._session,
            "POST",
            f"{__base_url__}interactions/{self.id}/{self.token}/callback",
            json=payload,
        )

    async def follow_up(
        self,
        content: str = None,
        embeds: list = None,
        ephemeral: bool = False,
        components: List[ActionRow] = None,
    ):
        """
        Send a follow-up message.
        """
        from .entities import Message  # Local import

        payload = InteractionPayload(
            content=content, embeds=embeds, ephemeral=ephemeral, components=components
        ).payload_tree

        data = await _request(
            self._session,
            "POST",
            f"{__base_url__}webhooks/{self.application_id}/{self.token}",
            json=payload,
        )
        return Message(
            data,
            self._session,
            self._auth,
            self.channel,
            interaction_token=self.token,
            application_id=self.application_id,
        )

    async def edit_response(
        self, content: str = None, embeds: list = None, message_id: str = "@original"
    ):
        """
        Edit the original interaction response or a follow-up message.
        """
        from .entities import Message  # Local import

        payload = InteractionPayload(content=content, embeds=embeds).payload_tree

        data = await _request(
            self._session,
            "PATCH",
            f"{__base_url__}webhooks/{self.application_id}/{self.token}/messages/{message_id}",
            json=payload,
        )
        return Message(
            data,
            self._session,
            self._auth,
            self.channel,
            interaction_token=self.token,
            application_id=self.application_id,
        )

    async def delete_response(self, message_id: str = "@original"):
        """
        Delete the original response or a specific follow-up message.
        """
        await _request(
            self._session,
            "DELETE",
            f"{__base_url__}webhooks/{self.application_id}/{self.token}/messages/{message_id}",
        )
