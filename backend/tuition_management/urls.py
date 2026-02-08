from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/me", views.CurrentUserView.as_view(), name="current_user"),
    path("api/", include("core.urls")),
]
