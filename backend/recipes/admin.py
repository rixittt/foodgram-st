from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    Recipe,
    Ingredient,
    RecipeIngredient,
    FavoriteRecipe,
    ShoppingCart
)


class RecipeIngredientInlineAdmin(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class FoodRecipeAdmin(admin.ModelAdmin):
    search_fields = ('name', 'author__username')
    list_display = (
        'name',
        'cooking_time',
        'author_name',
        'favorites_count',
        'ingredients_list_html',
        'image_preview_html',
    )
    list_display_links = ('name', 'author_name')
    readonly_fields = ('image_preview_html',)
    inlines = [RecipeIngredientInlineAdmin]

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.select_related('author').prefetch_related(
            'favoriterecipe_by_users',
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


@admin.register(Ingredient)
class FoodIngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'related_recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.prefetch_related('ingredient_recipes')

    @admin.display(description='Число рецептов')
    def related_recipes_count(self, ingredient):
        return ingredient.ingredient_recipes.count()


class BaseUserRecipeAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'recipe__name')
    list_display = ('display_user', 'display_recipe')
    list_display_links = ('display_user', 'display_recipe')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe')

    @admin.display(description='Пользователь')
    def display_user(self, obj):
        return obj.user.username

    @admin.display(description='Рецепт')
    def display_recipe(self, obj):
        return obj.recipe.name


@admin.register(FavoriteRecipe)
class FoodFavoriteRecipeAdmin(BaseUserRecipeAdmin):
    pass


@admin.register(ShoppingCart)
class FoodShoppingCartAdmin(BaseUserRecipeAdmin):
    pass
