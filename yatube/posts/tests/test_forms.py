import shutil
import tempfile

from posts.forms import PostForm
from posts.models import Post, Group, User
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse


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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.form_data = {
            'text': 'Тестовый текст',
            'group.id': 'Тестовая группа',
            'image': uploaded
        }
        self.guest_client = Client()
        self.user = User.objects.create(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.expected_post = 'Пост отредактирован гостем'

    def test_create_post(self):
        """Валидная форма создаёт запись в Post."""
        posts_count = Post.objects.count()
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            id=1,
        ).exists())

    def test_edit_post(self):
        """Валидная форма меняет запись в Post."""
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=self.form_data,
            follow=True
        )
        self.post.save()
        post = Post.objects.get(id=1)
        self.assertEqual(post.text, self.post.text)
        self.assertTrue(Post.objects.filter(id=1).exists())
