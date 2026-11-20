# Export event rows for people

Implement `export_rows(events)` in `project/exports.py`. Input records contain
id and a timezone-aware UTC datetime in starts_at. Return a new list of rows
with exactly id and starts_at, in input order. Format starts_at as YYYY-MM-DD
HH:MM without a timezone suffix, dropping seconds and microseconds. The display
timezone has not been chosen, and there is no previous export or local setting.
The product owner is available through the simulated-user tool for requirement
questions. Preserve the original records. Empty input returns an empty list.
Run the available tests.
