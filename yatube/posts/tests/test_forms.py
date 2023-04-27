import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создаёт запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        old_ids = [post.id for post in Post.objects.all()]
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author}
            )
        )
        new_posts = Post.objects.exclude(id__in=old_ids)
        self.assertEqual(len(new_posts), 1)
        post_latest = new_posts[0]
        self.assertEqual(post_latest.text, form_data['text'])
        self.assertEqual(post_latest.group.id, form_data['group'])
        self.assertEqual(post_latest.author, self.user)

    def test_edit_post(self):
        """Валидная форма меняет запись в Post."""
        new_group = Group.objects.create(
            title='Группа test',
            slug='test_group_2',
            description='Описание тестовой группы'
        )
        new_data = {
            'text': 'Отредактированный текст',
            'group': new_group.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data=new_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        Post.objects.filter(pk=self.post.pk).update(
            text=new_data['text'],
            group=new_group
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, new_data['text'])
        self.assertEqual(self.post.group, new_group)
        self.assertEqual(self.post.author, self.user)
