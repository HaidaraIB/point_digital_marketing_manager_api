from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Voucher
from .monthly_balance import rebuild_monthly_opening_balances


@receiver(post_save, sender=Voucher)
@receiver(post_delete, sender=Voucher)
def voucher_changed_rebuild_monthly_opening(sender, **kwargs):
    rebuild_monthly_opening_balances()
