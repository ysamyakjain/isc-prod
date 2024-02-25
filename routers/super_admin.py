import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from bson import ObjectId


from utils.db import Database
from models.m_shop import *
from utils.auth import *

router = APIRouter()

#get-everything about user
@router.get("/get-everything", tags=["super-admin"])
async def get_all_details(owner_id:str=None, page: int = 1, page_size: int = 10, current_user: dict = Depends(get_current_admin_user)):
    try:
        db = Database("isc", "owners")
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
        # Initialize the pipeline
        pipeline = []
        unique_id = owner_id
        # If unique_id is provided, add a $match stage to the pipeline
        if unique_id is not None:
            pipeline.append({"$match": {"unique_id": unique_id}})

        # Add the remaining stages to the pipeline
        pipeline.extend([
            {"$lookup": {
                "from": "shops",
                "let": {"owner_id": "$unique_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$owner", "$$owner_id"]}}},
                    {"$lookup": {
                        "from": "events",
                        "let": {"shop_id": "$shop_unique_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$shop_owner", "$$shop_id"]}}},
                            {"$sort": {"registered_on": -1}}
                        ],
                        "as": "events"
                    }},
                    {"$sort": {"registered_on": -1}}
                ],
                "as": "shops"
            }},
            {"$project": {
                "_id": 0,
                "password": 0,
                "shops._id": 0,
                "shops.events._id": 0
            }},
            {"$skip": page_size * (page - 1)},  # Skip the documents that come before the current page
            {"$limit": page_size},  # Limit the number of documents to the page size
        ])

        result = list(collection.aggregate(pipeline))
        logging.info(f"Data found: {result}")
        if not result:
            return JSONResponse(
                status_code=404,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Data not found",
                    "response": "No data found",
                },
            )
        # Return the result
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Data found",
                "response": result,
            },
        )
    except Exception as e:
        logging.error(f"Error getting everything: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )
