# 제공 자료와 구현 대조

기준: 사용자 제공 `ch05_모바일 앱으로 사용하는 기본포토블로그_v1.1.pdf` 및 Word 원본 양식.
강의 PDF는 저장소에 재배포하지 않습니다. 보고서 생성용 원본 양식은 `docs/templates/report-template.docx`입니다.

| 양식 ID | 기준 | 구현 / 증빙 |
| --- | --- | --- |
| 1–2 | ROOT 구조, GitHub push | PhotoBlogServer, PhotoViewer, 원본 양식에 작성한 보고서, Finder 캡처 및 저장소 URL |
| 3 | 7쪽 POST | /post/new/ multipart 웹 폼 → /post/{id}/ 상세, 주소창 포함 캡처 |
| 4 | 9쪽 API 검증 | scripts/verify_raw_http.py의 실제 TCP HTTP GET → JSON Array, 실제 Terminal 캡처 |
| 5 | 10쪽 CodeBeautify | 실제 codebeautify.org/jsonviewer에 TCP 응답 JSON 입력, Beautify/Validate/Tree 캡처 |
| 6 | Python 자동 테스트, Coverage | APITestCase 17개, 분기 포함 98%, docs/coverage/index.html 및 브라우저 캡처 |
| 7 | 24쪽 Socket Server | scripts/socket_capture.py가 실제 Android 요청 수신, 토큰 마스킹, .http 파일 VS Code 캡처 |
| 8–10 | 25쪽 로컬 연동 | 실제 localhost Chrome, Android 시작 및 강의 API 동기화 캡처 |
| 11 | 19쪽 Upload | UI 제공(상) 선택. onClickUpload → openEditor → uploadPost → 강의 API POST |
| 12–13 | PythonAnywhere | 새 Django 배포, 실제 HTTPS API 14개 검증, 브라우저·Android 동기화 증빙 |
| 14 | Client 편의 기능 최대 5개 | 즐겨찾기, 서버 설정, 목록 캐시, 내 사진 수정 UI, 삭제 확인 UI |

## 강의 API 계약

`GET /api_root/Post/`는 페이지 봉투 없이 JSON Array를 반환합니다. `author`는 사용자 숫자 ID이며 `title`, `text`, `created_date`, `published_date`, `image`를 제공합니다. 로컬 서버는 추가로 `id`, `author_name`을 반환합니다. 시간 필드는 내부 모델의 created_at/updated_at을 매핑한 값이며 별도의 초안/발행 워크플로는 구현하지 않았습니다.

Android는 위 경로를 기본 사용합니다. 설정의 `강의 API 사용 (JSON Array)`를 해제하면 확장 API `/api/posts/`의 페이지형 응답도 지원합니다. 기존 클라우드 서버처럼 id/author_name이 없는 응답도 읽기·사진 표시에 사용할 수 있습니다.

## 현대 Android에 맞춘 변경

- 강의 AsyncTask는 ExecutorService/Handler로 대체했습니다.
- 사진 목록은 RecyclerView + ImageAdapter로 표시합니다.
- ACTION_OPEN_DOCUMENT의 선택 파일 읽기 권한을 사용합니다. 전체 저장소 관리 권한은 요구하지 않습니다.
- HTTP는 로컬 주소만 허용하고 PythonAnywhere는 HTTPS를 사용합니다.
- 인증 토큰은 로그인으로 발급받으며 강의 예시 토큰을 복사하지 않습니다.

## 클라우드 증빙의 범위

`asdfgh0986.pythonanywhere.com`을 새 Django 서버로 전환했습니다. 강의·확장 API, 로그인, 사진 업로드·조회·수정·삭제를 실제 HTTPS 요청으로 검증했습니다. Android 동기화 캡처도 새 서버 기준입니다. 기존 프로젝트·DB 및 웹 설정은 보존했으며 경로와 복구 방법은 `PYTHONANYWHERE.md`에 기록했습니다.

## Coverage 범위

posts의 API/웹/모델/폼 코드를 측정합니다. 테스트 코드, migrations, 데모 데이터 생성 명령은 측정 대상에서 제외합니다. 실제 측정 결과는 docs/evidence/coverage.json 및 coverage-summary.txt에 있으며 수치는 변경 시 재생성해야 합니다.
