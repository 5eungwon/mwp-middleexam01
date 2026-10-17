from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'author', 'title', 'text', 'image', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def validate_image(self, image):
        if image.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('사진은 10MB 이하여야 합니다.')
        if image.image.format not in {'JPEG', 'PNG', 'WEBP'}:
            raise serializers.ValidationError('JPEG, PNG, WEBP 사진만 업로드할 수 있습니다.')
        if image.image.width * image.image.height > 25_000_000:
            raise serializers.ValidationError('사진은 2,500만 화소 이하여야 합니다.')
        return image


class LecturePostSerializer(PostSerializer):
    """Chapter 5 JSON Array contract; keeps the lecture's field names and author ID."""
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    created_date = serializers.DateTimeField(source='created_at', read_only=True)
    published_date = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta(PostSerializer.Meta):
        fields = ['id', 'author', 'author_name', 'title', 'text', 'created_date', 'published_date', 'image']
        read_only_fields = ['id', 'author', 'author_name', 'created_date', 'published_date']
