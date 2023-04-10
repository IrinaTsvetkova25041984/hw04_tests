from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


from posts.models import Post, Group

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.author = User.objects.create(username='admin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostPagesTests.author,
            group=PostPagesTests.group,
            text='Тестовый пост',
        )

    def setUp(self):
        self.user = User.objects.create(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_about_page_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны в приложении Posts."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_posts', kwargs={'slug': self.group.slug})
            ),
            'posts/profile.html': (
                reverse(
                    'posts:profile', kwargs={'username': self.user.username}
                )
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ),
            'posts/post_create.html': (
                reverse('posts:post_edit', kwargs={'post_id': self.post.id})
            ),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def assert_post_response(self):
        """Проверка Context."""
        response = self.authorized_client.get(reverse('posts:index'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_post_correct_appear(self):
        """Создание поста на страницах с выбранной группой."""
        urls = {
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            ),
        }
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertEqual(len(response.context['page_obj'].object_list), 1)

    def test_post_correct_not_appear(self):
        """Созданный пост не появляется в группе, которой не пренадлежит."""
        non_group = Group.objects.create(
            title='Дополнительная тестовая группа',
            slug='test-non-slug',
            description='Тестовое описание дополнительной группы'
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': non_group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(13):
            Post.objects.create(
                text=f'Пост {i}',
                author=cls.user,
                group=cls.group
            )

    def test_first_page_contains_ten_records(self):
        """Проверка паджинатора первых страниц шаблонов."""
        paginator_responses = [
            self.client.get(reverse('posts:index')),
            self.client.get(
                reverse('posts:group_list', kwargs={'slug': 'test-slug'})
            ),
            self.client.get(
                reverse('posts:profile', kwargs={'username': 'author'})
            ),
        ]
        for response in paginator_responses:
            self.assertEqual(len(
                response.context['page_obj']
            ), settings.LIMIT_POSTS)
