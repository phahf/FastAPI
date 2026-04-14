from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import hashlib


app = FastAPI()


### Minimalbeispiele

# Einfache Get-Anfragen 
class StatusResponse(BaseModel):
    status: str

@app.get("/")
def read_root():
    return {"status": "okkk"}

@app.get("/health", response_model=StatusResponse)
def health():
    return {"statuss": "healthy", "status": "yes"}


# Get-Anfrage mit Parameter
class GreetingResponse(BaseModel):
    greeting: str

@app.get("/greet", response_model=GreetingResponse)
def greet(name: str):
    return {"greeting": f"Hallo {name}"}


# Post-Anfrage
class EchoRequest(BaseModel):
    message: str

@app.post("/echo")
def echo(data: EchoRequest):
    return data


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

# Benutzer hinzufügen

class UserCreateRequest(BaseModel):
    username: str
    password: str

class UserCreateResponse(BaseModel):
    id: int
    username: str

@app.post("/users", response_model=UserCreateResponse)
def create_user(data: UserCreateRequest):

    # Passwort validieren
    valid, reason = validate_password_internal(data.password)
    if not valid:
        raise HTTPException(
            status_code=400,
            detail=reason
        )

    # Passwort hashen
    password_hash = hash_password(data.password)

    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (data.username, password_hash)
        )

        cursor.execute("SELECT last_insert_rowid()")
        user_id = cursor.fetchone()[0]

        conn.commit()

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    return {
    "id": user_id,
    "username": data.username
}

# Liste mit Usern zurückgeben
class UserReadResponse(BaseModel):
    id: int
    username: str

@app.get("/users", response_model=list[UserReadResponse])
def list_users():
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM users ORDER BY id ASC")
    rows = cursor.fetchall()

    return [
        {"id": row[0], "username": row[1]}
        for row in rows
    ]


# Passwortvalidierung, intern
def validate_password_internal(password: str) -> tuple[bool, str]:
    # Mindestens 8 Zeichen
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    # Groß- und Kleinbuchstaben
    if password.islower() or password.isupper():
        return False, "Password must contain upper- and lowercase letters"

    # Passwort entspricht den Anforderungen
    return True, "Password is valid"

# Passwortvalidierung, extern
class PasswordRequest(BaseModel):
    password: str

class PasswordValidationResponse(BaseModel):
    valid: bool
    reason: str

@app.post(
    "/validate-password",
    response_model=PasswordValidationResponse
)
def validate_password_external(data: PasswordRequest):
    valid, reason = validate_password_internal(data.password)
    return {"valid": valid, "reason": reason}

    
# Passwort hashen
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

