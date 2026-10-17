"""Chapter 5 p.9: send a literal HTTP request over TCP, like telnet."""
import json
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
request = ('GET /api_root/Post/ HTTP/1.1\r\nHost: 127.0.0.1:8000\r\n'
           'Accept: application/json\r\nConnection: close\r\n\r\n')
with socket.create_connection(('127.0.0.1', 8000), timeout=10) as connection:
    print('Connected to 127.0.0.1:8000 (TCP socket / telnet-compatible HTTP)')
    print('>>> REQUEST\n' + request)
    connection.sendall(request.encode('ascii'))
    response = bytearray()
    while True:
        block = connection.recv(65536)
        if not block:
            break
        response.extend(block)
headers, body = bytes(response).split(b'\r\n\r\n', 1)
assert headers.startswith(b'HTTP/1.1 200 OK'), headers
payload = json.loads(body)
assert isinstance(payload, list)
assert payload and all(k in payload[0] for k in ('author','title','text','created_date','published_date','image'))
out = ROOT / 'docs/evidence'
(out / '04-api-array.json').write_bytes(body)
text = headers.decode('iso-8859-1') + '\n\n' + json.dumps(payload, ensure_ascii=False, indent=2)
(out / '04-tcp-response.txt').write_text(request + '\n' + text)
print('<<< RESPONSE\n' + headers.decode('iso-8859-1') + '\n\n' + json.dumps(payload, ensure_ascii=False))
print(f'PASS: HTTP 200 / JSON Array / {len(payload)} posts / lecture fields present')
