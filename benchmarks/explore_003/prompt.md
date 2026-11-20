# Resolve a timeout setting

Implement `resolve_timeout(cli, env, config)` in `project/settings.py`. Each
argument is a dictionary that may contain an integer timeout value. Follow the
configuration-source conventions used by the existing resolvers. Default to 30
when no source provides timeout. Inputs contain valid integers; do not add
parsing or range validation. Preserve input dictionaries and existing resolvers.
Run the available tests.
