from datetime import datetime, timedelta
import json

import os
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models.functions import  ExtractDay, ExtractMonth

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny,  IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser

from base.models import Customer, Order, OrderItem, Product, ProductImage, ProductOption, OptionValue, ProductVariant, Shop, Collection
from base.serializers import CollectionSerializer, CustomerSerializer, OrderSerializer, ProductOptionSerializer, ProductSerializer, ProductVariantSerializer, ShopSerializer

User = get_user_model()


##########Shop##########
class ShopListAPIView(generics.ListAPIView):
    serializer_class = ShopSerializer

    def get_queryset(self):
        shop_id = self.kwargs.get('shop_id')
        return Shop.objects.filter(id=shop_id)

class ShopRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ShopSerializer
    lookup_url_kwarg = 'shop_id'

    def get_queryset(self):
        shop_id = self.kwargs.get('shop_id')
        return Shop.objects.filter(id=shop_id)

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

##########Collection##########
class CollectionListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CollectionSerializer
    #parser_classes = [MultiPartParser, FormParser, FileUploadParser]

    def get_queryset(self):
        shop_id = self.kwargs.get('shop_id')
        return Collection.objects.filter(shop_id=shop_id)

    def post(self, request, *args, **kwargs):
        shop_id = self.kwargs.get('shop_id')
        data = request.data.copy()
        products_data = data.pop('products', [{}])  # Remove products data from the request data
        if isinstance(products_data, str):
            products_data = json.loads(products_data)
        # Convert string items to dictionaries
        products_data = [json.loads(p) if isinstance(p, str) else p for p in products_data]
        data['shop'] = shop_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        for product_data in products_data:
            for product_data_dict in product_data:
                name = product_data_dict.get('name')
                product = Product.objects.get(name=name)
                instance.products.add(product)  # Add related products to the instance
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CollectionRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CollectionSerializer
    #lookup_url_kwarg = 'id'

    def get_object(self):
        lookup = self.kwargs['lookup']
        try:
            object_id = int(lookup)
            return Collection.objects.get(id=object_id)
        except ValueError:
            return Collection.objects.get(handle=lookup)

    def get_queryset(self):
        shop_id = self.kwargs.get('shop_id')
        return Collection.objects.filter(shop_id=shop_id)

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        print(data)
        # Check if image field is present and not a file
        if 'image' in data and not isinstance(data['image'], (InMemoryUploadedFile, TemporaryUploadedFile)):
            # Replace URL with existing file object
            data['image'] = instance.image

        products_data = data.pop('products', [{}])  # Remove products data from the request data
        if isinstance(products_data, str):
            products_data = json.loads(products_data)
        # Convert string items to dictionaries
        products_data = [json.loads(p) if isinstance(p, str) else p for p in products_data]
        data['products'] = products_data

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        value = self.perform_update(serializer)
        value = serializer.save()
        for product_data in products_data:
            for product_data_dict in product_data:
                name = product_data_dict.get('name')
                product = Product.objects.get(name=name)
                value.products.add(product)  # Add related products to the instance
        return Response(serializer.data)

