from sqlalchemy.orm import Session

from app.exceptions import AuthorizationError
from app.models import User
from app.repositories import UserRepository
from app.security import create_access_token, verify_password


class AuthService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)

    def authenticate(self, email: str, password: str) -> tuple[User, str]:
        user = self.users.get_by_email(email)
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthorizationError("invalid credentials")
        token = create_access_token(user.id, user.role)
        return user, token
