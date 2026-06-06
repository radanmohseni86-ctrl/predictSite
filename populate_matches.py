# populate_matches.py
import os
import django
from datetime import datetime, timedelta

# تنظیم محیط جنگو برای دسترسی به دیتابیس
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bet.settings')
django.setup()

from django.utils.timezone import make_aware
from games.models import Game, BetOption

# قدرت واقعی تیم‌ها (از 1 تا 100) برای محاسبه منطقی ضرایب شرط‌بندی
TEAM_POWER = {
    "Argentina": 95, "France": 95, "Brazil": 92, "England": 90, "Spain": 90,
    "Germany": 88, "Portugal": 88, "Belgium": 85, "Netherlands": 85,
    "Uruguay": 83, "Croatia": 82, "Colombia": 82, "Morocco": 80,
    "Senegal": 78, "Japan": 78, "United States": 78, "Switzerland": 78,
    "Mexico": 76, "Austria": 76, "Türkiye": 75, "Sweden": 75, "Ecuador": 75,
    "Iran": 74, "South Korea": 73, "Algeria": 72, "Norway": 72,
    "Egypt": 70, "Australia": 70, "Czech Republic": 70, "Ivory Coast": 70,
    "Saudi Arabia": 68, "Scotland": 68, "Canada": 68, "Tunisia": 68,
    "Bosnia and Herzegovina": 68, "Paraguay": 68, "Ghana": 68,
    "Panama": 65, "Uzbekistan": 65, "Iraq": 65, "South Africa": 65,
    "Qatar": 62, "Jordan": 62, "DR Congo": 62, "Cabo Verde": 60, "New Zealand": 60,
    "Haiti": 55, "Curaçao": 55
}


def calculate_realistic_odds(home_team, away_team):
    home_power = TEAM_POWER.get(home_team, 70)
    away_power = TEAM_POWER.get(away_team, 70)

    # محاسبه اختلاف قدرت دو تیم
    diff = home_power - away_power

    # توزیع شانس برد بر اساس فرمول ریاضی (شانس پایه 38٪ برای هر تیم)
    prob_home = 0.38 + (diff * 0.015)
    prob_away = 0.38 - (diff * 0.015)

    # محدود کردن شانس‌ها بین 10 تا 75 درصد
    prob_home = max(0.10, min(0.75, prob_home))
    prob_away = max(0.10, min(0.75, prob_away))
    prob_draw = 1.0 - prob_home - prob_away

    # تبدیل شانس به ضریب پرداختی (همراه با حاشیه سود سایت 95٪)
    margin = 0.95
    odds_home = round((1 / prob_home) * margin, 2)
    odds_away = round((1 / prob_away) * margin, 2)
    odds_draw = round((1 / prob_draw) * margin, 2)

    return odds_home, odds_draw, odds_away


def populate_real_world_cup_matches():
    Game.objects.all().delete()
    print("Deleted old games. Generating OFFICIAL FIFA World Cup 2026 Schedule with realistic odds and Tehran Time...")

    real_groups = {
        'A': ["Mexico", "South Africa", "South Korea", "Czech Republic"],
        'B': ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
        'C': ["Brazil", "Morocco", "Haiti", "Scotland"],
        'D': ["United States", "Paraguay", "Australia", "Türkiye"],
        'E': ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
        'F': ["Netherlands", "Japan", "Sweden", "Tunisia"],
        'G': ["Belgium", "Egypt", "Iran", "New Zealand"],
        'H': ["Spain", "Cabo Verde", "Saudi Arabia", "Uruguay"],
        'I': ["France", "Senegal", "Iraq", "Norway"],
        'J': ["Argentina", "Algeria", "Austria", "Jordan"],
        'K': ["Portugal", "DR Congo", "Colombia", "Uzbekistan"],
        'L': ["England", "Croatia", "Ghana", "Panama"],
    }

    # ساعت‌های بازی به وقت ایران (17:30، 21:30، و 01:30 بامداد فردا)
    tehran_match_hours = [(17, 30), (21, 30), (1, 30)]
    match_counter = 0

    for group_name, teams in real_groups.items():
        matchups = [
            (teams[0], teams[1], 0),
            (teams[2], teams[3], 0),
            (teams[0], teams[2], 7),
            (teams[1], teams[3], 7),
            (teams[0], teams[3], 12),
            (teams[1], teams[2], 12)
        ]

        for idx, (home, away, day_offset) in enumerate(matchups):
            # انتخاب یکی از سه تایم استاندارد پخش زنده برای هر بازی
            hour, minute = tehran_match_hours[match_counter % 3]

            # تنظیم روز بازی (اگر ساعت 1:30 بامداد بود، بازی در واقع روز بعد برگزار می‌شود)
            extra_day = 1 if hour == 1 else 0

            # ساخت آبجکت زمان با در نظر گرفتن منطقه زمانی تنظیم شده در Settings (تهران)
            naive_dt = datetime(2026, 6, 11 + day_offset + extra_day, hour, minute)
            match_time = make_aware(naive_dt)

            game = Game.objects.create(
                home_team=home,
                away_team=away,
                start_time=match_time,
                status='upcoming'
            )

            # دریافت ضرایب منطقی از تابع هوش مصنوعی
            odds_home, odds_draw, odds_away = calculate_realistic_odds(home, away)

            BetOption.objects.create(game=game, description=f"{home} Win", odds=odds_home)
            BetOption.objects.create(game=game, description="Draw", odds=odds_draw)
            BetOption.objects.create(game=game, description=f"{away} Win", odds=odds_away)

            match_counter += 1

    print(f"✅ SUCCESS: {match_counter} Matches generated with REALISTIC odds in TEHRAN Local Time!")


if __name__ == '__main__':
    populate_real_world_cup_matches()