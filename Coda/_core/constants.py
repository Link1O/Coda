from enum import Enum


__base_url__ = "https://discord.com/api/v10/"


class Intents(Enum):
    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_BANS = 1 << 2
    GUILD_EMOJIS_AND_STICKERS = 1 << 3
    GUILD_INTEGRATIONS = 1 << 4
    GUILD_WEBHOOKS = 1 << 5
    GUILD_INVITES = 1 << 6
    GUILD_VOICE_STATES = 1 << 7
    GUILD_PRESENCES = 1 << 8
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    GUILD_MESSAGE_TYPING = 1 << 11
    DIRECT_MESSAGES = 1 << 12
    DIRECT_MESSAGE_REACTIONS = 1 << 13
    DIRECT_MESSAGE_TYPING = 1 << 14
    MESSAGE_CONTENT = 1 << 15
    GUILD_SCHEDULED_EVENTS = 1 << 16
    ALL = sum(1 << i for i in range(17))


class Colors(Enum):
    RED = 0xFF0000
    GREEN = 0x00FF00
    BLUE = 0x0000FF
    YELLOW = 0xFFFF00
    ORANGE = 0xFFA500
    PURPLE = 0x800080
    CYAN = 0x00FFFF
    PINK = 0xFFC0CB
    TEAL = 0x008080
    AMBER = 0xFFBF00
    BROWN = 0xA52A2A
    GREY = 0x808080
    INDIGO = 0x4B0082
    LIME = 0x00FF00
    DEEP_PURPLE = 0x4B0082
    LIGHT_BLUE = 0xADD8E6
    LIGHT_GREEN = 0x90EE90
    DEEP_ORANGE = 0xFF4500
    LIGHT_GREY = 0xD3D3D3
    DARK_GREY = 0xA9A9A9
    BLUE_GREY = 0x4682B4
    SILVER = 0xC0C0C0
    GOLD = 0xFFD700
    MAROON = 0x800000
    OLIVE = 0x808000
    LAVENDER = 0xE6E6FA
    CYAN_BLUE = 0x00FFFF
    NAVY_BLUE = 0x000080
    DARK_GREEN = 0x006400
    DARK_BLUE = 0x00008B
    LIGHT_PURPLE = 0x9370DB
    DARK_PURPLE = 0x800080
    MINT_GREEN = 0x98FF98
    SALMON = 0xFA8072
    PEACH = 0xFFDAB9
    CORAL = 0xFF7F50
    SKY_BLUE = 0x87CEEB
    AQUAMARINE = 0x7FFFD4
    ROYAL_BLUE = 0x4169E1
    TURQUOISE = 0x40E0D0
    BEIGE = 0xF5F5DC
    DARK_RED = 0x8B0000
    ORCHID = 0xDA70D6
    SAND = 0xC2B280
    SIENNA = 0xA0522D
    PERIWINKLE = 0xCCCCFF
    VIOLET = 0xEE82EE
    CRIMSON = 0xDC143C
    PALE_GREEN = 0x98FB98
    LIGHT_YELLOW = 0xFFFFE0
    DARK_ORANGE = 0xFF8C00
    STEEL_BLUE = 0x4682B4
    DARK_MAGENTA = 0x8B008B
    CHOCOLATE = 0xD2691E
    GOLDENROD = 0xDAA520


class PresenceType(Enum):
    PLAYING = 0
    STREAMING = 1
    LISTENING = 2


class PresenceStatus(Enum):
    ONLINE = "online"
    IDLE = "idle"
    DND = "dnd"
    INVISIBLE = "invisible"


class AllowedMentions(Enum):
    ROLES = "roles"
    USERS = "users"
    EVERYONE = "everyone" # Includes @here
    NOBODY = {
        "parse": []
    }
    SELECTIVE = {
        "parse": [],
        "users": [],
        "roles": []
    }


class PollLayoutStyle(Enum):
    DEFAULT = 1


class InteractionType(Enum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class InteractionResponseType(Enum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9


class ApplicationCommandOptionType(Enum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10
    ATTACHMENT = 11


class ComponentType(Enum):
    ACTION_ROW = 1
    BUTTON = 2
    STRING_SELECT = 3
    TEXT_INPUT = 4
    USER_SELECT = 5
    ROLE_SELECT = 6
    MENTIONABLE_SELECT = 7
    CHANNEL_SELECT = 8


class ButtonStyle(Enum):
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5


class TextInputStyle(Enum):
    SHORT = 1
    PARAGRAPH = 2