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

## Share a hosted test version

The repository is the app's source code; it is not itself a hosted service. To share a URL, deploy this project to a Python web host that supports a `Procfile`. The app starts without credentials, so anyone who knows the deployment URL can use it. For a private test, set both of these environment variables in the host's service settings to enable HTTP Basic Auth:

- `FETCHBOX_USERNAME`: the shared login name for testers
- `FETCHBOX_PASSWORD`: a strong, unique shared password

If you set either credential, you must set both. Share the deployment's HTTPS URL and, when enabled, credentials only with your testers. Do not use the Flask development server for a public deployment.

The app also limits each server process to 60 lookups per minute, 10 downloads per hour, and 2 simultaneous downloads. These are shared limits for everyone using that deployment and reset when its process restarts; they are not a replacement for authentication or host-level quotas. Use a host with HTTPS, and do not put secrets in the repository.

## Troubleshooting

- **Downloads suddenly fail:** update yt-dlp with `py -m pip install -U yt-dlp`.
- **`pip` or `python` not recognized on Windows:** use `py -m pip` and `py` instead, or reinstall Python with "Add python.exe to PATH" ticked.
- **Use it from your phone:** install [Tailscale](https://tailscale.com) on both devices, set `FETCHBOX_USERNAME` and `FETCHBOX_PASSWORD`, then run `app.py` with `FETCHBOX_HOST=0.0.0.0`. Open `http://<your-pc-tailscale-address>:5000`.

## Notes

The server listens on `127.0.0.1` only by default, so it is not reachable from the internet. The built-in rate limits are per process, not a replacement for host-level quotas or monitoring.
