import pytest

import keycloak
from keycloak import KeycloakAdmin
from keycloak.connection import ConnectionManager
from keycloak.exceptions import (
    KeycloakDeleteError,
    KeycloakGetError,
    KeycloakPostError,
    KeycloakPutError,
)


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

    # Get non-existing realm
    with pytest.raises(KeycloakGetError) as err:
        admin.get_realm(realm_name="non-existent")
    assert err.match('404: b\'{"error":"Realm not found."}\'')

    # Update realm
    res = admin.update_realm(realm_name="test", payload={"accountTheme": "test"})
    assert res == dict(), res

    # Check that the update worked
    res = admin.get_realm(realm_name="test")
    assert res["realm"] == "test"
    assert res["accountTheme"] == "test"

    # Update wrong payload
    with pytest.raises(KeycloakPutError) as err:
        admin.update_realm(realm_name="test", payload={"wrong": "payload"})
    assert err.match('400: b\'{"error":"Unrecognized field')

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

    # Delete non-existing realm
    with pytest.raises(KeycloakDeleteError) as err:
        admin.delete_realm(realm_name="non-existent")
    assert err.match('404: b\'{"error":"Realm not found."}\'')


def test_import_export_realms(admin: KeycloakAdmin, realm: str):
    admin.realm_name = realm

    realm_export = admin.export_realm(export_clients=True, export_groups_and_role=True)
    assert realm_export != dict(), realm_export

    admin.delete_realm(realm_name=realm)
    admin.realm_name = "master"
    res = admin.import_realm(payload=realm_export)
    assert res == b"", res

    # Test bad import
    with pytest.raises(KeycloakPostError) as err:
        admin.import_realm(payload=dict())
    assert err.match('500: b\'{"error":"unknown_error"}\'')


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

    # Test update user fail
    with pytest.raises(KeycloakPutError) as err:
        admin.update_user(user_id=user_id, payload={"wrong": "payload"})
    assert err.match('400: b\'{"error":"Unrecognized field')

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

    # Test user groups bad id
    with pytest.raises(KeycloakGetError) as err:
        admin.get_user_groups(user_id="does-not-exist")
    assert err.match('404: b\'{"error":"User not found"}\'')

    # Test logout
    res = admin.user_logout(user_id=user["id"])
    assert res == dict(), res

    # Test logout fail
    with pytest.raises(KeycloakPostError) as err:
        admin.user_logout(user_id="non-existent-id")
    assert err.match('404: b\'{"error":"User not found"}\'')

    # Test consents
    res = admin.user_consents(user_id=user["id"])
    assert len(res) == 0, res

    # Test consents fail
    with pytest.raises(KeycloakGetError) as err:
        admin.user_consents(user_id="non-existent-id")
    assert err.match('404: b\'{"error":"User not found"}\'')

    # Test delete user
    res = admin.delete_user(user_id=user_id)
    assert res == dict(), res
    with pytest.raises(KeycloakGetError) as err:
        admin.get_user(user_id=user_id)
    err.match('404: b\'{"error":"User not found"}\'')

    # Test delete fail
    with pytest.raises(KeycloakDeleteError) as err:
        admin.delete_user(user_id="non-existent-id")
    assert err.match('404: b\'{"error":"User not found"}\'')


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

    # Test create idp fail
    with pytest.raises(KeycloakPostError) as err:
        admin.create_idp(payload={"providerId": "does-not-exist", "alias": "something"})
    assert err.match("Invalid identity provider id"), err

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

    # Test mapper fail
    with pytest.raises(KeycloakPostError) as err:
        admin.add_mapper_to_idp(idp_alias="does-no-texist", payload=dict())
    assert err.match('404: b\'{"error":"HTTP 404 Not Found"}\'')

    # Test delete
    res = admin.delete_idp(idp_alias="github")
    assert res == dict(), res

    # Test delete fail
    with pytest.raises(KeycloakDeleteError) as err:
        admin.delete_idp(idp_alias="does-not-exist")
    assert err.match('404: b\'{"error":"HTTP 404 Not Found"}\'')


