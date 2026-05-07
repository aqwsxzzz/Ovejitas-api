from ovejitas.core.security import hash_password
from ovejitas.features.user.models import User
from tests.factories._base import BaseFactory

FACTORY_PASSWORD = "password123"
_FACTORY_PASSWORD_HASH = hash_password(FACTORY_PASSWORD)


class UserFactory(BaseFactory):
    __model__ = User
    password_hash = _FACTORY_PASSWORD_HASH

    @classmethod
    def email(cls) -> str:
        return f"{cls.__faker__.user_name()}-{cls.__random__.randint(1, 9999999)}@test.com"

    @classmethod
    def name(cls) -> str:
        return cls.__faker__.name()
