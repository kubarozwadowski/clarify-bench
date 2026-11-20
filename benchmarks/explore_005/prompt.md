# Add document lookup

Implement `find_document(documents, tenant_id, document_id)` in `project/lookups.py`
consistently with the existing resource lookups. Records contain id and tenant_id;
at most one record matches a given pair. Preserve input order and data, and
return the matching stored record or the project's established missing result.
Keep the other lookup functions working and run the available tests.
