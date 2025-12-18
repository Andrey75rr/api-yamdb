from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CommentViewSet,
    ReviewViewSet,
    SignUpView,
    TokenView,
    UserViewSet,
)

main_router = DefaultRouter()
main_router.register('users', UserViewSet, basename='users')
reviews_router = DefaultRouter()
reviews_router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='title-reviews'
)

comments_router = DefaultRouter()
comments_router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='review-comments'
)

urlpatterns = [
    path('v1/auth/signup/', SignUpView.as_view()),
    path('v1/auth/token/', TokenView.as_view()),
    path('v1/', include(main_router.urls)),
    path('v1/', include(reviews_router.urls)),
    path('v1/', include(comments_router.urls)),
]
