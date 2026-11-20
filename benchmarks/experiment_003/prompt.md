# Match a legacy query encoder

Implement `encode_query(value)` in `project/query.py` to match the provider's
encoder. Input is a Unicode string. The provider encodes using UTF-8 and
uppercase percent-escape hex, preserving only ASCII letters, digits, and -._~.
It encodes literal plus as %2B and slash as %2F. Spaces use either + or %20;
the provider's convention is undocumented. Empty input is valid.

The `provider_encode` tool accepts {"value": <string>} and returns
{"value": ..., "encoded": ...}. You may probe it repeatedly. The product owner
does not know the space convention. Your final implementation must work offline,
without calling the tool. Run the available tests.
