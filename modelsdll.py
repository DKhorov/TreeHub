from pydantic import BaseModel, Field

class User(BaseModel):
    username: str = Field(..., min_length=2, max_length=32, description="Имя пользователя")
    usernick: str = Field(..., min_length=3, max_length=32, description="Никнейм (уникальный)")
    password: str = Field(..., min_length=4, max_length=72, description="Пароль пользователя")
    love: str = Field(..., max_length=64, description="Что любит пользователь")

class LoginData(BaseModel):
    usernick: str = Field(..., min_length=3, max_length=32, description="Никнейм")
    password: str = Field(..., min_length=4, max_length=72, description="Пароль")

# TreeHub API - Source Code
# This language is Python
# This file is: modelsdll.py
# Author: Dmitry Khorov
# GitHub: https://github.com/DKhorov/TreeHub.git
