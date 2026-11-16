"""회의 녹음 확장(capture/extension)이 보내는 탭 소리를 받는 로컬 수신기. 표준 라이브러리만 쓴다.

    python capture/receive.py                                   # 녹음·받아 적기까지
    python capture/receive.py --meeting "기술 블로그 주간 회의" [--attendees "김지현, 박도윤"]
                                                                # 멈추면 inbox 에 넣기까지 — 그 뒤는 scripts/watch.sh 가 맡는다

- POST /start {url,title} → 새 job(`jobs/meet-<시각>/`)을 열고 이름을 돌려준다.
- POST /chunk {job,pcm} → 16 kHz Int16 PCM(base64)을 `audio.wav` 에 이어 쓴다(`pcm_writer.PcmWriter`).
- POST /stop {job} → WAV 를 닫고 곧바로 전사(`transcribe.py`)한다. `--meeting` 을 줬으면 받아 적기가 끝난 것만
  녹음을 시작한 시각을 일시로 해서 inbox 에 넣는다(`publish.py`). 안 줬으면 사람이 회의 이름·일시를 주고 넣는다.
- 이 PC 안(127.0.0.1)에서만 받는다. 다른 곳에서 오는 요청은 열리지 않는다.

보장하지 않는 것: 탭 소리에 회의의 모든 사람이 들어 있는지(내 마이크 소리는 탭에 없다).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pcm_writer import PcmWriter  # noqa: E402

JOBS = HERE.parent / "jobs"
PORT = 8765
DAYS = "월화수목금토일"
MEETING: dict = {}          # --meeting · --attendees
recs: dict[str, PcmWriter] = {}
started: dict[str, float] = {}
lock = threading.Lock()


def transcribe(job: str, started: float) -> None:
    r = subprocess.run([sys.executable, str(HERE / "transcribe.py"), str(JOBS / job)], capture_output=True, text=True)
    print(f"[{job}] 전사 {r.stdout.strip() or r.stderr.strip()}", flush=True)
    if r.returncode != 0 or not MEETING.get("meeting"):
        return
    t = time.localtime(started)
    when = time.strftime("%Y-%m-%d", t) + f"({DAYS[t.tm_wday]}) " + time.strftime("%H:%M", t)
    cmd = [sys.executable, str(HERE / "publish.py"), str(JOBS / job), "--meeting", MEETING["meeting"], "--when", when]
    if MEETING.get("attendees"):
        cmd += ["--attendees", MEETING["attendees"]]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"[{job}] {r.stdout.strip() or r.stderr.strip()}", flush=True)


class H(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        with lock:
            if self.path == "/start":
                job = time.strftime("meet-%Y%m%d-%H%M%S")
                d = JOBS / job
                d.mkdir(parents=True, exist_ok=True)
                (d / "job.json").write_text(json.dumps({"url": body.get("url"), "title": body.get("title"),
                    "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "via": "extension"}, ensure_ascii=False, indent=2),
                    encoding="utf-8")
                recs[job] = PcmWriter(d / "audio.wav")
                started[job] = time.time()
                print(f"[{job}] 녹음 시작 — {body.get('title')}", flush=True)
                return self._send(200, {"job": job})
            rec = recs.get(body.get("job", ""))
            if rec is None:
                return self._send(404, {"error": "모르는 job"})
            if self.path == "/chunk":
                was = rec.recording
                rec.push(body["pcm"])
                if rec.recording and not was:
                    print(f"[{body['job']}] 소리 들어옴 — {rec.first_sound}초", flush=True)
                return self._send(200, {"seconds": rec.status()["seconds"]})
            if self.path == "/stop":
                st = rec.close()
                recs.pop(body["job"], None)
                print(f"[{body['job']}] 녹음 멈춤 {json.dumps(st, ensure_ascii=False)}", flush=True)
                if st["first_sound_at"] is not None:
                    threading.Thread(target=transcribe, args=(body["job"], started.pop(body["job"], time.time())),
                                     daemon=True).start()
                else:
                    print(f"[{body['job']}] 소리가 한 번도 안 들어와 전사하지 않음", flush=True)
                return self._send(200, st)
        self._send(404, {"error": "없는 주소"})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--meeting")
    ap.add_argument("--attendees")
    MEETING.update(vars(ap.parse_args()))
    print(f"수신기 대기 — http://127.0.0.1:{PORT}  (Ctrl+C 로 끈다)", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
