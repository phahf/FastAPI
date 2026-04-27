from fastapi import FastAPI, HTTPException, Path, Query, Depends
from pydantic import BaseModel
from typing import Literal
import sqlite3
import app.utilities as util
from app.service import UserService
from app.exceptions import ( 
        UserNotFound, 
        UserAlreadyExists,
        InvalidPassword, 
        InvalidCurrentPassword )


app = FastAPI()


# ### Minimalbeispiele

# # Einfache Get-Anfragen 
# class StatusResponse(BaseModel):
#     status: str

# @app.get("/")
# def read_root():
#     return {"status": "okkk"}

# @app.get("/health", response_model=StatusResponse)
# def health():
#     return {"statuss": "healthy", "status": "yes"}


# # Get-Anfrage mit Parameter
# class GreetingResponse(BaseModel):
#     greeting: str

# @app.get("/greet", response_model=GreetingResponse)
# def greet(name: str):
#     return {"greeting": f"Hallo {name}"}


# # Post-Anfrage
# class EchoRequest(BaseModel):
#     message: str

# @app.post("/echo")
# def echo(data: EchoRequest):
#     return data


### Nutzerdatenbank mit Passwortüberprüfung

# Datenbank
conn = sqlite3.connect("users.db", check_same_thread=False)
conn.cursor().execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    )
    """
)
conn.commit()

# Dependency 
def get_user_service() -> UserService:
    return UserService(conn)


# Benutzer hinzufügen
class UserCreateRequest(BaseModel):
    username: str
    password: str

class UserCreateResponse(BaseModel):
    id: int
    username: str

@app.post("/users", response_model=UserCreateResponse, status_code=201)
def create_user(data: UserCreateRequest,
                service:UserService = Depends(get_user_service) ):
    try:
        user = service.create_user(username = data.username,
                            password = data.password )
        return user
    except InvalidPassword as err:
        raise HTTPException(
                status_code=400, 
                detail=err.reason)
    except UserAlreadyExists:
        raise HTTPException(
                status_code=409,
                detail="Username already exists"
        )

# User löschen
@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int = Path(..., gt=0),
                service:UserService = Depends(get_user_service) ):
    try:
        service.delete_user(user_id)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
        


# Liste mit Usern zurückgeben
class UserReadResponse(BaseModel):
    id: int
    username: str

@app.get("/users", response_model=list[UserReadResponse])
def list_users(sort: Literal["id", "username"] =
               Query("id",description="Sort order of users, default 'id'"),
               service:UserService = Depends(get_user_service)  ):
    return service.get_users(sort)

# Einzelnen User zurückgeben
@app.get("/users/{user_id}", response_model=UserReadResponse)
def get_user(user_id: int = Path(..., gt=0),
             service:UserService = Depends(get_user_service) ):
    try:
        return service.get_user_by_id(user_id)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")


# Passwort ändern
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

@app.patch("/users/{user_id}/password", status_code=204)
def change_password(
        user_id: int = Path(..., gt=0),
        data: PasswordChangeRequest = ...,
        service:UserService = Depends(get_user_service) ):
    try:
        service.change_password(user_id, 
                                current_password = data.current_password,
                                new_password = data.new_password)
    except InvalidCurrentPassword:
        raise HTTPException(
            status_code=401,
            detail="Invalid current password")
    except InvalidPassword as err:
        raise HTTPException(
            status_code=400, 
            detail=err.reason)
    except UserNotFound:
        raise HTTPException(
            status_code=404, 
            detail="User not found")



# Passwortvalidierung, extern
class PasswordRequest(BaseModel):
    password: str

class PasswordValidationResponse(BaseModel):
    valid: bool
    reason: str

@app.post("/validate-password", response_model=PasswordValidationResponse)
def validate_password_external(data: PasswordRequest):
    valid, reason = util.validate_password_internal(data.password)
    return {"valid": valid, "reason": reason}

    


