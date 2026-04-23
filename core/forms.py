from django import forms
from .models import Invoice, InvoiceItem, DeliveryNote, DeliveryItem, StockMovement


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'supplier_name', 'invoice_date', 'file']
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['item_name', 'quantity', 'unit', 'net_price']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'net_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity <= 0:
            raise forms.ValidationError('Quantity must be greater than 0.')
        return quantity

    def clean_net_price(self):
        net_price = self.cleaned_data['net_price']
        if net_price < 0:
            raise forms.ValidationError('Net price cannot be negative.')
        return net_price


class DeliveryNoteForm(forms.ModelForm):
    class Meta:
        model = DeliveryNote
        fields = ['invoice', 'delivery_number', 'supplier_name', 'delivery_date', 'file']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'delivery_number': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        invoice = cleaned_data.get('invoice')
        supplier_name = cleaned_data.get('supplier_name')

        if invoice and supplier_name and invoice.supplier_name.strip().lower() != supplier_name.strip().lower():
            raise forms.ValidationError('Supplier of delivery note must match supplier of selected invoice.')

        return cleaned_data


class DeliveryItemForm(forms.ModelForm):
    class Meta:
        model = DeliveryItem
        fields = ['item_name', 'quantity', 'unit']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity <= 0:
            raise forms.ValidationError('Quantity must be greater than 0.')
        return quantity


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['stock_item', 'movement_type', 'quantity_change', 'reason']
        widgets = {
            'stock_item': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity_change': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_quantity_change(self):
        quantity_change = self.cleaned_data['quantity_change']
        if quantity_change == 0:
            raise forms.ValidationError('Quantity change cannot be 0.')
        return quantity_change

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        quantity_change = cleaned_data.get('quantity_change')

        if movement_type == 'goods_receipt' and quantity_change is not None and quantity_change < 0:
            raise forms.ValidationError('Goods receipt should be a positive quantity.')

        if movement_type in ['damage', 'return'] and quantity_change is not None and quantity_change > 0:
            raise forms.ValidationError('Damage and return should usually reduce stock, so use a negative value.')

        return cleaned_data