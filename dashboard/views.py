import csv
import io
import datetime
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone

try:
    from xhtml2pdf import pisa
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

from .models import Category, Transaction, Budget
from .forms import (
    RegisterForm, LoginForm, CategoryForm,
    TransactionForm, BudgetForm, CSVUploadForm
)


# ─────────────────────────── AUTH ────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        _create_default_categories(user)
        login(request, user)
        messages.success(request, f'Welcome, {user.username}! Your account has been created.')
        return redirect('dashboard')
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Welcome back, {user.username}!')
        return redirect(request.GET.get('next', 'dashboard'))
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def _create_default_categories(user):
    
    defaults = [
        ('Salary', 'income', 'bi-briefcase'),
        ('Freelance', 'income', 'bi-laptop'),
        ('Investment', 'income', 'bi-graph-up-arrow'),
        ('Other Income', 'income', 'bi-plus-circle'),
        ('Food & Dining', 'expense', 'bi-fork-knife'),
        ('Housing & Rent', 'expense', 'bi-house'),
        ('Transport', 'expense', 'bi-car-front'),
        ('Utilities', 'expense', 'bi-lightning-charge'),
        ('Health', 'expense', 'bi-heart-pulse'),
        ('Shopping', 'expense', 'bi-bag'),
        ('Entertainment', 'expense', 'bi-film'),
        ('Education', 'expense', 'bi-book'),
    ]
    for name, cat_type, icon in defaults:
        Category.objects.get_or_create(user=user, name=name, type=cat_type, defaults={'icon': icon})


# ─────────────────────────── DASHBOARD ────────────────────────────

@login_required
def dashboard_view(request):
    today = datetime.date.today()
    month_start = today.replace(day=1)

    transactions = Transaction.objects.filter(user=request.user)
    this_month_tx = transactions.filter(date__year=today.year, date__month=today.month)

    # Totals
    total_income = this_month_tx.filter(category__type='income').aggregate(
        s=Sum('amount'))['s'] or Decimal('0')
    total_expense = this_month_tx.filter(category__type='expense').aggregate(
        s=Sum('amount'))['s'] or Decimal('0')
    net_balance = total_income - total_expense

    # Recent 5 transactions
    recent_transactions = transactions[:5]

    # Spending by category (expense, this month)
    spending_by_cat = (
        this_month_tx.filter(category__type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    # Monthly trend — last 6 months
    monthly_trend = _get_monthly_trend(request.user, 6)

    # Budgets this month
    budgets = Budget.objects.filter(
        user=request.user,
        month=month_start
    ).select_related('category')

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'recent_transactions': recent_transactions,
        'spending_by_cat': spending_by_cat,
        'monthly_trend': monthly_trend,
        'budgets': budgets,
        'today': today,
    }
    return render(request, 'dashboard/dashboard.html', context)


def _get_monthly_trend(user, months=6):
    today = datetime.date.today()
    result = []
    for i in range(months - 1, -1, -1):
        # Go back i months
        if today.month - i <= 0:
            year = today.year - 1
            month = today.month - i + 12
        else:
            year = today.year
            month = today.month - i

        tx = Transaction.objects.filter(user=user, date__year=year, date__month=month)
        income = tx.filter(category__type='income').aggregate(s=Sum('amount'))['s'] or 0
        expense = tx.filter(category__type='expense').aggregate(s=Sum('amount'))['s'] or 0
        result.append({
            'label': datetime.date(year, month, 1).strftime('%b %Y'),
            'income': float(income),
            'expense': float(expense),
        })
    return result


# ─────────────────────────── TRANSACTIONS ────────────────────────────

@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).select_related('category')

    # Filters
    cat_filter = request.GET.get('category', '')
    type_filter = request.GET.get('type', '')
    month_filter = request.GET.get('month', '')

    if cat_filter:
        transactions = transactions.filter(category_id=cat_filter)
    if type_filter:
        transactions = transactions.filter(category__type=type_filter)
    if month_filter:
        try:
            year, month = month_filter.split('-')
            transactions = transactions.filter(date__year=year, date__month=month)
        except ValueError:
            pass

    categories = Category.objects.filter(user=request.user)
    context = {
        'transactions': transactions,
        'categories': categories,
        'cat_filter': cat_filter,
        'type_filter': type_filter,
        'month_filter': month_filter,
    }
    return render(request, 'dashboard/transactions.html', context)


