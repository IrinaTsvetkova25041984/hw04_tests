from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, User


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
            text='тестовый пост',
        )

    def setUp(self):
        self.user = User.objects.create_user(username='author')
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

    def test_correct_context(self):
        """Проверка Context."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        self.assertEqual(post_author_0, self.post.author.username)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group.title)

    def test_post_correct_appear(self):
        """Создание поста на страницах с выбранной группой."""
        pages_names = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.author},
            )
        ]
        for page in pages_names:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertIn(
                    self.post,
                    response.context['page_obj']
                )

    def test_post_correct_not_appear(self):
        """Созданный пост не появляется в группе, которой не пренадлежит."""
        non_group = Group.objects.create(
            title='Дополнительная тестовая группа',
            slug='test-non-slug',
            description='Тестовое описание дополнительной группы'
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': non_group.slug})
        )
        self.assertNotIn(Post.objects.get(id=1), response.context['page_obj'])

    def test_index_grop_list_profile_page_correct_context(self):
        """Шаблоны страниц index, group_list, profile
        с правильным контекстом.
        """
        responses = [
            self.client.get(reverse('posts:index')),
            self.client.get(
                reverse('posts:group_posts', kwargs={'slug': self.group.slug})
            ),
            self.client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.author.username}
                )
            ),
        ]
        for response in responses:
            with self.subTest(response=response):
                first_object = response.context['page_obj'][0]
                post_author_0 = first_object.author.username
                post_text_0 = first_object.text
                post_group_0 = first_object.group.title
                self.assertEqual(post_author_0, self.post.author.username)
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_group_0, self.group.title)


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
        for i in range(settings.LIMIT_ONE):
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
            with self.subTest(response=response):
                self.assertIn(
                    Post.objects.all()[0],
                    response.context['page_obj'], settings.LIMIT_POSTS
                )

    def test_second_page_contains_records(self):
        """Проверка паджинатора вторых страниц шаблонов."""
        paginator_responses = [
            self.client.get(reverse('posts:index') + '?page=2'),
            self.client.get(
                reverse(
                    'posts:group_list',
                    kwargs={'slug': 'test-slug'}
                ) + '?page=2'
            ),
            self.client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': 'author'}
                ) + '?page=2'
            ),
        ]
        for response in paginator_responses:
            with self.subTest(response=response):
                self.assertIn(
                    Post.objects.all()[10],
                    response.context['page_obj']
                )
