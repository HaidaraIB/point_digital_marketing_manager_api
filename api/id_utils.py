"""
Generate human-readable IDs in format PREFIX-NNNNNN (e.g. QT-596305, VC-355777).
Uses increment per prefix; existing UUIDs in DB are ignored.
"""
import re


def get_next_id(prefix: str, model_class) -> str:
    """
    Return next ID for the given model as PREFIX-XXXXXX (6-digit number).
    Queries existing PKs matching PREFIX-\\d+, finds max number, returns PREFIX-(max+1).
    """
    pk_field = model_class._meta.pk.name
    existing = model_class.objects.values_list(pk_field, flat=True)
    pattern = re.compile(r"^%s-(\d+)$" % re.escape(prefix))
    numbers = []
    for pk in existing:
        if isinstance(pk, str) and pattern.match(pk):
            numbers.append(int(pattern.match(pk).group(1)))
    next_num = max(numbers, default=0) + 1
    return f"{prefix}-{next_num:06d}"
