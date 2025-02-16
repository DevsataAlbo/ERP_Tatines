from django import template
from decimal import Decimal, InvalidOperation
import json

register = template.Library()

@register.filter
def divided_by(value, arg):
    try:
        # Validar que ambos valores no sean None
        if value is None or arg is None:
            return 0
            
        # Convertir los valores a Decimal
        value = Decimal(str(value)) if value else Decimal('0')
        arg = Decimal(str(arg)) if arg else Decimal('1')
        
        # Evitar división por cero
        if arg == 0:
            return 0
            
        return int(value / arg)
    except (TypeError, InvalidOperation):
        return 0