from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
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

    def page_test_query(self, response, find):
        """."""
        if find == 'page_obj':
            post = response.context.get(find).object_list[0]
        else:
            post = response.context.get('post')
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_index_context(self):
        """Index с правильным контекстом."""
        response = self.client.get(
            reverse('posts:index')
        )
        self.page_test_query(response, 'page_obj')

    def test_group_post_context(self):
        """Group_post с правильным контекстом."""
        response = self.client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            )
        )
        group = response.context.get('group')
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.slug, self.group.slug)

    def test_post_detail_context(self):
        """Post_detail с правильным контекстом."""
        response = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        post = response.context.get('post')
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)

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
        self.assertNotIn(Post.objects.get(), response.context['page_obj'])


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
        urls_paginator = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ),
        ]
        for url in urls_paginator:
            response = self.client.get(url)
            self.assertEqual(
                len(
                    response.context['page_obj']
                ), settings.LIMIT_POSTS
            )

    def test_second_page_contains_records(self):
        """Проверка паджинатора вторых страниц шаблонов."""
        urls_paginator = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user}
            ),
        ]
        for url in urls_paginator:
            response = self.client.get(url + '?page=2')
            self.assertEqual(
                len(
                    response.context['page_obj']
                ), settings.LIMIT_THREE
            )
