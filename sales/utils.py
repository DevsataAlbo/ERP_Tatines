from decimal import Decimal, ROUND_HALF_UP

def round_money(value):
    """
    Redondea valores monetarios a enteros:
    - Si el decimal es >= 0.5, redondea hacia arriba
    - Si el decimal es < 0.5, redondea hacia abajo
    """
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def calculate_bulk_quantity(amount, price_per_kilo):
    """
    Calcula la cantidad en kilos basada en el monto a vender.
    """
    amount = Decimal(str(amount))
    price_per_kilo = Decimal(str(price_per_kilo))
    quantity = (amount / price_per_kilo).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    return quantity, amount