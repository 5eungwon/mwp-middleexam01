import io
import shutil
import tempfile
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from .models import Post


def photo(name='test.jpg'):
    stream = io.BytesIO()
    Image.new('RGB', (40, 30), (45, 105, 82)).save(stream, 'JPEG')
    return SimpleUploadedFile(name, stream.getvalue(), content_type='image/jpeg')


class PostAPITests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media = tempfile.mkdtemp()
        cls.setting = override_settings(MEDIA_ROOT=cls.media)
        cls.setting.enable()

    @classmethod
    def tearDownClass(cls):
        cls.setting.disable()
        shutil.rmtree(cls.media)
        super().tearDownClass()

    def setUp(self):
        self.owner = get_user_model().objects.create_user('owner', password='Test-password-9842')
        self.other = get_user_model().objects.create_user('other', password='Another-9842')
        self.post = Post.objects.create(author=self.owner, title='산의 아침', text='초록 산책', image=photo())

    def login(self):
        response = self.client.post('/api/token/', {'username': 'owner', 'password': 'Test-password-9842'})
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['token'])

    def test_public_paginated_list_and_detail(self):
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(response.data['results'][0]['image'].startswith('http://testserver/media/'))
        self.assertEqual(self.client.get(f'/api/posts/{self.post.pk}/').data['title'], '산의 아침')

    def test_real_token_multipart_upload_and_media(self):
        self.login()
        response = self.client.post('/api/posts/', {'title': '새 사진', 'text': '업로드 성공', 'image': photo()}, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['author'], 'owner')
        post = Post.objects.get(pk=response.data['id'])
        with post.image.open('rb') as image:
            self.assertEqual(Image.open(image).size, (40, 30))

    def test_anonymous_cannot_write(self):
        self.assertEqual(self.client.post('/api/posts/', {'title': 'x'}).status_code, 401)
        self.assertEqual(self.client.delete(f'/api/posts/{self.post.pk}/').status_code, 401)

    def test_other_user_cannot_modify_or_delete(self):
        self.client.force_authenticate(self.other)
        url = f'/api/posts/{self.post.pk}/'
        self.assertEqual(self.client.patch(url, {'title': '변경'}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)

    def test_owner_patch_and_delete(self):
        self.login()
        url = f'/api/posts/{self.post.pk}/'
        self.assertEqual(self.client.patch(url, {'title': '수정됨'}).status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, '수정됨')
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_required_and_blank_fields(self):
        self.login()
        for payload in ({'title': '사진 없음'}, {'title': '', 'image': photo()}, {'title': ' '*3, 'image': photo()}):
            with self.subTest(payload=str(payload)[:40]):
                self.assertEqual(self.client.post('/api/posts/', payload, format='multipart').status_code, 400)

    def test_invalid_image(self):
        self.login()
        bad = SimpleUploadedFile('fake.jpg', b'not-an-image', content_type='image/jpeg')
        self.assertEqual(self.client.post('/api/posts/', {'title': '위조', 'image': bad}, format='multipart').status_code, 400)

    def test_oversize_image(self):
        self.login()
        image = SimpleUploadedFile('large.jpg', photo().read() + b'0' * (10 * 1024 * 1024), content_type='image/jpeg')
        self.assertEqual(self.client.post('/api/posts/', {'title': '큼', 'image': image}, format='multipart').status_code, 400)

    def test_search_order_and_second_page(self):
        for i in range(7):
            Post.objects.create(author=self.owner, title=f'바다 {i}', image=photo())
        self.assertEqual(self.client.get('/api/posts/?search=초록').data['count'], 1)
        first = self.client.get('/api/posts/?ordering=title').data
        self.assertEqual(len(first['results']), 6)
        self.assertIsNotNone(first['next'])
        self.assertEqual(len(self.client.get('/api/posts/?page=2').data['results']), 2)
        self.assertEqual(self.client.get('/api/posts/?page=999').status_code, 404)

    def test_invalid_login_and_missing_post(self):
        self.assertEqual(self.client.post('/api/token/', {'username': 'owner', 'password': 'wrong'}).status_code, 400)
        self.assertEqual(self.client.get('/api/posts/99999/').status_code, 404)

    def test_readonly_author_and_length(self):
        self.login()
        result = self.client.post('/api/posts/', {'title': '작성자 위조 방지', 'author': 'other', 'image': photo()}, format='multipart')
        self.assertEqual(result.data['author'], 'owner')
        self.assertEqual(self.client.patch(f'/api/posts/{self.post.pk}/', {'title': 'a'*101}).status_code, 400)

    def test_gallery_and_health(self):
        self.assertContains(self.client.get('/'), '빛의 기록')
        self.assertEqual(self.client.get('/api/health/').data['status'], 'ok')

    def test_lecture_contract_array_dates_and_numeric_author(self):
        response = self.client.get('/api_root/Post/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        item = response.data[0]
        self.assertEqual(item['author'], self.owner.pk)
        self.assertEqual(item['author_name'], 'owner')
        self.assertIn('created_date', item)
        self.assertIn('published_date', item)
        self.assertEqual(self.client.get('/api_root/Post/?search=초록').data[0]['title'], '산의 아침')

    def test_lecture_multipart_put_and_delete(self):
        self.login()
        created = self.client.post('/api_root/Post/', {'title': '강의 API', 'image': photo()}, format='multipart')
        self.assertEqual(created.status_code, 201)
        url = f'/api_root/Post/{created.data["id"]}/'
        updated = self.client.put(url, {'title': '전체 교체', 'text': 'PUT 검증', 'image': photo()}, format='multipart')
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data['text'], 'PUT 검증')
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_web_form_login_create_detail_and_invalid(self):
        self.assertEqual(self.client.get('/post/new/').status_code, 302)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get('/post/new/'), '새로운 순간 게시하기')
        invalid = self.client.post('/post/new/', {'title': '', 'image': photo()}, format='multipart')
        self.assertEqual(invalid.status_code, 200)
        self.assertContains(invalid, 'errorlist')
        created = self.client.post('/post/new/', {'title': '웹 등록', 'text': '브라우저 POST', 'image': photo()}, format='multipart')
        self.assertEqual(created.status_code, 302)
        self.assertContains(self.client.get(created['Location']), '웹 등록')
        self.assertEqual(self.client.get('/post/99999/').status_code, 404)

    def test_unsupported_format_and_web_form_image_validation(self):
        self.login()
        def gif():
            stream = io.BytesIO()
            Image.new('RGB', (40, 30)).save(stream, 'GIF')
            return SimpleUploadedFile('image.gif', stream.getvalue(), content_type='image/gif')
        self.assertEqual(self.client.post('/api_root/Post/', {'title': 'GIF', 'image': gif()}, format='multipart').status_code, 400)
        self.client.force_login(self.owner)
        response = self.client.post('/post/new/', {'title': 'GIF', 'image': gif()}, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'JPEG, PNG, WEBP')

    def test_overlarge_pixel_dimensions(self):
        self.login()
        stream = io.BytesIO()
        Image.new('RGB', (5001, 5000)).save(stream, 'PNG')
        large = SimpleUploadedFile('large.png', stream.getvalue(), content_type='image/png')
        response = self.client.post('/api_root/Post/', {'title': '화소 초과', 'image': large}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertIn('2,500만', str(response.data))
