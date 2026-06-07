from django.contrib import admin
from .models import Game, BetOption, Bet, GroupStandingBet
from django import forms

class BetOptionInline(admin.TabularInline):
    model = BetOption
    extra = 0

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    # نمایش فیلدها در لیست
    list_display = ('home_team', 'away_team', 'start_time', 'home_score', 'away_score', 'is_finished')
    # قابلیت ویرایش سریع گل‌ها و پایان بازی مستقیماً از روی لیست!
    list_editable = ('home_score', 'away_score', 'is_finished')
    list_filter = ('is_finished', 'start_time')
    search_fields = ('home_team', 'away_team')
    inlines = [BetOptionInline]

@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ('user', 'bet_option', 'amount', 'is_settled', 'won', 'payout')
    list_filter = ('is_settled', 'won')
    search_fields = ('user__username',)

@admin.register(GroupStandingBet)
class GroupStandingBetAdmin(admin.ModelAdmin):
    list_display = ('user', 'group_name', 'predicted_first', 'predicted_second', 'amount', 'is_settled', 'won')
    list_editable = ('is_settled', 'won') # تسویه دستی شرط‌های گروهی در پایان مرحله گروهی
    list_filter = ('group_name', 'is_settled', 'won')

class GroupStandingBetForm(forms.ModelForm):
    class Meta:
        model = GroupStandingBet
        fields = ['predicted_first', 'predicted_second', 'amount']

    def __init__(self, *args, **kwargs):
        teams = kwargs.pop('teams', [])
        super().__init__(*args, **kwargs)
        team_choices = [(t, t) for t in teams]
        self.fields['predicted_first'] = forms.ChoiceField(choices=team_choices, label="رتبه اول صعود کننده")
        self.fields['predicted_second'] = forms.ChoiceField(choices=team_choices, label="رتبه دوم صعود کننده")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('predicted_first') == cleaned_data.get('predicted_second'):
            raise forms.ValidationError("تیم اول و دوم نمی‌توانند یکسان باشند!")
        return cleaned_data