from .constants import InteractionResponseType
from typing import List, Optional, Any


class MessagePayload:
    """
    Builder for standard Discord message payloads.
    Used by Channel.send and Message.reply.
    """

    def __init__(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[Any]] = None,
        sticker_ids: Optional[List[str]] = None,
        poll: Optional[Any] = None,
        allowed_mentions: Optional[Any] = None,
        reference_message_id: Optional[str] = None,
        components: Optional[List[Any]] = None,
    ):
        self.content = content
        self.embeds = embeds
        self.sticker_ids = sticker_ids
        self.poll = poll
        self.allowed_mentions = allowed_mentions
        self.reference_message_id = reference_message_id
        self.components = components

    @property
    def payload_tree(self) -> dict:
        embeds_payload = []
        if self.embeds:
            if len(self.embeds) == 1:
                embeds_payload.append(self.embeds[0].tree)
            else:
                embeds_payload = [embed_item.tree for embed_item in self.embeds]
        stickers_payload = self.sticker_ids if self.sticker_ids else []
        poll_payload = self.poll.poll_tree if self.poll else self.poll

        payload = {
            "content": self.content or None,
            "embeds": embeds_payload,
            "sticker_ids": stickers_payload,
            "poll": poll_payload,
            "allowed_mentions": self.allowed_mentions,
            "message_reference": (
                {
                    "message_id": self.reference_message_id,
                    "fail_if_not_exists": False,
                }
                if self.reference_message_id is not None
                else self.reference_message_id
            ),
            "components": [c.tree for c in self.components] if self.components else [],
        }
        return payload


class InteractionPayload:
    """
    Builder for Discord interaction response payloads.
    Used by Interaction.reply, follow_up, and edit_response.
    """

    def __init__(
        self,
        type: InteractionResponseType = None,
        content: Optional[str] = None,
        embeds: Optional[List[Any]] = None,
        ephemeral: bool = False,
        poll: Optional[Any] = None,
        components: Optional[List[Any]] = None,
    ):
        self.type = type
        self.content = content
        self.embeds = embeds
        self.ephemeral = ephemeral
        self.poll = poll
        self.components = components

    @property
    def payload_tree(self) -> dict:
        embeds_payload = []
        if self.embeds:
            if len(self.embeds) == 1:
                embeds_payload.append(self.embeds[0].tree)
            else:
                embeds_payload = [embed_item.tree for embed_item in self.embeds]

        flags = 64 if self.ephemeral else None

        poll_payload = self.poll.poll_tree if self.poll else self.poll

        data = {
            "content": self.content,
            "embeds": embeds_payload,
            "flags": flags,
            "poll": poll_payload,
            "components": (
                [c.tree for c in self.components] if self.components else None
            ),
        }
        if self.type is None:
            return data
        payload = {"type": self.type.value, "data": data}
        return payload
