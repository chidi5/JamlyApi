from django.core.files.uploadedfile import InMemoryUploadedFile
from urllib.request import urlopen
from django.core.files import File
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import Customer, OptionValue, Order, OrderItem, Product, Collection, ProductImage, ProductOption, ProductVariant, Shop
from django.core.files.base import ContentFile

User = get_user_model()


class ShopSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'myjamly_domain']
        read_only_fields = ['id']

class UserSerializer(serializers.ModelSerializer):
    shop = ShopSignUpSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'is_shop_owner', 'shop']

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['customer_id', 'email', 'first_name', 'last_name', 'is_shop_owner', 'addresses', 'accepts_marketing']

class UserSerializerWithToken(serializers.ModelSerializer):
    token = serializers.SerializerMethodField(read_only=True)
    shop = ShopSignUpSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'is_shop_owner', 'shop', 'token']

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        serializer = UserSerializerWithToken(self.user).data
        for k, v in serializer.items():
            data[k] = v

        return data

class ShopOwnerSignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=128, write_only=True)
    shop = ShopSignUpSerializer(required=True)
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'is_shop_owner', 'shop', 'token']
        read_only_fields = ['id']
        extra_kwargs = {
            'is_shop_owner': {'required': True},
            'email': {'required': True},
        }
    
    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)

    def create(self, validated_data):
        shop_data = validated_data.pop('shop')
        user = User.objects.create(
            email=validated_data['email'],
            is_shop_owner=True,
            is_staff = True,
        )
        user.set_password(validated_data['password'])
        Shop.objects.create(
            name = shop_data['name'],
            myjamly_domain = shop_data['myjamly_domain'],
            owner = user
        )
        #user.shops.add(shop)
        user.save()
        return user

class CustomerSignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=128, write_only=True)
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Customer
        fields = ['customer_id', 'email', 'password', 'is_shop_owner', 'shop', 'token', 'addresses', 'name']
        #read_only_fields = ['id']
        read_only_fields = ('customer_id', 'status', 'created_at', 'fulfilled', 'addresses', 'name')
        extra_kwargs = {
            'is_shop_owner': {'required': False, 'read_only':True},
            'email': {'required': True},
        }
    
    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)

    def create(self, validated_data):
        shop = validated_data['shop']
        user = Customer.objects.create(
            email=validated_data['email'],
            is_shop_owner=False,
            shop=shop,
        )
        user.set_password(validated_data['password'])
        user.shops.add(shop)
        user.save()
        return user

class ShopSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    class Meta:
        model = Shop
        fields = '__all__'
        extra_kwargs = {
            'owner': {'required': True},
        }

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.email = validated_data.get('email', instance.email)
        instance.domain = validated_data.get('domain', instance.domain)
        instance.owner = validated_data.get('owner', instance.owner)
        instance.address = validated_data.get('address', instance.address)
        instance.city = validated_data.get('city', instance.city)
        instance.state = validated_data.get('state', instance.state)
        instance.zip_code = validated_data.get('zip_code', instance.zip_code)
        instance.country = validated_data.get('country', instance.country)
        instance.save()
        return instance

class OptionValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionValue
        fields = ('name',)

class ProductOptionSerializer(serializers.ModelSerializer):
    values = OptionValueSerializer(many=True)

    class Meta:
        model = ProductOption
        fields = ('id', 'name', 'product', 'values')
        extra_kwargs = {
            'product': {'required': False},
        }

    def create(self, validated_data):
        values_data = validated_data.pop('values')
        option = ProductOption.objects.create(**validated_data)
        for value_data in values_data:
            OptionValue.objects.create(option=option, **value_data)
        return option

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        values_data = validated_data.get('values', [])
        value_ids = [value['id'] for value in values_data if 'id' in value]
        for value in instance.values.all():
            if value.id not in value_ids:
                value.delete()
        for value_data in values_data:
            if 'id' in value_data:
                value = OptionValue.objects.get(pk=value_data['id'])
                value.name = value_data.get('name', value.name)
                value.save()
            else:
                OptionValue.objects.create(option=instance, **value_data)
        return instance

