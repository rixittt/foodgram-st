from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    FoodRecipe,
    FoodIngredient,
    FoodRecipeIngredient,
    FoodFavoriteRecipe,
    FoodShoppingCart
)


class RecipeIngredientInlineAdmin(admin.TabularInline):
    model = FoodRecipeIngredient
    extra = 1


@admin.register(FoodRecipe)
class FoodRecipeAdmin(admin.ModelAdmin):
    search_fields = ('name', 'author__username')
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author_name',
        'favorites_count',
        'ingredients_list_html',
        'image_preview_html',
    )
    readonly_fields = ('image_preview_html',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author').prefetch_related(
            'favoriterecipe_by_users',
            'ingredients',
            'recipe_ingredients',
            'recipe_ingredients__ingredient'
        )

    @admin.display(description='Автор')
    def author_name(self, recipe):
        return recipe.author.username

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favoriterecipe_by_users.count()

    @admin.display(description='Изображение')
    @mark_safe
    def image_preview_html(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" '
                f'width="100" height="100" style="object-fit: cover;" />'
            )
        return '—'

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_list_html(self, recipe):
        ingredients = recipe.recipe_ingredients.all()
        if not ingredients:
            return '—'
        return '<br>'.join(
            f'{ri.ingredient.name} — {ri.amount}{ri.ingredient.measurement_unit}'
            for ri in ingredients
        )


@admin.register(FoodIngredient)
class FoodIngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'related_recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('ingredient_recipes')

    @admin.display(description='Число рецептов')
    def related_recipes_count(self, ingredient):
        return ingredient.ingredient_recipes.count()


class BaseUserRecipeAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'recipe__name')
    list_select_related = ('user', 'recipe')
    list_display = ('display_user', 'display_recipe')

    @admin.display(description='Пользователь')
    def display_user(self, obj):
        return obj.user.username

    @admin.display(description='Рецепт')
    def display_recipe(self, obj):
        return obj.recipe.name
