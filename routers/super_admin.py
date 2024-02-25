"""

#get-everything about user
@app.get("/get-everything", tags=["everything"])
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

        # If owner_id is provided, add a $match stage to the pipeline
        if owner_id is not None:
            # Convert owner_id string to ObjectId
            owner_id = ObjectId(owner_id)
            pipeline.append({"$match": {"_id": owner_id}})

        # Add the remaining stages to the pipeline
        pipeline.extend([
            {"$lookup": {
                "from": "shops",
                "let": {"owner_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$owner", "$$owner_id"]}}},
                    {"$lookup": {
                        "from": "deals",
                        "let": {"shop_id": "$_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$shop_id", "$$shop_id"]}}},
                            {"$sort": {"registered_on": -1}}
                        ],
                        "as": "deals"
                    }},
                    {"$lookup": {
                        "from": "gateways",
                        "let": {"shop_owner_id": "$_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$shop_owner_id", "$$shop_owner_id"]}}},
                            {"$lookup": {
                                "from": "beacons",
                                "let": {"gateway_owner_id": "$_id"},
                                "pipeline": [
                                    {"$match": {"$expr": {"$eq": ["$gateway_owner_id", "$$gateway_owner_id"]}}},
                                    {"$sort": {"registered_on": -1}}
                                ],
                                "as": "beacons"
                            }},
                            {"$sort": {"registered_on": -1}}
                        ],
                        "as": "gateways"
                    }},
                    {"$sort": {"registered_on": -1}}
                ],
                "as": "shops"
            }},
            {"$project": {
                "password": 0,
                "shops.deals.shop_id": 0,
                "shops.gateways.shop_owner_id": 0,
                "shops.gateways.beacons.gateway_owner_id": 0
            }},
            {"$skip": page_size * (page - 1)},  # Skip the documents that come before the current page
            {"$limit": page_size},  # Limit the number of documents to the page size
        ])

        result = list(collection.aggregate(pipeline))
        # Convert ObjectId to string for JSON serialization
        for doc in result:
            if isinstance(doc.get('_id'), ObjectId):
                doc['_id'] = str(doc.get('_id'))
            doc['registered_on'] = doc.get('registered_on').strftime("%Y-%m-%d %H:%M:%S") if isinstance(doc.get('registered_on'), datetime) else None
            doc['last_updated'] = doc.get('last_updated').strftime("%Y-%m-%d %H:%M:%S") if isinstance(doc.get('last_updated'), datetime) else None
            for shop in doc.get('shops', []):
                if isinstance(shop.get('_id'), ObjectId):
                    shop['_id'] = str(shop.get('_id'))
                    shop['owner'] = str(shop.get('owner'))
                shop['registered_on'] = shop.get('registered_on').strftime("%Y-%m-%d %H:%M:%S") if isinstance(shop.get('registered_on'), datetime) else None
                shop['last_updated'] = shop.get('last_updated').strftime("%Y-%m-%d %H:%M:%S") if isinstance(shop.get('last_updated'), datetime) else None
                for deal in shop.get('deals', []):
                    if isinstance(deal.get('_id'), ObjectId):
                        deal['_id'] = str(deal.get('_id'))
                    deal['start_date'] = deal.get('start_date').strftime("%Y-%m-%d %H:%M:%S") if isinstance(deal.get('start_date'), datetime) else None
                    deal['end_date'] = deal.get('end_date').strftime("%Y-%m-%d %H:%M:%S") if isinstance(deal.get('end_date'), datetime) else None
                    deal['registered_on'] = deal.get('registered_on').strftime("%Y-%m-%d %H:%M:%S") if isinstance(deal.get('registered_on'), datetime) else None
                    deal['last_updated'] = deal.get('last_updated').strftime("%Y-%m-%d %H:%M:%S") if isinstance(deal.get('last_updated'), datetime) else None
                for gateway in shop.get('gateways', []):
                    if isinstance(gateway.get('_id'), ObjectId):
                        gateway['_id'] = str(gateway.get('_id'))
                    gateway['registered_on'] = gateway.get('registered_on').strftime("%Y-%m-%d %H:%M:%S") if isinstance(gateway.get('registered_on'), datetime) else None
                    gateway['last_updated'] = gateway.get('last_updated').strftime("%Y-%m-%d %H:%M:%S") if isinstance(gateway.get('last_updated'), datetime) else None
                    for beacon in gateway.get('beacons', []):
                        if isinstance(beacon.get('_id'), ObjectId):
                            beacon['_id'] = str(beacon.get('_id'))
                        beacon['registered_on'] = beacon.get('registered_on').strftime("%Y-%m-%d %H:%M:%S") if isinstance(beacon.get('registered_on'), datetime) else None
                        beacon['last_updated'] = beacon.get('last_updated').strftime("%Y-%m-%d %H:%M:%S") if isinstance(beacon.get('last_updated'), datetime) else None

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
                "response": jsonable_encoder(result),
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
"""