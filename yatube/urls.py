from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500
from django.contrib import admin
from django.contrib.flatpages import views
from django.urls import include, path

handler404 = "posts.views.page_not_found"  # noqa
handler500 = "posts.views.server_error"  # noqa

urlpatterns = [
    #  раздел администратора
    path("admin/", admin.site.urls),
    # flatpages
    path('about/', include('django.contrib.flatpages.urls')),
    #  регистрация и авторизация
    path("auth/", include("users.urls")),
    path("auth/", include("django.contrib.auth.urls")),
    #  обработчик для главной страницы ищем в urls.py приложения posts
    path("", include("posts.urls")),
]

urlpatterns += [
    path('about-author/', views.flatpage, {'url': '/about-author/'},
         name='author'),
    path('about-spec/', views.flatpage, {'url': '/about-spec/'},
         name='spec'),
    path('about-us/', views.flatpage, {'url': '/about-us/'}, name='about'),
    path('contacts/', views.flatpage, {'url': '/contacts/'}, name='contacts'),
    path('terms/', views.flatpage, {'url': '/terms/'}, name='terms'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
