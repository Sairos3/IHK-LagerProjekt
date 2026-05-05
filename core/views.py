from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    DeliveryItemForm,
    DeliveryNoteForm,
    InvoiceForm,
    InvoiceItemForm,
    StockMovementForm,
)
from .models import DeliveryItem, DeliveryNote, Invoice, InvoiceItem, StockItem, StockMovement


@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html', {
        'invoices': Invoice.objects.count(),
        'deliveries': DeliveryNote.objects.count(),
        'stock_items': StockItem.objects.count(),
        'open_invoices': Invoice.objects.filter(status='open').count(),
        'partial_invoices': Invoice.objects.filter(status='partial').count(),
        'complete_invoices': Invoice.objects.filter(status='complete').count(),
    })


@login_required
def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-created_at')

    search = request.GET.get('search', '').strip()
    supplier = request.GET.get('supplier', '').strip()
    status = request.GET.get('status', '').strip()

    if search:
        invoices = invoices.filter(invoice_number__icontains=search)

    if supplier:
        invoices = invoices.filter(supplier_name__icontains=supplier)

    if status:
        invoices = invoices.filter(status=status)

    return render(request, 'core/invoice_list.html', {
        'invoices': invoices,
        'search': search,
        'supplier': supplier,
        'status': status,
    })


@login_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()
            return redirect('invoice_list')
    else:
        form = InvoiceForm()
    return render(request, 'core/form.html', {'form': form, 'title': 'Create Invoice'})


