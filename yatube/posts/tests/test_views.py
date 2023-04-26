from django import forms
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
        """Страница тестовая."""
        if find == 'page_obj':
            post = response.context.get(find).object_list[0]
        else:
            post = response.context.get('post')
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.group.id, self.post.group.id)

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
        self.assertEqual(group, self.post.group)
        self.page_test_query(response, 'page_obj')

    def test_post_detail_context(self):
        """Post_detail с правильным контекстом."""
        response = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        response_post = response.context.get('post')
        self.assertEqual(PostPagesTests.post, response_post)

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
                kwargs={'username': self.post.author},
            )
        ]
        for page in pages_names:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                context_post = response.context['page_obj'][0]
                self.assertEqual(context_post, self.post)

    def test_post_correct_not_appear(self):
        """Созданный пост не появляется в группе, которой не пренадлежит."""
        form_fields = {
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)

    def test_profile_correct_context(self):
        """Profile с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.author})
        )
        author = response.context.get('author')
        self.assertEqual(author, self.post.author)
        self.page_test_query(response, 'page_obj')

    def test_post_create_correct_context(self):
        """Post_create с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Post_edit с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)


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
        for i in range(settings.ALL_RECORDS_ON_PAGE):
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
            with self.subTest(url):
                response = self.client.get(url)
                self.assertEqual(
                    len(
                        response.context['page_obj']
                    ), settings.NUMBER_OF_POSTS_PER_PAGE
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
            with self.subTest(url):
                response = self.client.get(url + '?page=2')
                self.assertEqual(
                    len(
                        response.context['page_obj']
                    ), settings.SECOND_PAGE_RECORDS
                )
