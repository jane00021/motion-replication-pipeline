"""Local reference-only review server. Stores human crop annotations, no rendering."""
import json, os, threading, argparse
from pathlib import Path
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PROJECT = Path(__file__).resolve().parents[2]
REVIEW = PROJECT / 'observations' / 'manual-review'
LOCK = threading.Lock()
FPS=30
TOTAL=1218

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def respond(self, status, value):
        data = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.split('?')[0] == '/api/manual-review':
            target = REVIEW / 'adjustments.json'
            self.respond(200, json.loads(target.read_text('utf-8')) if target.exists() else {'groups': None})
        elif self.path.split('?')[0].endswith(('/reference-source.mp4','/reference-browser.mp4')):
            filename = self.path.split('?')[0].rsplit('/',1)[-1]
            target = PROJECT / 'observations/decomposition-preview' / filename
            size = target.stat().st_size
            start, end = 0, size-1
            header = self.headers.get('Range')
            if header:
                try:
                    a, b = header.removeprefix('bytes=').split('-', 1)
                    start, end = int(a or 0), min(int(b) if b else size-1, size-1)
                    if not 0 <= start <= end < size:
                        raise ValueError()
                except ValueError:
                    self.send_error(416)
                    return
            self.send_response(206 if header else 200)
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Type', 'video/mp4')
            self.send_header('Content-Length', str(end-start+1))
            if header:
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.end_headers()
            try:
                with target.open('rb') as stream:
                    stream.seek(start)
                    remaining = end-start+1
                    while remaining:
                        chunk=stream.read(min(65536, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining-=len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != '/api/manual-review':
            return self.respond(404, {'error':'未找到保存入口'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size <= 0 or size > 300000:
                raise ValueError('请求长度不合法')
            value = json.loads(self.rfile.read(size))
            groups = value['groups']
            if not isinstance(groups, list) or not 1 <= len(groups) <= 100:
                raise ValueError('动效条目不合法')
            for g in groups:
                a, b = g['startFrame'], g['endFrame']
                if type(a) is not int or type(b) is not int or not 0 <= a < b <= TOTAL:
                    raise ValueError(f'起止帧须为 0 至 {TOTAL} 的整数，且起点小于终点')
                if not isinstance(g['name'], str) or not isinstance(g['members'], list):
                    raise ValueError('名称或合并关系不合法')
            value['schema'] = 1
            value['mode'] = 'human-reference-boundary-annotations'
            value['fps'] = FPS
            value['endFrameConvention'] = 'exclusive'
            value['savedAt'] = datetime.now(timezone.utc).isoformat()
            with LOCK:
                REVIEW.mkdir(parents=True, exist_ok=True)
                target = REVIEW / 'adjustments.json'
                if target.exists():
                    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
                    (REVIEW / f'history-{stamp}.json').write_bytes(target.read_bytes())
                tmp = REVIEW / 'adjustments.tmp'
                tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), 'utf-8')
                os.replace(tmp, target)
            self.respond(200, {'saved':True,'path':'observations/manual-review/adjustments.json','savedAt':value['savedAt']})
        except (ValueError, KeyError, TypeError) as exc:
            self.respond(400, {'error':str(exc)})

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,default=PROJECT)
    parser.add_argument('--port',type=int,default=8766)
    args=parser.parse_args()
    PROJECT=args.project.resolve();REVIEW=PROJECT/'observations/manual-review'
    metadata=json.loads((PROJECT/'observations/decomposition-preview/metadata.json').read_text('utf-8'))
    FPS=metadata['fps'];TOTAL=metadata['totalFrames']
    print(f'http://127.0.0.1:{args.port}/observations/decomposition-preview/index.html',flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
