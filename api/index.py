from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import httpx

app = FastAPI()

# Your Firebase Realtime Database URL
FIREBASE_DB_URL = "https://fran-eb915-default-rtdb.asia-southeast1.firebasedatabase.app"

class Auth(BaseModel):
    username: str
    password: str

class LocationData(Auth):
    latitude: float
    longitude: float

async def get_user(username: str):
    url = f"{FIREBASE_DB_URL}/Users/{username}.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
        return None

async def set_user(username: str, data: dict):
    url = f"{FIREBASE_DB_URL}/Users/{username}.json"
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=data)
        return response.status_code == 200

async def update_locations(username: str, timestamp: str, location_str: str):
    url = f"{FIREBASE_DB_URL}/Users/{username}/locations/{timestamp}.json"
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=location_str)
        return response.status_code == 200

@app.post("/register")
async def register(auth: Auth):
    user = await get_user(auth.username)
    if user is not None:
        raise HTTPException(status_code=400, detail="User already exists")
    data = {"password": auth.password, "locations": {}}
    success = await set_user(auth.username, data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to register user")
    return {"message": "User registered"}

@app.post("/add_location")
async def add_location(data: LocationData):
    user = await get_user(data.username)
    if not user or user.get("password") != data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    timestamp = datetime.utcnow().isoformat() + "Z"
    location_str = f"{data.latitude},{data.longitude}"
    success = await update_locations(data.username, timestamp, location_str)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add location")
    return {"message": "Location added", "timestamp": timestamp}

@app.post("/get_locations")
async def get_locations(auth: Auth):
    user = await get_user(auth.username)
    if not user or user.get("password") != auth.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    url = f"{FIREBASE_DB_URL}/Users/{auth.username}/locations.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            return {"locations": response.json() or {}}
        raise HTTPException(status_code=500, detail="Failed to fetch locations")

@app.get("/all")
async def get_all():
    url = f"{FIREBASE_DB_URL}/Users.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            return {"users": response.json() or {}}
        raise HTTPException(status_code=500, detail="Failed to fetch all users")
      
