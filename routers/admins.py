import logging
from datetime import datetime, timedelta
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from utils.db import Database
from models.m_admin import *
from utils.auth import *

router = APIRouter()


# register a new admin
@router.post("/admin-registeration", tags=["Admin-authentication"])
async def admin_registeration_api(data: NewAdminRegistration) -> JSONResponse:
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
        existing_admin = collection.find_one(
            {"$or": [{"username": data.username}, {"email": data.email}]}
        )
        if existing_admin:
            logging.info(f"Admin with username {data.username} already exists")
            return JSONResponse(
                status_code=400,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Admin with this username already exists",
                    "response": "Try a different username to register",
                },
            )
        logging.info(f"Admin with username does not exist, creating new admin")
        # Insert admin details into MongoDB
        admin_data = data.model_dump()
        admin_data["unique_id"] = await generate_unique_uuid()
        admin_data["password"] = await hash_key(data.password)
        admin_data["registered_on"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        admin_data["last_updated"] = None
        admin_data["role"] = "admin"
        admin_data["shops_owned"] = []
        inserted_admin = collection.insert_one(admin_data)
        logging.info(
            f"Admin registered successfully with id: {inserted_admin.inserted_id}"
        )
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Admin registered successfully",
                "response": "Sign in to continue with our services",
            },
        )
    except Exception as e:
        logging.error(f"Error registering admin: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# FastAPI route for admin login
@router.post("/admin-login", tags=["Admin-authentication"])
async def admin_login_api(admin_login: UserLogin) -> JSONResponse:
    try:
        # Check if email or username is provided
        if admin_login.email is None and admin_login.username is None:
            return JSONResponse(
                status_code=400,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "email or username is required to login",
                    "response": "Provide valid email or username to login",
                },
            )
    except Exception as e:
        logging.error(f"Error logging in admin: {e}")
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
        # Validate admin credentials
        if admin_login.email:
            admin = collection.find_one({"email": admin_login.email})
        else:
            admin = collection.find_one({"username": admin_login.username})
        logging.info(f"Admin found: {admin}")
        if not admin or not bcrypt.checkpw(
            admin_login.password.encode("utf-8"), admin["password"].encode("utf-8")
        ):
            logging.info(
                f"Invalid credentials for admin: {admin_login.email or admin_login.username}"
            )
            return JSONResponse(
                status_code=401,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Invalid credentials",
                    "response": "Please provide valid email/username and password",
                },
            )
        # Generate JWT token
        token_data = {
            "id": admin["unique_id"],
            "username": admin["username"],
            "email": admin["email"],
            "role": admin["role"],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=7 * 24 * 60),
            "Last-login": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "custom_data": [],
        }
        token = create_jwt_token(token_data)
        logging.info(f"Admin {admin['username']} logged in successfully")
        await db.close_connection()
        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "Admin logged in successfully",
                "response": {"token": token},
            },
        )
    except Exception as e:
        logging.error(f"Error logging in admin: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


