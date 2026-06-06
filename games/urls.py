# bet/games/urls.py
from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('games/', views.game_list_view, name='game_list'),
    path('bet/<int:game_id>/', views.place_bet_view, name='place_bet'),
    path('panel/', views.user_panel_view, name='user_panel'),
]