@login_required
def invoice_item_add(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        form = InvoiceItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.invoice = invoice
            item.save()
            return redirect('invoice_list')
    else:
        form = InvoiceItemForm()
    return render(request, 'core/form.html', {
        'form': form,
        'title': f'Add Item to Invoice {invoice.invoice_number}'
    })


@login_required
def delivery_list(request):
    deliveries = DeliveryNote.objects.all().order_by('-created_at')

    search = request.GET.get('search', '').strip()
    supplier = request.GET.get('supplier', '').strip()

    if search:
        deliveries = deliveries.filter(delivery_number__icontains=search)

    if supplier:
        deliveries = deliveries.filter(supplier_name__icontains=supplier)

    return render(request, 'core/delivery_list.html', {
        'deliveries': deliveries,
        'search': search,
        'supplier': supplier,
    })


@login_required
def delivery_create(request):
    if request.method == 'POST':
        form = DeliveryNoteForm(request.POST, request.FILES)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.created_by = request.user
            delivery.save()
            return redirect('delivery_list')
    else:
        form = DeliveryNoteForm()
    return render(request, 'core/form.html', {'form': form, 'title': 'Create Delivery Note'})


@login_required
def delivery_item_add(request, delivery_id):
    delivery = get_object_or_404(DeliveryNote, id=delivery_id)
    if request.method == 'POST':
        form = DeliveryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.delivery_note = delivery
            item.save()
            return redirect('delivery_list')
    else:
        form = DeliveryItemForm()
    return render(request, 'core/form.html', {
        'form': form,
        'title': f'Add Item to Delivery {delivery.delivery_number}'
    })


@login_required
def compare_documents(request):
    invoices = Invoice.objects.prefetch_related('items', 'delivery_notes__items').all()
    grouped_results = []

    for invoice in invoices:
        delivered_map = defaultdict(int)
        linked_deliveries = list(invoice.delivery_notes.all())

        for delivery_note in linked_deliveries:
            for delivery_item in delivery_note.items.all():
                key = delivery_item.item_name.strip().lower()
                delivered_map[key] += delivery_item.quantity

        invoice_status = 'complete' if invoice.items.exists() else 'open'
        item_results = []
        total_expected = 0
        total_delivered = 0

        for invoice_item in invoice.items.all():
            key = invoice_item.item_name.strip().lower()
            delivered_qty = delivered_map.get(key, 0)
            difference = delivered_qty - invoice_item.quantity

            total_expected += invoice_item.quantity
            total_delivered += delivered_qty

            if delivered_qty == 0:
                status = 'Open'
                invoice_status = 'open'
            elif delivered_qty < invoice_item.quantity:
                status = 'Partial'
                invoice_status = 'partial'
            elif delivered_qty == invoice_item.quantity:
                status = 'Complete'
                if invoice_status not in ['open', 'partial', 'difference']:
                    invoice_status = 'complete'
            else:
                status = 'Difference'
                invoice_status = 'difference'

            item_results.append({
                'item_name': invoice_item.item_name,
                'expected_quantity': invoice_item.quantity,
                'delivered_quantity': delivered_qty,
                'difference': difference,
                'status': status,
            })

        invoice.status = invoice_status
        invoice.save()

        grouped_results.append({
            'invoice': invoice,
            'deliveries': linked_deliveries,
            'items': item_results,
            'total_expected': total_expected,
            'total_delivered': total_delivered,
            'total_difference': total_delivered - total_expected,
        })

    return render(request, 'core/compare.html', {'grouped_results': grouped_results})


@login_required
def stock_list(request):
    stock_items = StockItem.objects.all().order_by('item_name')

    search = request.GET.get('search', '').strip()
    if search:
        stock_items = stock_items.filter(item_name__icontains=search)

    return render(request, 'core/stock_list.html', {
        'stock_items': stock_items,
        'search': search,
    })


@login_required
def apply_stock_from_deliveries(request):
    delivery_items = DeliveryItem.objects.all()
    aggregated = defaultdict(int)

    for item in delivery_items:
        aggregated[item.item_name.strip()] += item.quantity

    for item_name, quantity in aggregated.items():
        stock_item, _ = StockItem.objects.get_or_create(item_name=item_name)
        change = quantity - stock_item.current_quantity

        if change != 0:
            stock_item.current_quantity = quantity
            stock_item.save()

            StockMovement.objects.create(
                stock_item=stock_item,
                movement_type='goods_receipt',
                quantity_change=change,
                reason='Automatic stock update from deliveries',
                created_by=request.user
            )

    return redirect('stock_list')


@login_required
def stock_movement_create(request):
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.created_by = request.user
            movement.save()

            stock_item = movement.stock_item
            stock_item.current_quantity += movement.quantity_change
            stock_item.save()

            return redirect('stock_list')
    else:
        form = StockMovementForm()
    return render(request, 'core/form.html', {'form': form, 'title': 'Create Stock Movement'})


@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(
        Invoice.objects.prefetch_related('items', 'delivery_notes__items'),
        id=invoice_id
    )
    return render(request, 'core/invoice_detail.html', {'invoice': invoice})


@login_required
def delivery_detail(request, delivery_id):
    delivery = get_object_or_404(
        DeliveryNote.objects.prefetch_related('items'),
        id=delivery_id
    )
    return render(request, 'core/delivery_detail.html', {'delivery': delivery})


@login_required
def stock_movement_list(request):
    movements = StockMovement.objects.select_related('stock_item', 'created_by').order_by('-created_at')
    return render(request, 'core/stock_movement_list.html', {'movements': movements})


@login_required
def invoice_item_edit(request, item_id):
    item = get_object_or_404(InvoiceItem, id=item_id)
    if request.method == 'POST':
        form = InvoiceItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('invoice_detail', invoice_id=item.invoice.id)
    else:
        form = InvoiceItemForm(instance=item)

    return render(request, 'core/form.html', {
        'form': form,
        'title': f'Edit Invoice Item: {item.item_name}'
    })


@login_required
def invoice_item_delete(request, item_id):
    item = get_object_or_404(InvoiceItem, id=item_id)
    invoice_id = item.invoice.id

    if request.method == 'POST':
        item.delete()
        return redirect('invoice_detail', invoice_id=invoice_id)

    return render(request, 'core/confirm_delete.html', {
        'title': 'Delete Invoice Item',
        'message': f'Are you sure you want to delete "{item.item_name}" from invoice {item.invoice.invoice_number}?'
    })


@login_required
def delivery_item_edit(request, item_id):
    item = get_object_or_404(DeliveryItem, id=item_id)
    if request.method == 'POST':
        form = DeliveryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('delivery_detail', delivery_id=item.delivery_note.id)
    else:
        form = DeliveryItemForm(instance=item)

    return render(request, 'core/form.html', {
        'form': form,
        'title': f'Edit Delivery Item: {item.item_name}'
    })


@login_required
def delivery_item_delete(request, item_id):
    item = get_object_or_404(DeliveryItem, id=item_id)
    delivery_id = item.delivery_note.id

    if request.method == 'POST':
        item.delete()
        return redirect('delivery_detail', delivery_id=delivery_id)

    return render(request, 'core/confirm_delete.html', {
        'title': 'Delete Delivery Item',
        'message': f'Are you sure you want to delete "{item.item_name}" from delivery {item.delivery_note.delivery_number}?'
    })


@login_required
def invoice_edit(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES, instance=invoice)
        if form.is_valid():
            updated_invoice = form.save(commit=False)
            updated_invoice.created_by = invoice.created_by
            updated_invoice.save()
            return redirect('invoice_detail', invoice_id=invoice.id)
    else:
        form = InvoiceForm(instance=invoice)

    return render(request, 'core/form.html', {
        'form': form,
        'title': f'Edit Invoice {invoice.invoice_number}'
    })


@login_required
def invoice_delete(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        invoice.delete()
        return redirect('invoice_list')

    return render(request, 'core/confirm_delete.html', {
        'title': 'Delete Invoice',
        'message': f'Are you sure you want to delete invoice "{invoice.invoice_number}"? All linked invoice items and delivery notes will also be deleted.'
    })


@login_required
def delivery_edit(request, delivery_id):
    delivery = get_object_or_404(DeliveryNote, id=delivery_id)
    if request.method == 'POST':
        form = DeliveryNoteForm(request.POST, request.FILES, instance=delivery)
        if form.is_valid():
            updated_delivery = form.save(commit=False)
            updated_delivery.created_by = delivery.created_by
            updated_delivery.save()
            return redirect('delivery_detail', delivery_id=delivery.id)
    else:
        form = DeliveryNoteForm(instance=delivery)

    return render(request, 'core/form.html', {
        'form': form,
        'title': f'Edit Delivery Note {delivery.delivery_number}'
    })


@login_required
def delivery_delete(request, delivery_id):
    delivery = get_object_or_404(DeliveryNote, id=delivery_id)

    if request.method == 'POST':
        delivery.delete()
        return redirect('delivery_list')

    return render(request, 'core/confirm_delete.html', {
        'title': 'Delete Delivery Note',
        'message': f'Are you sure you want to delete delivery note "{delivery.delivery_number}"? All linked delivery items will also be deleted.'
    })


@login_required
def dashboard(request):
    recent_invoices = Invoice.objects.order_by('-created_at')[:5]
    recent_deliveries = DeliveryNote.objects.order_by('-created_at')[:5]
    recent_movements = StockMovement.objects.select_related('stock_item').order_by('-created_at')[:5]

    return render(request, 'core/dashboard.html', {
        'invoices': Invoice.objects.count(),
        'deliveries': DeliveryNote.objects.count(),
        'stock_items': StockItem.objects.count(),
        'open_invoices': Invoice.objects.filter(status='open').count(),
        'partial_invoices': Invoice.objects.filter(status='partial').count(),
        'complete_invoices': Invoice.objects.filter(status='complete').count(),
        'recent_invoices': recent_invoices,
        'recent_deliveries': recent_deliveries,
        'recent_movements': recent_movements,
    })


@login_required
def stock_movement_edit(request, movement_id):
    movement = get_object_or_404(StockMovement, id=movement_id)

    if request.method == 'POST':
        form = StockMovementForm(request.POST, instance=movement)
        if form.is_valid():
            old_quantity = movement.quantity_change

            updated = form.save(commit=False)
            updated.created_by = movement.created_by
            updated.save()

            # adjust stock difference
            stock_item = updated.stock_item
            stock_item.current_quantity += (updated.quantity_change - old_quantity)
            stock_item.save()

            return redirect('stock_movement_list')
    else:
        form = StockMovementForm(instance=movement)

    return render(request, 'core/form.html', {
        'form': form,
        'title': f'Edit Stock Movement'
    })


@login_required
def stock_movement_delete(request, movement_id):
    movement = get_object_or_404(StockMovement, id=movement_id)

    if request.method == 'POST':
        stock_item = movement.stock_item

        # reverse the movement
        stock_item.current_quantity -= movement.quantity_change
        stock_item.save()

        movement.delete()
        return redirect('stock_movement_list')

    return render(request, 'core/confirm_delete.html', {
        'title': 'Delete Stock Movement',
        'message': f'Are you sure you want to delete movement for "{movement.stock_item.item_name}"?'
    })

