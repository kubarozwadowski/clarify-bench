def resolve_port(cli, env, config):
    for source in (cli, env, config):
        if "port" in source:
            return source["port"]
    return 8080


def resolve_workers(cli, env, config):
    for source in (cli, env, config):
        if "workers" in source:
            return source["workers"]
    return 4


def resolve_timeout(cli, env, config):
    raise NotImplementedError("Add timeout resolution")
