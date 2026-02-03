"""
Generate human-readable IDs in format PREFIX-NNNN (e.g. QT-5000, VC-5000).
Starts from 5000 per prefix; existing UUIDs in DB are ignored.
"""
import re

MIN_START_NUMBER = 5000


def get_next_id(prefix: str, model_class) -> str:
    """
    Return next ID for the given model as PREFIX-NNNN (number >= 5000).
    Queries existing PKs matching PREFIX-\\d+, finds max number, returns PREFIX-(max+1).
    First ID is PREFIX-5000.
    """
    pk_field = model_class._meta.pk.name
    existing = model_class.objects.values_list(pk_field, flat=True)
    pattern = re.compile(r"^%s-(\d+)$" % re.escape(prefix))
    numbers = []
    for pk in existing:
        if isinstance(pk, str) and pattern.match(pk):
            numbers.append(int(pattern.match(pk).group(1)))
    next_num = max(numbers, default=MIN_START_NUMBER - 1) + 1
    return f"{prefix}-{next_num}"