def test_user_credentials(admin: KeycloakAdmin, user: str):
    res = admin.set_user_password(user_id=user, password="booya", temporary=True)
    assert res == dict(), res

    # Test user password set fail
    with pytest.raises(KeycloakPutError) as err:
        admin.set_user_password(user_id="does-not-exist", password="")
    assert err.match('404: b\'{"error":"User not found"}\'')

    credentials = admin.get_credentials(user_id=user)
    assert len(credentials) == 1
    assert credentials[0]["type"] == "password", credentials

    # Test get credentials fail
    with pytest.raises(KeycloakGetError) as err:
        admin.get_credentials(user_id="does-not-exist")
    assert err.match('404: b\'{"error":"User not found"}\'')

    res = admin.delete_credential(user_id=user, credential_id=credentials[0]["id"])
    assert res == dict(), res

    # Test delete fail
    with pytest.raises(KeycloakDeleteError) as err:
        admin.delete_credential(user_id=user, credential_id="does-not-exist")
    assert err.match('404: b\'{"error":"Credential not found"}\'')


def test_social_logins(admin: KeycloakAdmin, user: str):
    res = admin.add_user_social_login(
        user_id=user, provider_id="gitlab", provider_userid="test", provider_username="test"
    )
    assert res == dict(), res
    admin.add_user_social_login(
        user_id=user, provider_id="github", provider_userid="test", provider_username="test"
    )
    assert res == dict(), res

    # Test add social login fail
    with pytest.raises(KeycloakPostError) as err:
        admin.add_user_social_login(
            user_id="does-not-exist",
            provider_id="does-not-exist",
            provider_userid="test",
            provider_username="test",
        )
    assert err.match('404: b\'{"error":"User not found"}\'')

    res = admin.get_user_social_logins(user_id=user)
    assert res == list(), res

    # Test get social logins fail
    with pytest.raises(KeycloakGetError) as err:
        admin.get_user_social_logins(user_id="does-not-exist")
    assert err.match('404: b\'{"error":"User not found"}\'')

    res = admin.delete_user_social_login(user_id=user, provider_id="gitlab")
    assert res == {}, res

    res = admin.delete_user_social_login(user_id=user, provider_id="github")
    assert res == {}, res

    with pytest.raises(KeycloakDeleteError) as err:
        admin.delete_user_social_login(user_id=user, provider_id="instagram")
    assert err.match('404: b\'{"error":"Link not found"}\''), err


def test_server_info(admin: KeycloakAdmin):
    info = admin.get_server_info()
    assert set(info.keys()) == {
        "systemInfo",
        "memoryInfo",
        "profileInfo",
        "themes",
        "socialProviders",
        "identityProviders",
        "providers",
        "protocolMapperTypes",
        "builtinProtocolMappers",
        "clientInstallations",
        "componentTypes",
        "passwordPolicies",
        "enums",
    }, info.keys()


