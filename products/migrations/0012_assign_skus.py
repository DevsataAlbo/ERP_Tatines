from django.db import migrations

def assign_skus(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    next_number = 1
    
    for product in Product.objects.filter(sku__isnull=True).order_by('id'):
        product.sku = str(next_number).zfill(7)
        product.save()
        next_number += 1

def reverse_skus(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.all().update(sku=None)

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0011_product_sku_productvariant_productstock_variant'),  # Corregido
    ]

    operations = [
        migrations.RunPython(assign_skus, reverse_skus),
    ]