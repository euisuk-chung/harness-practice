// 탭 소리 → 16 kHz mono Int16 → 1초마다 POST /chunk. 탭 소리는 다시 스피커로도 흘려 사람이 계속 듣는다.
const SERVER = "http://127.0.0.1:8765";
const OUT_RATE = 16000;
let rec = null;

async function post(path, body) {
  const r = await fetch(SERVER + path, { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body) });
  if (!r.ok) throw new Error(path + " " + r.status);
  return r.json();
}

async function start(streamId, url, title) {
  const job = (await post("/start", { url, title })).job;
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: { mandatory: { chromeMediaSource: "tab", chromeMediaSourceId: streamId } } });
  const ctx = new AudioContext();
  const src = ctx.createMediaStreamSource(stream);
  src.connect(ctx.destination);                       // 탭이 음소거되지 않게 다시 내보낸다
  const proc = ctx.createScriptProcessor(4096, 1, 1);
  const ratio = ctx.sampleRate / OUT_RATE;
  const pending = [];
  let pos = 0;
  proc.onaudioprocess = (e) => {
    const x = e.inputBuffer.getChannelData(0);
    for (; pos < x.length; pos += ratio) {
      const v = Math.max(-1, Math.min(1, x[Math.floor(pos)]));
      pending.push(v < 0 ? v * 0x8000 : v * 0x7fff);
    }
    pos -= x.length;
  };
  src.connect(proc);
  proc.connect(ctx.destination);                      // 출력은 0 — 연결해야 onaudioprocess 가 불린다
  const timer = setInterval(async () => {
    if (!pending.length) return;
    const pcm = Int16Array.from(pending.splice(0));
    const bytes = new Uint8Array(pcm.buffer);
    let bin = "";
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    try { await post("/chunk", { job, pcm: btoa(bin) }); }
    catch (e) { chrome.runtime.sendMessage({ to: "background", cmd: "status", badge: "ERR", color: "#b00020" }); }
  }, 1000);
  rec = { job, stream, ctx, timer };
  return job;
}

async function stop() {
  if (!rec) return;
  clearInterval(rec.timer);
  rec.stream.getTracks().forEach((t) => t.stop());
  await rec.ctx.close();
  await post("/stop", { job: rec.job });
  rec = null;
}

chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  if (msg.to !== "offscreen") return;
  if (msg.cmd === "status") { reply({ recording: !!rec, job: rec && rec.job }); return; }
  const run = msg.cmd === "start" ? start(msg.streamId, msg.url, msg.title).then((job) => ({ ok: true, job }))
                                  : stop().then(() => ({ ok: true }));
  run.catch((e) => ({ ok: false, error: String(e && e.message || e) })).then(reply);
  return true;
});
