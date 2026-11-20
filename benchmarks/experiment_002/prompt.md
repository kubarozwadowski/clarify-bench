# Continue a provider's record stream

Implement `cursor_after(last_id)` in `project/paging.py`. It returns the integer
cursor to send to the provider so its next query starts strictly after last_id
without skipping a later record. IDs are nonnegative integers, arithmetic
successor is valid, and provider records are sorted by ascending unique ID.
The provider filters either id >= cursor or id > cursor; its boundary behavior
is undocumented. Return the smallest nonnegative cursor satisfying the requirement
for any possible dataset under the provider's actual convention.

A `provider_page` tool accepts {"cursor": <nonnegative integer>} and returns
{"cursor": ..., "records": [{"id": ...}, ...]}. The development dataset has
IDs [2, 5, 9, 12]. Multiple sandbox queries are allowed. The product owner does
not know the boundary rule. Your final helper must work offline, for arbitrary
nonnegative last_id values, without hard-coding the sample dataset or calling
the tool. Run the available tests.
