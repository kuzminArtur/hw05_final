from django.core.exceptions import ValidationError
from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    """Форма для создания и редактирования поста."""

    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        labels = {
            'group': 'Группа',
            'text': 'Текст',
            'image': 'Изображение',
        }
        help_texts = {
            'group': 'Выберите группу',
            'text': 'Введите текст поста',
            'image': 'Выбранная картинка отобразится в посте',
        }

    def clean_text(self):
        """Валидация длины теста поста."""
        data = self.cleaned_data['text']
        # Более интересная валидация ломает тесты((
        if len(data) < 10:
            raise ValidationError('Слишком короткий пост, нужно больше букв!')
        return data


class CommentForm(ModelForm):
    """Форма для создания комментария."""

    class Meta():
        model = Comment
        fields = ['text']
        labels = {'test': 'Текст комментария'}
        help_texts = {'text': 'Введите текст комментария'}
