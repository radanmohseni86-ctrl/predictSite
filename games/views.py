from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Game, BetOption, Bet, Profile
from .forms import RegistrationForm, BetForm
from .forms import DepositForm, WithdrawForm


def get_or_create_profile(user):
    profile, created = Profile.objects.get_or_create(user=user)
    if created:
        profile.balance = 1000.00
        profile.save()
    return profile

def home_view(request):
    upcoming_games = Game.objects.filter(status='upcoming', start_time__gt=timezone.now()).order_by('start_time')[:6]
    return render(request, 'games/home.html', {'upcoming_games': upcoming_games})

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            get_or_create_profile(user)
            login(request, user)
            messages.success(request, "Registration successful. Welcome!")
            return redirect('games:home')
    else:
        form = RegistrationForm()
    return render(request, 'games/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            get_or_create_profile(user)
            return redirect('games:home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'games/login.html')

def logout_view(request):
    logout(request)
    return redirect('games:home')

@login_required
def game_list_view(request):
    games = Game.objects.filter(status='upcoming', start_time__gt=timezone.now()).order_by('start_time')
    return render(request, 'games/game_list.html', {'games': games})

@login_required
def place_bet_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if game.status != 'upcoming' or game.start_time <= timezone.now():
        messages.error(request, "This game is not available for betting.")
        return redirect('games:game_list')

    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        form = BetForm(request.POST, game=game)
        if form.is_valid():
            bet_option = form.cleaned_data['bet_option']
            amount = form.cleaned_data['amount']

            if amount > profile.balance:
                messages.error(request, "Insufficient balance!")
            else:
                with transaction.atomic():
                    profile.balance -= amount
                    profile.save()
                    Bet.objects.create(
                        user=request.user,
                        bet_option=bet_option,
                        amount=amount
                    )
                messages.success(request, f"Bet of {amount} on '{bet_option.description}' placed.")
                return redirect('games:user_panel')
    else:
        form = BetForm(game=game)

    return render(request, 'games/place_bet.html', {'game': game, 'form': form, 'balance': profile.balance})

@login_required
def user_panel_view(request):
    profile = get_or_create_profile(request.user)
    bets = request.user.bets.all().order_by('-placed_at')
    return render(request, 'games/user_panel.html', {'bets': bets, 'balance': profile.balance})

@login_required
def deposit_view(request):
    profile = get_or_create_profile(request.user)
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            with transaction.atomic():
                profile.balance += amount
                profile.save()
            messages.success(request, f"Successfully added {amount} Toman to your balance.")
            return redirect('games:user_panel')
    else:
        form = DepositForm()
    return render(request, 'games/deposit.html', {'form': form, 'balance': profile.balance})

@login_required
def withdraw_view(request):
    profile = get_or_create_profile(request.user)
    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if amount > profile.balance:
                messages.error(request, "Insufficient balance for withdrawal.")
            else:
                with transaction.atomic():
                    profile.balance -= amount
                    profile.save()
                messages.success(request, f"Successfully withdrawn {amount} Toman from your balance.")
            return redirect('games:user_panel')
    else:
        form = WithdrawForm()
    return render(request, 'games/withdraw.html', {'form': form, 'balance': profile.balance})