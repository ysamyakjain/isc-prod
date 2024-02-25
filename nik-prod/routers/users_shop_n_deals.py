import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from utils.db import Database
from models.m_user import *
from utils.auth import *

router = APIRouter()

# get top 5 deals
@router.get("/get-top-deals", tags=["deals"])
async def get_top_deals(
    sort_by_date: bool = Query(False, description="Sort deals by date"),
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
        # Get top 5 deals based on discount_percent
        deals = collection.find({}, {"_id": 0})
        if sort_by_date:
            deals = deals.sort("date", 1)  # Sort deals by date in ascending order
        deals = deals.limit(5)
        deals = list(deals)
        logging.info(f"Top 5 deals found: {deals}")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Top 5 deals found",
                "response": deals,
            },
        )
    except Exception as e:
        logging.error(f"Error getting top 5 deals: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# search shops, deals with optional query parameters, filters, sortby discount, sort by date (everything is optional)
@router.get("/search-everything", tags=["shops"])
async def search_shops_deals(

    store_category: str = Query(None, description="Filter by store category"),
    city: str = Query(None, description="Filter by city"),
    state: str = Query(None, description="Filter by state"),
    zipcode: str = Query(None, description="Filter by zipcode"),
    country: str = Query(None, description="Filter by country"),
    store_type: str = Query(None, description="Filter by store type"),
    store_number: int = Query(None, description="Filter by store number"),
    tags: str = Query(None, description="Filter by tags"),
    
    deal_name: str = Query(None, description="Search by deal name"),
    category: str = Query(None, description="Filter by category"),
    sort_by_discount: bool = Query(False, description="Sort by discount"),
    sort_by_date: bool = Query(False, description="Sort by date"),
    min_discount: float = Query(None, description="Filter by minimum discount"),
    max_discount: float = Query(None, description="Filter by maximum discount"),
) -> JSONResponse:
    try:
        db = Database("isc", "shops")
        db1 = Database("isc", "deals")
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
        shop_params = [store_category, city, state, zipcode, country, store_type, store_number, tags]
        if any(param is not None for param in shop_params):
            # Build the query for shops
            query = {}
            if store_category:
                query["store_category"] = {'$regex': f'^{store_category}$', '$options': 'i'}
            if city:
                query["location.city"] = {'$regex': f'^{city}$', '$options': 'i'}
            if zipcode:
                query["location.zipcode"] = {'$regex': f'^{zipcode}$', '$options': 'i'}
            if state:
                query["location.state"] = {'$regex': f'^{state}$', '$options': 'i'}
            if country:
                query["location.country"] = {'$regex': f'^{country}$', '$options': 'i'}
            if store_type:
                query["store_types"] = {'$regex': f'^{store_type}$', '$options': 'i'}
            if store_number:
                query["store_number"] = {'$regex': f'^{store_number}$', '$options': 'i'}
            if tags:
                query["tags"] = {'$regex': f'^{tags}$', '$options': 'i'}

            # Search shops
            shops = shop_collection.find(query, {"_id": 0})

            # Convert the cursor to a list
            shops = list(shops)
        else:
            shops = []

        # Check if any deal parameters are provided
        deal_params = [deal_name, category, min_discount, max_discount]
        if any(param is not None for param in deal_params):
            # Build the query for deals
            deals_query = {}
            if category:
                deals_query["category"] = {'$regex': f'^{category}$', '$options': 'i'}
            if deal_name:
                deals_query["deal_name"] = {'$regex': f'^{deal_name}$', '$options': 'i'}
            if min_discount is not None:
                deals_query["discount_percent"] = {"$gte": min_discount}
            if max_discount is not None:
                deals_query["discount_percent"] = {"$lte": max_discount}

            # Search deals
            deals = deals_collection.find(deals_query, {"_id": 0})

            # Sort the results
            if sort_by_discount:
                deals = deals.sort("discount_percent", -1)
            if sort_by_date:
                deals = deals.sort("end_date", -1)

            # Convert the cursor to a list
            deals = list(deals)
        else:
            deals = []
        
        if not shops and not deals:
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "No shops and deals found",
                    "response": "No shops and deals found with the given search criteria",
                },
            )
        logging.info(f"Shops and deals found: {shops} and {deals}")
        
        result = deals if not shops else shops
        
        await db.close_connection()
        await db1.close_connection()  
          
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Shops and deals found",
                "response": result
            },
        )
    except Exception as e:
        logging.error(f"Error searching shops and deals: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )