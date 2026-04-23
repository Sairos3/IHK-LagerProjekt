from django import forms
from .models import Invoice, InvoiceItem, DeliveryNote, DeliveryItem, StockMovement


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'supplier_name', 'invoice_date', 'file']
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['item_name', 'quantity', 'unit', 'net_price']


class DeliveryNoteForm(forms.ModelForm):
    class Meta:
        model = DeliveryNote
        fields = ['invoice', 'delivery_number', 'supplier_name', 'delivery_date', 'file']

        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'delivery_number': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class DeliveryItemForm(forms.ModelForm):
    class Meta:
        model = DeliveryItem
        fields = ['item_name', 'quantity', 'unit']


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['stock_item', 'movement_type', 'quantity_change', 'reason']