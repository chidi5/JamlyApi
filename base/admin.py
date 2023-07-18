from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.
class PictureInline(admin.StackedInline):
    model = ProductImage
class ProductAdmin(admin.ModelAdmin):
    inlines = [PictureInline]

class ValueInline(admin.StackedInline):
    model = OptionValue
class OptionAdmin(admin.ModelAdmin):
    inlines = [ValueInline]


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'is_staff', 'is_shop_owner', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_shop_owner', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'first_name', 'last_name', 'password')}),
        ('Customer', {'fields': ('default_address', 'accepts_marketing', 'shops', 'profile_complete')}),
        ('Permissions', {'fields': ('is_shop_owner', 'is_staff', 'is_active', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Customer, CustomUserAdmin)
admin.site.register(CustomerAddress)
admin.site.register(Shop)
admin.site.register(Collection)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductOption, OptionAdmin)
admin.site.register(ProductVariant)
admin.site.register(Order)
admin.site.register(OrderItem)
