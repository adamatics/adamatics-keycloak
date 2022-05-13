import pytest

import keycloak
from keycloak import KeycloakAdmin
from keycloak.connection import ConnectionManager
from keycloak.exceptions import KeycloakGetError, KeycloakPostError


def test_keycloak_version():
    assert keycloak.__version__, keycloak.__version__


def test_keycloak_admin_bad_init(env):
    with pytest.raises(TypeError) as err:
        KeycloakAdmin(
            server_url=f"http://{env.KEYCLOAK_HOST}:{env.KEYCLOAK_PORT}",
            username=env.KEYCLOAK_ADMIN,
            password=env.KEYCLOAK_ADMIN_PASSWORD,
            auto_refresh_token=1,
        )
    assert err.match("Expected a list of strings")

    with pytest.raises(TypeError) as err:
        KeycloakAdmin(
            server_url=f"http://{env.KEYCLOAK_HOST}:{env.KEYCLOAK_PORT}",
            username=env.KEYCLOAK_ADMIN,
            password=env.KEYCLOAK_ADMIN_PASSWORD,
            auto_refresh_token=["patch"],
        )
    assert err.match("Unexpected method in auto_refresh_token")


def test_keycloak_admin_init(env):
    admin = KeycloakAdmin(
        server_url=f"http://{env.KEYCLOAK_HOST}:{env.KEYCLOAK_PORT}",
        username=env.KEYCLOAK_ADMIN,
        password=env.KEYCLOAK_ADMIN_PASSWORD,
    )
    assert admin.server_url == f"http://{env.KEYCLOAK_HOST}:{env.KEYCLOAK_PORT}", admin.server_url
    assert admin.realm_name == "master", admin.realm_name
    assert isinstance(admin.connection, ConnectionManager), type(admin.connection)
    assert admin.client_id == "admin-cli", admin.client_id
    assert admin.client_secret_key is None, admin.client_secret_key
    assert admin.verify, admin.verify
    assert admin.username == env.KEYCLOAK_ADMIN, admin.username
    assert admin.password == env.KEYCLOAK_ADMIN_PASSWORD, admin.password
    assert admin.totp is None, admin.totp
    assert admin.token is not None, admin.token
    assert admin.auto_refresh_token == list(), admin.auto_refresh_token
    assert admin.user_realm_name is None, admin.user_realm_name
    assert admin.custom_headers is None, admin.custom_headers


def test_realms(admin: KeycloakAdmin):
    # Get realms
    realms = admin.get_realms()
    assert len(realms) == 1, realms
    assert "master" == realms[0]["realm"]

    # Create a test realm
    res = admin.create_realm(payload={"realm": "test"})
    assert res == b"", res

    # Create the same realm, should fail
    with pytest.raises(KeycloakPostError) as err:
        res = admin.create_realm(payload={"realm": "test"})
    assert err.match('409: b\'{"errorMessage":"Conflict detected. See logs for details"}\'')

    # Create the same realm, skip_exists true
    res = admin.create_realm(payload={"realm": "test"}, skip_exists=True)
    assert res == {"msg": "Already exists"}, res

    # Get a single realm
    res = admin.get_realm(realm_name="test")
    assert res["realm"] == "test"

    # Update realm
    res = admin.update_realm(realm_name="test", payload={"accountTheme": "test"})
    assert res == dict(), res

    # Check that the update worked
    res = admin.get_realm(realm_name="test")
    assert res["realm"] == "test"
    assert res["accountTheme"] == "test"

    # Check that get realms returns both realms
    realms = admin.get_realms()
    realm_names = [x["realm"] for x in realms]
    assert len(realms) == 2, realms
    assert "master" in realm_names, realm_names
    assert "test" in realm_names, realm_names

    # Delete the realm
    res = admin.delete_realm(realm_name="test")
    assert res == dict(), res

    # Check that the realm does not exist anymore
    with pytest.raises(KeycloakGetError) as err:
        admin.get_realm(realm_name="test")
    assert err.match('404: b\'{"error":"Realm not found."}\'')


