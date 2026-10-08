from getpass import getpass

from app.domain.schemas.auth import LoginRequest
from app.infrastructure.database.auth import create_user
from app.services.auth_service import hash_password


def main():
    email = input("Account email: ")
    password = getpass("Password (at least 12 characters): ")
    confirmation = getpass("Confirm password: ")

    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters long")
    if password != confirmation:
        raise SystemExit("Passwords do not match")

    try:
        account = LoginRequest(email=email, password=password)
        created = create_user(account.email, hash_password(account.password))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Created account for {created['email']}")


if __name__ == "__main__":
    main()