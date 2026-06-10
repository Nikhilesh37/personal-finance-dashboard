"""
Run with: python seed_data.py
Creates a demo user and sample transactions.
"""
import os
import sys
import django
import datetime
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from dashboard.models import Category, Transaction, Budget

# Create demo user
username = 'demo'
password = 'demo1234'

user, created = User.objects.get_or_create(username=username, defaults={'email': 'demo@example.com'})
if created:
    user.set_password(password)
    user.save()
    print(f'Created user: {username} / {password}')
else:
    print(f'User "{username}" already exists')

# Create categories
categories = [
    ('Salary', 'income', 'bi-briefcase'),
    ('Freelance', 'income', 'bi-laptop'),
    ('Investment', 'income', 'bi-graph-up-arrow'),
    ('Food & Dining', 'expense', 'bi-fork-knife'),
    ('Housing & Rent', 'expense', 'bi-house'),
    ('Transport', 'expense', 'bi-car-front'),
    ('Utilities', 'expense', 'bi-lightning-charge'),
    ('Health', 'expense', 'bi-heart-pulse'),
    ('Shopping', 'expense', 'bi-bag'),
    ('Entertainment', 'expense', 'bi-film'),
    ('Education', 'expense', 'bi-book'),
]

cat_objs = {}
for name, cat_type, icon in categories:
    cat, _ = Category.objects.get_or_create(user=user, name=name, type=cat_type, defaults={'icon': icon})
    cat_objs[name] = cat
print(f'Created {len(cat_objs)} categories')

today = datetime.date.today()

# Transactions for last 3 months
transactions_data = []
for month_offset in range(3):
    if today.month - month_offset <= 0:
        year = today.year - 1
        month = today.month - month_offset + 12
    else:
        year = today.year
        month = today.month - month_offset

    # Income
    transactions_data += [
        (Decimal('45000'), 'Salary', datetime.date(year, month, 1), 'Monthly salary'),
        (Decimal(str(random.randint(5000, 15000))), 'Freelance', datetime.date(year, month, 10), 'Project payment'),
    ]
    # Expenses
    transactions_data += [
        (Decimal('12000'), 'Housing & Rent', datetime.date(year, month, 2), 'Monthly rent'),
        (Decimal(str(random.randint(3000, 6000))), 'Food & Dining', datetime.date(year, month, 8), 'Groceries & eating out'),
        (Decimal(str(random.randint(800, 2000))), 'Transport', datetime.date(year, month, 12), 'Petrol & commute'),
        (Decimal(str(random.randint(500, 1500))), 'Utilities', datetime.date(year, month, 5), 'Electricity & internet'),
        (Decimal(str(random.randint(200, 1000))), 'Entertainment', datetime.date(year, month, 18), 'Movies & subscriptions'),
        (Decimal(str(random.randint(500, 3000))), 'Shopping', datetime.date(year, month, 20), 'Online shopping'),
    ]

for amount, cat_name, date, desc in transactions_data:
    Transaction.objects.get_or_create(
        user=user,
        amount=amount,
        category=cat_objs[cat_name],
        date=date,
        description=desc,
    )

print(f'Created {len(transactions_data)} transactions')

# Budgets for current month
month_start = today.replace(day=1)
budgets = [
    ('Food & Dining', Decimal('7000')),
    ('Housing & Rent', Decimal('13000')),
    ('Transport', Decimal('2500')),
    ('Utilities', Decimal('2000')),
    ('Shopping', Decimal('4000')),
    ('Entertainment', Decimal('1500')),
]

for cat_name, limit in budgets:
    Budget.objects.get_or_create(
        user=user,
        category=cat_objs[cat_name],
        month=month_start,
        defaults={'monthly_limit': limit}
    )
print(f'Created {len(budgets)} budgets')

print('\n✅ Done! Login with: username=demo  password=demo1234')
print('   Run: python manage.py runserver')
