import logging
from datetime import datetime, timedelta
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from bson import ObjectId

from utils.db import Database
from models.m_beacon import *
from utils.auth import *

router = APIRouter()


# 7. POST /beacons
#    - Description: Add a new beacon and associated it with particular gateway_owner_id .
#    - Request Body: List of beacon objects.
#    - Response: List of created beacon objects.

@router.post("/add-beacons/{gateway_owner_id:str}", tags=["beacons"])
async def register_beacon( beacon: NewBeaconRegistration, gateway_owner_id: str, current_user: dict = Depends(get_current_admin_user)):
    
    #check whether that gateway id exists or not
    try:
        db1 = Database("isc", "gateways")
        collection1 = await db1.make_connection()
        gateway = collection1.find_one({"_id": ObjectId(gateway_owner_id)})
        if not gateway:
            logging.info(f"Gateway {gateway_owner_id} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Gateway not found, please provide correct details",
                    "response": "Gateway not found",
                },
            )
        await db1.close_connection()
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
    
    try:
        db = Database("isc", "beacons")
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
        # Insert beacon details into MongoDB
        beacon_data = beacon.dict()
        beacon_data["registered_on"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        beacon_data["last_updated"] = None
        beacon_data["gateway_owner_id"] = ObjectId(gateway_owner_id)
        inserted_beacon = collection.insert_one(beacon_data)
        logging.info(f"Beacon created successfully with id: {inserted_beacon.inserted_id}")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Beacon created successfully",
                "response": "New beacon added",
            },
        )
    except Exception as e:
        logging.error(f"Error creating beacon: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# 8. PUT /beacons/{beacon_id}
#    - Description: Update information about a specific beacon.
#    - Request Body: Updated beacon object.
#    - Response: Updated beacon object.

@router.put("/update-beacons/{beacon_id:str}", tags=["beacons"])
async def update_beacon( beacon: BeaconUpdate, beacon_id: str, current_user: dict = Depends(get_current_admin_user)):
    try:
        db = Database("isc", "beacons")
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
        beacon = beacon.dict(exclude_unset=True)
        # Update beacon details
        beacon["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_beacon = collection.update_one(
            {"_id": ObjectId(beacon_id)},
            {"$set": beacon},
        )

        if updated_beacon.modified_count == 0:
            logging.info(f"Beacon {current_user['username']} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Beacon details not updated",
                    "response": "Beacon not found",
                },
            )
        logging.info(f"Beacon {current_user['username']} updated successfully")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Beacon details updated successfully",
                "response": "Beacon details updated successfully",
            },
        )
    except Exception as e:
        logging.error(f"Error updating beacon: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )

#5. GET /all-beacons
#    - Description: Get information about all beacons associated with the gateway_id.
#    - Response: List of beacon objects.

@router.get("/all-beacons/{gateway_owner_id:str}", tags=["beacons"])
async def get_beacons(gateway_owner_id: str, current_user: dict = Depends(get_current_admin_user)):
    try:
        db = Database("isc", "beacons")
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
        # Get all beacons associated with the gateway
        beacons = collection.find({"gateway_owner_id": ObjectId(gateway_owner_id)})
        beacons = list(beacons)
        for beacon in beacons:
            beacon["_id"] = str(beacon["_id"])
            beacon["gateway_owner_id"] = str(beacon["gateway_owner_id"])
        logging.info(f"Beacons found: {beacons}")
        await db.close_connection()
        if not beacons:
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Beacons not found",
                    "response": "No beacons found",
                },
            )
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Beacons found",
                "response": beacons,
            },
        )
    except Exception as e:
        logging.error(f"Error getting beacons: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# 6. GET /beacons/{beacon_id}
#    - Description: Get information about a specific beacon.
#    - Response: Beacon object.

@router.get("/beacons/{beacon_id:str}", tags=["beacons"])
async def get_beacon(beacon_id: str, current_user: dict = Depends(get_current_admin_user)):
    try:
        db = Database("isc", "beacons")
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
        # Get one beacon
        beacon = collection.find_one({"_id": ObjectId(beacon_id)})
        if not beacon:
            logging.info(f"Beacon {current_user['username']} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Beacon not found",
                    "response": "Beacon not found",
                },
            )
        beacon["_id"] = str(beacon["_id"])
        beacon["gateway_owner_id"] = str(beacon["gateway_owner_id"])
        logging.info(f"Beacon found: {beacon}")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Beacon found",
                "response": beacon,
            },
        )
    except Exception as e:
        logging.error(f"Error getting beacon: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
