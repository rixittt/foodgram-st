from django.shortcuts import redirect


def redirect_to_recipe(request, recipe_id):
    return redirect(f'/recipes/{recipe_id}/')