@login_required
def transaction_add(request):
    form = TransactionForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tx = form.save(commit=False)
        tx.user = request.user
        tx.save()
        messages.success(request, 'Transaction added successfully.')
        return redirect('transaction_list')
    return render(request, 'dashboard/transaction_form.html', {'form': form, 'title': 'Add Transaction'})


@login_required
def transaction_edit(request, pk):
    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    form = TransactionForm(request.user, request.POST or None, instance=tx)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Transaction updated.')
        return redirect('transaction_list')
    return render(request, 'dashboard/transaction_form.html', {'form': form, 'title': 'Edit Transaction', 'tx': tx})


@login_required
def transaction_delete(request, pk):
    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        tx.delete()
        messages.success(request, 'Transaction deleted.')
        return redirect('transaction_list')
    return render(request, 'dashboard/confirm_delete.html', {'object': tx, 'type': 'transaction'})


# ─────────────────────────── CATEGORIES ────────────────────────────

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, 'dashboard/categories.html', {'categories': categories})


@login_required
def category_add(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cat = form.save(commit=False)
        cat.user = request.user
        cat.save()
        messages.success(request, 'Category created.')
        return redirect('category_list')
    return render(request, 'dashboard/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk, user=request.user)
    form = CategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('category_list')
    return render(request, 'dashboard/category_form.html', {'form': form, 'title': 'Edit Category', 'cat': cat})


@login_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted.')
        return redirect('category_list')
    return render(request, 'dashboard/confirm_delete.html', {'object': cat, 'type': 'category'})


# ─────────────────────────── BUDGETS ────────────────────────────

@login_required
def budget_list(request):
    today = datetime.date.today()
    month_start = today.replace(day=1)

    # Show selected month or current
    month_filter = request.GET.get('month', month_start.strftime('%Y-%m'))
    try:
        year, month = month_filter.split('-')
        selected_month = datetime.date(int(year), int(month), 1)
    except (ValueError, TypeError):
        selected_month = month_start

    budgets = Budget.objects.filter(
        user=request.user,
        month=selected_month
    ).select_related('category')

    budget_data = []
    for b in budgets:
        spent = b.get_spent()
        pct = b.get_percentage()
        budget_data.append({
            'budget': b,
            'spent': spent,
            'remaining': max(b.monthly_limit - spent, 0),
            'percentage': pct,
            'over': b.is_over_budget(),
        })

    context = {
        'budget_data': budget_data,
        'selected_month': selected_month,
        'month_filter': month_filter,
    }
    return render(request, 'dashboard/budgets.html', context)


@login_required
def budget_add(request):
    form = BudgetForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        budget = form.save(commit=False)
        budget.user = request.user
        budget.save()
        messages.success(request, 'Budget set successfully.')
        return redirect('budget_list')
    return render(request, 'dashboard/budget_form.html', {'form': form, 'title': 'Set Budget'})


@login_required
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    form = BudgetForm(request.user, request.POST or None, instance=budget)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Budget updated.')
        return redirect('budget_list')
    return render(request, 'dashboard/budget_form.html', {'form': form, 'title': 'Edit Budget', 'budget': budget})


@login_required
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted.')
        return redirect('budget_list')
    return render(request, 'dashboard/confirm_delete.html', {'object': budget, 'type': 'budget'})


# ─────────────────────────── CSV IMPORT / EXPORT ────────────────────────────

@login_required
def csv_export(request):
    transactions = Transaction.objects.filter(user=request.user).select_related('category')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(['date', 'amount', 'type', 'category', 'description'])
    for tx in transactions:
        writer.writerow([
            tx.date,
            tx.amount,
            tx.category.type if tx.category else '',
            tx.category.name if tx.category else '',
            tx.description,
        ])
    return response


@login_required
def csv_import(request):
    form = CSVUploadForm(request.POST or None, request.FILES or None)
    errors = []
    imported = 0

    if request.method == 'POST' and form.is_valid():
        csv_file = request.FILES['csv_file']
        try:
            decoded = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            for i, row in enumerate(reader, start=2):
                try:
                    date_str = row.get('date', '').strip()
                    amount_str = row.get('amount', '').strip()
                    cat_name = row.get('category', '').strip()
                    description = row.get('description', '').strip()

                    date = datetime.date.fromisoformat(date_str)
                    amount = Decimal(amount_str)
                    category = Category.objects.filter(user=request.user, name__iexact=cat_name).first()

                    Transaction.objects.create(
                        user=request.user,
                        amount=amount,
                        category=category,
                        date=date,
                        description=description,
                    )
                    imported += 1
                except Exception as e:
                    errors.append(f'Row {i}: {e}')
        except Exception as e:
            errors.append(f'File error: {e}')

        if imported:
            messages.success(request, f'Successfully imported {imported} transaction(s).')
        if errors:
            messages.warning(request, f'{len(errors)} row(s) had errors. Check details below.')

    return render(request, 'dashboard/csv_import.html', {'form': form, 'errors': errors})


# ─────────────────────────── PDF REPORT ────────────────────────────

@login_required
def pdf_report_page(request):
    
    today = datetime.date.today()
    month_filter = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        year, month = month_filter.split('-')
        selected_month = datetime.date(int(year), int(month), 1)
    except ValueError:
        selected_month = today.replace(day=1)

    transactions = Transaction.objects.filter(
        user=request.user,
        date__year=selected_month.year,
        date__month=selected_month.month,
    ).select_related('category')

    total_income = transactions.filter(category__type='income').aggregate(s=Sum('amount'))['s'] or 0
    total_expense = transactions.filter(category__type='expense').aggregate(s=Sum('amount'))['s'] or 0

    context = {
        'transactions': transactions,
        'total_income': total_income,
        'total_expense': total_expense,
        'net': total_income - total_expense,
        'selected_month': selected_month,
        'month_filter': month_filter,
        'pdf_available': PDF_AVAILABLE,
    }
    return render(request, 'dashboard/report_page.html', context)


@login_required
def pdf_download(request):
    
    today = datetime.date.today()
    month_filter = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        year, month = month_filter.split('-')
        selected_month = datetime.date(int(year), int(month), 1)
    except ValueError:
        selected_month = today.replace(day=1)

    transactions = Transaction.objects.filter(
        user=request.user,
        date__year=selected_month.year,
        date__month=selected_month.month,
    ).select_related('category')

    total_income = transactions.filter(category__type='income').aggregate(s=Sum('amount'))['s'] or 0
    total_expense = transactions.filter(category__type='expense').aggregate(s=Sum('amount'))['s'] or 0

    context = {
        'transactions': transactions,
        'total_income': total_income,
        'total_expense': total_expense,
        'net': total_income - total_expense,
        'selected_month': selected_month,
        'user': request.user,
        'generated_at': datetime.datetime.now(),
    }

    if not PDF_AVAILABLE:
        messages.warning(request, 'PDF library not installed. Run: pip install xhtml2pdf')
        return redirect('pdf_report')

    # Render the PDF-specific template to an HTML string
    from django.template.loader import render_to_string
    html_string = render_to_string('dashboard/report_pdf.html', context, request=request)

    # Convert HTML → PDF using xhtml2pdf
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        io.StringIO(html_string),
        dest=pdf_buffer,
        encoding='utf-8',
    )

    if pisa_status.err:
        messages.error(request, 'PDF generation failed. Please try again.')
        return redirect('pdf_report')

    pdf_buffer.seek(0)
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{month_filter}.pdf"'
    return response


# ─────────────────────────── AJAX ────────────────────────────

@login_required
def chart_data(request):
    
    trend = _get_monthly_trend(request.user, 6)
    return JsonResponse({'trend': trend})
