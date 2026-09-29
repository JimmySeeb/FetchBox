# Fetchbox

Fetchbox is a small web app that runs on your own computer. Paste a video link, choose the video resolution or audio quality, and save the file. It works with the sites supported by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and uses a bundled copy of ffmpeg.

Only download content you own, that is Creative Commons or public domain, or that you have permission to use. Respect the terms of the sites you download from.

## Features

- Video (MP4) in every resolution the source offers, with approximate file sizes
- Audio (MP3) at 64, 128, 192 or 320 kbps
- Paste and Clear buttons, dark mode
- Permission checkbox before any download
- Temporary files are deleted after each download

## Requirements

- Python 3.9 or newer
- No separate ffmpeg install needed. It comes with `imageio-ffmpeg`.

## Run it

Download or clone this repository, open a terminal in the `fetchbox` folder, then run the commands below. On Windows use `py`. On Mac or Linux use `python3` and `pip3`.

```
py -m pip install -r requirements.txt
py app.py
```

Open http://127.0.0.1:5000 in your browser. Press `Ctrl+C` in the terminal to stop it.

## Troubleshooting

- **Downloads suddenly fail:** update yt-dlp with `py -m pip install -U yt-dlp`.
- **`pip` or `python` not recognized on Windows:** use `py -m pip` and `py` instead, or reinstall Python with "Add python.exe to PATH" ticked.
- **Use it from your phone:** install [Tailscale](https://tailscale.com) on both devices, change the last line of `app.py` to `app.run(host="0.0.0.0", port=5000)`, and open `http://<your-pc-tailscale-address>:5000`. Only do this on a private network, since the app has no login.

## Notes

The server listens on `127.0.0.1` only, so it is not reachable from the internet by default. Fetchbox is a personal tool and is not built to be hosted publicly. It has no login or usage limits.
