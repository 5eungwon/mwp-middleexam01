# PythonAnywhere 배포 절차

현재 검증된 서비스: https://asdfgh0986.pythonanywhere.com

- 기존 루트 블로그: HTTP 200.
- **강의 API `/api_root/Post/`: HTTP 200 / JSON Array / 사진 URL 포함.**
- `/api/posts/`, `/api/health/`는 새 확장 API이므로 기존 서버에는 없습니다.
- 새 Android 앱을 기존 HTTPS 서버와 연동해 동기화를 검증합니다. 증빙은 docs/evidence/12-cloud-server.png, 12-cloud-api.png, 13-cloud-client-synced.png입니다.

이 결과는 기존 배포 서버와 새 클라이언트의 호환 연동입니다. 저장소에 새로 구현한 Django 서버를 재배포한 것은 아닙니다. 기존 클라우드 사이트의 UI와 새 로컬 UI는 서로 다릅니다.

아래 절차는 새 Django 소스까지 클라우드에 반영하려 할 때 사용하는 별도 재배포 안내입니다. 현재 Web 탭의 Source/WSGI/Virtualenv 설정을 기록하고 기존 프로젝트 폴더는 보존한 상태에서 전환합니다.

## 1. PythonAnywhere Bash 콘솔

Python 3.12를 지원하는 환경을 선택합니다.

```bash
git clone https://github.com/5eungwon/mwp-middleexam01.git
cd ~/mwp-middleexam01
python3.12 -m venv ~/.virtualenvs/photoblog
source ~/.virtualenvs/photoblog/bin/activate
pip install -r PhotoBlogServer/requirements.txt
mkdir -p ~/.config
python - <<'PY'
import getpass, json, secrets
from pathlib import Path
hostname = input('Web 탭의 실제 도메인 (예: asdfgh0986.pythonanywhere.com): ').strip()
p = Path.home() / '.config/photoblog.json'
p.write_text(json.dumps({'hostname': hostname, 'secret_key': secrets.token_urlsafe(64)}))
p.chmod(0o600)
PY
cd PhotoBlogServer
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py collectstatic --noinput
```

## 2. Web 탭 설정

1. Add a new web app → Manual configuration → Python 3.12.
2. Source code: `/home/asdfgh0986/mwp-middleexam01/PhotoBlogServer`.
3. Virtualenv: `/home/asdfgh0986/.virtualenvs/photoblog`.
4. Web 탭의 WSGI configuration file 링크를 엽니다. 그 파일 내용을 저장소 `PhotoBlogServer/deploy/pythonanywhere_wsgi.py` 내용으로 교체합니다. 프로젝트 `config/wsgi.py`를 편집하는 것과는 다릅니다.
5. Static files 매핑:

| URL | Directory |
| --- | --- |
| `/static/` | `/home/asdfgh0986/mwp-middleexam01/PhotoBlogServer/staticfiles` |
| `/media/` | `/home/asdfgh0986/mwp-middleexam01/PhotoBlogServer/media` |

6. HTTPS를 활성화하고 Reload를 누릅니다. 이미지 업로드는 공개 갤러리용이므로 업로드 사진은 공개됩니다.

## 3. 실제 동작 확인 및 보고서 마무리

- `https://실제도메인/api/health/`: `status: ok` 확인.
- `/api/posts/`: 목록 JSON/DRF 페이지 확인.
- Android 앱 설정에서 서버 주소를 `https://실제도메인`으로 변경하고 다시 로그인합니다. 주소 변경 시 기존 토큰은 제거됩니다.
- 앱에서 업로드 → 클라우드 브라우저에서 같은 제목/사진 확인.
- 도메인 주소가 보이는 서버 화면과 Android 완료 화면을 캡처합니다.
- `docs/evidence/09-pythonanywhere.png`에 실제 캡처를 저장한 다음 `python scripts/build_report.py`를 다시 실행합니다. 실제 동작 URL도 README와 보고서에 기입합니다.

## 문제 해결

- 400 DisallowedHost: `~/.config/photoblog.json` hostname이 Web 탭의 실제 도메인과 같은지 확인 후 Reload.
- 500: Web 탭 Error log와 virtualenv/Python 버전 확인.
- 이미지 404: `/media/` 매핑과 파일 권한 확인.
- 로그인 실패: `createsuperuser`로 생성한 계정을 사용합니다. `seed_demo` 사용자는 로그인 비밀번호가 없습니다.
- 앱 연결 실패: HTTPS를 사용합니다. HTTP는 로컬 에뮬레이터/루프백 주소만 허용됩니다.

공식 문서: https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/
