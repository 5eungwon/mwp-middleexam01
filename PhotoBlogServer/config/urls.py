from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from posts.views import PostViewSet, LecturePostViewSet, health, post_detail, post_new

router = DefaultRouter()
router.register('posts', PostViewSet)
lecture_router = DefaultRouter()
lecture_router.register('Post', LecturePostViewSet, basename='lecture-post')
urlpatterns = [
    path('api_root/', include(lecture_router.urls)),
    path('post/new/', post_new, name='post_new'),
    path('post/<int:pk>/', post_detail, name='post_detail'),
    path('', TemplateView.as_view(template_name='gallery.html'), name='gallery'),
    path('admin/', admin.site.urls),
    path('api/health/', health),
    path('api/token/', obtain_auth_token),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
