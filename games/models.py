# bet/games/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# 1. مدل پروفایل برای مدیریت کیف پول (سکه) کاربران
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)  # 1000 سکه رایگان برای شروع

    def __str__(self):
        return f"{self.user.username} Profile"


# ساخت اتوماتیک پروفایل هنگام ثبت‌نام کاربر
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# 2. مدل بازی‌ها (با قابلیت ثبت نتیجه و تسویه خودکار)
class Game(models.Model):
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    status = models.CharField(max_length=20, default='upcoming')

    # فیلدهای جدید برای ثبت نتیجه توسط ادمین
    home_score = models.IntegerField(null=True, blank=True, verbose_name="گل‌های میزبان")
    away_score = models.IntegerField(null=True, blank=True, verbose_name="گل‌های میهمان")
    is_finished = models.BooleanField(default=False, verbose_name="بازی تمام شده؟")

    def save(self, *args, **kwargs):
        # بررسی وضعیت قبلی بازی برای جلوگیری از تسویه مجدد
        was_finished = False
        if self.pk:
            try:
                old_game = Game.objects.get(pk=self.pk)
                was_finished = old_game.is_finished
            except Game.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # اجرای اتوماتیک تسویه شرط‌ها اگر ادمین تیک پایان بازی را زد
        if self.is_finished and not was_finished and self.home_score is not None and self.away_score is not None:
            self.auto_settle_bets()

    def auto_settle_bets(self):
        # تشخیص برنده
        if self.home_score > self.away_score:
            winning_desc = f"{self.home_team} Win"
        elif self.home_score < self.away_score:
            winning_desc = f"{self.away_team} Win"
        else:
            winning_desc = "Draw"

        winning_option = self.bet_options.filter(description=winning_desc).first()
        all_bets = Bet.objects.filter(bet_option__game=self, is_settled=False)

        # بررسی تمام پیش‌بینی‌ها و واریز سکه
        for bet in all_bets:
            bet.is_settled = True
            if winning_option and bet.bet_option == winning_option:
                bet.won = True
                bet.payout = float(bet.amount) * float(bet.bet_option.odds)
                # شارژ حساب کاربر برنده
                bet.user.profile.balance += bet.payout
                bet.user.profile.save()
            else:
                bet.won = False
                bet.payout = 0
            bet.save()

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"


# 3. مدل گزینه‌های پیش‌بینی هر بازی (برد، باخت، مساوی)
class BetOption(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='bet_options')
    description = models.CharField(max_length=100)
    odds = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.game} - {self.description} ({self.odds})"


# 4. مدل ثبت پیش‌بینی بازی‌ها توسط کاربر
class Bet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bets')
    bet_option = models.ForeignKey(BetOption, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    placed_at = models.DateTimeField(auto_now_add=True)
    is_settled = models.BooleanField(default=False)
    won = models.BooleanField(default=False)
    payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username} - {self.bet_option}"


# 5. مدل ثبت پیش‌بینی رتبه‌بندی مرحله گروهی
class GroupStandingBet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=1)
    predicted_first = models.CharField(max_length=50, verbose_name="تیم اول")
    predicted_second = models.CharField(max_length=50, verbose_name="تیم دوم")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="مبلغ (سکه)")
    odds = models.DecimalField(max_digits=5, decimal_places=2, default=8.50)
    is_settled = models.BooleanField(default=False)
    won = models.BooleanField(default=False)
    payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    placed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Group {self.group_name}"

    def save(self, *args, **kwargs):
        was_settled = False
        if self.pk:
            try:
                old_bet = GroupStandingBet.objects.get(pk=self.pk)
                was_settled = old_bet.is_settled
            except GroupStandingBet.DoesNotExist:
                pass

        # اگر ادمین تیک برد را زد و شرط در حال تسویه بود
        if self.is_settled and not was_settled:
            if self.won:
                # محاسبه جایزه (مبلغ ضربدر ضریب ثابت 8.50)
                self.payout = float(self.amount) * float(self.odds)
                # واریز مستقیم به کیف پول
                self.user.profile.balance += self.payout
                self.user.profile.save()
            else:
                self.payout = 0

        super().save(*args, **kwargs)