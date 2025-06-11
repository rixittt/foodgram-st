from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.db.models import OuterRef, Exists, Prefetch, Sum, F
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from djoser.views import UserViewSet as DjoserUserViewSet

from users.models import UserSubscription
from recipes.models import (
    FoodRecipe,
    FoodFavoriteRecipe,
    FoodShoppingCart,
    FoodIngredient,
    FoodRecipeIngredient
)

from .paginators import CustomPagePagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    ExtendedUserSerializer,
    UserAvatarSerializer,
    UserAvatarSerializer,
    IngredientSerializer,
    GetUserSubscriptionSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer, RecipeShortSerializer
)
from .filters import IngredientSearchFilter, RecipeSearchFilter
from .services.pdf import IngredientPDFExporter


User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    serializer_class = ExtendedUserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        return super().me(request)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated])
    def update_avatar(self, request):
        user = request.user
        if request.data.get('avatar'):
            serializer = UserAvatarSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(
            {'detail': 'Поле не заполнено'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def check_self_subscription(user, author):
        if user == author:
            raise ValidationError(
                {'error': 'Нельзя подписаться на самого себя'}
            )

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        user = request.user
        author = get_object_or_404(User, id=kwargs['id'])

        self.check_self_subscription(user, author)
        subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            author=author
        )

        if not created:
            return Response(
                {'error': 'Вы уже подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            GetUserSubscriptionSerializer(
                author, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, *args, **kwargs):
        get_object_or_404(
            UserSubscription,
            user_id=request.user.id,
            author_id=kwargs['id']
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriptions = User.objects.filter(
            authors__user=self.request.user
        ).prefetch_related(
            Prefetch(
                'recipes',
                queryset=FoodRecipe.objects.all()
            )
        )
        paginated_subscriptions = self.paginate_queryset(subscriptions)
        serializer = GetUserSubscriptionSerializer(
            paginated_subscriptions,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientSearchFilter
    queryset = FoodIngredient.objects.all()
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    pagination_class = CustomPagePagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name', 'author__username')
    filterset_class = RecipeSearchFilter

    def get_queryset(self):
        base_qs = FoodRecipe.objects.select_related('author').prefetch_related(
            'ingredients', 'recipe_ingredients__ingredient'
        )
        if self.request.user.is_authenticated:
            base_qs = base_qs.annotate(
                is_in_shopping_cart=Exists(
                    FoodShoppingCart.objects.filter(
                        user=self.request.user, recipe=OuterRef('pk')
                    )
                ),
                is_favorited=Exists(
                    FoodFavoriteRecipe.objects.filter(
                        user=self.request.user, recipe=OuterRef('pk')
                    )
                )
            )
        return base_qs

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, *args, **kwargs):
        if request.method == 'POST':
            return self.create_user_recipe_relation(
                FoodShoppingCart, self.kwargs['pk']
            )
        return self.delete_user_recipe_relation(
            FoodShoppingCart, self.kwargs['pk'])

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, *args, **kwargs):
        if request.method == 'POST':
            return self.create_user_recipe_relation(
                FoodFavoriteRecipe,
                self.kwargs['pk']
            )
        return self.delete_user_recipe_relation(
            FoodFavoriteRecipe,
            self.kwargs['pk']
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
    )
    def get_link(self, request, pk):
        get_object_or_404(FoodRecipe, id=pk)
        return Response(
            {
                'short-link': request.build_absolute_uri(
                    reverse(
                        'redirect_to_recipe',
                        kwargs={'recipe_id': pk}
                    )
                )
            },
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        pdf_creator = IngredientPDFExporter()
        ingredients = self.get_all_ingredients_for_shopping(request.user)
        pdf_creator.add_items(ingredients)
        buffer = pdf_creator.finalize()
        return FileResponse(
            buffer,
            as_attachment=True,
            filename='ingredients.pdf'
        )

    @staticmethod
    def get_all_ingredients_for_shopping(user):
        ingredients = (
            FoodRecipeIngredient.objects
            .filter(recipe__foodshoppingcart_by_users__user=user)
            .values(
                name=F('ingredient__name'),
                measurement_unit=F('ingredient__measurement_unit')
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        return ingredients

    def create_user_recipe_relation(self, model, recipe_pk):
        recipe = get_object_or_404(FoodRecipe, pk=recipe_pk)
        if model.objects.filter(
                user=self.request.user,
                recipe=recipe
        ).exists():
            raise ValidationError(
                f'Рецепт уже есть в {model._meta.verbose_name}!'
            )
        model.objects.create(
            user=self.request.user,
            recipe=recipe
        )
        serializer = RecipeShortSerializer(
            instance=recipe
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_user_recipe_relation(self, model, recipe_pk):
        get_object_or_404(
            model, user=self.request.user, recipe_id=recipe_pk
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return super().get_serializer_class()
