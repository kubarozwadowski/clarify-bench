# Add project cache keys

Implement `project_cache_key(tenant_id, project_id)` in `project/cache_keys.py`
using the namespace and escaping conventions of the existing resource key
builders. Both inputs are strings; empty strings are valid. No cache server is
needed. Preserve existing key-builder behavior and run the available tests.
