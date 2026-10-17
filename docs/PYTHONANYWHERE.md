# PythonAnywhere 배포와 복구

서비스: https://asdfgh0986.pythonanywhere.com

새 Django 서버를 기존 주소로 전환했습니다. 이전 프로젝트 파일과 DB는 보존하며, 새 서버는 별도 DB와 미디어 폴더를 사용합니다.

## 배포 경로

| 항목 | 경로 |
| --- | --- |
| Source directory | `/home/asdfgh0986/photoblog-server-v2/PhotoBlogServer` |
| Working directory | `/home/asdfgh0986/` |
| Python / Virtualenv | 3.12 / `/home/asdfgh0986/.virtualenvs/photoblog-v2` |
| WSGI | `/var/www/asdfgh0986_pythonanywhere_com_wsgi.py` |
| 비밀 설정 | `~/.config/photoblog-v2.json` |
| 관리자 계정 설정 | `~/.config/photoblog-v2-admin.json` (권한 600, Git 미포함) |
| 이전 상태 백업 | `~/photoblog-backups/before-v2-20261017/` |

WSGI의 저장소 원본은 `PhotoBlogServer/deploy/pythonanywhere_wsgi.py`입니다. 비밀 설정 JSON에는 `project`, `hostname`, `secret_key`가 필요합니다. DEBUG는 끄고 HTTPS를 사용합니다.

| Static URL | Directory |
| --- | --- |
| `/static/` | `/home/asdfgh0986/photoblog-server-v2/PhotoBlogServer/staticfiles` |
| `/media/` | `/home/asdfgh0986/photoblog-server-v2/PhotoBlogServer/media` |

## 동작 확인

- `/`: 새 사진 갤러리.
- `/api/health/`: `status: ok`, `service: PhotoBlogServer`.
- `/api_root/Post/`: 강의 JSON Array API.
- `/api/posts/`: 페이지형 확장 API, 인증 후 multipart POST / PATCH / DELETE.
- `/api/token/`: Android 로그인 토큰 발급.
- 실제 검증 결과: `docs/evidence/12-cloud-api-verification.json`.
- 백업 DB 무결성: `docs/evidence/12-cloud-backup-check.json` (`integrity_check: ok`).
- 재검증: `python scripts/verify_cloud.py --credentials /안전한/경로/계정.json` (테스트 사진 생성 후 삭제).
- Android 실제 업로드: `Cloud Android Upload` 게시물(id 5), 서버 API에서 별도 조회해 저장 확인.
- 실제 브라우저·Android 캡처: `12-cloud-server.png`, `12-cloud-api.png`, `13-cloud-client-synced.png`.

Android 설정에서 서버 주소에 `https://asdfgh0986.pythonanywhere.com`을 입력합니다. 로그인할 관리자 비밀번호는 PythonAnywhere 로그인 비밀번호와 별개입니다. PythonAnywhere Files에서 본인 계정의 `~/.config/photoblog-v2-admin.json`을 확인하거나 콘솔에서 아래처럼 원하는 비밀번호로 변경할 수 있습니다. 비밀번호는 GitHub나 보고서에 올리지 않습니다.

```bash
source ~/.virtualenvs/photoblog-v2/bin/activate
cd ~/photoblog-server-v2/PhotoBlogServer
export DJANGO_DEBUG=0
export DJANGO_ALLOWED_HOSTS=asdfgh0986.pythonanywhere.com
export DJANGO_SECRET_KEY=$(python -c 'import json,pathlib; print(json.loads((pathlib.Path.home()/".config/photoblog-v2.json").read_text())["secret_key"])')
python manage.py changepassword photoblog-admin
```

## 이전 사이트 복구

백업에는 `old-wsgi.py`, `old-web-settings.json`, `mwp-assignment-03/`, 기존 `mysite/`가 포함됩니다. SQLite DB는 SQLite backup API로 백업했습니다. 기존 원본 프로젝트도 그대로 남아 있습니다.

1. Web 탭의 Source code를 `/home/asdfgh0986/mysite`, Working directory를 `/home/asdfgh0986/`, Virtualenv를 빈칸으로 되돌립니다. Python 버전은 3.12입니다.
2. `/static/`를 `/home/asdfgh0986/mwp-assignment-03/staticfiles`, `/media/`를 `/home/asdfgh0986/mwp-assignment-03/media`로 되돌립니다.
3. 콘솔에서 WSGI를 복구합니다.

```bash
cp ~/photoblog-backups/before-v2-20261017/old-wsgi.py /var/www/asdfgh0986_pythonanywhere_com_wsgi.py
```

4. Web 탭에서 Reload를 누릅니다. 변경 전 Force HTTPS는 꺼져 있었으며 원래 설정 전체는 `old-web-settings.json`에 기록되어 있습니다.

새 서버에 작성한 사진은 별도 DB·media에 있으므로 이전 사이트로 복구해도 삭제되지 않습니다.

계정의 웹앱 만료일은 배포 당시 **2026-10-27**입니다. 무료 계정은 Web 탭에서 기간을 연장해야 계속 접근할 수 있습니다.

공식 문서: https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/
