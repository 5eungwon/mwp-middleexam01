from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Post
from .serializers import PostSerializer, LecturePostSerializer


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.author_id == request.user.id


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('author').all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    search_fields = ['title', 'text', 'author__username']
    ordering_fields = ['created_at', 'title']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health(request):
    return Response({'status': 'ok', 'service': 'PhotoBlogServer', 'posts': Post.objects.count()})


class LecturePostViewSet(PostViewSet):
    serializer_class = LecturePostSerializer
    pagination_class = None


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import PostForm


def post_detail(request, pk):
    return render(request, 'post_detail.html', {'post': get_object_or_404(Post.objects.select_related('author'), pk=pk)})


@login_required(login_url='/api-auth/login/')
def post_new(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('post_detail', pk=post.pk)
    return render(request, 'post_form.html', {'form': form})
