from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Category, Tag, Expense, FinancialYear, CategoryBudget
from .serializers import (
    CategorySerializer, TagSerializer, ExpenseSerializer, 
    FinancialYearSerializer, CategoryBudgetSerializer,
    CustomTokenObtainPairSerializer
)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class FinancialYearViewSet(viewsets.ModelViewSet):
    queryset = FinancialYear.objects.all().order_by('-start_date')
    serializer_class = FinancialYearSerializer

class CategoryBudgetViewSet(viewsets.ModelViewSet):
    queryset = CategoryBudget.objects.all()
    serializer_class = CategoryBudgetSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        financial_year = self.request.query_params.get('financial_year')
        category = self.request.query_params.get('category')
        if financial_year:
            qs = qs.filter(financial_year_id=financial_year)
        if category:
            qs = qs.filter(category_id=category)
        return qs

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        sub_category = self.request.query_params.get('sub_category')
        month = self.request.query_params.get('month')
        tag = self.request.query_params.get('tag')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if category:
            qs = qs.filter(category_id=category)
        if sub_category:
            qs = qs.filter(sub_category=sub_category)
        if month:
            qs = qs.filter(date__month=month.split('-')[1], date__year=month.split('-')[0]) if '-' in month else qs.filter(date__month=month)
        if tag:
            qs = qs.filter(tag_id=tag)
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        
        return qs.order_by('-date', '-id')

@api_view(['GET'])
def dashboard_view(request):
    fy_id = request.query_params.get('fy_id')
    if fy_id:
        fy = FinancialYear.objects.filter(id=fy_id).first()
    else:
        fy = FinancialYear.objects.filter(is_active=True).first()

    if not fy:
        return Response({'error': 'No financial year found'}, status=400)

    budgets = CategoryBudget.objects.filter(financial_year=fy)
    
    expenses_qs = Expense.objects.filter(date__gte=fy.start_date, date__lte=fy.end_date)
    
    budgeted_cat_ids = budgets.values_list('category_id', flat=True)
    exp_cat_ids = expenses_qs.values_list('category_id', flat=True)
    categories = Category.objects.filter(Q(id__in=budgeted_cat_ids) | Q(id__in=exp_cat_ids))
    
    total_budget = budgets.aggregate(Sum('sanctioned_amount'))['sanctioned_amount__sum'] or 0
    total_spent = expenses_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = float(total_budget) - float(total_spent)
    
    total_opex = expenses_qs.filter(category__is_capex=False).aggregate(Sum('amount'))['amount__sum'] or 0
    total_capex = expenses_qs.filter(category__is_capex=True).aggregate(Sum('amount'))['amount__sum'] or 0

    sub_categories = {
        'ACTUAL': float(expenses_qs.filter(sub_category='ACTUAL').aggregate(Sum('amount'))['amount__sum'] or 0),
        'ADDITIONAL': float(expenses_qs.filter(sub_category='ADDITIONAL').aggregate(Sum('amount'))['amount__sum'] or 0),
        'OTHERS': float(expenses_qs.filter(sub_category='OTHERS').aggregate(Sum('amount'))['amount__sum'] or 0),
    }

    monthly_trend_dict = {}
    curr = fy.start_date.replace(day=1)
    end_date = fy.end_date.replace(day=1)
    while curr <= end_date:
        key = curr.strftime('%Y-%m')
        label = curr.strftime('%b \'%y')
        monthly_trend_dict[key] = {
            'month': label,
            'total_amount': 0.0,
            'count': 0
        }
        if curr.month == 12:
            curr = curr.replace(year=curr.year+1, month=1)
        else:
            curr = curr.replace(month=curr.month+1)

    monthly_trend_qs = expenses_qs.annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount'), count=Count('id'))
    for mt in monthly_trend_qs:
        if mt['month']:
            key = mt['month'].strftime('%Y-%m')
            if key in monthly_trend_dict:
                monthly_trend_dict[key]['total_amount'] = float(mt['total'] or 0)
                monthly_trend_dict[key]['count'] = mt['count']

    monthly_trend = list(monthly_trend_dict.values())

    expenses = expenses_qs.select_related('category', 'tag').order_by('date', 'id')
    expenses_data = []
    for exp in expenses:
        expenses_data.append({
            'id': exp.id,
            'date': exp.date.strftime('%Y-%m-%d'),
            'month': exp.date.replace(day=1).strftime('%Y-%m-%d'),
            'category_id': exp.category.id,
            'category_name': exp.category.name,
            'is_capex': getattr(exp.category, 'is_capex', False),
            'sub_category': exp.sub_category,
            'amount': float(exp.amount),
            'description': exp.description,
            'reference_no': exp.reference_no,
            'tag_id': exp.tag.id if exp.tag else None,
            'tag_name': exp.tag.name if exp.tag else None,
        })

    category_data = []
    for cat in categories:
        budget_obj = budgets.filter(category=cat).first()
        sanctioned = float(budget_obj.sanctioned_amount) if budget_obj else 0.0
        
        spent = float(expenses_qs.filter(category=cat).aggregate(Sum('amount'))['amount__sum'] or 0)
        cat_balance = sanctioned - spent
        perc_used = (spent / sanctioned * 100) if sanctioned > 0 else 0
        
        status = 'Not Started'
        if perc_used == 0:
            status = 'Not Started'
        elif perc_used < 50:
            status = 'On Track'
        elif perc_used < 80:
            status = 'Monitor'
        elif perc_used < 100:
            status = 'Alert'
        else:
            status = 'Overrun'

        category_data.append({
            'id': cat.id,
            'name': cat.name,
            'is_capex': getattr(cat, 'is_capex', False),
            'sanctioned': sanctioned,
            'spent': spent,
            'balance': cat_balance,
            'perc_used': perc_used,
            'status': status
        })

    return Response({
        'financial_year': fy.label,
        'start_date': fy.start_date.strftime('%b %Y'),
        'end_date': fy.end_date.strftime('%b %Y'),
        'total_budget': float(total_budget),
        'total_spent': float(total_spent),
        'balance': balance,
        'utilisation': (float(total_spent) / float(total_budget) * 100) if float(total_budget) > 0 else 0,
        'total_opex': float(total_opex),
        'total_capex': float(total_capex),
        'categories': category_data,
        'sub_categories': sub_categories,
        'monthly_trend': monthly_trend,
        'expenses': expenses_data
    })