class ProductVariantSerializer(serializers.ModelSerializer):
    values = OptionValueSerializer(many=True)

    class Meta:
        model = ProductVariant
        fields = ('id', 'name', 'product', 'sku', 'price', 'inventory', 'values')

    def create(self, validated_data):
        values_data = validated_data.pop('values')
        variant = ProductVariant.objects.create(**validated_data)
        for value_data in values_data:
            value = OptionValue.objects.get(name=value_data['name'])
            variant.values.add(value)
        return variant

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.sku = validated_data.get('sku', instance.sku)
        instance.price = validated_data.get('price', instance.price)
        instance.inventory = validated_data.get('inventory', instance.inventory)
        instance.save()
        values_data = validated_data.get('values', [])
        value_ids = [value['id'] for value in values_data if 'id' in value]
        instance.values.clear()
        for value_data in values_data:
            if 'name' in value_data:
                value = OptionValue.objects.get(name=value_data['name'])
                instance.values.add(value)
        return instance

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    collections = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all(), many=True, required=False)
    options = ProductOptionSerializer(many=True, required=False)
    variants = ProductVariantSerializer(many=True, required=False)
    images = ProductImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child = serializers.ImageField(max_length=1000000, allow_empty_file=False),
        write_only = True,
        required=False,
        default=[]
    )

    class Meta:
        model = Product
        fields = ['id', 'shop', 'name', 'handle', 'description', 'price', 'status', 'thumbnail', 'weight', 'length', 'height', 'width', 'collections', 'options', 'variants', 'images', 'uploaded_images',]

    def create(self, validated_data):
        images_data = validated_data.pop('uploaded_images', [])
        collections_data = validated_data.pop('collections', None)
        options_data = validated_data.pop('options', [])
        variants_data = validated_data.pop('variants', [])
        product = Product.objects.create(**validated_data)
        
        for image_data in images_data:
            #image = ContentFile(image_data.read())
            ProductImage.objects.create(product=product, image=image_data)
        
        for collection_data in collections_data:
            product.collections.add(collection_data)
        
        for option_data in options_data:
            values_data = option_data.pop('values', [])
            option = ProductOption.objects.create(product=product, **option_data)
            for value_data in values_data:
                OptionValue.objects.create(option=option, **value_data)

        for variant_data in variants_data:
            values_data = validated_data.pop('values', [])
            variant = ProductVariant.objects.create(product=product, **validated_data)
            for value_data in values_data:
                value = OptionValue.objects.get(name=value_data['name'])
                variant.values.add(value)
        
        
        return product
    
    def update(self, instance, validated_data):
        collections_data = validated_data.pop('collections')
        images_data = validated_data.pop('uploaded_images')
        options_data = validated_data.pop('options', [])
        variants_data = validated_data.pop('variants', [])

        instance.name = validated_data.get('name', instance.name)
        instance.price = validated_data.get('price', instance.price)
        instance.description = validated_data.get('description', instance.description)
        instance.handle = validated_data.get('handle', instance.handle)
        instance.status = validated_data.get('status', instance.status)
        instance.thumbnail = validated_data.get('thumbnail', instance.thumbnail)
        instance.weight = validated_data.get('weight', instance.weight)
        instance.length = validated_data.get('length', instance.length)
        instance.height = validated_data.get('height', instance.height)
        instance.width = validated_data.get('width', instance.width)
        instance.save()

        instance.collections.clear()
        for collection_data in collections_data:
            instance.collections.add(collection_data)

        instance.images.all().delete()
        for image_data in images_data:
            ProductImage.objects.create(product=instance, image=image_data)

        instance.options.all().delete()
        for option_data in options_data:
            values_data = option_data.pop('values', [])
            option = ProductOption.objects.create(product=instance, **option_data)
            for value_data in values_data:
                OptionValue.objects.create(option=option, **value_data)

        instance.variants.all().delete()
        for variant_data in variants_data:
            values_data = validated_data.pop('values', [])
            variant = ProductVariant.objects.create(product=instance, **validated_data)
            for value_data in values_data:
                value = OptionValue.objects.get(name=value_data['name'])
                variant.values.add(value)        

        return instance

'''
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'value', 'price', 'created_at']

class ProductOptionSerializer(serializers.ModelSerializer):
    variations = ProductVariationSerializer(many=True, required=False)

    class Meta:
        model = ProductOption
        fields = ['id', 'product', 'name', 'created_at', 'variations']

    def create(self, validated_data):
        variations_data = validated_data.pop('variations', [])
        option = ProductOption.objects.create(**validated_data)

        for variation_data in variations_data:
            ProductVariation.objects.create(option=option, **variation_data)

        return option

    def update(self, instance, validated_data):
        variations_data = validated_data.pop('variations', [])
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        existing_variations = {v.id: v for v in instance.variations.all()}

        for variation_data in variations_data:
            variation_id = variation_data.get('id', None)

            if variation_id in existing_variations:
                existing_variation = existing_variations.pop(variation_id)
                variation_serializer = ProductVariationSerializer(
                    existing_variation, data=variation_data)
                if variation_serializer.is_valid():
                    variation_serializer.save()
            else:
                ProductVariation.objects.create(option=instance, **variation_data)

        for variation in existing_variations.values():
            variation.delete()

        return instance
'''
class SimpleProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, required=False)
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id', 'name', 'handle', 'price', 'thumbnail', 'images', 'variants']
        read_only_fields = ['id', 'thumbnail']

class CollectionSerializer(serializers.ModelSerializer):
    products = SimpleProductSerializer(many=True, required=False)
    image = serializers.ImageField(required=False)

    class Meta:
        model = Collection
        fields = '__all__'

    def create(self, validated_data):
        products_data = validated_data.pop('products', [])
        collection = Collection.objects.create(**validated_data)
        for product_data in products_data:
            product = Product.objects.get(name=product_data['name'])
            collection.products.add(product)
        return collection

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', [])
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.image = validated_data.get('image', instance.image)
        instance.handle = validated_data.get('handle', instance.handle)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        instance.products.clear()
        print(products_data)
        for product_data in products_data:
            #print(product_data)
            product = Product.objects.get(name=product_data['name'])
            instance.products.add(product)
        return instance
    
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('product', 'variant', 'quantity', 'price')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ('id', 'customer', 'status', 'created_at', 'fulfilled', 'items', 'get_total_cost')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order