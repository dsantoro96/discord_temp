from enum import Enum

class DispatchType(str, Enum):
    READY = "READY"
    TYPING_START = "TYPING_START"
    MESSAGE_CREATE = "MESSAGE_CREATE"
    INTERACTION_CREATE = "INTERACTION_CREATE"

class MessageOpcode(int, Enum):
    DISPATCH = 0
    HEARTBEAT = 1

    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6

    RECONNECT = 7

    REQUEST_GUILD_MEMBERS = 8

    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11

class RequestMethod(str, Enum):
    GET = "GET"
    PUT = "PUT"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"

class InteractionType(int, Enum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5

class InteractionCallbackType(int, Enum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    EFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9

GATEWAY_URL = "wss://gateway.discord.gg"
DISCORD_API_URL = "https://discord.com/api/v10"

LIB_NAME = "test-dis-todo"