def test_import_export_realms(admin: KeycloakAdmin, realm: str):
    admin.realm_name = realm

    realm_export = admin.export_realm(export_clients=True, export_groups_and_role=True)
    assert realm_export != dict(), realm_export

    admin.delete_realm(realm_name=realm)
    admin.realm_name = "master"
    res = admin.import_realm(payload=realm_export)
    assert res == b"", res


def test_users(admin: KeycloakAdmin, realm: str):
    admin.realm_name = realm

    # Check no users present
    users = admin.get_users()
    assert users == list(), users

    # Test create user
    user_id = admin.create_user(payload={"username": "test", "email": "test@test.test"})
    assert user_id is not None, user_id

    # Test create the same user
    with pytest.raises(KeycloakPostError) as err:
        admin.create_user(payload={"username": "test", "email": "test@test.test"})
    assert err.match('409: b\'{"errorMessage":"User exists with same username"}\'')

    # Test create the same user, exists_ok true
    user_id_2 = admin.create_user(
        payload={"username": "test", "email": "test@test.test"}, exist_ok=True
    )
    assert user_id == user_id_2

    # Test get user
    user = admin.get_user(user_id=user_id)
    assert user["username"] == "test", user["username"]
    assert user["email"] == "test@test.test", user["email"]

    # Test update user
    res = admin.update_user(user_id=user_id, payload={"firstName": "Test"})
    assert res == dict(), res
    user = admin.get_user(user_id=user_id)
    assert user["firstName"] == "Test"

    # Test get users again
    users = admin.get_users()
    usernames = [x["username"] for x in users]
    assert "test" in usernames

    # Test users counts
    count = admin.users_count()
    assert count == 1, count

    # Test user groups
    groups = admin.get_user_groups(user_id=user["id"])
    assert len(groups) == 0

    # Test logout
    res = admin.user_logout(user_id=user["id"])
    assert res == dict(), res

    # Test consents
    res = admin.user_consents(user_id=user["id"])
    assert len(res) == 0, res

    # Test delete user
    res = admin.delete_user(user_id=user_id)
    assert res == dict(), res
    with pytest.raises(KeycloakGetError) as err:
        admin.get_user(user_id=user_id)
    err.match('404: b\'{"error":"User not found"}\'')


def test_users_pagination(admin: KeycloakAdmin, realm: str):
    admin.realm_name = realm

    for ind in range(admin.PAGE_SIZE + 50):
        username = f"user_{ind}"
        admin.create_user(payload={"username": username, "email": f"{username}@test.test"})

    users = admin.get_users()
    assert len(users) == admin.PAGE_SIZE + 50, len(users)

    users = admin.get_users(query={"first": 100})
    assert len(users) == 50, len(users)

    users = admin.get_users(query={"max": 20})
    assert len(users) == 20, len(users)


def test_idps(admin: KeycloakAdmin, realm: str):
    admin.realm_name = realm

    # Create IDP
    res = admin.create_idp(
        payload=dict(
            providerId="github", alias="github", config=dict(clientId="test", clientSecret="test")
        )
    )
    assert res == b"", res

    # Test listing
    idps = admin.get_idps()
    assert len(idps) == 1
    assert "github" == idps[0]["alias"]

    # Test adding a mapper
    res = admin.add_mapper_to_idp(
        idp_alias="github",
        payload={
            "identityProviderAlias": "github",
            "identityProviderMapper": "github-user-attribute-mapper",
            "name": "test",
        },
    )
    assert res == b"", res

    # Test delete
    res = admin.delete_idp(idp_alias="github")
    assert res == dict(), res


def test_user_credentials(admin: KeycloakAdmin, user: str):
    res = admin.set_user_password(user_id=user, password="booya", temporary=True)
    assert res == dict(), res

    credentials = admin.get_credentials(user_id=user)
    assert len(credentials) == 1
    assert credentials[0]["type"] == "password", credentials

    res = admin.delete_credential(user_id=user, credential_id=credentials[0]["id"])
    assert res == dict(), res
