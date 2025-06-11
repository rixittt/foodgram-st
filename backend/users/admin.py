from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import User, UserSubscription


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        'id', 'username', 'full_name', 'email', 'avatar_img',
        'recipes_count', 'subscriptions_count', 'subscribers_count',
    )
    readonly_fields = ('avatar_img',)
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_queryset(self, request):
        queryset = super().get_queryset(request).prefetch_related('recipes')
        queryset = queryset.annotate(
            _recipes_count=Count('recipes', distinct=True),
            _subscriptions_count=Count('subscribers', distinct=True),
            _subscribers_count=Count('authors', distinct=True),
        ).prefetch_related('subscribers__author', 'authors__user')
        return queryset

    @admin.display(description='ФИО')
    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_img(self, obj):
        if obj.avatar:
            return (
                f'<img src="{obj.avatar.url}"'
                f' style="height:200px;border-radius:5px;" />'
            )
        return '—'

    @admin.display(description='Рецептов')
    def recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Подписок')
    def subscriptions_count(self, obj):
        return obj.subscribers.count()

    @admin.display(description='Подписчиков')
    def subscribers_count(self, obj):
        return obj.authors.count()


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user', 'author')
