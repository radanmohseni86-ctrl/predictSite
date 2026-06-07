# bet/games/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _  # 🔴 اضافه شدن تابع ترجمه
from .models import Game, BetOption, Bet, GroupStandingBet, Profile
from .forms import RegistrationForm, BetForm, GroupStandingBetForm


def home_view(request):
    upcoming_games = Game.objects.filter(status='upcoming', start_time__gt=timezone.now()).order_by('start_time')
    return render(request, 'games/home.html', {'upcoming_games': upcoming_games})


def game_list_view(request):
    games = Game.objects.filter(status='upcoming', start_time__gt=timezone.now()).order_by('start_time')
    return render(request, 'games/game_list.html', {'games': games})


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _("Registration successful!"))
            return redirect('games:home')
    else:
        form = RegistrationForm()
    return render(request, 'games/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, _("Welcome %(username)s!") % {'username': user.username})
            return redirect('games:home')
    else:
        form = AuthenticationForm()
    return render(request, 'games/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, _("Logged out successfully."))
    return redirect('games:home')


@login_required
def user_panel_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    bets = Bet.objects.filter(user=request.user).order_by('-placed_at')
    group_bets = GroupStandingBet.objects.filter(user=request.user).order_by('-placed_at')

    return render(request, 'games/user_panel.html', {
        'bets': bets,
        'group_bets': group_bets,
        'balance': profile.balance
    })


@login_required
def place_bet_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = BetForm(request.POST, game=game)
        if form.is_valid():
            bet_option = form.cleaned_data['bet_option']
            amount = form.cleaned_data['amount']

            if profile.balance >= amount:
                profile.balance -= amount
                profile.save()
                Bet.objects.create(user=request.user, bet_option=bet_option, amount=amount)
                messages.success(request, _("Your prediction was placed successfully!"))
                return redirect('games:user_panel')
            else:
                messages.error(request, _("Not enough coins!"))
    else:
        form = BetForm(game=game)

    return render(request, 'games/place_bet.html', {'game': game, 'form': form, 'balance': profile.balance})


@login_required
def place_group_bet_view(request, group_letter):
    group_letter = group_letter.upper()
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

    teams = real_groups.get(group_letter)
    if not teams:
        return redirect('games:home')

    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = GroupStandingBetForm(request.POST, teams=teams)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if profile.balance >= amount:
                profile.balance -= amount
                profile.save()

                bet = form.save(commit=False)
                bet.user = request.user
                bet.group_name = group_letter
                bet.save()

                messages.success(request, _("Prediction for Group %(group_letter)s placed successfully.") % {
                    'group_letter': group_letter})
                return redirect('games:user_panel')
            else:
                messages.error(request, _("Not enough coins!"))
    else:
        form = GroupStandingBetForm(teams=teams)

    return render(request, 'games/group_bet.html', {
        'form': form, 'group_letter': group_letter, 'balance': profile.balance
    })