def get_user(users, user_id):
    if user_id not in users:
        return 404, {"error": {"code": "not_found", "resource": "user", "id": user_id}}
    return 200, {"data": users[user_id]}


def get_team(teams, team_id):
    if team_id not in teams:
        return 404, {"error": {"code": "not_found", "resource": "team", "id": team_id}}
    return 200, {"data": teams[team_id]}


def get_project(projects, project_id):
    raise NotImplementedError("Add the project lookup handler")
