from api import DiscordApi
from gateway import Gateway
from utils import InteractionCallbackType

TODO = '☐'
DONE = '☒'
SEPARATOR = " | "

DONE_COMPONENT = {
    "type": 2,
    "custom_id": 'done',
    "label": "✔️",
    "style": 2,
}

UNDO_COMPONENT = {
    "type": 2,
    "custom_id": 'undo',
    "label": "↩️",
    "style": 2,
}

EDIT_COMPONENT = {
    "type": 2,
    "custom_id": 'edit',
    "label": "✏️",
    "style": 2,
}

DELETE_COMPONENT = {
    "type": 2,
    "custom_id": 'delete',
    "label": "❌",
    "style": 2,
}

with open(".token", 'r') as file:
    token = file.read()

gateway = Gateway(token)
api = DiscordApi(token)

def split_content(content: str) -> list:
    box = content[0]
    separator = content[1:4]
    text = content[4:]

    return [box, separator, text]

def do_undo_text(content: str, strike: bool) -> str:
    if strike:
        return "~~" + content + "~~"
    else:
        return content[2:-2]

def get_new_content(content: str, done: bool) -> str:
    splits = split_content(content)
    splits[0] = DONE if done else TODO
    splits[2] = do_undo_text(splits[2], done)
    return "".join(splits)

def get_data(content: str, components: list):
    return {
        "content": content,
        "components": [
            {
                "type": 1,
                "components": components
            }
        ]
    }

@gateway.command("!")
def todo(msg, content):
    if content:
        api.delete_message(msg["channel_id"], msg["id"])
        full_content = f"{TODO}{SEPARATOR}{content}"
        components = [DONE_COMPONENT, EDIT_COMPONENT, DELETE_COMPONENT]
        data = get_data(full_content, components)
        api.create_message(msg["channel_id"], data)

@gateway.interaction
def done(ctx):
    content = ctx["message"]["content"]
    full_content = get_new_content(content, True)
    components = [UNDO_COMPONENT, DELETE_COMPONENT]
    inner_data = get_data(full_content, components)
    data = {
        "type": InteractionCallbackType.UPDATE_MESSAGE,
        "data": inner_data
    }
    api.create_interaction_response(ctx, data)

@gateway.interaction
def undo(ctx):
    content = ctx["message"]["content"]
    full_content = get_new_content(content, False)
    components = [DONE_COMPONENT, EDIT_COMPONENT, DELETE_COMPONENT]
    inner_data = get_data(full_content, components)
    data = {
        "type": InteractionCallbackType.UPDATE_MESSAGE,
        "data": inner_data
    }
    api.create_interaction_response(ctx, data)

@gateway.interaction
def delete(ctx):
    channel_id = ctx["channel_id"]
    message_id = ctx["message"]["id"]
    api.delete_message(channel_id, message_id)

@gateway.interaction
def edit(ctx):
    content = split_content(ctx["message"]["content"])[2]
    data = {
        "type": InteractionCallbackType.MODAL,
        "data": {
            "title": "Edit TODO.",
            "custom_id": "edit_modal",
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 4,
                            "custom_id": 'edit_modal_text',
                            "label": "Insert TODO here.",
                            "style": 2,
                            "value": content,
                            "min_length": 1,
                            "max_length": 4000,
                            "placeholder": 'TODO',
                            "required": True
                        }
                    ],
                }
            ]
        }
    }
    api.create_interaction_response(ctx, data)

@gateway.interaction
def edit_modal(ctx):
    modal_content = ctx["data"]["components"][0]["components"][0]["value"]
    full_content = f"{TODO}{SEPARATOR}{modal_content}"
    components = [DONE_COMPONENT, EDIT_COMPONENT, DELETE_COMPONENT]
    inner_data = get_data(full_content, components)
    data = {
        "type": InteractionCallbackType.UPDATE_MESSAGE,
        "data": inner_data
    }
    api.create_interaction_response(ctx, data)

gateway.run()
