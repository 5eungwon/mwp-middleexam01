from django import forms
from rest_framework.exceptions import ValidationError as APIValidationError
from .models import Post
from .serializers import PostSerializer


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'image']
        labels = {'title': '제목', 'text': '이야기', 'image': '사진'}
        widgets = {'text': forms.Textarea(attrs={'rows': 4})}

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'image'):
            try:
                PostSerializer().validate_image(image)
            except APIValidationError as exc:
                raise forms.ValidationError(exc.detail)
        return image
