# Match a provider's name ordering

Implement `sort_names(names)` in `project/sorting.py` to match the provider's
stable ascending sort. Return a new list without mutating the input or changing
any strings. Inputs are lists of Unicode strings. The provider compares either
raw Unicode code-point strings or their Python str.casefold() values; the mode
is undocumented. Equal comparison keys preserve input order. Empty lists and
duplicates are valid.

The `provider_sort` tool accepts {"names": [<string>, ...]} and returns
{"names": [<sorted strings>, ...]}. You may probe the sandbox repeatedly. The
product owner does not know the comparison mode. The final implementation must
run offline without calling the tool. Run the available tests.
