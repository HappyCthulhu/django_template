"""URL configuration for server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

"""
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


PREFIX = "api"


urlpatterns = [
    path(f"{PREFIX}/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(f"{PREFIX}/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path(f"{PREFIX}/admin/", admin.site.urls),
    path(f"{PREFIX}/core/", include("server.apps.core.urls")),
    path(f"{PREFIX}/auth/", include("server.apps.core.auth.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
