from django.urls import path
from .views import UserRegistrationView,Usergetrole
urlpatterns=[
    path('register/',UserRegistrationView.as_view(),name='user_registration'),
    path('userowner/',Usergetrole.as_view(),name='user_getrole'),
]