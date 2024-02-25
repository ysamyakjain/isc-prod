import logging
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from utils.db import Database
from models.m_event import *
from utils.auth import *

router = APIRouter()


# create a event under a shop
@router.post("/create-event/{shop_id:str}", tags=["Events"])
async def create_event(
    shop_id: str,
    event: RegisterNewEvent,
    current_user: dict = Depends(get_current_admin_user),
) -> JSONResponse:

    # check whether that shop id exists or not
    try:
        db1 = Database("isc", "shops")
        collection1 = await db1.make_connection()
        shop = collection1.find_one(
            {"shop_unique_id": shop_id, "shop_status": "active"}
        )
        if not shop:
            logging.info(f"Shop {shop_id} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Shop not found",
                    "response": "Shop not found, please enter a valid shop id",
                },
            )
        event_unique_id = await generate_unique_uuid()
        collection1.update_one(
            {"shop_unique_id": shop_id, "shop_status": "active"},
            {"$push": {"events_under_shop": event_unique_id}},
        )
        await db1.close_connection()
        db = Database("isc", "events")
        collection = await db.make_connection()

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
        # Insert event details into MongoDB
        deal_data = event.model_dump()
        deal_data["is_active"] = True
        deal_data["registered_on"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        deal_data["last_updated"] = None
        deal_data["event_unique_id"] = event_unique_id
        deal_data["shop_owner"] = shop_id
        inserted_deal = collection.insert_one(deal_data)
        logging.info(f"event created successfully with id: {inserted_deal.inserted_id}")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "event created successfully",
                "response": "New event added",
            },
        )
    except Exception as e:
        logging.error(f"Error creating event: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# update a event
@router.put("/update-event/{event_id:str}", tags=["Events"])
async def update_event(
    event: UpdateEvent,
    event_id: str,
    current_user: dict = Depends(get_current_admin_user),
) -> JSONResponse:
    try:
        db = Database("isc", "events")
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
        event = event.model_dump(exclude_unset=True)
        # Update event details
        event["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_event = collection.update_one(
            {"event_unique_id": event_id, "is_active": True},
            {"$set": event},
        )

        if updated_event.modified_count == 0:
            logging.info(f"event {current_user['username']} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "event details not updated",
                    "response": "event not found",
                },
            )
        logging.info(f"event {current_user['username']} updated successfully")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "event details updated successfully",
                "response": "event details updated successfully",
            },
        )
    except Exception as e:
        logging.error(f"Error updating event: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# get all events
@router.get("/get-all-events/{shop_id:str}", tags=["Events"])
async def get_all_events(
    shop_id: str, current_user: dict = Depends(get_current_admin_user)
) -> JSONResponse:
    try:
        db = Database("isc", "events")
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
        # get all events associated with the shop
        events = collection.find(
            {"shop_owner": shop_id, "is_active": True}, projection={"_id": 0}
        )
        events = list(events)
        logging.info(f"events found: {events}")
        await db.close_connection()
        if not events:
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "events not found",
                    "response": "No events found",
                },
            )
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "events found",
                "response": events,
            },
        )
    except Exception as e:
        logging.error(f"Error getting events: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# get a event
@router.get("/get-event/{event_id:str}", tags=["Events"])
async def get_a_event(
    event_id: str,
    current_user: dict = Depends(get_current_admin_user),
) -> JSONResponse:
    try:
        db = Database("isc", "events")
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
        # Get one event and check if it is active and end_date has not been surpassed
        event = collection.find_one(
            {"event_unique_id": (event_id), "is_active": True}, projection={"_id": 0}
        )
        if (
            not event
            or datetime.strptime(event["end_date"], "%Y-%m-%d %H:%M:%S") < datetime.now()
        ):
            logging.info(
                f"event {event_id} not found or not active or end_date surpassed"
            )
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "No events found",
                    "response": "event not found or not active or end_date surpassed",
                },
            )

        logging.info(f"event found: {event}")
        await db.close_connection()

        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "event found",
                "response": event,
            },
        )
    except Exception as e:
        logging.error(f"Error getting event: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# delete a event
@router.delete("/delete-event/{event_id:str}", tags=["Events"])
async def delete_a_event(
    event_id: str,
    current_user: dict = Depends(get_current_admin_user),
) -> JSONResponse:
    try:
        db = Database("isc", "events")
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
    # updating is_active to False
    try:
        updated_event = collection.update_one(
            {"event_unique_id": (event_id)},
            {"$set": {"is_active": False}},
        )

        if updated_event.modified_count == 0:
            logging.info(f"event {current_user['username']} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "event not deleted",
                    "response": "event not found",
                },
            )
        logging.info(f"event {current_user['username']} deleted successfully")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "event deleted successfully",
                "response": "event deleted successfully",
            },
        )
    except Exception as e:
        logging.error(f"Error deleting event: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
