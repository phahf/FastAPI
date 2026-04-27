# Passwort hashen
import hashlib
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

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