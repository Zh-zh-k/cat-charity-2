from fastapi import Depends
from fastapi_users import (BaseUserManager, FastAPIUsers, IntegerIDMixin,
                           exceptions)
from fastapi_users.authentication import (AuthenticationBackend,
                                          BearerTransport, JWTStrategy)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import JWT_LIFETIME_SECONDS, MIN_PASSWORD_LENGTH
from app.core.db import get_async_session
from app.models.user import User

SECRET = 'SECRET'


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
):
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def validate_password(
        self,
        password: str,
        user: User,
    ) -> None:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise exceptions.InvalidPasswordException(
                reason=(
                    'Password should be at least '
                    f'{MIN_PASSWORD_LENGTH} characters'
                )
            )


async def get_user_manager(
    user_db=Depends(get_user_db),
):
    yield UserManager(user_db)


bearer_transport = BearerTransport(
    tokenUrl='auth/jwt/login',
)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=SECRET,
        lifetime_seconds=JWT_LIFETIME_SECONDS,
    )


auth_backend = AuthenticationBackend(
    name='jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)


current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(
    active=True,
    superuser=True,
)
