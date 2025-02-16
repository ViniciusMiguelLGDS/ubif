from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('autenticacao.urls')),
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),
    path('cadastros/', include('cadastros.urls')),
]

# Adiciona suporte para arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