##########Product##########
class ProductListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        shop_id = self.kwargs.get('shop_id')
        return Product.objects.filter(shop_id=shop_id)

    def post(self, request, *args, **kwargs):
        shop_id = self.kwargs.get('shop_id')
        data = request.data.copy()
        data['shop'] = shop_id
        print(data)

        options_data = data.pop('options', [])
        if isinstance(options_data, str):
            options_data = json.loads(options_data)  # Parse options data as JSON
        # Convert string items to dictionaries
        options_data = [json.loads(p) if isinstance(p, str) else p for p in options_data]

        #variants
        variants_data = data.pop('variants', [])
        if isinstance(variants_data, str):
            variants_data = json.loads(variants_data)  # Parse variants data as JSON
        # Convert string items to dictionaries
        variants_data = [json.loads(p) if isinstance(p, str) else p for p in variants_data]

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        product = self.perform_create(serializer)
        
        self.create_options(product, options_data)
        self.create_variants(product, variants_data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save()

    def create_options(self, product, options_data):
        for option_data in options_data:
            values_data = option_data.pop('values', [])
            option = ProductOption.objects.create(product=product, **option_data)
            for value_data in values_data:
                OptionValue.objects.create(option=option, **value_data)

    def create_variants(self, product, variants_data):
        for variant_data in variants_data:
            values_data = variant_data.pop('values', [{}])
            print(product)
            variant = ProductVariant.objects.create(product=product, **variant_data)

            if isinstance(values_data, str):
                values_data = json.loads(values_data)  # Parse variants data as JSON
            # Convert string items to dictionaries
            values_data = [json.loads(p) if isinstance(p, str) else p for p in values_data]

            for value_data in values_data:
                print('1', type(value_data))
                print(value_data)
                name = value_data.get('name')
                print('name:', name)
                value = OptionValue.objects.get(option__product_id=product.id, name=name)
                variant.values.add(value)

class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    #lookup_url_kwarg = 'product_id'

    def get_object(self):
        lookup = self.kwargs['lookup']
        try:
            object_id = int(lookup)
            return Product.objects.get(id=object_id)
        except ValueError:
            return Product.objects.get(handle=lookup)

    def get_queryset(self):
        shop_id = self.kwargs.get('shop_id')
        return Product.objects.filter(shop_id=shop_id)

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()

        # Check if image field is present and not a file
        if 'thumbnail' in data and not isinstance(data['thumbnail'], (InMemoryUploadedFile, TemporaryUploadedFile)):
            # Replace URL with existing file object
            data['thumbnail'] = instance.thumbnail

        # Handle uploaded_images
        uploaded_images = data.pop('uploaded_images', None)
        updated_uploaded_images = []
        existing_images = instance.images.all()
        if uploaded_images is not None:
            for uploaded_image in uploaded_images:
                print(uploaded_image)
                if isinstance(uploaded_image, str):
                    # Extract file name from the URL
                    file_name = os.path.basename(uploaded_image)
                    # Replace URL with existing file object
                    existing_image = existing_images.filter(image__contains=file_name).first()
                    if existing_image:
                        updated_uploaded_images.append(existing_image.image)
                else:
                    updated_uploaded_images.append(uploaded_image)

            for i in range(0, len(updated_uploaded_images)):
                data['uploaded_images'+str([i])] = updated_uploaded_images[i]
        
        print(data)

        # Update handling of options
        options_data = data.pop('options', [])
        if isinstance(options_data, str):
            options_data = json.loads(options_data)  # Parse options data as JSON
        # Convert string items to dictionaries
        options_data = [json.loads(p) if isinstance(p, str) else p for p in options_data]

        # Update handling of variants
        variants_data = data.pop('variants', [])
        if isinstance(variants_data, str):
            variants_data = json.loads(variants_data)  # Parse variants data as JSON
        # Convert string items to dictionaries
        variants_data = [json.loads(p) if isinstance(p, str) else p for p in variants_data]
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            product = serializer.save()
            self.update_options(product, options_data)
            self.update_variants(product, variants_data)
            return Response(serializer.data)
        except ValidationError as e:
            print(e)
        print("weeee", serializer.errors)
        return Response(serializer.errors)

    def update_options(self, product, options_data):
        for option_data in options_data:
            values_data = option_data.pop('values', [])
            option = ProductOption.objects.create(product=product, **option_data)
            for value_data in values_data:
                OptionValue.objects.create(option=option, **value_data)

    def update_variants(self, product, variants_data):
        print(variants_data)
        for variant_data in variants_data:
            print(variant_data)
            values_data = variant_data.pop('values', [{}])
            product_id = variant_data.pop('product', None)
            print('wee', variant_data)
            variant = ProductVariant.objects.create(product=product, **variant_data)

            if isinstance(values_data, str):
                values_data = json.loads(values_data)  # Parse variants data as JSON
            # Convert string items to dictionaries
            values_data = [json.loads(p) if isinstance(p, str) else p for p in values_data]

            for value_data in values_data:
                name = value_data.get('name')
                value = OptionValue.objects.get(option__product_id=product.id, name=name)
                variant.values.add(value)

class OptionList(generics.ListCreateAPIView):
    queryset = ProductOption.objects.all()
    serializer_class = ProductOptionSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        options_data = data.get('options', [])
        serializer = self.get_serializer(data=options_data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

class OptionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductOption.objects.all()
    serializer_class = ProductOptionSerializer

class VariantList(generics.ListCreateAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer

class VariantDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer

class PlaceOrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        customer_id = self.kwargs.get('customer_id')
        return Order.objects.filter(customer_id=customer_id)

    def post(self, request, *args, **kwargs):
        customer_id = self.kwargs.get('customer_id')
        data = request.data.copy()
        data['customer'] = customer_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CustomerList(generics.ListAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        shop_id = self.kwargs.get('shop_id')
        return Customer.objects.filter(shops=shop_id)

############ADMIN###########
@permission_classes(['IsAuthenticated'])
@api_view(['GET'])
def getShopData(request, user_id):
    data=request.data

    user = User.objects.get(id=user_id)
    shop = Shop.objects.get(owner=user)
    shop_serializer = ShopSerializer(shop, many=False)

    products = Product.objects.filter(shop=shop)
    product_serializer = ProductSerializer(products, many=True)
    
    orders = Order.objects.filter(shop=shop).order_by('-created_at')
    order_serializer = OrderSerializer(orders, many=True)

    new_orders = orders.filter(created_at=user.last_login).order_by('-created_at')
    new_order_serializer = OrderSerializer(new_orders, many=True)

    open_orders = orders.filter(fulfilled = False).order_by('-created_at')
    open_order_serializer = OrderSerializer(open_orders, many=True)

    #All time sales
    all_sales = orders.aggregate(Sum('total_price'))

    #Sales for the week day 
    today_orders = orders.filter(created_at__gte=timezone.now().replace(hour=0, minute=0, second=0), created_at__lte=timezone.now().replace(hour=23, minute=59, second=59))
    total_daily_sales = today_orders.aggregate(Sum('total_price'))

    top_order = OrderItem.objects.filter(product__shop=shop, created_at__gte = datetime.now()-timedelta(days=7))
    best_sellers = top_order.values('product').annotate(num_buys=Sum('quantity')).order_by('-num_buys')

    
    best_sellers_list = []

    for x in best_sellers:
        product = Product.objects.get(id = x['product'])
        serializer = ProductSerializer(product)
        best_sellers_list.append(serializer.data)

    #daily sales for the current month 

    '''first_present_month = datetime.today().replace(day=1, hour=0, minute=0, second=0)
    first_next_month = first_present_month + relativedelta.relativedelta(months=1)

    extracted_month_sales = orders.filter(
        created_at__range = [first_present_month, first_next_month]).annotate(
        created_at_day = ExtractDay('created_at')
        ).values('created_at_day').order_by('created_at_day').annotate(total_sales = Sum('get_total_cost'))

    thirty_day_sales = OrderAnalyticsSerializer(extracted_month_sales, many=True).data

    last_30_day_sales = [0 for x in range(31)]
    
    for x in thirty_day_sales:
        index = int(x['created_at_day']) - 1
        last_30_day_sales[index] = x['total_sales']'''

    #Number of customers in the store
    customers = shop.customers.all()
    num_customers = len(customers)


    #update_last_login(None, user)

    return Response({
            'shop': shop_serializer.data,
            'products' : product_serializer.data,
            'all_sales': all_sales,
            'daily_sales': total_daily_sales,
            'orders' : order_serializer.data,
            'new_orders': new_order_serializer.data,
            'open_orders': open_order_serializer.data,
            'top_orders': best_sellers_list,
            #'thirty_day_sales': last_30_day_sales,
            'num_customers': num_customers,
        })


####### StoreFront #######
@api_view(['GET'])
def storefront(request, domain_name):
    shop = get_object_or_404(Shop, myjamly_domain=domain_name)

    shop_serializer = ShopSerializer(shop)

    products = Product.objects.filter(shop=shop)[:8]
    product_serializer = ProductSerializer(products, many=True, context={'request':request})

    collections = Collection.objects.filter(shop=shop)
    collection_serializer = CollectionSerializer(collections, many=True, context={'request':request})

    data = {
        'shop': shop_serializer.data,
        'products': product_serializer.data,
        'collections': collection_serializer.data,
    }

    return Response(data)