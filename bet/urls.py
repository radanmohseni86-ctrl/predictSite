# bet/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')), # <--- مسیر تغییر زبان
    path('admin/', admin.site.urls),
    path('', include('games.urls')),
]