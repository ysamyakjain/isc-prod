import logging
from datetime import datetime, timedelta
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from bson import ObjectId

from utils.db import Database
from models.m_gateway import *
from utils.auth import *


router = APIRouter()

#gateways and beacon apis
# 1. GET /gateways
#    - Description: Get information about all gateways associated with that shop_id.
#    - Response: List of gateway objects.


@router.get("/all-gateways/{shop_owner_id:str}", tags=["gateways"])
async def get_gateways(shop_owner_id:str, current_user: dict = Depends(get_current_admin_user)):
    try:
        db = Database("isc", "gateways")
        collection = await db.make_connection()
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
    try:
        # Get all gateways associated with the shop
        gateways = collection.find({"shop_owner_id": ObjectId(shop_owner_id)})
        gateways = list(gateways)
        for gateway in gateways:
            gateway["_id"] = str(gateway["_id"])
            gateway["shop_owner_id"] = str(gateway["shop_owner_id"])
        logging.info(f"Gateways found: {gateways}")
        await db.close_connection()
        if not gateways:
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Gateways not found",
                    "response": "No gateways found",
                },
            )
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Gateways found",
                "response": gateways,
            },
        )
    except Exception as e:
        logging.error(f"Error getting gateways: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
    
        
        

# 2. GET /gateways/?{gateway_id}
#    - Description: Get information about a specific gateway.
#    - Response: Gateway object.

@router.get("/gateways/{gateway_id:str}", tags=["gateways"])
async def get_gateway(gateway_id:str, current_user: dict = Depends(get_current_admin_user)):
    try:
        db = Database("isc", "gateways")
        collection = await db.make_connection()
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
    try:
        # Get one gateway
        gateway = collection.find_one({"_id": ObjectId(gateway_id)})
        logging.info(f"Gateway found: {gateway}")
        if not gateway:
            logging.info(f"Gateway {current_user['username']} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Gateway not found",
                    "response": "Gateway not found",
                },
            )
        gateway["_id"] = str(gateway["_id"])
        gateway["shop_owner_id"] = str(gateway["shop_owner_id"])
        logging.info(f"Gateway found: {gateway}")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Gateway found",
                "response": gateway,
            },
        )
    except Exception as e:
        logging.error(f"Error getting gateway: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )   
    


# 3. POST /gateways
#    - Description: Add a new gateway to a specific shop.
#    - Request Body: List of gateway objects.
#    - Response: success/failure.

@router.post("/register-gateways/{shop_owner_id:str}", tags=["gateways"])
async def register_gateway( gateway: NewGatewayRegistration, shop_owner_id: str, current_user: dict = Depends(get_current_admin_user)):
    #check whether that shop id exists or not
    try:
        db1 = Database("isc", "shops")
        collection1 = await db1.make_connection()
        shop = collection1.find_one({"_id": ObjectId(shop_owner_id)})
        if not shop:
            logging.info(f"Shop {shop_owner_id} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Shop not found",
                    "response": "Shop not found",
                },
            )
        await db1.close_connection()
    except Exception as e:
        logging.error(f"Error getting shop: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
    try:
        db = Database("isc", "gateways")
        collection = await db.make_connection()
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
    try:
        # Insert gateway details into MongoDB
        gateway_data = gateway.dict()
        gateway_data["registered_on"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gateway_data["last_updated"] = None
        gateway_data["shop_owner_id"] = ObjectId(shop_owner_id)
        inserted_gateway = collection.insert_one(gateway_data)
        logging.info(f"Gateway created successfully with id: {inserted_gateway.inserted_id}")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Gateway created successfully",
                "response": "New gateway added",
            },
        )
    except Exception as e:
        logging.error(f"Error creating gateway: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# 4. PUT /gateways/?{gateway_id}
#    - Description: Update information about a specific gateway.
#    - Request Body: Updated gateway object.
#    - Response: Updated gateway object.

@router.put("/update-gateways/{gateway_id:str}", tags=["gateways"])
async def update_gateway( gateway: GatewayUpdate, gateway_id: str, current_user: dict = Depends(get_current_admin_user)):
    try:
        db = Database("isc", "gateways")
        collection = await db.make_connection()
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
    try:
        gateway = gateway.dict(exclude_unset=True)
        # Update gateway details
        gateway["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_gateway = collection.update_one(
            {"_id": ObjectId(gateway_id)},
            {"$set": gateway},
        )

        if updated_gateway.modified_count == 0:
            logging.info(f"Gateway {current_user['username']} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Gateway details not updated",
                    "response": "Gateway not found",
                },
            )
        logging.info(f"Gateway {current_user['username']} updated successfully")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Gateway details updated successfully",
                "response": "Gateway details updated successfully",
            },
        )
    except Exception as e:
        logging.error(f"Error updating gateway: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )