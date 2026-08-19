
from fastapi import WebSocket
import json


class connectionmanager:
    def __init__(self):
        self.userconnection = {}

    async def accept(self,ws:WebSocket,client_id:str):
        await ws.accept()
        self.userconnection[client_id] = ws
    def desconnect(self,client_id:str):
        ws = self.userconnection.get(client_id)
        if ws:
            self.userconnection.pop(ws,None)

    async def message(self,client_id:str):
        ws = self.userconnection.get(client_id)
        if ws:
            ws.send_json(
                json.dumps(
                    {
                        "type":"message",
                        "text": "seccess recuv msg"
                    }
                )
            )




