import argparse
from datetime import datetime, timedelta, timezone

from app.domain.schemas.auth import EmailAddress
from app.infrastructure.database.auth import create_invite
from app.services.auth_service import create_invite_code, hash_invite_code
from app.services.email_service import send_generic_invite_email


def _dev_only_invite(email: str) -> str:
    code = create_invite_code()
    sent = send_generic_invite_email(email, code)
    if sent:
        print(f"Invite sent to {email}.")
    else:
        print(f"Invite email could not be sent to {email}.")
    print(f"Invite code: {code}")
    print("Use this code to create your account.")
    return code


def main():
    parser = argparse.ArgumentParser(description="Create invite credentials for a user.")
    parser.add_argument("--email", help="Developer email address")
    parser.add_argument(
        "--dev-only",
        action="store_true",
        help="Send a simple no-reply invitation without storing the invite in MongoDB.",
    )
    args = parser.parse_args()

    email = args.email or input("Developer email: ")
    account = EmailAddress(email=email)

    if args.dev_only:
        _dev_only_invite(account.email)
        return

    code = create_invite_code()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=72)
    try:
        create_invite(account.email, hash_invite_code(code), expires_at)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    sent = send_generic_invite_email(account.email, code)
    if sent:
        print(f"Invite sent to {account.email}.")
    else:
        print(f"Invite created for {account.email} but email delivery is not configured or failed.")
    print(f"Invite code: {code}")
    print("Share this code privately. It can only be used once with this email and expires in 72 hours.")


if __name__ == "__main__":
    main()