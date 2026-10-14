from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'financial_years', views.FinancialYearViewSet)
router.register(r'category_budgets', views.CategoryBudgetViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'tags', views.TagViewSet)
router.register(r'expenses', views.ExpenseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('summary/', views.summary_view, name='summary'),
    path('ot-breakdown/', views.ot_breakdown_view, name='ot-breakdown'),
]
