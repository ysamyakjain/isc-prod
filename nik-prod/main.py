import logging
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI, Request, HTTPException, status

from utils import *
from routers import users, admins, shops, deals, gateways, beacons, users_shop_n_deals

app = FastAPI()

# Configure the logging format and level
logging.basicConfig(
    level=logging.INFO,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# custom error handler for validation errors coming from pydantic
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = [
        {"field": error["loc"][-1], "message": error["msg"]} for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": False,
            "message": "Validation error",
            "response": error_messages,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "message": "HTTP exception",
            "response": str(exc.detail),
        },
    )


@app.get("/", tags=["Created with ❤️ by Samyak"])
async def Below_are_all_the_APIs():
    return {"message": "Created with ❤️ by Samyak."}


#including the routes from routers/users.py
app.include_router(users.router)

#including the routes from routers/admins.py
app.include_router(admins.router)

#including the routes from routers/shops.py
app.include_router(shops.router)

#including the routes from routers/deals.py
app.include_router(deals.router)


#including the routes from routers/gateways.py
app.include_router(users_shop_n_deals.router)

#including the routes from routers/gateways.py
#app.include_router(gateways.router)

#including the routes from routers/beacons.py
#app.include_router(beacons.router)
