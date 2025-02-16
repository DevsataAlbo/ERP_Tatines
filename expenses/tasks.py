# tasks.py
from django.utils import timezone
from calendar import monthrange
from datetime import datetime

def close_previous_month():
    today = timezone.now()
    # Si estamos en cualquier día después del 1ro, cerramos el mes anterior
    if today.day >= 1:
        # Obtenemos el último día del mes anterior
        first_day = today.replace(day=1)
        last_month = first_day - timezone.timedelta(days=1)
        _, last_day = monthrange(last_month.year, last_month.month)

        # Verificar si el mes ya está cerrado
        if not MonthlyClose.objects.filter(
            year=last_month.year,
            month=last_month.month
        ).exists():
            # Obtener todos los gastos del mes anterior
            expenses = Expense.objects.filter(
                date__year=last_month.year,
                date__month=last_month.month
            )
            
            # Crear el cierre
            MonthlyClose.objects.create(
                month=last_month.month,
                year=last_month.year,
                closed_at=timezone.now(),
                closed_by=None,  # O un usuario sistema
                total_amount=expenses.aggregate(Sum('amount'))['amount__sum'] or 0
            )