from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)

    def __str__(self):
        return f"{self.user.username} - Balance: {self.balance}"

class Game(models.Model):
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=[('upcoming', 'Upcoming'), ('finished', 'Finished')], default='upcoming')
    # نتیجه نهایی بازی (برای تسویه توسط ادمین)
    result_description = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Home win 2-1")

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

class BetOption(models.Model):
    """هر گزینه شرط‌بندی مرتبط با یک بازی (مثل برد میزبان، مساوی، بیش از ۲.۵ گل و...)"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='bet_options')
    description = models.CharField(max_length=200)  # مثلاً "Home Win", "Draw", "Over 2.5", "Exact Score 2-1"
    odds = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    is_active = models.BooleanField(default=True)  # فعال/غیرفعال کردن گزینه
    # برای تسویه: ادمین مشخص می‌کند کدام گزینه برنده شده است
    is_winner = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.game} - {self.description} ({self.odds})"

class Bet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bets')
    bet_option = models.ForeignKey(BetOption, on_delete=models.CASCADE, related_name='bets')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    placed_at = models.DateTimeField(auto_now_add=True)
    is_settled = models.BooleanField(default=False)
    won = models.BooleanField(default=False)
    payout = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} bet on {self.bet_option} - {self.amount}"

# همان سیگنال برای ساخت خودکار پروفایل
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


# ======================== AUTO SETTLE SIGNAL ========================
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction


@receiver(post_save, sender=BetOption)
def auto_settle_bets_on_winner(sender, instance, created, **kwargs):
    """
    وقتی یک BetOption به عنوان برنده علامت‌گذاری می‌شود (is_winner=True)
    و بازی مرتبط با آن تمام شده است (status='finished')،
    تمام شرط‌های تسویه‌نشده آن بازی را تصفیه می‌کند.
    """
    # فقط در صورتی که گزینه برنده شده و بازی تمام شده باشد
    if instance.is_winner and instance.game.status == 'finished':
        # پیدا کردن شرط‌های تسویه‌نشده این بازی
        unsettled_bets = Bet.objects.filter(bet_option__game=instance.game, is_settled=False)

        if not unsettled_bets.exists():
            return  # همه شرط‌ها قبلاً تسویه شده‌اند

        with transaction.atomic():
            for bet in unsettled_bets:
                if bet.bet_option == instance:
                    # شرط برنده
                    bet.won = True
                    bet.payout = bet.amount * bet.bet_option.odds
                    # افزایش موجودی کاربر
                    profile = bet.user.profile
                    profile.balance += bet.payout
                    profile.save()
                else:
                    # شرط بازنده
                    bet.won = False
                    bet.payout = None
                bet.is_settled = True
                bet.save()