def test_groups(admin: KeycloakAdmin, user: str):
    # Test get groups
    groups = admin.get_groups()
    assert len(groups) == 0

    # Test create group
    group_id = admin.create_group(payload={"name": "main-group"})
    assert group_id is not None, group_id

    # Test create subgroups
    subgroup_id_1 = admin.create_group(payload={"name": "subgroup-1"}, parent=group_id)
    subgroup_id_2 = admin.create_group(payload={"name": "subgroup-2"}, parent=group_id)

    # Test create group fail
    with pytest.raises(KeycloakPostError) as err:
        admin.create_group(payload={"name": "subgroup-1"}, parent=group_id)
    assert err.match('409: b\'{"error":"unknown_error"}\''), err

    # Test skip exists OK
    subgroup_id_1_eq = admin.create_group(
        payload={"name": "subgroup-1"}, parent=group_id, skip_exists=True
    )
    assert subgroup_id_1_eq is None

    # Test get groups again
    groups = admin.get_groups()
    assert len(groups) == 1, groups
    assert len(groups[0]["subGroups"]) == 2, groups["subGroups"]
    assert groups[0]["id"] == group_id
    assert {x["id"] for x in groups[0]["subGroups"]} == {subgroup_id_1, subgroup_id_2}

    # Test get groups query
    groups = admin.get_groups(query={"max": 10})
    assert len(groups) == 1, groups
    assert len(groups[0]["subGroups"]) == 2, groups["subGroups"]
    assert groups[0]["id"] == group_id
    assert {x["id"] for x in groups[0]["subGroups"]} == {subgroup_id_1, subgroup_id_2}

    # Test get group
    res = admin.get_group(group_id=subgroup_id_1)
    assert res["id"] == subgroup_id_1, res
    assert res["name"] == "subgroup-1"
    assert res["path"] == "/main-group/subgroup-1"

    # Test get group fail
    with pytest.raises(KeycloakGetError) as err:
        admin.get_group(group_id="does-not-exist")
    assert err.match('404: b\'{"error":"Could not find group by id"}\''), err

    # Create 1 more subgroup
    subsubgroup_id_1 = admin.create_group(payload={"name": "subsubgroup-1"}, parent=subgroup_id_2)
    main_group = admin.get_group(group_id=group_id)

    # Test nested searches
    res = admin.get_subgroups(group=main_group, path="/main-group/subgroup-2/subsubgroup-1")
    assert res is not None, res
    assert res["id"] == subsubgroup_id_1

    # Test empty search
    res = admin.get_subgroups(group=main_group, path="/none")
    assert res is None, res

    # Test get group by path
    res = admin.get_group_by_path(path="/main-group/subgroup-1")
    assert res is None, res

    res = admin.get_group_by_path(path="/main-group/subgroup-1", search_in_subgroups=True)
    assert res is not None, res
    assert res["id"] == subgroup_id_1, res

    res = admin.get_group_by_path(
        path="/main-group/subgroup-2/subsubgroup-1/test", search_in_subgroups=True
    )
    assert res is None, res

    res = admin.get_group_by_path(
        path="/main-group/subgroup-2/subsubgroup-1", search_in_subgroups=True
    )
    assert res is not None, res
    assert res["id"] == subsubgroup_id_1

    res = admin.get_group_by_path(path="/main-group")
    assert res is not None, res
    assert res["id"] == group_id, res

    # Test group members
    res = admin.get_group_members(group_id=subgroup_id_2)
    assert len(res) == 0, res

    # Test fail group members
    with pytest.raises(KeycloakGetError) as err:
        admin.get_group_members(group_id="does-not-exist")
    assert err.match('404: b\'{"error":"Could not find group by id"}\'')

    res = admin.group_user_add(user_id=user, group_id=subgroup_id_2)
    assert res == dict(), res

    res = admin.get_group_members(group_id=subgroup_id_2)
    assert len(res) == 1, res
    assert res[0]["id"] == user

    # Test get group members query
    res = admin.get_group_members(group_id=subgroup_id_2, query={"max": 10})
    assert len(res) == 1, res
    assert res[0]["id"] == user

    with pytest.raises(KeycloakDeleteError) as err:
        admin.group_user_remove(user_id="does-not-exist", group_id=subgroup_id_2)
    assert err.match('404: b\'{"error":"User not found"}\''), err

    res = admin.group_user_remove(user_id=user, group_id=subgroup_id_2)
    assert res == dict(), res

    # Test set permissions
    res = admin.group_set_permissions(group_id=subgroup_id_2, enabled=True)
    assert res["enabled"], res
    res = admin.group_set_permissions(group_id=subgroup_id_2, enabled=False)
    assert not res["enabled"], res
    with pytest.raises(KeycloakPutError) as err:
        admin.group_set_permissions(group_id=subgroup_id_2, enabled="blah")
    assert err.match('500: b\'{"error":"unknown_error"}\''), err

    # Test update group
    res = admin.update_group(group_id=subgroup_id_2, payload={"name": "new-subgroup-2"})
    assert res == dict(), res
    assert admin.get_group(group_id=subgroup_id_2)["name"] == "new-subgroup-2"

    # test update fail
    with pytest.raises(KeycloakPutError) as err:
        admin.update_group(group_id="does-not-exist", payload=dict())
    assert err.match('404: b\'{"error":"Could not find group by id"}\''), err

    # Test delete
    res = admin.delete_group(group_id=group_id)
    assert res == dict(), res
    assert len(admin.get_groups()) == 0

    # Test delete fail
    with pytest.raises(KeycloakDeleteError) as err:
        admin.delete_group(group_id="does-not-exist")
    assert err.match('404: b\'{"error":"Could not find group by id"}\''), err


