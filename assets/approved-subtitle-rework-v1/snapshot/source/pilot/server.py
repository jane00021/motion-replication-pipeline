"""Read-only pilot review server; byte ranges are required for reliable native video seek."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import argparse
P=Path(__file__).resolve().parents[2]
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(P),**kw)
    def do_GET(self):
        path=Path(self.translate_path(self.path)).resolve()
        if path.suffix.lower()!='.mp4' or not path.is_file():return super().do_GET()
        if not path.is_relative_to(P):return self.send_error(403)
        size=path.stat().st_size;start=0;end=size-1;r=self.headers.get('Range')
        if r:
            try:
                a,b=r.removeprefix('bytes=').split('-',1)
                if a:start=int(a);end=min(int(b) if b else end,end)
                else:start=max(0,size-int(b))
                if not 0<=start<=end<size:raise ValueError()
            except ValueError:return self.send_error(416)
        self.send_response(206 if r else 200);self.send_header('Content-Type','video/mp4');self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
        if r:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        try:
            with path.open('rb') as f:
                f.seek(start);remaining=end-start+1
                while remaining:
                    chunk=f.read(min(65536,remaining))
                    if not chunk:break
                    self.wfile.write(chunk);remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError):pass
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8768);args=ap.parse_args()
    print(f'http://127.0.0.1:{args.port}/render/pilot/index.html',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
