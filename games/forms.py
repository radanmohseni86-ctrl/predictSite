# bet/games/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Bet, BetOption, GroupStandingBet


# 1. فرم ثبت‌نام کاربران
class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_("Email"))

    class Meta:
        model = User
        fields = ['username', 'email']


# 2. فرم پیش‌بینی یک مسابقه خاص
class BetForm(forms.Form):
    bet_option = forms.ModelChoiceField(
        queryset=BetOption.objects.none(),
        widget=forms.RadioSelect,
        label=_("Select your bet")
    )
    amount = forms.DecimalField(min_value=0.01, max_digits=10, decimal_places=2, label=_("Amount (Coins)"))

    def __init__(self, *args, **kwargs):
        game = kwargs.pop('game', None)
        super().__init__(*args, **kwargs)
        if game:
            self.fields['bet_option'].queryset = BetOption.objects.filter(game=game, is_active=True)
            self.fields['bet_option'].empty_label = None

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError(_("Coin amount must be greater than zero."))
        return amount


# 3. فرم پیش‌بینی رتبه اول و دوم گروه‌ها
class GroupStandingBetForm(forms.ModelForm):
    class Meta:
        model = GroupStandingBet
        fields = ['predicted_first', 'predicted_second', 'amount']

    def __init__(self, *args, **kwargs):
        teams = kwargs.pop('teams', [])
        super().__init__(*args, **kwargs)
        # ترجمه نام تیم‌ها داخل منوی کشویی
        team_choices = [(t, _(t)) for t in teams]
        self.fields['predicted_first'] = forms.ChoiceField(choices=team_choices, label=_("1st Place Team"))
        self.fields['predicted_second'] = forms.ChoiceField(choices=team_choices, label=_("2nd Place Team"))
        self.fields['amount'].label = _("Amount (Coins)")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('predicted_first') == cleaned_data.get('predicted_second'):
            raise forms.ValidationError(_("The first and second teams cannot be the same!"))
        return cleaned_data