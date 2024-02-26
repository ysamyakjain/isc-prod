import logging
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from utils.db import Database
from models.m_user import *
from utils.auth import *

router = APIRouter()


# get top 5 events
@router.get("/get-top-events", tags=["Events"])
async def get_top_events(
    sort_by_date: bool = Query(False, description="Sort events by date"),
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
        # Get top 5 events based on discount_percent
        events = collection.find({}, {"_id": 0})
        if sort_by_date:
            events = events.sort("date", 1)  # Sort events by date in ascending order
        events = events.limit(5)
        events = list(events)
        logging.info(f"Top 5 events found: {events}")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Top 5 events found",
                "response": events,
            },
        )
    except Exception as e:
        logging.error(f"Error getting top 5 events: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# search shops, events with optional query parameters, filters, sortby discount, sort by date (everything is optional)
@router.get("/search-everything", tags=["Search"])
async def search_shops_n_events(
    store_category: str = Query(None, description="Filter by store category"),
    city: str = Query(None, description="Filter by city"),
    state: str = Query(None, description="Filter by state"),
    zipcode: str = Query(None, description="Filter by zipcode"),
    country: str = Query(None, description="Filter by country"),
    store_type: str = Query(None, description="Filter by store type"),
    store_number: int = Query(None, description="Filter by store number"),
    tags: str = Query(None, description="Filter by tags"),
    store_name: str = Query(None, description="Search by store name"),
    event_name: str = Query(None, description="Search by event name"),
    category: str = Query(None, description="Filter by category"),
    sort_by_discount: bool = Query(False, description="Sort by discount"),
    sort_by_date: bool = Query(False, description="Sort by date"),
    min_discount: float = Query(None, description="Filter by minimum discount"),
    max_discount: float = Query(None, description="Filter by maximum discount"),
) -> JSONResponse:
    try:
        db = Database("isc", "shops")
        db1 = Database("isc", "events")
        shop_collection = await db.make_connection()
        deals_collection = await db1.make_connection()
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
        # Check if any shop parameters are provided
        shop_params = [
            store_name,
            store_category,
            city,
            state,
            zipcode,
            country,
            store_type,
            store_number,
            tags,
        ]
        if any(param is not None for param in shop_params):
            # Build the query for shops
            query = {}
            if store_name:
                query["store_name"] = {"$regex": f"{store_name}", "$options": "i"}
            if store_category:
                query["store_category"] = {
                    "$regex": f"^{store_category}$",
                    "$options": "i",
                }
            if city:
                query["location.city"] = {"$regex": f"^{city}$", "$options": "i"}
            if zipcode:
                query["location.zipcode"] = {"$regex": f"^{zipcode}$", "$options": "i"}
            if state:
                query["location.state"] = {"$regex": f"^{state}$", "$options": "i"}
            if country:
                query["location.country"] = {"$regex": f"^{country}$", "$options": "i"}
            if store_type:
                query["store_types"] = {"$regex": f"^{store_type}$", "$options": "i"}
            if store_number:
                query["store_number"] = {"$regex": f"^{store_number}$", "$options": "i"}
            if tags:
                query["tags"] = {"$regex": f"^{tags}$", "$options": "i"}

            # Search shops
            shops = shop_collection.find(query, {"_id": 0})

            # Convert the cursor to a list
            shops = list(shops)
        else:
            shops = []

        # Check if any event parameters are provided
        event_params = [event_name, category, min_discount, max_discount]
        if any(param is not None for param in event_params):
            # Build the query for events
            event_query = {}
            if category:
                event_query["category"] = {"$regex": f"^{category}$", "$options": "i"}
            if event_name:
                event_query["event_name"] = {"$regex": f"{event_name}", "$options": "i"}
            if min_discount is not None:
                event_query["discount_percent"] = {"$gte": min_discount}
            if max_discount is not None:
                event_query["discount_percent"] = {"$lte": max_discount}

            # Search events
            events = deals_collection.find(event_query, {"_id": 0})

            # Sort the results
            if sort_by_discount:
                events = events.sort("discount_percent", -1)
            if sort_by_date:
                events = events.sort("end_date", -1)

            # Convert the cursor to a list
            events = list(events)
        else:
            events = []

        if not shops and not events:
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "No shops and events found",
                    "response": "No shops and events found with the given search criteria",
                },
            )
        logging.info(f"Shops and events found: {shops} and {events}")

        result = events if not shops else shops

        await db.close_connection()
        await db1.close_connection()

        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Shops and events found",
                "response": result,
            },
        )
    except Exception as e:
        logging.error(f"Error searching shops and events: {e}")
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
@router.get("/get-all-shops-details", tags=["shops"])
async def get_all_shops_details() -> JSONResponse:
    try:
        db = Database("isc", "shops")
        collection = await db.make_connection()
        shops = collection.find(
            {"shop_status": "active"},
            {"_id": 0},
        )
        shops_list = list(shops)
        logging.info(f"Shops found: {shops_list}")
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
@router.get("/get-shop-details/{shop_id:str}", tags=["shops"])
async def get_a_shop_details(shop_id: str) -> JSONResponse:
    try:
        db = Database("isc", "shops")
        collection = await db.make_connection()
        shop = collection.find_one(
            {"shop_unique_id": shop_id, "shop_status": "active"},
            {"_id": 0},
        )
        logging.info(f"Shop found: {shop}")
        if not shop:
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Shop not found",
                    "response": "Shop not found, may be it's not active or doesn't exist",
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
