from django.core.management.base import BaseCommand
from expenses.models import Category
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Carga las categorías principales de gastos'

    def handle(self, *args, **kwargs):
        # Obtener usuario admin
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No se encontró un usuario admin'))
            return

        # Categorías principales
        main_categories = [
            {
                'name': 'Ingresos',
                'description': 'Ingresos operacionales y no operacionales',
                'order': 1,
                'is_main': True
            },
            {
                'name': 'Costos',
                'description': 'Costos directos e indirectos',
                'order': 2,
                'is_main': True
            },
            {
                'name': 'Gastos de Administración y Ventas',
                'description': 'Gastos operativos del negocio',
                'order': 3,
                'is_main': True
            },
            {
                'name': 'Gastos Financieros',
                'description': 'Gastos relacionados con operaciones financieras',
                'order': 4,
                'is_main': True
            }
        ]

        # Subcategorías sugeridas
        suggested_subcategories = {
            'Ingresos': ['Ventas', 'Otros Ingresos'],
            'Costos': ['Costo de Ventas', 'Otros Costos'],
            'Gastos de Administración y Ventas': [
                'Remuneraciones',
                'Servicios Básicos',
                'Arriendos',
                'Mantenciones',
                'Asesorías',
                'Otros Gastos'
            ],
            'Gastos Financieros': [
                'Comisiones Bancarias',
                'Intereses'
            ]
        }

        # Crear categorías principales
        created_categories = {}
        for cat_data in main_categories:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'order': cat_data['order'],
                    'is_main': True,
                    'created_by': admin_user
                }
            )
            created_categories[cat_data['name']] = cat
            status = 'creada' if created else 'ya existía'
            self.stdout.write(self.style.SUCCESS(f'Categoría principal {cat.name} {status}'))

        # Crear subcategorías sugeridas
        for parent_name, subcats in suggested_subcategories.items():
            parent = created_categories.get(parent_name)
            if parent:
                for subcat_name in subcats:
                    subcat, created = Category.objects.get_or_create(
                        name=subcat_name,
                        defaults={
                            'parent': parent,
                            'is_main': False,
                            'created_by': admin_user
                        }
                    )
                    status = 'creada' if created else 'ya existía'
                    self.stdout.write(
                        self.style.SUCCESS(f'Subcategoría {subcat.name} {status} en {parent_name}')
                    )