from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime


class Category(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    icon = models.CharField(max_length=50, default='bi-tag')  # Bootstrap Icons class

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='transactions')
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description or 'Transaction'} — ₹{self.amount} on {self.date}"

    @property
    def is_income(self):
        return self.category and self.category.type == 'income'

    @property
    def is_expense(self):
        return self.category and self.category.type == 'expense'


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.DateField()  # store first day of the month

    class Meta:
        unique_together = ['user', 'category', 'month']
        ordering = ['-month']

    def __str__(self):
        return f"{self.category.name} budget for {self.month.strftime('%B %Y')}"

    def get_spent(self):
        
        return self.category.transactions.filter(
            user=self.user,
            date__year=self.month.year,
            date__month=self.month.month,
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    def get_percentage(self):
        
        if self.monthly_limit == 0:
            return 0
        spent = self.get_spent()
        return min(int((spent / self.monthly_limit) * 100), 100)

    def is_over_budget(self):
        return self.get_spent() > self.monthly_limit
