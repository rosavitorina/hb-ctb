import base64
import hashlib
import hmac
import secrets

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_SIZE = 16
_HASH_SIZE = 32


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_SIZE)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_HASH_SIZE,
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii")
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${encoded_salt}${encoded_digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, n, r, p, encoded_salt, encoded_digest = password_hash.split("$", 5)
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected = base64.urlsafe_b64decode(encoded_digest.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, OverflowError):
        return False


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_invite_code() -> str:
    return secrets.token_urlsafe(24)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_invite_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()