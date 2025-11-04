from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta

from databasedll import users_collection
from modelsdll import User, LoginData
from logapidll import write_log
from cashdll import check_rate_limit

SECRET_KEY = "supersecretkey123"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usernick: str = payload.get("sub")
        if usernick is None:
            raise HTTPException(status_code=401, detail="Неверный токен")
        return usernick
    except JWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")

def server():
    app = FastAPI()

    @app.get("/")
    def root():
        return {"message": "Сервер работает. Конфиг читается из dataApi.txt"}

    @app.post("/register")
    def register(user: User, request: Request):
        try:
            client_ip = request.client.host
            check_rate_limit(client_ip)

            if users_collection.find_one({"usernick": user.usernick}):
                write_log(f"❌ Повторная регистрация: {user.usernick} (IP: {client_ip})")
                raise HTTPException(status_code=400, detail="Пользователь уже существует")

            users_collection.insert_one(user.dict())
            write_log(f"✅ Новый пользователь: {user.username} ({user.usernick}), IP: {client_ip}")
            return {"message": f"Пользователь {user.username} успешно зарегистрирован!"}

        except Exception as e:
            write_log(f"❌ Ошибка регистрации: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/login")
    def login(data: LoginData, request: Request):
        client_ip = request.client.host
        user = users_collection.find_one({"usernick": data.usernick})

        if not user:
            write_log(f"⚠️ Попытка входа с несуществующим ником: {data.usernick} (IP: {client_ip})")
            raise HTTPException(status_code=400, detail="Пользователь не найден")

        if data.password != user["password"]:
            write_log(f"⚠️ Неверный пароль: {data.usernick} (IP: {client_ip})")
            raise HTTPException(status_code=400, detail="Неверный пароль")

        # создаем токен
        access_token = create_access_token(data={"sub": data.usernick})
        write_log(f"✅ Успешный вход: {data.usernick} (IP: {client_ip})")
        return {"access_token": access_token, "token_type": "bearer"}

    @app.get("/profile")
    def profile(usernick: str = Depends(verify_token)):
        user = users_collection.find_one({"usernick": usernick})
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return {"username": user["username"], "usernick": user["usernick"], "love": user["love"]}

    return app

# TreeHub API - Source Code
# This language is Python
# This file is: serverdll.py
# Author: Dmitry Khorov
# GitHub: https://github.com/DKhorov/TreeHub.git
