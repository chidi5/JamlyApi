from random import randint
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.functional import cached_property
from ckeditor.fields import RichTextField


def randomWithN(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

#####USER#####
class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    id = models.BigIntegerField(primary_key=True, editable=False)
    username = None
    email = models.EmailField(unique=True)
    accepts_marketing = models.BooleanField(default=False)
    default_address = models.ForeignKey('CustomerAddress', on_delete=models.CASCADE, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_complete = models.BooleanField(default=False)
    token = models.CharField(max_length=50, blank=True, null=True)
    shops = models.ManyToManyField('Shop', related_name='customers', blank=True)
    is_active = models.BooleanField(default=True, help_text=('Designates whether the user is active.'))
    is_shop_owner = models.BooleanField(default=False, help_text=('Designates whether the user is a shop owner and can log into a shop admin site.'))


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.is_staff = True
        if not self.id: 
            self.id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return ' '.join(filter(None, [self.first_name, self.last_name]))

    def get_short_name(self):
        return self.first_name


class CustomerManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs.prefetch_related('customeraddress_set').select_related('default_address')
        return qs


class Customer(User):

    #objects = CustomerManager()
    customer_id = models.BigIntegerField(primary_key=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.customer_id:  
            self.customer_id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
    
    @cached_property
    def addresses(self):
        """
        Returns an array of all addresses associated with a customer. See
        customer_address for a full list of available attributes.
        """
        return list(self.customeraddress_set.all())

    @cached_property
    def addresses_count(self):
        """
        Returns the number of addresses associated with a customer.
        """
        return len(self.addresses)

    @cached_property
    def default_address(self):
        """
        Returns the default customer_address.
        """
        if self.addresses:
            return self.addresses[0]

    @cached_property
    def has_account(self):
        """
        Returns true if the email associated with an order is also tied to a
        customer account. Returns false if it is not. Helpful in email
        templates. In the theme, that will always be true.
        """
        return True

    @cached_property
    def last_order(self):
        """
        Returns the last order placed by the customer, not including test
        orders.
        """
        #if self.orders_count:
            #return self.orders[0]

    @cached_property
    def last_order_id(self):
        """
        The id of the customer's last order.
        """
        #if self.last_order:
            #return self.last_order.pk

    @cached_property
    def last_order_name(self):
        """
        The name of the customer's last order. This is directly related to the
        Order's name field.
        """
        #if self.last_order:
            #return self.last_order.name

    @cached_property
    def name(self):
        """
        Alias for get_full_name
        """
        return self.get_full_name()

    @cached_property
    def orders(self):
        """
        Returns an array of all orders placed by the customer.
        """
        #return list(self.order_set.all())

    @cached_property
    def orders_count(self):
        """
        Returns the total number of orders a customer has placed.
        """
        #return len(self.orders)

    @cached_property
    def total_spent(self):
        """
        Returns the total amount spent on all orders.
        """
        raise NotImplemented


class CustomerAddress(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, blank=True, null=True)
    street_address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    country = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)

    def save(self, *args, **kwargs):
        if not self.id:  
            self.id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state} {self.zip_code}"


#####SHOP#####
class Shop(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    description = RichTextField(max_length=255, blank=True, null=True)
    domain = models.CharField(max_length=200, unique=True, default=None, null=True, blank=True)
    myjamly_domain = models.CharField(max_length=200, unique=True, default=None, null=True)
    shop_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'shop'
        verbose_name_plural = 'shops'
        ordering = ('name',)

    def save(self, *args, **kwargs):
        if not self.id:  
            self.id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


#####PRODUCT, COLLECTION, AND ORDER#####
class Collection(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='collection', blank=True, null=True)
    handle = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    #products = models.ManyToManyField('Product', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        unique_together = ('shop', 'handle',)

    def save(self, *args, **kwargs):
        if not self.id:  
            self.id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class Product(models.Model):
    PRODUCT_STATUS = (
        ('PUBLISHED', 'Published'),
        ('DRAFT', 'Draft'),
    )
    id = models.BigIntegerField(primary_key=True, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = RichTextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    handle = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PRODUCT_STATUS, default='PUBLISHED')
    thumbnail = models.ImageField(upload_to='product_thumbnail', blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    length = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    collections = models.ManyToManyField(Collection, related_name='products', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('shop', 'handle',)

    def save(self, *args, **kwargs):
        if not self.id:  
            self.id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:  
            self.id = randomWithN(10)
        super().save(*args, **kwargs)


class ProductOption(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    product = models.ForeignKey(Product, related_name="options", on_delete=models.CASCADE)
    name = models.CharField(max_length=255, )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.id:  
            self.id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"product: {self.product.id} - {self.name}"
        

class OptionValue(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    option = models.ForeignKey(ProductOption, related_name="values", on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.id:  
            self.id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"
    

class ProductVariant(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    inventory = models.PositiveIntegerField(default=0)
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    values = models.ManyToManyField(OptionValue)

    def save(self, *args, **kwargs):
        if not self.id:  
            self.id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"poduct: {self.product.id}, {self.product} - {self.name}"
    

class Order(models.Model):
    ORDER_STATUS = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    id = models.BigIntegerField(primary_key=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(CustomerAddress, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='PENDING')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    fulfilled = models.BooleanField(default=False)
    products = models.ManyToManyField(Product, through='OrderItem')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:  
            self.id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.first_name}"
    
    def get_total_cost(self):
        return sum(item.get_total_price() for item in self.products.all())


class OrderItem(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.id:  
            self.id = randomWithN(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.variant}) for Order #{self.order.id}"
    
    def get_total_price(self):
        return self.quantity * self.variant.price