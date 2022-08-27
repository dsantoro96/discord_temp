import json
import utils
import asyncio
import logging
import websockets

from utils import DispatchType, InteractionType, MessageOpcode

class Gateway():

    def __init__(self, token: str, session_id: str = None, sequence: int = None):
        self._running = False
        self._send_q = asyncio.Queue()
        self._res_q = asyncio.Queue()
        self._token = token
        self._pulse = 20
        self._session_id = session_id
        self._sequence = sequence
        self._reconnect = False
        self._commands = {}
        self._interactions = {}
        self.application_id = None

    async def _open_ws(self):
        self._running = True
        wsuri = f"{utils.GATEWAY_URL}/?v=9&encoding=json"
        self._ws = await websockets.connect(wsuri)

    async def _close_ws(self):
        self._running = False
        await self._ws.close()

    async def _run(self):
        await asyncio.gather(
            self._send(),
            self._recv(),
            self._ping(),
            self._resp()
        )

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._open_ws())

        try:
            loop.run_until_complete(self._run())
        except:
            pass
        finally:
            loop.run_until_complete(self._close_ws())

        return (self._token, self._session_id, self._sequence)

    async def _identify(self):
        i_msg = {
            "op": 2,
            "d": {
                "token": self._token,
                "intents": 3584,
                "properties": {
                    "os": "linux",
                    "browser": utils.LIB_NAME,
                    "device": utils.LIB_NAME
                }
            }
        }
        await self.send(i_msg)

    async def _resume(self):
        r_msg = {
            "op": 6,
            "d": {
                "token": self._token,
                "session_id": self._session_id,
                "seq": self._sequence,
            }
        }
        await self.send(r_msg)

    async def handle_msg(self, msg):
        j_msg = json.loads(msg)
        print(j_msg)
        match j_msg["op"]:
            case MessageOpcode.DISPATCH:
                match j_msg["t"]:
                    case DispatchType.READY: 
                        self._session_id = j_msg["d"]["session_id"]
                        self.application_id = j_msg["d"]["application"]["id"]
                    case DispatchType.TYPING_START:
                        logging.info("TYPING_START")
                    case DispatchType.MESSAGE_CREATE:
                        data = j_msg["d"]
                        if data["content"]:
                            full_content = data["content"].split()
                            first = full_content[0]
                            prefix = first[0]
                            command = first[1:]
                            content = " ".join(full_content[1:]) if len(full_content) > 1 else None
                            if prefix in self._commands:
                                p_dict = self._commands[prefix]
                                if command in p_dict:
                                    fn = p_dict[command]
                                    await self._res_q.put({
                                        "fn": fn,
                                        "args": [data, content]
                                    })
                    case DispatchType.INTERACTION_CREATE:
                        ctx = j_msg["d"]
                        match ctx["type"]:
                            case InteractionType.PING:
                                logging.info("PING")
                            case InteractionType.APPLICATION_COMMAND:
                                logging.info("APPLICATION_COMMAND")
                            case InteractionType.MESSAGE_COMPONENT | InteractionType.MODAL_SUBMIT:
                                data = ctx["data"]
                                custom_id = data["custom_id"]
                                interaction = self._interactions[custom_id]
                                await self._res_q.put({
                                    "fn": interaction,
                                    "args": [ctx]
                                })
                            case InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE:
                                logging.info("APPLICATION_COMMAND_AUTOCOMPLETE")

                if j_msg["s"]:
                    self._sequence = j_msg["s"]

            case MessageOpcode.HEARTBEAT:
                await self._send_ping()
            case MessageOpcode.RECONNECT:
                self._reconnect = True
                await self._close_ws()
                await self._open_ws()
                self._reconnect = False
            case MessageOpcode.INVALID_SESSION:
                await asyncio.sleep(5)
                if j_msg["d"]:
                    await self._resume()
                else:
                    await self._identify()
            case MessageOpcode.HELLO:
                self._pulse = j_msg["d"]["heartbeat_interval"] / 1000
                if self._session_id is not None and self._sequence is not None:
                    await self._resume()
                else:
                    await self._identify()
            case MessageOpcode.HEARTBEAT_ACK:
                logging.info("HEARTBEAT ACK")
            case _:
                logging.error("Unhandled op: {}".format(j_msg["op"]))

    async def send(self, msg):
        await self._send_q.put(msg)

    async def _send_ping(self):
        ping_msg = {"op": 1, "d": self._sequence}
        await self._ws.send(json.dumps(ping_msg))

    async def _send(self):
        while self._running:
            try:
                msg = await self._send_q.get()
                msg_j = json.dumps(msg)
                print(msg_j)
                await self._ws.send(msg_j)
            except Exception as e:
                self._running = False
                logging.exception(e)

    async def _recv(self):
        while self._running:
            try:
                msg = await self._ws.recv()
                await self.handle_msg(msg)
            except Exception as e:
                self._running = False
                logging.exception(e)

    async def _ping(self):
        while self._running:
            if not self._reconnect:
                try:
                    await asyncio.sleep(self._pulse)
                    await self._send_ping()
                except Exception as e:
                    self._running = False
                    logging.exception(e)

    async def _resp(self):
        while self._running:
            o = await self._res_q.get()
            fn = o["fn"]
            args = o["args"]
            fn(*args)

    def command(self, prefix: str):
        def wrapper(fn):
            if prefix not in self._commands:
                self._commands[prefix] = {}

            self._commands[prefix][fn.__name__] = fn

        return wrapper

    def interaction(self, fn):
        self._interactions[fn.__name__] = fn
