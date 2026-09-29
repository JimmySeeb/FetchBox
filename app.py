"""Fetchbox: a small local web UI around yt-dlp for saving video and audio.

Use it only for videos you own, have permission to download,
or that are Creative Commons / public domain.
Run:  py app.py   then open http://127.0.0.1:5000
"""
import os
import shutil
import tempfile
from urllib.parse import urlparse

import imageio_ffmpeg
import yt_dlp
from flask import Flask, jsonify, request, send_file

app = Flask(__name__)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
BITRATES = (64, 128, 192, 320)


def clean_error(e):
    return str(e).replace("ERROR: ", "").split("\n")[0][:300]


def valid(url):
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def coerce_int(value, default):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


@app.post("/api/info")
def info():
    url = (request.json or {}).get("url", "").strip()
    if not valid(url):
        return jsonify(error="Paste a full link starting with https://"), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": True}) as ydl:
            d = ydl.extract_info(url, download=False) or {}
    except Exception as e:
        return jsonify(error=clean_error(e)), 400

    if not isinstance(d, dict):
        return jsonify(error="Could not read that video."), 400

    heights, audio_size = {}, 0
    for f in d.get("formats") or []:
        size = f.get("filesize") or f.get("filesize_approx") or 0
        has_v = f.get("vcodec") not in (None, "none")
        has_a = f.get("acodec") not in (None, "none")
        if has_v and f.get("height") and f["height"] >= 144:
            heights[f["height"]] = max(heights.get(f["height"], 0), size)
        elif has_a and not has_v:
            audio_size = max(audio_size, size)
    video = [
        {"height": h, "size": (s + audio_size) if s else None}
        for h, s in sorted(heights.items(), reverse=True)
    ]
    duration = coerce_int(d.get("duration"), 0)
    return jsonify(
        title=d.get("title"),
        channel=d.get("uploader"),
        thumbnail=d.get("thumbnail"),
        duration=duration,
        license=d.get("license") or "Standard licence",
        video=video,
        audio_seconds=duration,
    )


@app.post("/api/download")
def download():
    data = request.json or {}
    url = str(data.get("url", "")).strip()
    kind = str(data.get("kind", "video")).lower()
    if not valid(url):
        return jsonify(error="Paste a full link starting with https://"), 400

    tmp = tempfile.mkdtemp(prefix="fetchbox_")
    opts = {
        "quiet": True,
        "noplaylist": True,
        "ffmpeg_location": FFMPEG,
        "outtmpl": os.path.join(tmp, "%(title).100s.%(ext)s"),
    }
    if kind == "audio":
        br = coerce_int(data.get("bitrate"), 192)
        br = br if br in BITRATES else 192
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": str(br)}
        ]
    else:
        h = coerce_int(data.get("height"), 4320)
        if h <= 0:
            h = 4320
        opts["format"] = (
            f"bv*[height<={h}][ext=mp4]+ba[ext=m4a]/bv*[height<={h}]+ba/b[height<={h}]/b"
        )
        opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        candidates = [
            os.path.join(tmp, name)
            for name in os.listdir(tmp)
            if os.path.isfile(os.path.join(tmp, name))
        ]
        if not candidates:
            raise FileNotFoundError("No file was produced for this download.")
        path = max(candidates, key=os.path.getmtime)
    except Exception as e:
        shutil.rmtree(tmp, ignore_errors=True)
        return jsonify(error=clean_error(e)), 400

    resp = send_file(path, as_attachment=True, download_name=os.path.basename(path))
    resp.call_on_close(lambda: shutil.rmtree(tmp, ignore_errors=True))
    return resp


