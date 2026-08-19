from fastapi import APIRouter,WebSocket,WebSocketDisconnect,Depends
from services.appservice import connectionmanager
from services.users import check_login,reply_sold

router = APIRouter()

MANAGER = connectionmanager()






@router.websocket("/ws/{client_id}")
async def websocket_endpoint(ws:WebSocket,client_id:str) :
    await MANAGER.accept(ws,client_id)

    try:
        while True:
            msg = ws.receive_json()
            match msg.get("type"):
                case "message":
                    MANAGER.message(client_id)

    except WebSocketDisconnect as err_desconnected :
        print(err_desconnected.code)
        MANAGER.desconnect(client_id)





@router.post("/login/{user_id}")
async def user_login(user=Depends(check_login)):
    return user


@router.get("/sold")
async def user_sold(token = Depends(reply_sold)):
    return token