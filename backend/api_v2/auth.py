from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from database import AsyncSessionLocal
from models_v2 import User
from passlib.hash import pbkdf2_sha256
import jwt
import datetime
import os

router = APIRouter()
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'acd-sdi-platform-secret-2025')

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    identifier: str
    password: str

@router.post("/signup")
async def signup(request: SignupRequest):
    async with AsyncSessionLocal() as session:
        # Check if exists
        q = select(User).where(or_(User.username == request.username, User.email == request.email))
        result = await session.execute(q)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Username or Email already exists")
        
        new_user = User(
            username=request.username,
            email=request.email,
            password_hash=pbkdf2_sha256.hash(request.password)
        )
        session.add(new_user)
        await session.commit()
        return {"message": "User created successfully"}

@router.post("/login")
async def login(request: LoginRequest):
    async with AsyncSessionLocal() as session:
        q = select(User).where(or_(User.username == request.identifier, User.email == request.identifier))
        result = await session.execute(q)
        user = result.scalars().first()
        
        if not user or not pbkdf2_sha256.verify(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')
        
        return {
            "token": token,
            "user": user.to_dict()
        }

@router.get("/verify")
async def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        async with AsyncSessionLocal() as session:
            q = select(User).where(User.id == payload['user_id'])
            result = await session.execute(q)
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return {"user": user.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