def test_clients(admin: KeycloakAdmin, realm: str):
    admin.realm_name = realm

    # Test get clients
    clients = admin.get_clients()
    assert len(clients) == 6, clients
    assert {x["name"] for x in clients} == set(
        [
            "${client_admin-cli}",
            "${client_security-admin-console}",
            "${client_account-console}",
            "${client_broker}",
            "${client_account}",
            "${client_realm-management}",
        ]
    ), clients

    # Test create client
    client_id = admin.create_client(payload={"name": "test-client", "clientId": "test-client"})
    assert client_id, client_id

    with pytest.raises(KeycloakPostError) as err:
        admin.create_client(payload={"name": "test-client", "clientId": "test-client"})
    assert err.match('409: b\'{"errorMessage":"Client test-client already exists"}\''), err

    client_id_2 = admin.create_client(
        payload={"name": "test-client", "clientId": "test-client"}, skip_exists=True
    )
    assert client_id == client_id_2, client_id_2

    # Test get client
    res = admin.get_client(client_id=client_id)
    assert res["clientId"] == "test-client", res
    assert res["name"] == "test-client", res
    assert res["id"] == client_id, res

    with pytest.raises(KeycloakGetError) as err:
        admin.get_client(client_id="does-not-exist")
    assert err.match('404: b\'{"error":"Could not find client"}\'')
    assert len(admin.get_clients()) == 7

    # Test get client id
    assert admin.get_client_id(client_name="test-client") == client_id
    assert admin.get_client_id(client_name="does-not-exist") is None

    # Test update client
    res = admin.update_client(client_id=client_id, payload={"name": "test-client-change"})
    assert res == dict(), res

    with pytest.raises(KeycloakPutError) as err:
        admin.update_client(client_id="does-not-exist", payload={"name": "test-client-change"})
    assert err.match('404: b\'{"error":"Could not find client"}\'')

    # Test authz
    auth_client_id = admin.create_client(
        payload={
            "name": "authz-client",
            "clientId": "authz-client",
            "authorizationServicesEnabled": True,
            "serviceAccountsEnabled": True,
        }
    )
    res = admin.get_client_authz_settings(client_id=auth_client_id)
    assert res["allowRemoteResourceManagement"]
    assert res["decisionStrategy"] == "UNANIMOUS"
    assert len(res["policies"]) >= 0

    with pytest.raises(KeycloakGetError) as err:
        admin.get_client_authz_settings(client_id=client_id)
    assert err.match('500: b\'{"error":"HTTP 500 Internal Server Error"}\'')

    # Authz resources
    res = admin.get_client_authz_resources(client_id=auth_client_id)
    assert len(res) == 1
    assert res[0]["name"] == "Default Resource"

    with pytest.raises(KeycloakGetError) as err:
        admin.get_client_authz_resources(client_id=client_id)
    assert err.match('500: b\'{"error":"unknown_error"}\'')

    res = admin.create_client_authz_resource(
        client_id=auth_client_id, payload={"name": "test-resource"}
    )
    assert res["name"] == "test-resource", res
    test_resource_id = res["_id"]

    with pytest.raises(KeycloakPostError) as err:
        admin.create_client_authz_resource(
            client_id=auth_client_id, payload={"name": "test-resource"}
        )
    assert err.match('409: b\'{"error":"invalid_request"')
    assert admin.create_client_authz_resource(
        client_id=auth_client_id, payload={"name": "test-resource"}, skip_exists=True
    ) == {"msg": "Already exists"}

    res = admin.get_client_authz_resources(client_id=auth_client_id)
    assert len(res) == 2
    assert {x["name"] for x in res} == {"Default Resource", "test-resource"}

    # Authz policies
    res = admin.get_client_authz_policies(client_id=auth_client_id)
    assert len(res) == 1, res
    assert res[0]["name"] == "Default Policy"
    assert len(admin.get_client_authz_policies(client_id=client_id)) == 1

    with pytest.raises(KeycloakGetError) as err:
        admin.get_client_authz_policies(client_id="does-not-exist")
    assert err.match('404: b\'{"error":"Could not find client"}\'')

    role_id = admin.get_realm_role(role_name="offline_access")["id"]
    res = admin.create_client_authz_role_based_policy(
        client_id=auth_client_id,
        payload={"name": "test-authz-rb-policy", "roles": [{"id": role_id}]},
    )
    assert res["name"] == "test-authz-rb-policy", res

    with pytest.raises(KeycloakPostError) as err:
        admin.create_client_authz_role_based_policy(
            client_id=auth_client_id,
            payload={"name": "test-authz-rb-policy", "roles": [{"id": role_id}]},
        )
    assert err.match('409: b\'{"error":"Policy with name')
    assert admin.create_client_authz_role_based_policy(
        client_id=auth_client_id,
        payload={"name": "test-authz-rb-policy", "roles": [{"id": role_id}]},
        skip_exists=True,
    ) == {"msg": "Already exists"}
    assert len(admin.get_client_authz_policies(client_id=auth_client_id)) == 2

    # Test authz permissions
    res = admin.get_client_authz_permissions(client_id=auth_client_id)
    assert len(res) == 1, res
    assert res[0]["name"] == "Default Permission"
    assert len(admin.get_client_authz_permissions(client_id=client_id)) == 1

    with pytest.raises(KeycloakGetError) as err:
        admin.get_client_authz_permissions(client_id="does-not-exist")
    assert err.match('404: b\'{"error":"Could not find client"}\'')

    res = admin.create_client_authz_resource_based_permission(
        client_id=auth_client_id,
        payload={"name": "test-permission-rb", "resources": [test_resource_id]},
    )
    assert res, res
    assert res["name"] == "test-permission-rb"
    assert res["resources"] == [test_resource_id]

    with pytest.raises(KeycloakPostError) as err:
        admin.create_client_authz_resource_based_permission(
            client_id=auth_client_id,
            payload={"name": "test-permission-rb", "resources": [test_resource_id]},
        )
    assert err.match('409: b\'{"error":"Policy with name')
    assert admin.create_client_authz_resource_based_permission(
        client_id=auth_client_id,
        payload={"name": "test-permission-rb", "resources": [test_resource_id]},
        skip_exists=True,
    ) == {"msg": "Already exists"}
    assert len(admin.get_client_authz_permissions(client_id=auth_client_id)) == 2

    # Test authz scopes
    res = admin.get_client_authz_scopes(client_id=auth_client_id)
    assert len(res) == 0, res

    with pytest.raises(KeycloakGetError) as err:
        admin.get_client_authz_scopes(client_id=client_id)
    assert err.match('500: b\'{"error":"unknown_error"}\'')

    # Test service account user
    res = admin.get_client_service_account_user(client_id=auth_client_id)
    assert res["username"] == "service-account-authz-client", res

    with pytest.raises(KeycloakGetError) as err:
        admin.get_client_service_account_user(client_id=client_id)
    assert err.match('400: b\'{"error":"unknown_error"}\'')

    # Test delete client
    res = admin.delete_client(client_id=auth_client_id)
    assert res == dict(), res
    with pytest.raises(KeycloakDeleteError) as err:
        admin.delete_client(client_id=auth_client_id)
    assert err.match('404: b\'{"error":"Could not find client"}\'')


