def should_retry(status_code, retries_used):
    """Decide whether another retry is permitted."""
    raise NotImplementedError("Implement the retry predicate")
