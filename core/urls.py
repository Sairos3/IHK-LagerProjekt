from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/add-item/', views.invoice_item_add, name='invoice_item_add'),

    path('deliveries/', views.delivery_list, name='delivery_list'),
    path('deliveries/create/', views.delivery_create, name='delivery_create'),
    path('deliveries/<int:delivery_id>/', views.delivery_detail, name='delivery_detail'),
    path('deliveries/<int:delivery_id>/add-item/', views.delivery_item_add, name='delivery_item_add'),

    path('invoice-items/<int:item_id>/edit/', views.invoice_item_edit, name='invoice_item_edit'),
    path('invoice-items/<int:item_id>/delete/', views.invoice_item_delete, name='invoice_item_delete'),

    path('delivery-items/<int:item_id>/edit/', views.delivery_item_edit, name='delivery_item_edit'),
    path('delivery-items/<int:item_id>/delete/', views.delivery_item_delete, name='delivery_item_delete'),

    path('compare/', views.compare_documents, name='compare_documents'),

    path('stock/', views.stock_list, name='stock_list'),
    path('stock/apply/', views.apply_stock_from_deliveries, name='apply_stock_from_deliveries'),
    path('stock/movements/', views.stock_movement_list, name='stock_movement_list'),
    path('stock/movement/add/', views.stock_movement_create, name='stock_movement_create'),
]