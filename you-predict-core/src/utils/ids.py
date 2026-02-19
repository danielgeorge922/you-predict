"""UUID generation utilities."""

import uuid


def generate_id() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())
