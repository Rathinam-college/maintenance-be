from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import datetime

class FinancialYear(models.Model):
    label = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("End date must be after the start date.")

    def __str__(self):
        return self.label

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_capex = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name

class CategoryBudget(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='budgets')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE, related_name='budgets')
    sanctioned_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)])

    class Meta:
        unique_together = ('category', 'financial_year')
        
    def __str__(self):
        return f"{self.category.name} - {self.financial_year.label}"

class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Expense(models.Model):
    SUB_CATEGORY_CHOICES = [
        ('ACTUAL', 'Actual Expenses'),
        ('ADDITIONAL', 'Additional Work'),
        ('OTHERS', 'Others'),
    ]

    category = models.ForeignKey(Category, related_name='expenses', on_delete=models.PROTECT)
    sub_category = models.CharField(max_length=20, choices=SUB_CATEGORY_CHOICES)
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.00)])
    reference_no = models.CharField(max_length=100, blank=True, null=True)  # Opex No / Capex No
    tag = models.ForeignKey(Tag, related_name='expenses', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.category.name} - {self.date.strftime('%d %b %y')} - {self.amount}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=FinancialYear)
def clone_budgets_for_new_year(sender, instance, created, **kwargs):
    if created:
        prev_fy = FinancialYear.objects.filter(start_date__lt=instance.start_date).order_by('-start_date').first()
        if prev_fy:
            prev_budgets = CategoryBudget.objects.filter(financial_year=prev_fy)
            for pb in prev_budgets:
                CategoryBudget.objects.create(
                    category=pb.category,
                    financial_year=instance,
                    sanctioned_amount=0.00
                )
