from django.contrib import admin
from .models import Invoice, InvoiceItem, DeliveryNote, DeliveryItem, StockItem, StockMovement


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


class DeliveryItemInline(admin.TabularInline):
    model = DeliveryItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'supplier_name', 'invoice_date', 'status')
    inlines = [InvoiceItemInline]


@admin.register(DeliveryNote)
class DeliveryNoteAdmin(admin.ModelAdmin):
    list_display = ('delivery_number', 'supplier_name', 'delivery_date')
    inlines = [DeliveryItemInline]


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'current_quantity', 'updated_at')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('stock_item', 'movement_type', 'quantity_change', 'created_at')