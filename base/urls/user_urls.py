from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from base.views.user_views import CustomerSignUpView, MyObtainTokenPairView, ShopOwnerSignUpView


urlpatterns = [
    path('user/login/', MyObtainTokenPairView.as_view(), name='user_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('sign-up/shop-owner/', ShopOwnerSignUpView.as_view(), name='shop-owner-sign-up'),
    path('sign-up/customer/', CustomerSignUpView.as_view(), name='customer-sign-up'),
]