from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
)
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserRegisterRequest


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repository = UserRepository(session)

    async def register(
        self,
        request: UserRegisterRequest,
    ) -> User:
        existing_user = await self.user_repository.get_by_email(
            request.email,
        )

        if existing_user is not None:
            raise EmailAlreadyExistsError

        user = await self.user_repository.create(
            email=request.email,
            hashed_password=hash_password(request.password),
            full_name=request.full_name,
        )

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise EmailAlreadyExistsError

        await self.session.refresh(user)

        return user

    async def authenticate(
        self,
        *,
        email: str,
        password: str,
    ) -> str:
        user = await self.user_repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError

        if not user.is_active:
            raise InactiveUserError

        return create_access_token(user.id)