import io
import math
from PIL import Image, ImageDraw
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from posts.models import Post


class Command(BaseCommand):
    help = '직접 그린 데모 풍경 3장을 생성합니다. 비밀번호는 만들지 않습니다.'

    def handle(self, *args, **options):
        user, created = get_user_model().objects.get_or_create(username='demo')
        if created:
            user.set_unusable_password()
            user.save()
        scenes = [('산의 아침', '고요한 능선 위로 새로운 하루가 밝아옵니다.', (208, 224, 211), (74, 116, 102)),
                  ('해 질 녘 바다', '파도 소리를 따라 걷던 어느 저녁.', (242, 202, 166), (77, 128, 143)),
                  ('숲으로 가는 길', '잠깐 멈추어 초록의 여유를 담았습니다.', (218, 225, 189), (58, 96, 68))]
        for index, (title, text, sky, land) in enumerate(scenes):
            if Post.objects.filter(author=user, title=title).exists():
                continue
            image = Image.new('RGB', (1200, 900), sky)
            draw = ImageDraw.Draw(image)
            draw.ellipse((820, 100, 970, 250), fill=(255, 240, 200))
            if index == 1:
                draw.rectangle((0, 400, 1200, 900), fill=land)
                for y in range(470, 900, 50):
                    draw.line((600-(y-400)//2, y, 900+(y-400)//3, y), fill=sky, width=5)
            else:
                for layer in range(3):
                    points = [(0, 900)] + [(x, int(420 + layer*145 + 110*math.sin(x/210 + layer*2))) for x in range(0, 1201, 10)] + [(1200, 900)]
                    draw.polygon(points, fill=tuple(max(0, c-layer*18) for c in land))
            buf = io.BytesIO()
            image.save(buf, format='JPEG', quality=90)
            post = Post(author=user, title=title, text=text)
            post.image.save(f'demo-{index}.jpg', ContentFile(buf.getvalue()), save=True)
        self.stdout.write(self.style.SUCCESS(f'데모 준비 완료: {Post.objects.count()}개'))
