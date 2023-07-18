from django.urls import include, path

from base.views.shop_views import CollectionListCreateAPIView, CollectionRetrieveUpdateDestroyAPIView, OptionDetail, OptionList, PlaceOrderView, ProductListCreateAPIView, ProductRetrieveUpdateDestroyAPIView, ShopListAPIView, ShopRetrieveUpdateDestroyAPIView, VariantDetail, VariantList, getShopData, CustomerList, storefront


urlpatterns = [
    ## Shop
    path('shop/<str:shop_id>/', ShopListAPIView.as_view(), name='shop-list'),
    path('shop/<str:shop_id>/update/', ShopRetrieveUpdateDestroyAPIView.as_view(), name='shop-update'),
    ## Shop collection
    path('shop/<str:shop_id>/collections/', CollectionListCreateAPIView.as_view(), name='collection-list'),
    path('shop/<str:shop_id>/collections/<str:lookup>/', CollectionRetrieveUpdateDestroyAPIView.as_view(), name='collection-detail'),
    ## Shop product
    path('shop/<str:shop_id>/products/', ProductListCreateAPIView.as_view(), name='product-list'),
    path('shop/<str:shop_id>/products/<str:lookup>/', ProductRetrieveUpdateDestroyAPIView.as_view(), name='product-detail'),
    ## Product options
    path('options/', OptionList.as_view(), name='option-list'),
    path('options/<int:pk>/', OptionDetail.as_view(), name='option-detail'),
    path('variants/', VariantList.as_view(), name='variant-list'),
    path('variants/<int:pk>/', VariantDetail.as_view(), name='variant-detail'),
    path('place_order/<str:customer_id>/', PlaceOrderView.as_view(), name='place_order'),
    ## Admin
    path('getshop/<str:user_id>/', getShopData, name='get_store'),
    path('customers/<str:shop_id>/', CustomerList.as_view(), name='customers'),
    ## StoreFront
    path('storefront/<str:domain_name>/', storefront, name='storefront'),

]
