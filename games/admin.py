from django.contrib import admin
from .models import Profile, Game, BetOption, Bet

class BetOptionInline(admin.TabularInline):
    """نمایش گزینه‌های شرط درون صفحه ویرایش بازی"""
    model = BetOption
    extra = 3  # تعداد ردیف خالی برای اضافه کردن گزینه جدید
    fields = ['description', 'odds', 'is_active', 'is_winner']
    # توضیح: is_winner فقط برای بازی‌های تمام شده باید علامت بخورد

class GameAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'away_team', 'start_time', 'status', 'result_description']
    list_filter = ['status', 'start_time']
    search_fields = ['home_team', 'away_team']
    inlines = [BetOptionInline]
    # هیچ اکشن اضافی برای تسویه نیاز نیست، سیگنال بعد از ذخیره خودکار انجام می‌دهد

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance']
    search_fields = ['user__username']

class BetAdmin(admin.ModelAdmin):
    list_display = ['user', 'bet_option', 'amount', 'placed_at', 'is_settled', 'won', 'payout']
    list_filter = ['is_settled', 'won', 'bet_option__game']
    search_fields = ['user__username', 'bet_option__description']
    readonly_fields = ['placed_at']  # زمان ثبت شرط قابل ویرایش نباشد

# ثبت مدل‌ها در پنل ادمین
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Bet, BetAdmin)