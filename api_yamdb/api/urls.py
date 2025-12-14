from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SignUpView, TokenView, UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/signup/', SignUpView.as_view()),
    path('auth/token/', TokenView.as_view()),
    path('', include(router.urls)),
]
