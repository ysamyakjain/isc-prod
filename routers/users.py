import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from utils.db import Database
from models.m_user import *
from utils.auth import *

router = APIRouter()

# New user registration route
@router.post("/user-registeration", tags=["User-authentication"])
async def user_registeration_api(user: NewUserRegistration) -> JSONResponse:
    try:
        # Connect to MongoDB
        db = Database("isc", "users")
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
        # Check if user already exists
        existing_user = collection.find_one(
            {"$or": [{"username": user.username}, {"email": user.email}]}
        )
        if existing_user:
            logging.info(f"User with username {user.username} already exists")
            return JSONResponse(
                status_code=400,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "User with this username/email already exists",
                    "response": "Try a different username and email to register",
                },
            )

        logging.info(f"User with username {user.username} does not exist, creating new user")

        # Hash the password before saving to MongoDB
        hashed_password = await hash_key(user.password)

        # Insert user details into MongoDB
        user_data = user.model_dump()
        user_data["unique_id"] = await generate_unique_uuid()
        user_data["password"] = hashed_password
        user_data["registered_on"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_data["last_updated"] = None
        user_data["role"] = "user"
        inserted_user = collection.insert_one(user_data)

        logging.info(f"User registered successfully with id: {inserted_user.inserted_id}")

        await db.close_connection()

        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "User registered successfully",
                "response": "Sign in to continue with our services",
            },
        )
    except Exception as e:
        logging.error(f"Error registering user: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# FastAPI route for user login
@router.post("/user-login", tags=["User-authentication"])
async def user_login_api(user_login: UserLogin) -> JSONResponse:
    try:
        # Check if email or username is provided
        if user_login.email is None and user_login.username is None:
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
        logging.error(f"Error logging in user: {e}")
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
        # Connect to MongoDB
        db = Database("isc", "users")
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
        # Validate user credentials
        if user_login.email:
            user = collection.find_one({"email": user_login.email})
        else:
            user = collection.find_one({"username": user_login.username})

        logging.info(f"User found")

        if not user or not bcrypt.checkpw(
            user_login.password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            logging.info(
                f"Invalid credentials for user: {user_login.email or user_login.username}"
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
            "id": user["unique_id"],
            "email": user["email"],
            "username": user["username"],
            "role": user["role"],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=7 * 24 * 60),
            "last-login": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "custom_data": [],
        }
        token = create_jwt_token(token_data)

        logging.info(f"User {user['username']} logged in successfully")

        await db.close_connection()

        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "User logged in successfully",
                "response": {"token": token},
            },
        )
    except Exception as e:
        logging.error(f"Error logging in user: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )


# Route for updating the user details
@router.put("/update-user", tags=["User-authentication"])
async def update_user_details_api(
    user: UpdateUser, current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    try:
        # Connect to MongoDB
        db = Database("isc", "users")
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
        user = user.model_dump(exclude_unset=True)

        # Update user details
        if "password" in user:
            user["password"] = await hash_key(user["password"])
        user["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        updated_user = collection.update_one(
            {"unique_id": current_user["id"]},
            {"$set": user},
        )

        await db.close_connection()

        if updated_user.modified_count == 0:
            logging.info(f"{current_user['username']} not found")
            return JSONResponse(
                status_code=400,
                media_type="application/json",
                content={
                    "status": False,
                    "message": "Users details not updated",
                    "response": "Nothing to update",
                },
            )

        logging.info(f"User {current_user['username']} updated successfully")

        return JSONResponse(
            status_code=200,
            media_type="application/json",
            content={
                "status": True,
                "message": "User details updated successfully",
                "response": "User details updated successfully",
            },
        )
    except Exception as e:
        logging.error(f"Error updating user: {e}")
        return JSONResponse(
            status_code=500,
            media_type="application/json",
            content={
                "status": False,
                "message": "Internal server error",
                "response": "There is some issue with our services, please try again later",
            },
        )





