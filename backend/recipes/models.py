import os
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class FoodIngredient(models.Model):
    name = models.CharField(
        'Название',
        unique=True,
        max_length=128
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class FoodRecipe(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Описание')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(1)]
    )
    ingredients = models.ManyToManyField(
        FoodIngredient,
        through='FoodRecipeIngredient',
        verbose_name='Продукты'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение'
    )

    def delete(self, *args, **kwargs):
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)

    class Meta:
        default_related_name = 'recipes'
        ordering = ['-pub_date']
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'


class FoodRecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        FoodRecipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        FoodIngredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Продукт'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]
        ordering = ('recipe', 'ingredient')
        verbose_name = 'Продукт рецепта'
        verbose_name_plural = 'Продукты рецепта'


class BaseUserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s_links',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        FoodRecipe,
        on_delete=models.CASCADE,
        related_name='%(class)s_by_users',
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique_user_recipe'
            )
        ]
        ordering = ('-id',)

    def __str__(self):
        return f'{self.user} — {self.recipe}'


class FoodFavoriteRecipe(BaseUserRecipeRelation):
    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class FoodShoppingCart(BaseUserRecipeRelation):
    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
