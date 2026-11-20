# Implement an explicit retry policy

Implement `should_retry(status_code, retries_used)` in `project/retry.py`.
Return True only when the status is 429 or in the inclusive range 500–599 AND
fewer than three retries have already been used. Return False otherwise.
Inputs are integer status codes 100–599 and nonnegative integer retries_used.
Return an actual boolean. Do not sleep or make network requests; this function
only makes the decision. Run the available tests.
