from fastapi import FastAPI, HTTPException, Path
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

# Einzelnen User zurückgeben
@app.get("/users/{user_id}", response_model=UserReadResponse)
def user( user_id: int = Path(..., gt=0) ):
    cursor = conn.cursor()
    cursor.execute(
    "SELECT id, username FROM users WHERE id = ?", (user_id,) )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return { "id": row[0], "username": row[1] }

# Passwort ändern
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

@app.patch("/users/{user_id}/password", status_code=204)
def change_password(
        user_id: int = Path(..., gt=0),
        data: PasswordChangeRequest = ... ):
    cursor = conn.cursor()
    cursor.execute(
    "SELECT password_hash FROM users WHERE id = ?", (user_id,) )
    row = cursor.fetchone()
    # Cecken ob der User existiert
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    # Angegebenes Passwort mit gespeichertem Passwort verleichen
    stored_password_hash = row[0]
    current_password_hash = hash_password(data.current_password)
    if current_password_hash != stored_password_hash:
        raise HTTPException(
            status_code=401,
            detail="Password is incorrect"
        )
    # Neues Password validieren
    valid, reason = validate_password_internal(data.new_password)
    if not valid:
        raise HTTPException(
            status_code=400,
            detail=reason
        )
    # Neues Passwort hashen und speichern
    new_password_hash = hash_password(data.new_password)
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (new_password_hash, user_id)
    )
    conn.commit()



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

