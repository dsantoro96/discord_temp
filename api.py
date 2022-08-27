import time
import requests
import dateparser

from datetime import datetime
from dataclasses import dataclass
from multiprocessing import Process
from utils import RequestMethod, DISCORD_API_URL

@dataclass
class JsonResponse():
    status_code: int
    content: object

    def __init__(self, response: requests.Response):
        self.status_code = response.status_code
        self.content = response.json() if response.content else None

    def __repr__(self):
        return f"JsonResponse({self.status_code}, {self.content})"

class DiscordApi:

    def __init__(self, token: str) -> None:
        self._token = token

    def _request(self, method: RequestMethod, path: str, params: object = None, headers: object = {}, json: object = None, data: object = None):
        url = f"{DISCORD_API_URL}{path}"
        headers["Authorization"] = f"Bot {self._token}"
        response = requests.request(method=method, url=url, headers=headers, params=params, json=json, data=data)
        return JsonResponse(response)

    def get_channel(self, channel_id: str) -> JsonResponse:
        path = f"/channels/{channel_id}"
        return self._request(RequestMethod.GET, path=path)

    def get_channel_messages(self, channel_id: str, params: object = None):
        path = f"/channels/{channel_id}/messages"
        return self._request(RequestMethod.GET, path=path, params=params)

    def get_all_channel_messages(self, channel_id: str):
        response = self.get_channel_messages(channel_id, {"limit": 100})
        res = response
        while len(res.content) == 100:
            last_message = res.content[-1]
            message_id = last_message["id"]
            res = self.get_channel_messages(channel_id, {"limit": 100, "before": message_id})
            response.content = response.content + res.content

        return response

    def get_channel_message(self, channel_id: str, message_id: str):
        path = f"/channels/{channel_id}/messages/{message_id}"
        return self._request(RequestMethod.GET, path=path)

    def create_message(self, channel_id: str, json: object):
        path = f"/channels/{channel_id}/messages"
        headers = {
            "Content-Type": "application/json"
        }
        return self._request(RequestMethod.POST, path=path, headers=headers, json=json)

    def delete_messages(self, channel_id: str, messages: list):
        path = f"/channels/{channel_id}/messages/bulk-delete"
        headers = {
            "Content-Type": "application/json"
        }
        return self._request(RequestMethod.POST, path=path, headers=headers, json={"messages": messages})

    def pin_message(self, channel_id: str, message_id: str):
        path = f"/channels/{channel_id}/pins/{message_id}"
        return self._request(RequestMethod.PUT, path=path)

    def edit_message(self, channel_id: str, message_id: str, json: object):
        path = f"/channels/{channel_id}/messages/{message_id}"
        return self._request(RequestMethod.PATCH, path=path, json=json)

    def delete_message(self, channel_id: str, message_id: str):
        path = f"/channels/{channel_id}/messages/{message_id}"
        return self._request(RequestMethod.DELETE, path=path)

    def unpin_message(self, channel_id: str, message_id: str):
        path = f"/channels/{channel_id}/pins/{message_id}"
        return self._request(RequestMethod.DELETE, path=path)

    def _delete_single_messages(self, channel_id: str, messages: list):
        for message in messages:
            self.delete_message(channel_id, message["id"])

    def _delete_bulk_messages(self, channel_id: str, messages_list: list):
        for messages in messages_list:
            ids = [message["id"] for message in messages]
            res = self.delete_messages(channel_id, ids)
            if res.status_code == 429:
                time.sleep(res.content["retry_after"] / 1000)
                self.delete_messages(channel_id, ids)

    def delete_messagesso(self, channel_id: str, messages: list):
        bulk = []
        single = []

        for message in messages:
            date = dateparser.parse(message["timestamp"])
            date = date.replace(tzinfo=None)
            time_diff = datetime.now() - date
            if time_diff.days > 14:
                single.append(message)
            else:
                bulk.append(message)

        bulk = [bulk[i:i + 99] for i in range(0, len(bulk), 99)]

        if len(bulk) == 1 and len(bulk[0]) == 1:
            single = single + bulk[0]
            bulk = []

        if single:
            old_proc = Process(target=self._delete_single_messages, args=(channel_id, single))
            old_proc.start()
        if bulk:
            new_proc = Process(target=self._delete_bulk_messages, args=(channel_id, bulk))
            new_proc.start()

    def create_interaction_response(self, interaction: object, data: object):
        interaction_id = interaction["id"]
        interaction_token = interaction["token"]
        path = f"/interactions/{interaction_id}/{interaction_token}/callback"
        return self._request(RequestMethod.POST, path, json=data)

    def create_global_command(self, application_id: str, data: object):
        path = f"/applications/{application_id}/commands"
        return self._request(RequestMethod.POST, path, json=data)

    def get_global_commands(self, application_id: str):
        path = f"/applications/{application_id}/commands"
        return self._request(RequestMethod.GET, path)

    def delete_global_command(self, application_id: str, command_id: str):
        path = f"/applications/{application_id}/commands/{command_id}"
        return self._request(RequestMethod.DELETE, path)
