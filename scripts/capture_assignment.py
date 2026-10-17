"""Capture required evidence in actual Chrome windows, including the URL bar.
macOS screen capture permission and Chrome are required. No browser frame is drawn.
"""
import json
import re
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence'

def screen(name):
    time.sleep(1)
    subprocess.run(['/usr/sbin/screencapture', '-x', '-R0,33,1512,874', str(OUT/name)], check=True)

if __name__ == '__main__':
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=False,
            args=['--window-position=0,33', '--window-size=1512,874', '--deny-permission-prompts'])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        page.bring_to_front()
        credentials = json.loads(Path('/tmp/photoblog-test-credentials.json').read_text())
        page.goto('http://127.0.0.1:8000/api-auth/login/?next=/post/new/', wait_until='networkidle')
        page.locator('[name=username]').fill(credentials['username'])
        page.locator('[name=password]').fill(credentials['password'])
        page.locator('input[type=submit]').click()
        page.wait_for_url('**/post/new/')
        page.locator('[name=title]').fill('강의자료 POST 검증')
        page.locator('[name=text]').fill('강의 7쪽: 브라우저 입력 폼에서 사진과 설명을 multipart POST로 게시합니다.')
        page.locator('[name=image]').set_input_files('/tmp/AndroidUpload.jpg')
        screen('03-web-post-form.png')
        page.get_by_role('button', name='게시하기', exact=True).click()
        page.wait_for_url(re.compile(r'/post/\d+/$'))
        page.locator('img').wait_for()
        screen('03-web-post-detail.png')
        (OUT/'03-web-post-result.json').write_text(json.dumps({'url':page.url,'title':'강의자료 POST 검증','method':'browser multipart POST'},ensure_ascii=False,indent=2))
        page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
        screen('08-server-browser.png')
        page.goto('http://127.0.0.1:8000/api_root/Post/', wait_until='networkidle')
        screen('03-lecture-api-browser.png')
        page.goto((ROOT/'docs/coverage/index.html').as_uri(), wait_until='load')
        screen('06-coverage-html.png')
        page.goto('https://github.com/5eungwon/mwp-middleexam01', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(2000)
        screen('01-repository-structure.png')
        response = context.request.get('http://127.0.0.1:8000/api_root/Post/', headers={'Accept':'application/json'})
        array=response.json()
        assert isinstance(array,list)
        raw=json.dumps(array,ensure_ascii=False)
        (OUT/'04-api-array.json').write_text(raw)
        page.goto('https://codebeautify.org/jsonviewer',wait_until='domcontentloaded',timeout=60000)
        page.wait_for_function('window.inputJSONEditor && window.outputJSONEditor',timeout=30000)
        page.evaluate('(raw)=>inputJSONEditor.setText(raw)',raw)
        page.get_by_role('button', name='Beautify', exact=True).click()
        page.wait_for_timeout(1000)
        page.get_by_role('button', name='Validate', exact=True).click()
        page.wait_for_timeout(1000)
        screen('05-codebeautify-code.png')
        page.evaluate('outputJSONEditor.setMode("tree");outputJSONEditor.expandAll()')
        page.wait_for_timeout(500)
        screen('05-codebeautify-tree.png')
        parsed=page.evaluate('inputJSONEditor.get()')
        assert parsed==array
        (OUT/'05-codebeautify-result.json').write_text(json.dumps({'service':page.url,'json_array':True,'posts':len(parsed),'input_matches_live_api':True,'actions':['Beautify','Validate','Tree expandAll']},indent=2))
        browser.close()
