import logging
from datetime import datetime, timedelta
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from utils.db import Database
from models.m_deal import *
from utils.auth import *

router = APIRouter()


# create a deal under a shop
@router.post("/create-deal/{shop_id:str}", tags=["Events"])
async def create_event(
    shop_id: str,
    deal: RegisterNewDeal,
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
        deal_unique_id = await generate_unique_uuid()
        collection1.update_one(
            {"shop_unique_id": shop_id, "shop_status": "active"},
            {"$push": {"deals_under_shop": deal_unique_id}},
        )
        await db1.close_connection()
        db = Database("isc", "deals")
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
        # Insert deal details into MongoDB
        deal_data = deal.model_dump()
        deal_data["is_active"] = True
        deal_data["registered_on"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        deal_data["last_updated"] = None
        deal_data["deal_unique_id"] = deal_unique_id
        deal_data["shop_owner"] = shop_id
        inserted_deal = collection.insert_one(deal_data)
        logging.info(f"Deal created successfully with id: {inserted_deal.inserted_id}")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Deal created successfully",
                "response": "New deal added",
            },
        )
    except Exception as e:
        logging.error(f"Error creating deal: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# update a deal
@router.put("/update-deal/{deal_id:str}", tags=["Events"])
async def update_event(
    deal: UpdateDeal,
    deal_id: str,
    current_user: dict = Depends(get_current_admin_user),
) -> JSONResponse:
    try:
        db = Database("isc", "deals")
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
        deal = deal.model_dump(exclude_unset=True)
        # Update deal details
        deal["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_deal = collection.update_one(
            {"deal_unique_id": deal_id, "is_active": True},
            {"$set": deal},
        )

        if updated_deal.modified_count == 0:
            logging.info(f"Deal {current_user['username']} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Deal details not updated",
                    "response": "Deal not found",
                },
            )
        logging.info(f"Deal {current_user['username']} updated successfully")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Deal details updated successfully",
                "response": "Deal details updated successfully",
            },
        )
    except Exception as e:
        logging.error(f"Error updating deal: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# get all deals
@router.get("/get-all-deals/{shop_id:str}", tags=["Events"])
async def get_all_events(
    shop_id: str, current_user: dict = Depends(get_current_admin_user)
) -> JSONResponse:
    try:
        db = Database("isc", "deals")
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
        # get all deals associated with the shop
        deals = collection.find(
            {"shop_owner": shop_id, "is_active": True}, projection={"_id": 0}
        )
        deals = list(deals)
        logging.info(f"Deals found: {deals}")
        await db.close_connection()
        if not deals:
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Deals not found",
                    "response": "No deals found",
                },
            )
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Deals found",
                "response": deals,
            },
        )
    except Exception as e:
        logging.error(f"Error getting deals: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# get a deal
@router.get("/get-deal/{deal_id:str}", tags=["Events"])
async def get_a_event(
    deal_id: str,
    current_user: dict = Depends(get_current_admin_user),
) -> JSONResponse:
    try:
        db = Database("isc", "deals")
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
        # Get one deal and check if it is active and end_date has not been surpassed
        deal = collection.find_one(
            {"deal_unique_id": (deal_id), "is_active": True}, projection={"_id": 0}
        )
        if (
            not deal
            or datetime.strptime(deal["end_date"], "%Y-%m-%d %H:%M:%S") < datetime.now()
        ):
            logging.info(
                f"Deal {deal_id} not found or not active or end_date surpassed"
            )
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "No Deals found",
                    "response": "Deal not found or not active or end_date surpassed",
                },
            )

        logging.info(f"Deal found: {deal}")
        await db.close_connection()

        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Deal found",
                "response": deal,
            },
        )
    except Exception as e:
        logging.error(f"Error getting deal: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# delete a deal
@router.delete("/delete-deal/{deal_id:str}", tags=["Events"])
async def delete_a_event(
    deal_id: str,
    current_user: dict = Depends(get_current_admin_user),
) -> JSONResponse:
    try:
        db = Database("isc", "deals")
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
        updated_deal = collection.update_one(
            {"deal_unique_id": (deal_id)},
            {"$set": {"is_active": False}},
        )

        if updated_deal.modified_count == 0:
            logging.info(f"Deal {current_user['username']} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Deal not deleted",
                    "response": "Deal not found",
                },
            )
        logging.info(f"Deal {current_user['username']} deleted successfully")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Deal deleted successfully",
                "response": "Deal deleted successfully",
            },
        )
    except Exception as e:
        logging.error(f"Error deleting deal: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
