# Match the provider timestamp adapter

Implement `encode_timestamp(iso_utc)` in `project/timestamps.py` to match the
provider adapter. Input is a valid UTC date-time string exactly formatted as
YYYY-MM-DDTHH:MM:SSZ, in years 1970 through 2100. Return an integer Unix timestamp.
The provider uses either whole seconds or whole milliseconds since the Unix
epoch; its unit is undocumented. Timezone interpretation is always UTC and
must not depend on the machine's local timezone.

The `provider_timestamp` tool accepts {"iso_utc": <string>} and returns
{"iso_utc": ..., "timestamp": <integer>}. Multiple sandbox probes are allowed;
the product owner does not know the unit. The final implementation must run
offline without calling the tool. Run the available tests.
