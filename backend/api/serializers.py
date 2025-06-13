import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from rest_framework import serializers
from djoser.serializers import UserSerializer as DjoserUserSerializer

from recipes.models import (
    Recipe,
    Ingredient,
    RecipeIngredient
)

from users.models import UserSubscription

User = get_user_model()


class CustomBase64ImageField(serializers.ImageField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_url = False

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        return instance.url if instance else None


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class ExtendedUserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = CustomBase64ImageField(required=False)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'avatar', 'is_subscribed'
        )

    def get_is_subscribed(self, user):
        request = self.context['request']
        return request.user.is_authenticated and request.user.subscribers.filter(author=user).exists()


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = CustomBase64ImageField(required=False)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(
        many=True,
        required=True,
        source='recipe_ingredients'
    )
    author = ExtendedUserSerializer(read_only=True)
    image = CustomBase64ImageField(required=False)
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'author',
            'image', 'ingredients', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = fields


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = CustomBase64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'ingredients', 'image', 'cooking_time')

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.recreate_ingredients(recipe, ingredients)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        self.recreate_ingredients(recipe, ingredients)
        return super().update(recipe, validated_data)

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужно добавить продукты'
            })

        ingredients_list = []
        for ingredient in ingredients:
            if ingredient['ingredient'] in ingredients_list:
                raise serializers.ValidationError({
                    'ingredients': 'Продукты должны быть уникальными'
                })
            ingredients_list.append(ingredient['ingredient'])
        return data

    def recreate_ingredients(self, recipe, ingredients):
        recipe.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        )

    def to_representation(self, recipe):
        return RecipeSerializer(recipe, context=self.context).data


class GetUserSubscriptionSerializer(ExtendedUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
            'recipes',
            'recipes_count',
            'is_subscribed',
        )

    def get_recipes(self, user):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None

        if limit is not None and limit.isdigit():
            limit = int(limit)
            if limit > 0:
                recipes = user.recipes.all()[:limit]
        else:
            recipes = user.recipes.all()

        serializer = RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        )
        return serializer.data


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = ('user', 'author')

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        if UserSubscription.objects.filter(
            user=data['user'], author=data['author']
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя'
            )
        return data
