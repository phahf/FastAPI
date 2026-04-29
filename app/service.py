import sqlite3
import app.utilities as util
from typing import Literal
from app.exceptions import ( 
        UserNotFound, 
        UserAlreadyExists,
        InvalidPassword, 
        InvalidCurrentPassword )
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.db.engine import get_session
from app.db.models import User


class UserService:    
    def __init__(self, session):
        self.session = session
 
    def _get_user_row(self, user_id: int):
        statement = select(User).where(User.id == user_id)
        user = self.session.exec(statement).first()

        # Testen ob der angegebene User existiert
        if user is None:
            raise UserNotFound()
        
        return user


    def get_user_by_id(self, user_id: int) -> dict:
        user = self._get_user_row(user_id)
        return { 
            "id": user.id,
            "username": user.username
        }
    
    
    def create_user(self, username: str, password: str) -> dict:
        # Passwort validieren
        valid, reason = util.validate_password_internal(password)
        if not valid:
            raise InvalidPassword(reason)

        # Passwort hashen
        password_hash = util.hash_password(password)

        # User anlegen
        try:
            user = User(username=username,
                        password_hash=password_hash)
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)

        except IntegrityError:
            # Username existiert bereits
            self.session.rollback()
            raise UserAlreadyExists()

        # Ergebnis zurückgeben
        return {
            "id": user.id,
            "username": username
        }


    def delete_user(self, user_id: int) -> None:
        # Testen ob User existiert
        self._get_user_row(user_id)

        # Eintrag löschen
        statement = select(User).where(User.id == user_id)
        user = self.session.exec(statement).first()
        self.session.delete(user)
        self.session.commit()



    def change_password(self,
                        user_id: int,
                        current_password: str,
                        new_password: str ) -> None:
        # User auslesen oder Fehler werfen, falls kein Eintrag existiert
        user = self._get_user_row(user_id)

        # Aktuelles Passwort prüfen
        stored_password_hash = user.password_hash
        if util.hash_password(current_password) != stored_password_hash:
            raise InvalidCurrentPassword()
        
        # Neues Passwort validieren
        valid, reason = util.validate_password_internal(new_password)
        if not valid:
            raise InvalidPassword(reason)

        # Neues Passwort speichern
        new_hash = util.hash_password(new_password)
        user.password_hash = new_hash
        self.session.commit()


    def get_users(self, sort: Literal["id", "username"]) -> list[dict]:
        statement = select(User)
        if sort == "username":
            statement = statement.order_by(User.username)
        else:
            statement = statement.order_by(User.id)
        users = self.session.exec(statement).all()
        return [
            {"id": user.id, "username": user.username}
            for user in users ]
    
