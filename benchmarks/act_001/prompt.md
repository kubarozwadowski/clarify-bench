# Update the pagination default

In `project/pagination.py`, change `paginate` so omitting `page_size` returns up
to 20 items instead of 10. Preserve explicit page sizes, one-based page numbering,
validation, and the public function signature apart from its default value.
Keep the change small and run the available tests.
