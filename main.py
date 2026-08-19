from fastapi import FastAPI,Request,responses
from routers.users import router as routerusers
from contextlib import asynccontextmanager



@asynccontextmanager
async def Lifespan(app:FastAPI):

    app.state.config = {
        "debbug" : True
    }

    print("running")
    yield
    print("end")




app = FastAPI(lifespan=Lifespan)
app.include_router(
    routerusers,
    prefix="/api/v1",
    tags=["Users"]
)


@app.middleware("http")
async def ban_log(request:Request , next_call):

    if request.client.host == "127.0.0.2" :
        create_log(f"{request.client.host} | {request.method}  --> Banned \n" )
        return responses.JSONResponse(
            content={
            "status" : "ip is banned"
            },
            status_code= 401

        ) 

    response = await next_call(request)

    create_log(f"{request.client.host} | {request.method} \n" )

    return response


def create_log(log:str):
    with open("logs/rapports.log" , "a") as f :
        f.write(log)




