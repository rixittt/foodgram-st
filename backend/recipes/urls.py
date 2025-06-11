from django.urls import path
from . import views

app_name = 'recipes'

urlpatterns = [
    path(
        's/<int:recipe_id>/',
        views.redirect_to_recipe,
        name='redirect_to_recipe'
    ),
]