@app.get("/")
def home():
    return PAGE


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fetchbox</title>
<style>
  :root { --bg:#fff; --ink:#0d0d0d; --muted:#6a6a6a; --line:#e4e4e4; --soft:#f4f4f4;
          --btn:#0d0d0d; --btn-ink:#fff; --err:#c0281d; }
  :root[data-theme=dark] { --bg:#0b0b0b; --ink:#f3f3f3; --muted:#9a9a9a; --line:#2a2a2a;
          --soft:#161616; --btn:#f3f3f3; --btn-ink:#0b0b0b; --err:#ff6b5e; }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme=light]) { --bg:#0b0b0b; --ink:#f3f3f3; --muted:#9a9a9a; --line:#2a2a2a;
          --soft:#161616; --btn:#f3f3f3; --btn-ink:#0b0b0b; --err:#ff6b5e; } }
  * { box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:16px/1.55 Inter,"Segoe UI",system-ui,sans-serif; }
  a { color:inherit; }
  .wrap { max-width:760px; margin:0 auto; padding:0 20px; }
  header { border-bottom:1px solid var(--line); }
  header .wrap { display:flex; align-items:center; justify-content:space-between; height:60px; max-width:1000px; }
  .brand { font-weight:700; font-size:1.1rem; text-decoration:none; letter-spacing:-.01em; }
  nav { display:flex; gap:22px; align-items:center; }
  nav a { text-decoration:none; color:var(--muted); font-size:.95rem; }
  nav a:hover { color:var(--ink); }
  button { font:inherit; cursor:pointer; }
  .icon { background:none; border:1px solid var(--line); color:var(--ink); border-radius:8px; padding:6px 10px; font-size:.85rem; }
  .btn { background:var(--btn); color:var(--btn-ink); border:0; border-radius:10px; padding:12px 22px; font-weight:600; }
  .btn:disabled { opacity:.4; cursor:default; }
  .ghost { background:var(--soft); color:var(--ink); border:1px solid var(--line); border-radius:8px; padding:8px 14px; font-size:.9rem; }
  :focus-visible { outline:3px solid #3b82f6; outline-offset:2px; }

  .hero { text-align:center; padding:72px 0 40px; }
  h1 { font-size:clamp(2rem,6vw,3rem); line-height:1.1; letter-spacing:-.03em; margin:0 0 12px; }
  .sub { color:var(--muted); margin:0 auto 32px; max-width:44ch; }
  .box { text-align:left; border:1px solid var(--line); border-radius:16px; padding:18px; background:var(--soft); }
  .box label.t { display:block; font-size:.85rem; color:var(--muted); margin:0 0 8px; }
  .field { display:flex; gap:8px; flex-wrap:wrap; }
  .field input { flex:1 1 220px; min-width:0; padding:12px 14px; font:inherit; color:var(--ink);
         background:var(--bg); border:1px solid var(--line); border-radius:10px; }
  #msg { min-height:1.6em; margin:12px 0 0; color:var(--muted); font-size:.95rem; }
  #msg.err { color:var(--err); }

  #result { display:none; margin-top:20px; border:1px solid var(--line); border-radius:16px; overflow:hidden; text-align:left; }
  .head { display:flex; gap:14px; padding:16px; border-bottom:1px solid var(--line); }
  .head img { width:140px; aspect-ratio:16/9; object-fit:cover; border-radius:8px; background:var(--soft); flex:none; }
  .head h2 { font-size:1.05rem; margin:0 0 4px; line-height:1.3; }
  .meta { color:var(--muted); font-size:.88rem; margin:0; }
  .pick { padding:16px; }
  .tabs { display:inline-flex; background:var(--soft); border:1px solid var(--line); border-radius:10px; padding:3px; margin-bottom:14px; }
  .tabs button { background:none; border:0; color:var(--muted); padding:7px 16px; border-radius:8px; font-weight:600; }
  .tabs button[aria-selected=true] { background:var(--btn); color:var(--btn-ink); }
  .chips { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:6px; }
  .chip { background:var(--bg); color:var(--ink); border:1px solid var(--line); border-radius:10px; padding:8px 14px; text-align:left; line-height:1.25; }
  .chip small { display:block; color:var(--muted); font-size:.78rem; }
  .chip[aria-pressed=true] { border-color:var(--ink); box-shadow:inset 0 0 0 1px var(--ink); }
  .note { color:var(--muted); font-size:.82rem; margin:8px 0 14px; }
  .own { display:flex; gap:10px; align-items:flex-start; font-size:.92rem; margin:0 0 14px; }
  .own input { margin-top:5px; }

  section.block { padding:56px 0 8px; }
  h2.s { font-size:1.5rem; letter-spacing:-.02em; margin:0 0 6px; }
  .lead { color:var(--muted); margin:0 0 24px; }
  .steps { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }
  .step { border:1px solid var(--line); border-radius:14px; padding:16px; }
  .step span { color:var(--muted); font-size:.8rem; }
  .step h3 { font-size:1rem; margin:4px 0 4px; }
  .step p { margin:0; color:var(--muted); font-size:.9rem; }
  details { border-bottom:1px solid var(--line); padding:14px 0; }
  summary { cursor:pointer; font-weight:600; }
  details p { color:var(--muted); margin:8px 0 0; }
  footer { margin-top:64px; border-top:1px solid var(--line); padding:24px 0 40px; color:var(--muted); font-size:.88rem; }
  @media (max-width:520px) { .head { flex-direction:column; } .head img { width:100%; } nav a { display:none; } }
</style>
</head>
<body>
<header><div class="wrap">
  <a class="brand" href="#top">Fetchbox</a>
  <nav><a href="#how">How it works</a><a href="#faq">FAQ</a>
    <button class="icon" id="theme" aria-label="Toggle dark mode">Dark mode</button></nav>
</div></header>

<main class="wrap" id="top">
  <div class="hero">
    <h1>Fetchbox</h1>
    <p class="sub">Save a video or its audio in the quality you choose.</p>

    <div class="box">
      <label class="t" for="url">Video link</label>
      <div class="field">
        <input id="url" type="url" placeholder="https://" autocomplete="off">
        <button class="ghost" id="paste">Paste</button>
        <button class="ghost" id="clear">Clear</button>
        <button class="btn" id="look">Look up</button>
      </div>
      <p id="msg" role="status"></p>
    </div>

    <div id="result" aria-live="polite">
      <div class="head">
        <img id="thumb" alt="">
        <div><h2 id="title"></h2><p class="meta" id="meta"></p></div>
      </div>
      <div class="pick">
        <div class="tabs" role="tablist">
          <button role="tab" id="tv" aria-selected="true">Video (MP4)</button>
          <button role="tab" id="ta" aria-selected="false">Audio (MP3)</button>
        </div>
        <div class="chips" id="chips"></div>
        <p class="note" id="note"></p>
        <label class="own"><input type="checkbox" id="own">
          <span>I own this video, or the owner has given permission to download it.</span></label>
        <button class="btn" id="go" disabled>Download</button>
      </div>
    </div>
  </div>

  <section class="block" id="how">
    <h2 class="s">How to download a video</h2>
    <p class="lead">Save a video in four steps.</p>
    <div class="steps">
      <div class="step"><span>Step 1</span><h3>Copy the link</h3><p>Copy the video's address from your browser or the Share menu.</p></div>
      <div class="step"><span>Step 2</span><h3>Paste it here</h3><p>Paste the link in the box at the top and press Look up.</p></div>
      <div class="step"><span>Step 3</span><h3>Choose quality</h3><p>Pick video or audio, then the resolution or bitrate you want.</p></div>
      <div class="step"><span>Step 4</span><h3>Save your file</h3><p>Press Download. The file goes to your Downloads folder.</p></div>
    </div>
  </section>

  <section class="block" id="faq">
    <h2 class="s">Frequently asked questions</h2>
    <details><summary>Which qualities can I choose?</summary>
      <p>Video: every resolution the source offers, from 144p up to 4K where available. Audio: MP3 at 64, 128, 192 or 320 kbps.</p></details>
    <details><summary>Why is 320 kbps not always better?</summary>
      <p>Audio is converted from the source, which is often around 128 to 160 kbps. Higher settings make a bigger file but cannot add detail that was never there.</p></details>
    <details><summary>Am I allowed to download any video?</summary>
      <p>Only save videos you own, that are Creative Commons or public domain, or that you have permission to use.</p></details>
  </section>
</main>

<footer><div class="wrap">This tool runs on your own computer. Files are deleted from the temporary folder right after they are sent to you.</div></footer>

<script>
const $ = id => document.getElementById(id);
const root = document.documentElement;
const st = {kind:"video", height:null, bitrate:192, info:null};
const say = (t, err=false) => { $("msg").textContent = t; $("msg").className = err ? "err" : ""; };
const post = (p, b) => fetch(p, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(b)});
const mb = s => !s ? "" : s > 1e9 ? "~" + (s/1e9).toFixed(1) + " GB" : "~" + Math.round(s/1048576) + " MB";
const dur = s => !s ? "" : (s >= 3600 ? Math.floor(s/3600) + ":" : "") + String(Math.floor(s%3600/60)).padStart(s >= 3600 ? 2 : 1, "0") + ":" + String(s%60).padStart(2, "0");
const label = h => h >= 2160 ? "4K" : h >= 1440 ? "1440p" : h + "p";

try { const t = localStorage.getItem("theme"); if (t) root.dataset.theme = t; } catch {}
$("theme").onclick = () => {
  const cur = root.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const next = cur === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  try { localStorage.setItem("theme", next); } catch {}
};

function chip(main, sub, on, click) {
  const b = document.createElement("button");
  b.className = "chip"; b.setAttribute("aria-pressed", on);
  b.append(main);
  if (sub) { const s = document.createElement("small"); s.textContent = sub; b.append(s); }
  b.onclick = click; return b;
}

function render() {
  const box = $("chips"); box.textContent = "";
  $("tv").setAttribute("aria-selected", st.kind === "video");
  $("ta").setAttribute("aria-selected", st.kind === "audio");
  if (st.kind === "video") {
    st.info.video.forEach(v => box.append(chip(label(v.height), mb(v.size), v.height === st.height, () => { st.height = v.height; render(); })));
    $("note").textContent = "Saved as MP4 with sound. Bigger resolutions make bigger files.";
    $("go").textContent = "Download MP4" + (st.height ? " (" + label(st.height) + ")" : "");
  } else {
    [[320, "Best"], [192, "Good"], [128, "Standard"], [64, "Small file"]].forEach(([k, n]) =>
      box.append(chip(k + " kbps", n, k === st.bitrate, () => { st.bitrate = k; render(); })));
    $("note").textContent = "Converted to MP3. Quality is limited by the original audio.";
    $("go").textContent = "Download MP3 (" + st.bitrate + " kbps)";
  }
}

$("tv").onclick = () => { st.kind = "video"; render(); };
$("ta").onclick = () => { st.kind = "audio"; render(); };
$("own").onchange = () => { $("go").disabled = !$("own").checked; };
$("paste").onclick = async () => {
  try { $("url").value = await navigator.clipboard.readText(); } catch { say("Could not read the clipboard. Paste with Ctrl+V instead.", true); }
};
$("clear").onclick = () => { $("url").value = ""; $("result").style.display = "none"; say(""); $("url").focus(); };

async function lookup() {
  $("result").style.display = "none"; $("own").checked = false; $("own").onchange();
  say("Looking up the video..."); $("look").disabled = true;
  try {
    const r = await post("/api/info", {url: $("url").value});
    const d = await r.json();
    if (!r.ok) return say(d.error, true);
    st.info = d; st.height = d.video.length ? d.video[0].height : null; st.kind = "video";
    $("thumb").src = d.thumbnail || ""; $("title").textContent = d.title;
    $("meta").textContent = [d.channel, dur(d.duration), d.license].filter(Boolean).join("  |  ");
    render(); $("result").style.display = "block"; say("");
  } catch { say("Could not reach the local server. Is app.py still running?", true); }
  finally { $("look").disabled = false; }
}

async function save() {
  $("go").disabled = true;
  say("Downloading. Longer or higher quality videos can take a few minutes...");
  const body = {url: $("url").value, kind: st.kind, height: st.height, bitrate: st.bitrate};
  try {
    const r = await post("/api/download", body);
    if (!r.ok) return say((await r.json()).error, true);
    const m = (r.headers.get("Content-Disposition") || "").match(/filename\\*?=(?:UTF-8'')?"?([^";]+)/i);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(await r.blob());
    a.download = m ? decodeURIComponent(m[1]) : (st.kind === "audio" ? "audio.mp3" : "video.mp4");
    a.click(); say("Saved to your Downloads folder.");
  } catch { say("Download failed. Check the terminal window for details.", true); }
  finally { $("own").onchange(); }
}

$("look").onclick = lookup;
$("go").onclick = save;
$("url").onkeydown = e => { if (e.key === "Enter") lookup(); };
</script>
</body>
</html>
"""

if __name__ == "__main__":
    # Bound to localhost only: this is a personal tool, not a public service.
    app.run(host="127.0.0.1", port=5000)
