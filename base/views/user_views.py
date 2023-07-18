from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from base.serializers import CustomerSignUpSerializer, MyTokenObtainPairSerializer, ShopOwnerSignUpSerializer


class MyObtainTokenPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = MyTokenObtainPairSerializer

class ShopOwnerSignUpView(generics.CreateAPIView):
    serializer_class = ShopOwnerSignUpSerializer
    permission_classes = [AllowAny]

class CustomerSignUpView(generics.CreateAPIView):
    serializer_class = CustomerSignUpSerializer
    permission_classes = [AllowAny]