def paginate(items, page=1, page_size=10):
    """Return one page of items; page numbers start at one."""
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be positive")
    start = (page - 1) * page_size
    return items[start:start + page_size]
