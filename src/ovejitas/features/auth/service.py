from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ConflictError, UnauthorizedError
from ovejitas.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from ovejitas.features.auth.schemas import (
    FarmMembershipRead,
    LoginInput,
    MeResponse,
    RegisterInput,
    TokenPair,
    UserRead,
)
from ovejitas.features.currency.models import Currency
from ovejitas.features.farm.models import Farm
from ovejitas.features.farm_member.models import FarmMember, FarmRole
from ovejitas.features.user.models import User

DEFAULT_FARM_NAME = "My Farm"
DEFAULT_CURRENCY = "USD"


def issue_token_pair(user: User) -> TokenPair:
    """Mint an access + refresh token pair for a user. Reused by the invite-accept flow."""
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, *, email: str, name: str, password: str) -> User:
        """Add + flush a user (no commit), so callers control the surrounding transaction."""
        user = User(email=email, name=name, password_hash=hash_password(password))
        self.db.add(user)
        try:
            await self.db.flush()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError("Email already registered") from exc
        return user

    async def register(self, data: RegisterInput) -> TokenPair:
        user = await self.create_user(email=data.email, name=data.name, password=data.password)

        farm = Farm(name=DEFAULT_FARM_NAME, default_currency=DEFAULT_CURRENCY)
        if data.timezone is not None:
            farm.timezone = data.timezone
        self.db.add(farm)
        await self.db.flush()

        # Seed the currency matching the farm's preferred code so per-entry
        # currency defaulting resolves to a real row from day one.
        self.db.add(Currency(farm_id=farm.id, code=DEFAULT_CURRENCY, name=DEFAULT_CURRENCY))
        self.db.add(FarmMember(user_id=user.id, farm_id=farm.id, role=FarmRole.OWNER))
        await self.db.commit()
        return issue_token_pair(user)

    async def login(self, data: LoginInput) -> TokenPair:
        user = await self.find_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Incorrect email or password")
        return issue_token_pair(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = self._decode_or_raise(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid refresh token")
        user = await self.db.get(User, int(str(payload["sub"])))
        if user is None:
            raise UnauthorizedError("User not found")
        return issue_token_pair(user)

    async def me(self, user: User) -> MeResponse:
        stmt = (
            select(FarmMember.farm_id, FarmMember.role, Farm.default_currency)
            .join(Farm, Farm.id == FarmMember.farm_id)
            .where(FarmMember.user_id == user.id)
        )
        rows = (await self.db.execute(stmt)).all()
        return MeResponse(
            user=UserRead.model_validate(user),
            memberships=[
                FarmMembershipRead(
                    farm_id=farm_id,
                    role=role.value,
                    default_currency=default_currency,
                )
                for farm_id, role, default_currency in rows
            ],
        )

    async def find_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def _decode_or_raise(self, token: str) -> dict[str, object]:
        try:
            return decode_token(token)
        except Exception as exc:
            raise UnauthorizedError("Invalid token") from exc
