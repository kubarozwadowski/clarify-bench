def list_users(users):
    return [user for user in users if user.get("deleted_at") is None]


def list_projects(projects):
    return [project for project in projects if project.get("deleted_at") is None]


def list_teams(teams):
    raise NotImplementedError("Add the team listing")
