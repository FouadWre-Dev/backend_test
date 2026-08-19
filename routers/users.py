from fastapi import APIRouter,WebSocket,WebSocketDisconnect,Depends
from services.appservice import connectionmanager
from services.users import check_login,reply_sold

router = APIRouter()

MANAGER = connectionmanager()






@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    ws: WebSocket,
    client_id: str,
):
    await MANAGER.connect(ws, client_id)

    try:
        while True:
            msg = await ws.receive_json()

            match msg.get("type"):

                case "message":
                    await MANAGER.send_message(
                        client_id,
                        msg.get("text", ""),
                    )

    except WebSocketDisconnect as exc:
        print(f"Client {client_id} disconnected: {exc.code}")
        MANAGER.disconnect(client_id)




@router.post("/login/{user_id}")
async def user_login(user=Depends(check_login)):
    return user


@router.get("/sold")
async def user_sold(token = Depends(reply_sold)):
    return token