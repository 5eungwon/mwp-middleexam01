"""Chapter 5 p.24: real TCP socket proxy recording the Android request headers.
Run beside Django: python scripts/socket_capture.py --port 8001
Set the Android server to http://10.0.2.2:8001, log in, then synchronize.
Passwords and request bodies are never saved. Tokens are redacted before writing.
"""
import argparse
import http.client
import json
import re
import socketserver
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence'
lock = threading.Lock()

class CaptureHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(30)
        line = self.rfile.readline(65536)
        if not line:
            return
        method, path, protocol = line.decode('iso-8859-1').strip().split(' ', 2)
        headers = http.client.parse_headers(self.rfile)
        length = int(headers.get('Content-Length', '0'))
        if length > 12 * 1024 * 1024:
            return
        body = self.rfile.read(length) if length else None
        if method == 'GET' and path.startswith('/api_root/Post/'):
            lines = [line.decode('iso-8859-1').rstrip()]
            for key, value in headers.items():
                if key.lower() in {'authorization', 'cookie'}:
                    value = 'Token [REDACTED]' if key.lower() == 'authorization' else '[REDACTED]'
                lines.append(f'{key}: {value}')
            captured = '\n'.join(lines) + '\n\n'
            with lock:
                (OUT / '07-android-request.http').write_text(captured)
                (OUT / '07-socket-metadata.json').write_text(json.dumps({
                    'source': 'Actual Android HttpURLConnection TCP request',
                    'listen_port': self.server.server_address[1],
                    'forward_to': '127.0.0.1:8000',
                    'authorization_redacted': True,
                }, indent=2))
            print(captured, flush=True)
        upstream = http.client.HTTPConnection('127.0.0.1', 8000, timeout=30)
        try:
            forwarded = {k: v for k, v in headers.items() if k.lower() != 'connection'}
            upstream.request(method, path, body=body, headers=forwarded)
            response = upstream.getresponse()
            data = response.read()
            response_headers = [(k,v) for k,v in response.getheaders() if k.lower() not in {'connection','content-length','transfer-encoding'}]
            start = f'HTTP/1.1 {response.status} {response.reason}\r\n'
            start += ''.join(f'{k}: {v}\r\n' for k,v in response_headers)
            start += f'Content-Length: {len(data)}\r\nConnection: close\r\n\r\n'
            self.wfile.write(start.encode('iso-8859-1') + data)
        finally:
            upstream.close()

class CaptureServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    with CaptureServer(('0.0.0.0', args.port), CaptureHandler) as server:
        print(f'Socket capture proxy :{args.port} -> Django :8000', flush=True)
        server.serve_forever()
