from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import CommentForm, PostForm
from .models import Group, Post, Follow

User = get_user_model()


def index(request):
    """Представление для отображения главной страницы."""
    post_list = Post.objects.select_related('author').select_related(
        'group').order_by('-pub_date')
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    """Представление для вывода постов в группе."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, 'paginator': paginator}
    )


class PostValidationMixin:
    """Миксин реализцющий методы валидации для формы поста."""

    def form_valid(self, form):
        """Обработка валидных данных."""
        form.instance.author = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        """Возврат сообщения об ошибке."""
        return super().render_to_response(
            self.get_context_data(form=form)
        )


class PostCreate(LoginRequiredMixin, PostValidationMixin, CreateView):
    """Представление для создания нового поста."""
    form_class = PostForm
    success_url = reverse_lazy('index')
    template_name = "new_post.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new_post'] = True
        return context


class PostEdit(LoginRequiredMixin, PermissionRequiredMixin,
               PostValidationMixin, UpdateView):
    """Представление для редактирования поста."""
    form_class = PostForm
    success_url = reverse_lazy('index')
    template_name = "new_post.html"

    def get_object(self):
        """Получение объекта редактируемого поста."""
        post_id = self.kwargs['post_id']
        username = self.kwargs['username']
        PostEdit.success_url = reverse_lazy('post', kwargs=self.kwargs)
        return get_object_or_404(Post, author__username=username, pk=post_id)

    def has_permission(self):
        """Проверка является ли пользователь автором поста."""
        return self.request.user == get_object_or_404(User, posts=self.kwargs[
            'post_id'])

    def handle_no_permission(self):
        """Редирект при попытке редактирования не своего поста."""
        return redirect(reverse_lazy('post', kwargs=self.kwargs))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new_post'] = False
        return context


def profile(request, username):
    """Представление для отображения профиля пользователя."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    following = request.user.is_authenticated and Follow.objects.filter(
        author=author,
        user=request.user).exists()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {
        'author': author,
        'page': page,
        'paginator': paginator,
        'following': following,
    })


def post_view(request, username, post_id):
    """Представление для просмотра поста."""
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = CommentForm()
    comments = post.comments.select_related('author')
    return render(request, 'post.html', {
        'post': post,
        'form': form,
        'comments': comments,
        'hide_comment_btn': True,
    })


def page_not_found(request, exception):
    """Отображает страницу 404 ошибки"""
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    """Отображает страницу 500 ошибки"""
    return render(request, "misc/500.html", status=500)


class CommentCreate(LoginRequiredMixin, CreateView):
    """Представление для создания коментария."""
    form_class = CommentForm
    template_name = "comments.html"

    def get(self, request, *args, **kwargs):
        """Возвращаем страницу просмотра поста при get-запросе."""
        return redirect(reverse_lazy('post', kwargs=self.kwargs))

    def form_valid(self, form):
        """Обработка валидных данных."""
        post_id = self.kwargs['post_id']
        self.success_url = reverse_lazy('post', kwargs=self.kwargs)
        form.instance.author = self.request.user
        form.instance.post_id = post_id
        return super().form_valid(form)


@login_required
def follow_index(request):
    """Представление ленты подписок."""
    post_list = Post.objects.filter(
        author__following__user=request.user)
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    """Представление обработчика подписки."""
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(author=author, user=user)
    return HttpResponseRedirect(reverse('profile',
                                        kwargs={'username': author}))


@login_required
def profile_unfollow(request, username):
    """Представление обработчика отписки."""
    follow = get_object_or_404(Follow, user=request.user,
                               author__username=username)
    follow.delete()
    return HttpResponseRedirect(reverse('profile',
                                        kwargs={'username': username}))
