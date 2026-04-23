from django.conf import settings
from django.db import models


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('partial', 'Partial'),
        ('complete', 'Complete'),
        ('difference', 'Difference'),
    ]

    invoice_number = models.CharField(max_length=100, unique=True)
    supplier_name = models.CharField(max_length=255)
    invoice_date = models.DateField()
    file = models.FileField(upload_to='invoices/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=50, default='Stk')
    net_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.item_name} ({self.invoice.invoice_number})"


class DeliveryNote(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='delivery_notes',
        null=True,
        blank=True
    )
    delivery_number = models.CharField(max_length=100, unique=True)
    supplier_name = models.CharField(max_length=255)
    delivery_date = models.DateField()
    file = models.FileField(upload_to='deliveries/', blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.delivery_number


class DeliveryItem(models.Model):
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=50, default='Stk')

    def __str__(self):
        return f"{self.item_name} ({self.delivery_note.delivery_number})"


class StockItem(models.Model):
    item_name = models.CharField(max_length=255, unique=True)
    current_quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name}: {self.current_quantity}"


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('goods_receipt', 'Goods Receipt'),
        ('correction', 'Correction'),
        ('damage', 'Damage'),
        ('return', 'Return'),
    ]

    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity_change = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stock_item.item_name}: {self.quantity_change}"