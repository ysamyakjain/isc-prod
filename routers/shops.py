import logging
from datetime import datetime, timedelta
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from bson import ObjectId


from utils.db import Database
from models.m_shop import *
from utils.auth import *

router = APIRouter()


# route to register a NewShopRegistration
@router.post("/new-shop-registration", tags=["shops"])
async def new_shop_registeration(
    shop: NewShopRegistration, current_user: dict = Depends(get_current_admin_user)
) -> JSONResponse:
    try:
        db = Database("isc", "shops")
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
        # Insert shop details into MongoDB
        shop_data = shop.model_dump()
        shop_data["registered_on"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shop_data["last_updated"] = None
        shop_data["owner"] = current_user["id"]
        shop_data["shop_unique_id"] = await generate_unique_uuid()
        shop_data["events_under_shop"] = []
        shop_data["shop_status"] = "active"
        inserted_shop = collection.insert_one(shop_data)
        logging.info(
            f"Shop registered successfully with id: {inserted_shop.inserted_id}"
        )
        await db.close_connection()

        # inserting the shop id into the admin collection
        try:
            db = Database("isc", "owners")
            collection = await db.make_connection()
            collection.update_one(
                {"unique_id": current_user["id"]},
                {"$push": {"shops_owned": shop_data["shop_unique_id"]}},
            )
            logging.info(f"Admin {current_user['username']} updated successfully")
            await db.close_connection()
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
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Shop registered successfully",
                "response": "New shop added",
            },
        )
    except Exception as e:
        logging.error(f"Error registering shop: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# route to update the shop details
@router.put("/update-shop/{shop_id:str}", tags=["shops"])
async def update_shop_details(
    shop: UpdateShopDetails,
    shop_id: str,
    current_user: dict = Depends(get_current_admin_user),
) -> JSONResponse:
    try:
        db = Database("isc", "shops")
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
        shop = shop.model_dump(exclude_unset=True)
        # Update shop details
        shop["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_shop = collection.update_one(
            {"shop_unique_id": shop_id, "shop_status": "active"},
            {"$set": shop},
        )
        if updated_shop.modified_count == 0:
            logging.info(f"Shop {current_user['username']} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Shop details not updated",
                    "response": "Shop not found",
                },
            )
        logging.info(f"Shop {current_user['username']} updated successfully")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Shop details updated successfully",
                "response": "Shop details updated successfully",
            },
        )
    except Exception as e:
        logging.error(f"Error updating shop: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# get all shops
@router.get("/get-all-shops", tags=["shops"])
async def get_all_shops_associated_with_the_current_user(
    current_user: dict = Depends(get_current_admin_user),
) -> JSONResponse:
    try:
        db = Database("isc", "shops")
        collection = await db.make_connection()
        shops = collection.find(
            {"owner": current_user["id"], "shop_status": "active"},
            {"_id": 0, "owner": 0, "events_under_shop": 0},
        )
        shops_list = list(shops)
        logging.info(f"Shops found: {shops_list}")
        if not shops_list:
            logging.info(f"No shops found for {current_user['username']}")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Shops not found",
                    "response": "No shops found for this User",
                },
            )
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Shops found",
                "response": shops_list,
            },
        )
    except Exception as e:
        logging.error(f"Error getting shops: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# get one shop
@router.get("/get-shop/{shop_id:str}", tags=["shops"])
async def get_a_shop_details(
    shop_id: str, current_user: dict = Depends(get_current_admin_user)
) -> JSONResponse:
    try:
        db = Database("isc", "shops")
        collection = await db.make_connection()
        shop = collection.find_one(
            {"shop_unique_id": shop_id, "shop_status": "active"},
            {"_id": 0, "owner": 0, "events_under_shop": 0},
        )
        logging.info(f"Shop found: {shop}")
        if not shop:
            logging.info(f"Shop not found for {current_user['username']}")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Shop not found",
                    "response": "Shop not found, may be it's not active or deleted by the owner",
                },
            )
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Shop found",
                "response": shop,
            },
        )
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


# delete shop
@router.delete("/delete-shop/{shop_id:str}", tags=["shops"])
async def delete_shop_details(
    shop_id: str, current_user: dict = Depends(get_current_admin_user)
) -> JSONResponse:
    try:
        db = Database("isc", "shops")
        collection = await db.make_connection()
        shop = collection.find_one({"shop_unique_id": shop_id})
        if not shop:
            logging.info(f"Shop not found for {current_user['username']}")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Shop not found",
                    "response": "Shop not found for this User",
                },
            )
        deleted_shop = collection.update_one(
            {"shop_unique_id": shop_id, "shop_status": "active"},
            {
                "$set": {
                    "shop_status": "inactive",
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            },
        )
        logging.info(deleted_shop)
        if deleted_shop.modified_count == 0:
            logging.info(f"Shop {current_user['username']} not found")
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Shop not deleted",
                    "response": "Shop not found",
                },
            )
        logging.info(f"Shop {current_user['username']} deleted successfully")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Shop deleted successfully",
                "response": "Shop deleted successfully",
            },
        )
    except Exception as e:
        logging.error(f"Error deleting shop: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
