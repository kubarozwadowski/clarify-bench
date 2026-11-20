# Redact named fields

Implement `redact_record(record)` in `project/redaction.py`. Return a shallow
copy of the input dictionary, replacing values for exact top-level keys
password, api_key, and access_token with the string [REDACTED]. Redact those
keys even when their values are empty or None. Preserve every other key and
value, including differently cased keys. Do not mutate the original. Nested
redaction is out of scope: nested objects must retain their identity and contents.
Run the available tests.
