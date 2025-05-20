from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import datetime

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FIREBASE_URL = "https://fran-eb915-default-rtdb.asia-southeast1.firebasedatabase.app"

# Models
class AuthModel(BaseModel):
    username: str
    password: str

class LocationModel(AuthModel):
    latitude: float
    longitude: float

# Helper function: Get user data
async def get_user(username: str):
    try:
        async with httpx.AsyncClient() as client:
            url = f"{FIREBASE_URL}/Users/{username}.json"
            res = await client.get(url)
            if res.status_code == 200:
                return res.json()
            raise HTTPException(status_code=res.status_code, detail="Failed to get user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

# Route: Register new user
@app.post("/register")
async def register(data: AuthModel):
    try:
        existing = await get_user(data.username)
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        
        async with httpx.AsyncClient() as client:
            url = f"{FIREBASE_URL}/Users/{data.username}.json"
            res = await client.put(url, json={"password": data.password})
            if res.status_code == 200:
                return {"message": "User registered"}
            raise HTTPException(status_code=500, detail="Failed to register user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")

# Route: User login
@app.post("/login")
async def login(data: AuthModel):
    user = await get_user(data.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("password") != data.password:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"message": "Login successful"}

# Route: Add location for user
@app.post("/add_location")
async def add_location(data: LocationModel):
    user = await get_user(data.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("password") != data.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    location_data = {
        "latitude": data.latitude,
        "longitude": data.longitude,
        "time": datetime.datetime.now().isoformat()
    }

    try:
        async with httpx.AsyncClient() as client:
            url = f"{FIREBASE_URL}/Users/{data.username}/locations.json"
            res = await client.post(url, json=location_data)
            if res.status_code == 200:
                return {"message": "Location added"}
            raise HTTPException(status_code=500, detail=f"Firebase error: {res.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Route: Get locations for a user
@app.post("/get_locations")
async def get_locations(data: AuthModel):
    user = await get_user(data.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("password") != data.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    try:
        async with httpx.AsyncClient() as client:
            url = f"{FIREBASE_URL}/Users/{data.username}/locations.json"
            res = await client.get(url)
            if res.status_code == 200:
                return {"locations": res.json() or {}}
            raise HTTPException(status_code=500, detail="Failed to fetch locations")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Route: Get all users and locations
@app.get("/all")
async def all_data():
    try:
        async with httpx.AsyncClient() as client:
            url = f"{FIREBASE_URL}/Users.json"
            res = await client.get(url)
            if res.status_code == 200:
                return {"data": res.json() or {}}
            raise HTTPException(status_code=500, detail="Failed to fetch all data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
