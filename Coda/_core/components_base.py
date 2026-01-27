from .constants import ComponentType, ButtonStyle, TextInputStyle
from typing import Optional, List, Union


class Button:
    """
    Represents a Discord Button component.
    """
    def __init__(
        self,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        style: ButtonStyle = ButtonStyle.PRIMARY,
        emoji: Optional[dict] = None,
        url: Optional[str] = None,
        disabled: bool = False
    ):
        self.label = label
        self.custom_id = custom_id
        self.style = style
        self.emoji = emoji
        self.url = url
        self.disabled = disabled

    @property
    def tree(self) -> dict:
        payload = {
            "type": ComponentType.BUTTON.value,
            "style": self.style.value,
            "disabled": self.disabled
        }
        if self.label:
            payload["label"] = self.label
        if self.custom_id:
            payload["custom_id"] = self.custom_id
        if self.emoji:
            payload["emoji"] = self.emoji
        if self.url:
            payload["url"] = self.url
        return payload

class SelectOption:
    """
    Represents an option in a Select Menu.
    """
    def __init__(
        self,
        label: str,
        value: str,
        description: Optional[str] = None,
        emoji: Optional[dict] = None,
        default: bool = False
    ):
        self.label = label
        self.value = value
        self.description = description
        self.emoji = emoji
        self.default = default

    @property
    def tree(self) -> dict:
        payload = {
            "label": self.label,
            "value": self.value,
            "default": self.default
        }
        if self.description:
            payload["description"] = self.description
        if self.emoji:
            payload["emoji"] = self.emoji
        return payload

class BaseSelect:
    """
    Base class for all Discord Select Menu types.
    """
    def __init__(
        self,
        custom_id: str,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        type: ComponentType = ComponentType.STRING_SELECT
    ):
        self.custom_id = custom_id
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled
        self.type = type

    @property
    def tree(self) -> dict:
        payload = {
            "type": self.type.value,
            "custom_id": self.custom_id,
            "min_values": self.min_values,
            "max_values": self.max_values,
            "disabled": self.disabled
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder
        return payload

class StringSelect(BaseSelect):
    """
    Represents a Select Menu with a list of custom string options.
    """
    def __init__(
        self,
        custom_id: str,
        options: List[SelectOption],
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False
    ):
        super().__init__(custom_id, placeholder, min_values, max_values, disabled, ComponentType.STRING_SELECT)
        self.options = options

    @property
    def tree(self) -> dict:
        payload = super().tree
        payload["options"] = [o.tree for o in self.options]
        return payload

class UserSelect(BaseSelect):
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(custom_id, type=ComponentType.USER_SELECT, **kwargs)

class RoleSelect(BaseSelect):
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(custom_id, type=ComponentType.ROLE_SELECT, **kwargs)

class MentionableSelect(BaseSelect):
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(custom_id, type=ComponentType.MENTIONABLE_SELECT, **kwargs)

class ChannelSelect(BaseSelect):
    def __init__(self, custom_id: str, channel_types: Optional[List[int]] = None, **kwargs):
        super().__init__(custom_id, type=ComponentType.CHANNEL_SELECT, **kwargs)
        self.channel_types = channel_types

    @property
    def tree(self) -> dict:
        payload = super().tree
        if self.channel_types:
            payload["channel_types"] = self.channel_types
        return payload


class TextInput:
    """
    Represents a Text Input component for use in Modals.
    """
    def __init__(
        self,
        custom_id: str,
        label: str,
        style: TextInputStyle = TextInputStyle.SHORT,
        placeholder: Optional[str] = None,
        value: Optional[str] = None,
        min_length: int = 0,
        max_length: int = 4000,
        required: bool = True
    ):
        self.custom_id = custom_id
        self.label = label
        self.style = style
        self.placeholder = placeholder
        self.value = value
        self.min_length = min_length
        self.max_length = max_length
        self.required = required

    @property
    def tree(self) -> dict:
        payload = {
            "type": ComponentType.TEXT_INPUT.value,
            "custom_id": self.custom_id,
            "label": self.label,
            "style": self.style.value,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "required": self.required
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder
        if self.value:
            payload["value"] = self.value
        return payload

class ActionRow:
    """
    Represents an Action Row component that holds other interactive components.
    Discord allows up to 5 action rows per message.
    """
    def __init__(self, components: Optional[List[Union[Button, StringSelect, UserSelect, RoleSelect, MentionableSelect, ChannelSelect, TextInput]]] = None):
        self.components = components or []

    def add_component(self, component: Union[Button, StringSelect, UserSelect, RoleSelect, MentionableSelect, ChannelSelect, TextInput]):
        self.components.append(component)
        return self

    @property
    def tree(self) -> dict:
        return {
            "type": ComponentType.ACTION_ROW.value,
            "components": [c.tree for c in self.components]
        }

