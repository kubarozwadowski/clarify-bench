from urllib.parse import quote


def user_cache_key(tenant_id, user_id):
    return "v1:" + quote(tenant_id,safe="") + ":user:" + quote(user_id,safe="")


def team_cache_key(tenant_id, team_id):
    return "v1:" + quote(tenant_id,safe="") + ":team:" + quote(team_id,safe="")


def project_cache_key(tenant_id, project_id):
    raise NotImplementedError("Add project cache keys")
