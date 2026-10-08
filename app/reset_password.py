from getpass import getpass

from app.domain.schemas.auth import LoginRequest
from app.infrastructure.database.auth import update_user_password
from app.services.auth_service import hash_password


def main():
    email = input("Account email: ")
    password = getpass("New password (at least 12 characters): ")
    confirmation = getpass("Confirm new password: ")

    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters long")
    if password != confirmation:
        raise SystemExit("Passwords do not match")

    try:
        account = LoginRequest(email=email, password=password)
        updated = update_user_password(account.email, hash_password(account.password))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if updated is None:
        raise SystemExit("No account exists with that email")

    print(f"Updated password and revoked active sessions for {updated['email']}")


if __name__ == "__main__":
    main()