def test_realm_roles(admin: KeycloakAdmin, realm: str):
    admin.realm_name = realm

    # Test get realm roles
    roles = admin.get_realm_roles()
    assert len(roles) == 3, roles
    role_names = [x["name"] for x in roles]
    assert "uma_authorization" in role_names, role_names
    assert "offline_access" in role_names, role_names

    # Test empty members
    with pytest.raises(KeycloakGetError) as err:
        admin.get_realm_role_members(role_name="does-not-exist")
    assert err.match('404: b\'{"error":"Could not find role"}\'')
    members = admin.get_realm_role_members(role_name="offline_access")
    assert members == list(), members

    # Test create realm role
    role_id = admin.create_realm_role(payload={"name": "test-realm-role"})
    assert role_id, role_id
    with pytest.raises(KeycloakPostError) as err:
        admin.create_realm_role(payload={"name": "test-realm-role"})
    assert err.match('409: b\'{"errorMessage":"Role with name test-realm-role already exists"}\'')
    role_id_2 = admin.create_realm_role(payload={"name": "test-realm-role"}, skip_exists=True)
    assert role_id == role_id_2

    # Test update realm role
    res = admin.update_realm_role(
        role_name="test-realm-role", payload={"name": "test-realm-role-update"}
    )
    assert res == dict(), res
    with pytest.raises(KeycloakPutError) as err:
        admin.update_realm_role(
            role_name="test-realm-role", payload={"name": "test-realm-role-update"}
        )
    assert err.match('404: b\'{"error":"Could not find role"}\''), err

    # Test realm role user assignment
    user_id = admin.create_user(payload={"username": "role-testing", "email": "test@test.test"})
    with pytest.raises(KeycloakPostError) as err:
        admin.assign_realm_roles(user_id=user_id, roles=["bad"])
    assert err.match('500: b\'{"error":"unknown_error"}\'')
    res = admin.assign_realm_roles(
        user_id=user_id,
        roles=[
            admin.get_realm_role(role_name="offline_access"),
            admin.get_realm_role(role_name="test-realm-role-update"),
        ],
    )
    assert res == dict(), res
    assert admin.get_user(user_id=user_id)["username"] in [
        x["username"] for x in admin.get_realm_role_members(role_name="offline_access")
    ]
    assert admin.get_user(user_id=user_id)["username"] in [
        x["username"] for x in admin.get_realm_role_members(role_name="test-realm-role-update")
    ]

    roles = admin.get_realm_roles_of_user(user_id=user_id)
    assert len(roles) == 3
    assert "offline_access" in [x["name"] for x in roles]
    assert "test-realm-role-update" in [x["name"] for x in roles]

    with pytest.raises(KeycloakDeleteError) as err:
        admin.delete_realm_roles_of_user(user_id=user_id, roles=["bad"])
    assert err.match('500: b\'{"error":"unknown_error"}\'')
    res = admin.delete_realm_roles_of_user(
        user_id=user_id, roles=[admin.get_realm_role(role_name="offline_access")]
    )
    assert res == dict(), res
    assert admin.get_realm_role_members(role_name="offline_access") == list()
    roles = admin.get_realm_roles_of_user(user_id=user_id)
    assert len(roles) == 2
    assert "offline_access" not in [x["name"] for x in roles]
    assert "test-realm-role-update" in [x["name"] for x in roles]

    roles = admin.get_available_realm_roles_of_user(user_id=user_id)
    assert len(roles) == 2
    assert "offline_access" in [x["name"] for x in roles]
    assert "uma_authorization" in [x["name"] for x in roles]

    # Test realm role group assignment
    group_id = admin.create_group(payload={"name": "test-group"})
    with pytest.raises(KeycloakPostError) as err:
        admin.assign_group_realm_roles(group_id=group_id, roles=["bad"])
    assert err.match('500: b\'{"error":"unknown_error"}\'')
    res = admin.assign_group_realm_roles(
        group_id=group_id,
        roles=[
            admin.get_realm_role(role_name="offline_access"),
            admin.get_realm_role(role_name="test-realm-role-update"),
        ],
    )
    assert res == dict(), res

    roles = admin.get_group_realm_roles(group_id=group_id)
    assert len(roles) == 2
    assert "offline_access" in [x["name"] for x in roles]
    assert "test-realm-role-update" in [x["name"] for x in roles]

    with pytest.raises(KeycloakDeleteError) as err:
        admin.delete_group_realm_roles(group_id=group_id, roles=["bad"])
    assert err.match('500: b\'{"error":"unknown_error"}\'')
    res = admin.delete_group_realm_roles(
        group_id=group_id, roles=[admin.get_realm_role(role_name="offline_access")]
    )
    assert res == dict(), res
    roles = admin.get_group_realm_roles(group_id=group_id)
    assert len(roles) == 1
    assert "test-realm-role-update" in [x["name"] for x in roles]

    # Test composite realm roles
    composite_role = admin.create_realm_role(payload={"name": "test-composite-role"})
    with pytest.raises(KeycloakPostError) as err:
        admin.add_composite_realm_roles_to_role(role_name=composite_role, roles=["bad"])
    assert err.match('500: b\'{"error":"unknown_error"}\'')
    res = admin.add_composite_realm_roles_to_role(
        role_name=composite_role, roles=[admin.get_realm_role(role_name="test-realm-role-update")]
    )
    assert res == dict(), res

    res = admin.get_composite_realm_roles_of_role(role_name=composite_role)
    assert len(res) == 1
    assert "test-realm-role-update" in res[0]["name"]
    with pytest.raises(KeycloakGetError) as err:
        admin.get_composite_realm_roles_of_role(role_name="bad")
    assert err.match('404: b\'{"error":"Could not find role"}\'')

    res = admin.get_composite_realm_roles_of_user(user_id=user_id)
    assert len(res) == 4
    assert "offline_access" in {x["name"] for x in res}
    assert "test-realm-role-update" in {x["name"] for x in res}
    assert "uma_authorization" in {x["name"] for x in res}
    with pytest.raises(KeycloakGetError) as err:
        admin.get_composite_realm_roles_of_user(user_id="bad")
    assert err.match('404: b\'{"error":"User not found"}\'')

    with pytest.raises(KeycloakDeleteError) as err:
        admin.remove_composite_realm_roles_to_role(role_name=composite_role, roles=["bad"])
    assert err.match('500: b\'{"error":"unknown_error"}\'')
    res = admin.remove_composite_realm_roles_to_role(
        role_name=composite_role, roles=[admin.get_realm_role(role_name="test-realm-role-update")]
    )
    assert res == dict(), res

    res = admin.get_composite_realm_roles_of_role(role_name=composite_role)
    assert len(res) == 0

    # Test delete realm role
    res = admin.delete_realm_role(role_name=composite_role)
    assert res == dict(), res
    with pytest.raises(KeycloakDeleteError) as err:
        admin.delete_realm_role(role_name=composite_role)
    assert err.match('404: b\'{"error":"Could not find role"}\'')


