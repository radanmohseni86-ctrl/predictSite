# bet/games/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Bet, BetOption

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email'] # 🔴 فیلدهای password نباید اینجا باشن، خود UserCreationForm اونا رو مدیریت میکنه

class BetForm(forms.Form):
    bet_option = forms.ModelChoiceField(
        queryset=BetOption.objects.none(),
        widget=forms.RadioSelect,
        label="Select your bet"
    )
    amount = forms.DecimalField(min_value=0.01, max_digits=10, decimal_places=2, label="Amount (Coins)")

    def __init__(self, *args, **kwargs):
        game = kwargs.pop('game', None)
        super().__init__(*args, **kwargs)
        if game:
            self.fields['bet_option'].queryset = BetOption.objects.filter(game=game, is_active=True)
            self.fields['bet_option'].empty_label = None

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("مقدار سکه باید بیشتر از صفر باشد.")
        return amount

# فرم‌های DepositForm و WithdrawForm کاملا حذف شدند.