@api_view(['GET'])
def summary_view(request):
    fy_id = request.query_params.get('financial_year')
    if not fy_id:
        return Response({}, status=400)
        
    try:
        fy = FinancialYear.objects.get(id=fy_id)
    except FinancialYear.DoesNotExist:
        return Response({}, status=404)

    # Fetch categories that have a budget in this Financial Year
    budgets = CategoryBudget.objects.filter(financial_year=fy).select_related('category')
    categories = sorted([b.category for b in budgets if b.category.is_active], key=lambda c: c.sort_order)
    budget_map = {b.category.name: float(b.sanctioned_amount) for b in budgets}
    
    # Initialize dictionary so that Python insertion-order is maintained in JSON
    summary_data = {}
    for cat in categories:
        summary_data[cat.name] = {
            'sanctioned': budget_map.get(cat.name, 0.0),
            'months': {}
        }
        
    # Filter expenses by the Financial Year dates
    expenses = Expense.objects.filter(date__gte=fy.start_date, date__lte=fy.end_date).annotate(month=TruncMonth('date')).values('category__name', 'sub_category', 'month').annotate(total=Sum('amount'))
    
    # Fill in the data
    for exp in expenses:
        cat_name = exp['category__name']
        sub = exp['sub_category']
        month = exp['month'].strftime('%Y-%m') if exp['month'] else ''
        
        # In case there's an expense with a deleted/inactive category
        if cat_name not in summary_data:
            summary_data[cat_name] = {
                'sanctioned': 0.0,
                'months': {}
            }
            
        if month not in summary_data[cat_name]['months']:
            summary_data[cat_name]['months'][month] = {'ACTUAL': 0, 'ADDITIONAL': 0, 'OTHERS': 0}
            
        summary_data[cat_name]['months'][month][sub] = float(exp['total'])

    return Response(summary_data)

@api_view(['GET'])
def ot_breakdown_view(request):
    expenses = Expense.objects.exclude(tag__isnull=True).annotate(month=TruncMonth('date')).values('tag__name', 'month').annotate(total=Sum('amount'))
    
    ot_data = {}
    for exp in expenses:
        tag = exp['tag__name']
        month = exp['month'].strftime('%Y-%m') if exp['month'] else ''
        
        if tag not in ot_data:
            ot_data[tag] = {}
            
        ot_data[tag][month] = float(exp['total'])

    return Response(ot_data)
