import sqlite3
import utilities as util
from typing import Literal
from exceptions import ( 
        UserNotFound, 
        UserAlreadyExists,
        InvalidPassword, 
        InvalidCurrentPassword )

class UserService:    
    def __init__(self, conn):
        self.conn = conn
 
    def _get_user_row(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()

        # Testen ob der angegebene User existiert
        if row is None:
            raise UserNotFound()
        
        return {
            "id": row[0],
            "username": row[1],
            "password_hash": row[2],
        }


    def get_user_by_id(self, user_id: int) -> dict:
        user = self._get_user_row(user_id)
        return { 
            "id": user["id"],
            "username": user["username"]
        }
    
    
    def create_user(self, username: str, password: str) -> dict:
        # Passwort validieren
        valid, reason = util.validate_password_internal(password)
        if not valid:
            raise InvalidPassword(reason)

        # Passwort hashen
        password_hash = util.hash_password(password)

        # User anlegen
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            cursor.execute("SELECT last_insert_rowid()")
            user_id = cursor.fetchone()[0]
            self.conn.commit()

        except sqlite3.IntegrityError:
            # Fachlicher Konflikt
            raise UserAlreadyExists()

        # Ergebnis zurückgeben
        return {
            "id": user_id,
            "username": username
        }


    def delete_user(self, user_id: int) -> None:
        # Testen ob User existiert
        self._get_user_row(user_id)

        # Eintrag löschen
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
        self.conn.commit()


    def change_password(self,
                        user_id: int,
                        current_password: str,
                        new_password: str ) -> None:
        # User auslesen oder Fehler werfen, falls kein Eintrag existiert
        user = self._get_user_row(user_id)

        # Aktuelles Passwort prüfen
        stored_password_hash = user["password_hash"]
        if util.hash_password(current_password) != stored_password_hash:
            raise InvalidCurrentPassword()
        
        # Neues Passwort validieren
        valid, reason = util.validate_password_internal(new_password)
        if not valid:
            raise InvalidPassword(reason)

        # Neues Passwort speichern
        new_hash = util.hash_password(new_password)
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, user_id)
        )
        self.conn.commit()


    def get_users(self, sort: Literal["id", "username"]) -> list[dict]:
        cursor = self.conn.cursor()
        if sort == "username":
            cursor.execute("SELECT id, username FROM users ORDER BY username")
        else:
            cursor.execute("SELECT id, username FROM users ORDER BY id ASC")
        rows = cursor.fetchall()
        return [
            {"id": row[0], "username": row[1]}
            for row in rows
        ]