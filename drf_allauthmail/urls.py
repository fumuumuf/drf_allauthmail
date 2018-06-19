from django.urls import path

from . import views

urlpatterns = [
    path('', views.email_list_view),
    path('<int:pk>/set_primary/', views.email_set_primary),
    path('<int:pk>/sent_confirmation/', views.email_sent_confirmation),
    path('<int:pk>/', views.email_detail_view),
]
