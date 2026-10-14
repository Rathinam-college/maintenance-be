from django.contrib import admin
from .models import FinancialYear, Category, CategoryBudget, Tag, Expense

@admin.register(FinancialYear)
class FinancialYearAdmin(admin.ModelAdmin):
    list_display = ('label', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_capex', 'sort_order', 'is_active')
    list_filter = ('is_capex', 'is_active')

@admin.register(CategoryBudget)
class CategoryBudgetAdmin(admin.ModelAdmin):
    list_display = ('financial_year', 'category', 'sanctioned_amount')
    list_filter = ('financial_year', 'category__is_capex')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'sub_category', 'date', 'amount', 'reference_no', 'tag')
    list_filter = ('sub_category', 'date', 'category__is_capex')