def test_email(admin: KeycloakAdmin, user: str):
    # Emails will fail as we don't have SMTP test setup
    with pytest.raises(KeycloakPutError) as err:
        admin.send_update_account(user_id=user, payload=dict())
    assert err.match('500: b\'{"error":"unknown_error"}\'')

    admin.update_user(user_id=user, payload={"enabled": True})
    with pytest.raises(KeycloakPutError) as err:
        admin.send_verify_email(user_id=user)
    assert err.match('500: b\'{"errorMessage":"Failed to send execute actions email"}\'')


def test_get_sessions(admin: KeycloakAdmin):
    sessions = admin.get_sessions(user_id=admin.get_user_id(username=admin.username))
    assert len(sessions) >= 1
    with pytest.raises(KeycloakGetError) as err:
        admin.get_sessions(user_id="bad")
    assert err.match('404: b\'{"error":"User not found"}\'')


def test_get_client_installation_provider(admin: KeycloakAdmin, client: str):
    with pytest.raises(KeycloakGetError) as err:
        admin.get_client_installation_provider(client_id=client, provider_id="bad")
    assert err.match('404: b\'{"error":"Unknown Provider"}\'')

    installation = admin.get_client_installation_provider(
        client_id=client, provider_id="keycloak-oidc-keycloak-json"
    )
    assert set(installation.keys()) == {
        "auth-server-url",
        "confidential-port",
        "credentials",
        "realm",
        "resource",
        "ssl-required",
    }
