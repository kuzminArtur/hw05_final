"""Тесты адресов."""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Установка переменных для тестирования."""
        super().setUpClass()
        # Устанавливаем данные для тестирования
        # Создаём пользователя
        cls.user = User.objects.create_user(username='StasBasov')
        # Создаем клиент и авторизуем пользователя
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # Создаём второй клиент, без авторизации
        cls.unauthorized_client = Client()

        # Предустанавка url
        cls.index_url = reverse('index')
        cls.new_post_url = reverse('new_post')
        cls.login_url = reverse('login')

    def test_homepage(self):
        """Проверка доступности главной страницы."""
        response = self.unauthorized_client.get(self.index_url)
        self.assertEqual(response.status_code, 200)

    def test_force_login(self):
        """
        Проверка доступности страницы /new/ для авторизованного пользователя.
        """
        # Делаем запрос к странице /new/ и проверяем статус
        response = self.authorized_client.get(self.new_post_url)
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_user_newpage(self):
        """
        Проверка доступности страницы /new/ для неавторизованного пользователя.
        """
        # Запретим редирект, чтобы увидеть, какой статус вернёт страница /new/
        response = self.unauthorized_client.get(self.new_post_url,
                                                follow=False)
        self.assertRedirects(response,
                             f'{self.login_url}?next={self.new_post_url}',
                             status_code=302, target_status_code=200)

    def test_new_user_profile(self):
        """Проверка сущетвования персональной страницы нового пользователя."""
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)

    def test_not_exist_page(self):
        """Проверка доступности главной страницы."""
        response_unauthorized = self.unauthorized_client.get('not_exist/')
        response_authorized = self.authorized_client.get('not_exist/')
        self.assertEqual(response_unauthorized.status_code, 404)
        self.assertEqual(response_authorized.status_code, 404)
