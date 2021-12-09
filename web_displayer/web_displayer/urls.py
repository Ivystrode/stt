
from django.contrib import admin
from django.urls import path, include
import displayer, sentiment_display

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sentiment/', include('sentiment_display.urls'), name="sentiment_display"),
    path('', include('displayer.urls'), name="displayer"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
