
from fastapi import Depends,responses,status,HTTPException
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime,timezone,timedelta


p_hash = PasswordHash.recommended()
keyjwt = "FouadWre-Dev"
algorithm = "HS256"


bearerauth = OAuth2PasswordBearer(tokenUrl="/sold")

USERS = {
    "azerty123456":{
        "username" : "mahmoud",
        "password" : p_hash.hash("123456789"),
        "age": 30,
        "sold": 1500

    },
    "azerty888":{
        "username" : "hakim",
        "password" : p_hash.hash("12345"),
        "age": 30,
        "sold": 70

    },
}



async def check_login(user_id:str, user=Depends(OAuth2PasswordRequestForm)):

    Currentuser = USERS.get(user_id)
    if Currentuser:
        if (user.username == Currentuser.get("username") and 
            p_hash.verify(
                user.password,
                Currentuser.get("password")
            )
            ):

            accesstoken = create_access_token(user_id)

            return {
                "accesstoken" : accesstoken ,
                "status" : True,
                "text": "welcom to hakim servers"
            }
        else:
            return responses.JSONResponse(
                content={
                    "status" : False,
                    "text": "username or password invalid"
                },
                status_code=401
            )

    return responses.JSONResponse(
        content={
            "status" : False,
            "text": "this user is not found .. pls contact me for activated compte"
        },
        status_code=401
    )

async def reply_sold(token:str=Depends(bearerauth)):
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    user = USERS.get(user_id)

    username = user.get("username")
    sold = user.get("sold")

    return {
        "status": True,
        "username": username,
        "sold" : sold
    }




def create_access_token(user_id:str):
    expiry = datetime.now(timezone.utc) + timedelta(minutes=2)
    payload = {
        "exp": expiry,
        "sub": user_id
    }
    return jwt.encode(
        payload,
        keyjwt,
        algorithm=algorithm

    )

def decode_access_token(token:str):
    try:
        payload = jwt.decode(
            token,
            keyjwt,
            algorithms=[algorithm]
        )

        return payload

    except InvalidTokenError:
        return responses.JSONResponse(
            content={
                "status": False,
                "text": "invalid token",
            },
            status_code=401
        )
    


