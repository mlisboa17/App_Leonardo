"""
URLs da aplicação do dashboard
"""
from django.urls import path
from . import views

app_name = 'bot_dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/status/', views.get_bot_status, name='get_bot_status'),
    path('api/config/', views.get_config, name='get_config'),
    path('api/config/update/', views.update_config, name='update_config'),
    path('api/price-history/', views.get_price_history, name='get_price_history'),
]