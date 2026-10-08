from datetime import datetime, timedelta, timezone

from app.domain.schemas.auth import EmailAddress
from app.infrastructure.database.auth import create_invite
from app.services.auth_service import create_invite_code, hash_invite_code


def main():
    try:
        account = EmailAddress(email=input("Developer email: "))
        code = create_invite_code()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=72)
        create_invite(account.email, hash_invite_code(code), expires_at)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Invite for {account.email} (expires in 72 hours):")
    print(code)
    print("Share this code privately. It can only be used once with this email.")


if __name__ == "__main__":
    main()