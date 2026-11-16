// 아이콘을 누를 때만 녹음한다(사람이 누른 행동이 있어야 tabCapture 가 허락된다). 회의 화면은 건드리지 않는다.
// 녹음 중인지는 이 service worker 에 두지 않는다 — MV3 는 쉬는 동안 worker 를 내렸다 다시 올려 변수가 사라진다
// (2026-11-16 실측: 두 번째 클릭이 멈춤이 아니라 새 시작으로 처리됐다). 녹음하는 offscreen 문서에 묻는다.

async function ensureOffscreen() {
  if (await chrome.offscreen.hasDocument()) return;
  await chrome.offscreen.createDocument({ url: "offscreen.html", reasons: ["USER_MEDIA"],
    justification: "회의 탭 소리를 녹음해 로컬 수신기로 보낸다" });
}

async function setBadge(text, color) {
  await chrome.action.setBadgeText({ text });
  if (color) await chrome.action.setBadgeBackgroundColor({ color });
}

chrome.action.onClicked.addListener(async (tab) => {
  await ensureOffscreen();
  const st = await chrome.runtime.sendMessage({ to: "offscreen", cmd: "status" });
  if (st && st.recording) {
    const res = await chrome.runtime.sendMessage({ to: "offscreen", cmd: "stop" });
    await setBadge(res && res.ok ? "" : "ERR", res && res.ok ? null : "#b00020");
    await chrome.action.setTitle({ title: res && res.ok ? "회의 녹음 시작" : "멈춤 실패: " + (res && res.error) });
    return;
  }
  const streamId = await chrome.tabCapture.getMediaStreamId({ targetTabId: tab.id });
  const res = await chrome.runtime.sendMessage({ to: "offscreen", cmd: "start", streamId,
    url: tab.url, title: tab.title });
  if (!res || !res.ok) {
    await setBadge("ERR", "#b00020");
    await chrome.action.setTitle({ title: "녹음 실패: " + (res && res.error) + " — 수신기(capture/receive.py)가 켜져 있나?" });
    return;
  }
  await setBadge("REC", "#d93025");
  await chrome.action.setTitle({ title: "녹음 중 — 누르면 멈춤 (job " + res.job + ")" });
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.to === "background" && msg.cmd === "status") setBadge(msg.badge, msg.color);
});
