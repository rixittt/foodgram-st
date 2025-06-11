import json

from django.core.management.base import BaseCommand

from recipes.models import FoodIngredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        json_file = 'data/ingredients.json'
        try:
            with open(json_file, encoding='utf-8') as file:
                created_objects = FoodIngredient.objects.bulk_create(
                    (FoodIngredient(**row) for row in json.load(file)),
                    ignore_conflicts=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully ended: {len(created_objects)}'
                        f' objects created'
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Error loading ingredients from {json_file}: {e}'
            ))
