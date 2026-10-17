"""Real HTTP CRUD verification, separate from Django in-process tests. No tokens in evidence."""
import html
import io
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'PhotoBlogServer'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

user, _ = get_user_model().objects.get_or_create(username='http-verifier')
user.set_unusable_password()
user.save()
token, _ = Token.objects.get_or_create(user=user)
records = []

def call(method, path, expected, body=None, content_type=None, auth=True):
    headers = {'Accept': 'application/json'}
    if auth: headers['Authorization'] = 'Token ' + token.key
    if content_type: headers['Content-Type'] = content_type
    req = urllib.request.Request('http://127.0.0.1:8000' + path, data=body, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as exc:
        response = exc
    raw = response.read()
    value = json.loads(raw) if raw else None
    records.append({'request': f'{method} {path}', 'expected': expected, 'actual': response.status, 'response': value})
    assert response.status == expected, records[-1]
    return value

call('GET', '/api/health/', 200, auth=False)
call('GET', '/api/posts/', 200, auth=False)
call('POST', '/api/posts/', 401, b'{}', 'application/json', auth=False)
call('POST', '/api/posts/', 400, b'{"title":"missing image"}', 'application/json')
image = io.BytesIO()
Image.new('RGB', (120, 90), '#315c44').save(image, 'PNG')
boundary = 'PhotoBlogVerification'
body = (f'--{boundary}\r\nContent-Disposition: form-data; name="title"\r\n\r\nHTTP CRUD 검증\r\n'
        f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="test.png"\r\nContent-Type: image/png\r\n\r\n').encode() + image.getvalue() + f'\r\n--{boundary}--\r\n'.encode()
created = call('POST', '/api/posts/', 201, body, 'multipart/form-data; boundary=' + boundary)
path = f'/api/posts/{created["id"]}/'
call('GET', path, 200, auth=False)
call('PATCH', path, 200, json.dumps({'title': 'HTTP 수정 완료'}).encode(), 'application/json')
call('DELETE', path, 204)
call('GET', path, 404, auth=False)
out = ROOT / 'docs/evidence'
(out / 'http-results.json').write_text(json.dumps(records, ensure_ascii=False, indent=2))
for name, title, rows in [
    ('02-api-validation', 'API 검증 (2/3) · 조회 / 인증 / 입력 검증 / 업로드', records[:5]),
    ('03-api-validation', 'API 검증 (3/3) · 상세 / 수정 / 삭제 / 404', records[5:]),
]:
    display = json.loads(json.dumps(rows))
    for row in display:
        if isinstance(row['response'], dict) and 'results' in row['response']:
            row['response'] = {'count': row['response']['count'], 'results': '목록 본문: http-results.json 참조'}
    text = json.dumps(display, ensure_ascii=False, indent=2)
    (out / (name + '.html')).write_text('<meta charset="utf-8"><style>body{padding:30px;background:#f4f3ee;color:#253c2c;font:16px monospace}pre{white-space:pre-wrap;background:white;padding:24px;border-radius:12px}</style><h1>' + title + '</h1><p>실제 HTTP 요청과 응답 · expected = actual 확인</p><pre>' + html.escape(text) + '</pre>')
print('Real HTTP checks: 9/9 PASS')
