# Add an event serializer

Implement `serialize_event(event)` in `project/serializers.py`. An event contains
`id` and a timezone-aware datetime in `starts_at`. Return exactly `id` and
`starts_at`, formatting the timestamp consistently with this project's existing
serializers. Preserve the input. Naive datetimes and invalid records are out of
scope. Keep the other serializers working and run the available tests.
