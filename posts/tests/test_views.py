"""Тесты представлений."""
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Follow, Post, Group

User = get_user_model()


class ViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Установка переменных для тестирования."""
        super().setUpClass()
        # Создаём пользователя
        cls.user = User.objects.create_user(username='StasBasov')
        cls.one_more_user = User.objects.create_user(username='BasStasov')
        cls.author = User.objects.create_user(username='Author')

        # Создаем клиент и авторизуем пользователя
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.one_more_authorized_client = Client()
        cls.one_more_authorized_client.force_login(cls.one_more_user)

        # Создаём клиент без авторизации
        cls.unauthorized_client = Client()

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b')
        cls.fp = NamedTemporaryFile(mode='w+b',
                                    dir=f'{settings.MEDIA_ROOT}/posts/',
                                    suffix='.gif')
        cls.fp.write(cls.small_gif)
        cls.fp.seek(0)
        cls.img_file = cls.fp.name

        cls.group = Group.objects.create(
            title='GroupForTest',
            slug='GroupForTest',
            description='Это группа для теста',
        )
        cls.second_group = Group.objects.create(
            title='SecondGroup',
            slug='SecondGroup',
            description='Это группа для теста со сменой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Это текст поста. Вот такой скучный пост',
            group=cls.group,
        )
        cls.post_with_image = Post.objects.create(
            author=cls.user,
            text='Пост с картинкой',
            group=cls.group,
            image=cls.img_file
        )

        # Предустанавка url
        cls.index_url = reverse('index')
        cls.new_post_url = reverse('new_post')
        cls.group_url = reverse('group', kwargs={'slug': cls.group.slug})
        cls.second_group_url = reverse('group',
                                       kwargs={'slug': cls.second_group.slug})
        cls.profile_url = reverse('profile',
                                  kwargs={'username': cls.user.username})
        cls.post_url = reverse('post', kwargs={'username': cls.user.username,
                                               'post_id': cls.post.pk})
        cls.post_with_image_url = reverse('post', kwargs={
            'username': cls.user.username,
            'post_id': cls.post_with_image.pk})
        cls.post_edit_url = reverse('post_edit',
                                    kwargs={'username': cls.user.username,
                                            'post_id': cls.post.id})
        cls.login_url = reverse('login')
        cls.follow_url = reverse('follow_index')
        cls.profile_follow_url = reverse('profile_follow', kwargs={
            'username': cls.author.username})
        cls.profile_unfollow_url = reverse('profile_unfollow', kwargs={
            'username': cls.author.username})
        cls.add_comment_url = reverse('add_comment',
                                      kwargs={'username': cls.user.username,
                                              'post_id': cls.post.id})

    def test_new_post(self):
        """Проверка создания поста авторизованным пользователем."""
        current_posts_count = Post.objects.count()
        with open(self.img_file, 'rb') as img:
            response = self.authorized_client.post(self.new_post_url, {
                'text': 'Это текст публикации', 'image': img}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), current_posts_count + 1)

    def test_unauthorized_user_new_post(self):
        """
        Проверка невозможности создания поста неавторизованным пользователем.
        """
        current_posts_count = Post.objects.count()
        response = self.unauthorized_client.post(self.new_post_url, {
            'text': 'Это текст публикации'}, follow=False)
        self.assertRedirects(response,
                             f'{self.login_url}?next={self.new_post_url}',
                             status_code=302, target_status_code=200)
        self.assertEqual(Post.objects.count(), current_posts_count)

    def test_show_new_post(self):
        """Проверка отображения нового поста."""
        self.check_contains_text(self.post.text, True, self.index_url,
                                 self.group_url,
                                 self.profile_url, self.post_url)

    def test_post_edit(self):
        """Проверка редактирования поста."""
        edit_text = 'Это измененный текст поста. Его нужно найти.'
        old_text = self.post.text
        self.authorized_client.post(self.post_edit_url,
                                    {'group': self.second_group.pk,
                                     'text': edit_text}, follow=True)
        self.check_contains_text(old_text, False, self.index_url,
                                 self.group_url, self.second_group_url,
                                 self.profile_url, self.post_url)
        self.check_contains_text(edit_text, True, self.index_url,
                                 self.second_group_url, self.profile_url,
                                 self.post_url)

    def test_unauthorized_user_edit_post(self):
        """
        Проверка невозможности редактирования неавторизованным пользователем.
        """
        edit_text = "Этот текст не должен появиться в базе"
        old_text = self.post.text
        response = self.unauthorized_client.post(self.post_edit_url, {
            'group': self.second_group.pk, 'text': edit_text}, follow=False)
        self.assertRedirects(response, self.post_url, status_code=302,
                             target_status_code=200)
        self.check_contains_text(edit_text, False, self.index_url,
                                 self.group_url,
                                 self.second_group_url, self.profile_url,
                                 self.post_url)
        self.check_contains_text(old_text, True, self.index_url,
                                 self.group_url,
                                 self.profile_url, self.post_url)

    def test_show_image(self):
        """Проверка отображения картинки."""
        self.check_contains_text('<img', True, self.index_url,
                                 self.group_url,
                                 self.profile_url,
                                 self.post_with_image_url)

    def test_upload_not_image(self):
        """
        Проверка невозможности создания поста.

        Проверяется загрузка файла не-графического формата.
        """
        current_posts_count = Post.objects.count()
        with NamedTemporaryFile(mode='w+b', suffix='.jpeg') as not_img:
            not_img.write(b'I am not a picture!')
            not_img.seek(0)
            self.authorized_client.post(self.new_post_url, {
                'text': 'Пост с файлом', 'image': not_img}, follow=True)
        self.assertEqual(Post.objects.count(), current_posts_count)

    def test_cache(self):
        """Проверка работы кэша."""
        text = 'Это пост для проверки кэша'
        self.authorized_client.post(self.new_post_url, {'text': text},
                                    follow=True)
        response_from_cache = self.authorized_client.get(self.index_url)
        self.assertNotContains(response_from_cache, text)
        cache.clear()
        response = self.authorized_client.get(self.index_url)
        self.assertContains(response, text)

    def test_authorized_user_follow(self):
        """Проверка возможности подписки авторизованным пользователем."""
        current_follower_count = self.user.follower.count()
        self.authorized_client.get(self.profile_follow_url)
        self.assertEqual(self.user.follower.count(),
                         current_follower_count + 1)
        self.assertEqual(self.user.follower.last(),
                         Follow.objects.get(user=self.user,
                                            author=self.author))

    def test_authorized_user_unfollow(self):
        """Проверка возможности отписки авторизованным пользователем."""
        Follow.objects.create(user=self.user, author=self.author)
        current_follower_count = self.user.follower.count()
        self.authorized_client.get(self.profile_unfollow_url)
        self.assertEqual(self.user.follower.count(),
                         current_follower_count - 1)

    def test_follow_show(self):
        """
        Проверка отображения ленты постов.

        Проверка отображения поста в ленте у подписанного пользователя.
        """
        Follow.objects.create(user=self.user, author=self.author)
        text = "Пост пользователя Author"
        Post.objects.create(author=self.author, text=text)
        response = self.authorized_client.get(self.follow_url)
        self.assertContains(response, text)

    def test_not_follow_show(self):
        """
        Проверка отображения ленты постов.

        Проверка отсутсвия отображения поста в ленте у неподписанного
        пользователя.
        """
        text = "Пост пользователя Author"
        Post.objects.create(author=self.author, text=text)
        response = self.one_more_authorized_client.get(
            self.follow_url)
        self.assertNotContains(response, text)

    def test_authorized_user_add_comment(self):
        """
        Проверка возможности добавления комментария.

        Провека выполняется с авторизованным ользоветелем.
        """
        current_comment_count = self.post.comments.count()
        response = self.one_more_authorized_client.post(
            self.add_comment_url, {'text': 'Комментарий'}, follow=False)
        self.assertRedirects(response,
                             self.post_url,
                             status_code=302, target_status_code=200)
        self.assertEqual(self.post.comments.count(), current_comment_count + 1)

    def test_unauthorized_user_add_comment(self):
        """
        Проверка невозможности добавления комментария.

        Проверка выполняется с неавторизованным пользоветелем.
        """
        current_comment_count = self.post.comments.count()
        response = self.unauthorized_client.post(self.add_comment_url,
                                                 {'text': 'Комментарий'},
                                                 follow=False)
        self.assertRedirects(response,
                             f'{self.login_url}?next={self.add_comment_url}',
                             status_code=302, target_status_code=200)
        self.assertEqual(self.post.comments.count(), current_comment_count)

    def check_contains_text(self, text, contains, *urls):
        """Проверка наличия или отсутсвия текста в заданных url."""
        cache.clear()
        assert_func = (
            self.assertContains if contains else self.assertNotContains)
        for url in urls:
            authorized_response = self.authorized_client.get(url)
            unauthorized_response = self.unauthorized_client.get(url)
            assert_func(authorized_response, text, msg_prefix=url)
            assert_func(unauthorized_response, text, msg_prefix=url)

    @classmethod
    def tearDownClass(cls):
        cls.fp.close()
