import os
import uuid

import pytest

from keycloak import KeycloakAdmin


@pytest.fixture
def env():
    class KeycloakTestEnv(object):
        KEYCLOAK_HOST = os.environ["KEYCLOAK_HOST"]
        KEYCLOAK_PORT = os.environ["KEYCLOAK_PORT"]
        KEYCLOAK_ADMIN = os.environ["KEYCLOAK_ADMIN"]
        KEYCLOAK_ADMIN_PASSWORD = os.environ["KEYCLOAK_ADMIN_PASSWORD"]

    return KeycloakTestEnv()


@pytest.fixture
def admin(env):
    return KeycloakAdmin(
        server_url=f"http://{env.KEYCLOAK_HOST}:{env.KEYCLOAK_PORT}",
        username=env.KEYCLOAK_ADMIN,
        password=env.KEYCLOAK_ADMIN_PASSWORD,
    )


@pytest.fixture
def realm(admin: KeycloakAdmin) -> str:
    realm_name = str(uuid.uuid4())
    admin.create_realm(payload={"realm": realm_name})
    yield realm_name
    admin.delete_realm(realm_name=realm_name)
