from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from . import settings

urlpatterns = [
    path('', include('recipes.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns.extend(
        [
            path('__debug__/', include('debug_toolbar.urls')),
            path(
                "api-auth/", include("rest_framework.urls")
            )
        ]
    )

admin.site.site_header = 'Администрирование Foodgram'
