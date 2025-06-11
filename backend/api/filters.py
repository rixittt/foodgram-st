import django_filters
from django.contrib.auth import get_user_model
from recipes.models import FoodIngredient, FoodRecipe


User = get_user_model()


class IngredientSearchFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = FoodIngredient
        fields = ['name']


class RecipeSearchFilter(django_filters.FilterSet):
    author = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='author'
    )
    is_in_shopping_cart = django_filters.CharFilter(method='filter_cart')
    is_favorited = django_filters.CharFilter(method='filter_favorite')

    class Meta:
        model = FoodRecipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    def filter_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(foodshoppingcart_by_users__user=self.request.user)
        return queryset

    def filter_favorite(self, queryset, name, value):
        if value == '1' and self.request.user.is_authenticated:
            return queryset.filter(foodfavoriterecipe_by_users__user=self.request.user)
        return queryset
