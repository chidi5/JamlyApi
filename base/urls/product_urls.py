from django.urls import include, path
from rest_framework.routers import DefaultRouter
from base.views.product_views import ProductViewSet

router = DefaultRouter()
router.register(r'create/product', ProductViewSet, basename='create_product')


urlpatterns = [
    path('', include(router.urls))
]
#urlpatterns += router.urls