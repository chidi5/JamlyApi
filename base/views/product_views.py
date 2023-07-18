from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from base.models import Product
from base.serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]  #isAuthenticate

    def get_queryset(self):
        return self.queryset.filter(shop__owner=2)
        #return self.queryset.filter(shop__owner=[self.request.user])

    def perform_create(self, serializer):
        #serializer.save(shop=2)
        serializer.save(shop=self.request.user.shop)

'''
class CollectionListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CollectionSerializer

    def get_queryset(self):
        shop_id = self.kwargs.get('shop_id')
        return Collection.objects.filter(shop_id=shop_id)

    def post(self, request, *args, **kwargs):
        shop_id = self.kwargs.get('shop_id') #shop=self.request.user.shop
        data = request.data.copy()
        data['shop'] = shop_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        collection = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
'''