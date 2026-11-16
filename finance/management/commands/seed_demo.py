from django.core.management.base import BaseCommand
from django.utils import timezone

from finance.demo import DEMO_EMAIL, build_demo
from finance.models import Transaction, Transfer, Wallet


class Command(BaseCommand):
    help = "Create or reset the demo account with three months of realistic data."

    def handle(self, *args, **options):
        today = timezone.localdate()
        user = build_demo(today)
        wallets = Wallet.objects.for_user(user).with_balance()
        self.stdout.write(self.style.SUCCESS(f"Demo account {DEMO_EMAIL} ready (data up to {today:%d %b %Y})."))
        self.stdout.write(
            f"  {Transaction.objects.filter(user=user).count()} transactions, "
            f"{Transfer.objects.filter(user=user).count()} transfers"
        )
        for wallet in wallets:
            self.stdout.write(f"  {wallet.name:<10} Rp{wallet.balance:,}".replace(",", "."))
