from django import forms
from .models import Invoice, InvoiceItem, DeliveryNote, DeliveryItem, StockMovement


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'supplier_name', 'invoice_date', 'file']
        labels = {
            'invoice_number': 'Rechnungs Nr.',
            'supplier_name': 'Lieferantenname',
            'invoice_date': 'Rechnungsdatum',
            'file': 'Datei',
        }
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['invoice_date'].input_formats = ['%Y-%m-%d']

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
        labels = {
            'invoice': 'Rechnungs Nr.',
            'delivery_number': 'Lieferschein Nr.',
            'supplier_name': 'Lieferantenname',
            'delivery_date': 'Rechnungsdatum',
            'file': 'Datei',
        }
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'delivery_number': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_name': forms.Select(attrs={'class': 'form-select'}),
            'delivery_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        invoice = cleaned_data.get('invoice')
        supplier_name = cleaned_data.get('supplier_name')

        if invoice and supplier_name and invoice.supplier_name.strip().lower() != supplier_name.strip().lower():
            raise forms.ValidationError('Der Lieferant des Lieferscheins muss mit dem Lieferanten der ausgewählten Rechnung übereinstimmen.')

        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        open_invoices = Invoice.objects.exclude(status='complete')

        # include currently selected invoice while editing
        if self.instance and self.instance.pk and self.instance.invoice:
            open_invoices = open_invoices | Invoice.objects.filter(
                pk=self.instance.invoice.pk
            )

        self.fields['invoice'].queryset = open_invoices.distinct()

        supplier_choices = [('', '---------')]
        supplier_choices += [
            (name, name)
            for name in open_invoices
                .exclude(supplier_name__isnull=True)
                .exclude(supplier_name='')
                .values_list('supplier_name', flat=True)
                .distinct()
                .order_by('supplier_name')
        ]

        # include current supplier while editing
        if self.instance and self.instance.pk and self.instance.supplier_name:
            current_supplier = self.instance.supplier_name

            if (current_supplier, current_supplier) not in supplier_choices:
                supplier_choices.append(
                    (current_supplier, current_supplier)
                )

        self.fields['supplier_name'].widget = forms.Select(
            choices=supplier_choices,
            attrs={'class': 'form-select'}
        )

        self.fields['delivery_date'].input_formats = ['%Y-%m-%d']


class DeliveryItemForm(forms.ModelForm):
    class Meta:
        model = DeliveryItem
        fields = ['item_name', 'quantity', 'unit']
        labels = {
            'item_name': 'Artikel',
            'quantity': 'Menge',
            'unit': 'Einheit',
        }
        
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
        labels = {
            'stock_item': 'Artikel',
            'movement_type': 'Grund',
            'quantity_change': 'Menge',
            'reason': 'Beschreibung',
        }
        widgets = {
            'stock_item': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity_change': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Beschreibe den Grund der Eintragung'
                }),
        }

    def clean_quantity_change(self):
        quantity_change = self.cleaned_data['quantity_change']
        if quantity_change == 0:
            raise forms.ValidationError('Menge kann nicht 0 sein.')
        return quantity_change

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        quantity_change = cleaned_data.get('quantity_change')

        if movement_type in ['damage', 'return'] and quantity_change is not None and quantity_change > 0:
            raise forms.ValidationError('Damage and return should usually reduce stock, so use a negative value.')

        return cleaned_data