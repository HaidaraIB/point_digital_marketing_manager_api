"""
Monthly cash opening balances: each month's opening IQD balance equals the prior month's closing.
Rebuilt whenever vouchers change.
"""
import re
from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import AgencySettings, MonthlyOpeningBalance, Voucher

_AR_TRANS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def parse_voucher_month(date_str: str) -> str | None:
    if not date_str or not isinstance(date_str, str):
        return None
    s = date_str.strip()
    m = re.match(r"^(\d{4})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    parts = s.split("/")
    if len(parts) < 3:
        return None
    clean = [p.translate(_AR_TRANS) for p in parts]
    try:
        day = int(clean[0])
        month = int(clean[1])
        year = int(clean[2])
    except ValueError:
        return None
    if month < 1 or month > 12:
        return None
    return f"{year:04d}-{month:02d}"


def _month_add(ym: str, delta: int = 1) -> str:
    y, mo = map(int, ym.split("-"))
    mo += delta
    while mo > 12:
        mo -= 12
        y += 1
    while mo < 1:
        mo += 12
        y -= 1
    return f"{y:04d}-{mo:02d}"


def _iter_months(ym_start: str, ym_end: str):
    cur = ym_start
    yield cur
    while cur < ym_end:
        cur = _month_add(cur, 1)
        yield cur


def rebuild_monthly_opening_balances() -> None:
    settings = AgencySettings.objects.first()
    default_rate = (
        Decimal(str(settings.exchange_rate)) if settings and settings.exchange_rate is not None else Decimal("1500")
    )

    vouchers = list(Voucher.objects.all())
    months_with_data: set[str] = set()
    for v in vouchers:
        ym = parse_voucher_month(v.date)
        if ym:
            months_with_data.add(ym)

    if not months_with_data:
        MonthlyOpeningBalance.objects.all().delete()
        return

    min_ym = min(months_with_data)
    today = timezone.now().date()
    current_ym = f"{today.year:04d}-{today.month:02d}"
    max_ym = max(max(months_with_data), current_ym)

    receipts: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    payments: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    def amount_iqd(v: Voucher) -> Decimal:
        amt = Decimal(str(v.amount))
        rate = (
            Decimal(str(v.exchange_rate))
            if v.exchange_rate is not None
            else default_rate
        )
        if v.currency == "USD":
            return amt * rate
        return amt

    for v in vouchers:
        ym = parse_voucher_month(v.date)
        if not ym:
            continue
        a = amount_iqd(v)
        if v.type == Voucher.VoucherType.RECEIPT:
            receipts[ym] += a
        else:
            payments[ym] += a

    opening_by_month: dict[str, Decimal] = {}
    opening = Decimal("0")
    for ym in _iter_months(min_ym, max_ym):
        opening_by_month[ym] = opening
        closing = opening + receipts[ym] - payments[ym]
        opening = closing

    with transaction.atomic():
        keep = set(opening_by_month.keys())
        MonthlyOpeningBalance.objects.exclude(year_month__in=keep).delete()
        for ym, op in opening_by_month.items():
            MonthlyOpeningBalance.objects.update_or_create(
                year_month=ym,
                defaults={"opening_iqd": op},
            )
