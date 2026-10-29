# DAVEFLIX

A Cloudflare-hosted personal streaming interface with videos supplied by your Windows PC. Cloudflare serves only the interface. Library records, My List, progress and video files live on your PC. The browser connects directly to that PC through private HTTPS using Tailscale Serve. Your PC must be awake and the Python server running while watching.

## 1. Deploy the website from this repository

In Cloudflare Workers, connect this GitHub repository and select the main branch.

- Project name: daveflix
- Build command: leave empty
- Deploy command: npx wrangler deploy
- Root directory: repository root

The included wrangler.jsonc deploys public/ as static assets. No Python runs on Cloudflare. No video files, pairing key or database are uploaded. Once deployment succeeds, copy the website URL from Cloudflare.

## 2. Get the PC server

Install Python 3.11+ and Git on Windows, then run PowerShell:

```powershell
git clone https://github.com/imdavidj13-droid/daveflix.git D:\DAVEFLIX
Set-Location D:\DAVEFLIX
.\CONFIGURE_WEBSITE.bat
```

If the repository is already cloned, stop the old server and run:

```powershell
Set-Location D:\DAVEFLIX
git pull --ff-only
.\CONFIGURE_WEBSITE.bat
```

Paste your deployed HTTPS website URL when asked. This authorizes that exact website origin. The server starts and prints your pairing key. Keep the window open and keep the key private. Future starts use START_DAVEFLIX.bat; configuration persists in connection.json. Run CONFIGURE_WEBSITE.bat again if the website address changes.

## 3. Give the PC a private HTTPS address

Install Tailscale from https://tailscale.com/download/windows on your PC. Sign in, then open a second PowerShell window and run:

```powershell
tailscale serve --bg http://127.0.0.1:8787
```

If asked to enable HTTPS, follow the link Tailscale prints. Copy the https://your-pc.your-tailnet.ts.net address shown by the command. Use `tailscale serve status` to see it again. This is private Serve, not public Funnel. Do not configure router port forwarding or expose this Python server directly to the internet.

Install Tailscale and sign in to the same private network on each device you want to watch on. The watching device needs an active Tailscale connection, including the PC itself. This version supports browser devices that can run Tailscale; smart TV support has not been implemented. Tailscale account and current plan limits apply.

## 4. Connect and watch

Open the Cloudflare DAVEFLIX website. Click Connect PC. Enter the Tailscale HTTPS server address and the pairing key printed by the Python server. After connecting, enter the folder path ON YOUR PC, for example D:\Videos, and scan. Connection credentials are stored in browser sessionStorage for that tab; reconnect in a new session. Settings gear opens connection settings; Manage library opens folder scanning. Disconnect clears credentials from the current tab.

If Windows or your browser asks permission for the website to connect to your private network, allow it for your DAVEFLIX website. If connecting fails, check Tailscale, the Python window, the exact allowed website URL, and the pairing key. This cross-origin private-network connection still needs testing in your browser on Windows; browser policy can affect access.

## Supported files and features

Movies may have any filename. Name episodes `Show Name S01E01.mp4` for series grouping and ordering. Nested folders are scanned. A matching `Show Name S01E01.vtt` provides optional WebVTT subtitles. Use one parent video folder for your whole collection. Rescan when files change. Scanning does not move or modify videos.

MP4 with H.264 video and AAC audio is recommended. Browser support for MKV, AVI, MOV and other codecs varies. Transcoding, embedded audio-track selection, downloaded poster artwork, profiles and automatic next-episode countdown are not implemented. Included: styled title cards, film/series browsing, search, My List, Continue Watching, seeking, native fullscreen controls, saved progress and a next-episode button.

The database daveflix.db, connection.json and pairing.key stay on the PC and are ignored by Git. Back up the database to preserve watch history. To rotate the pairing key, stop the server, delete pairing.key and restart; reconnect browser tabs with the new key. The key grants full access to this personal library, including changing its folder. API calls use a bearer token; native video and subtitle requests carry the key in their query string. Those query strings are excluded from server request logs, and referrers are suppressed. Do not share media URLs or pairing keys.

## Development checks

```powershell
python -m unittest discover -s tests -v
node --check public/app.js
```

Automated tests cover unauthorized access, origin restrictions, CORS preflight, library reading, partial video responses and saved progress. Cloudflare deployment, Tailscale pairing, Windows launch and actual browser codec playback require end-to-end verification on your devices.

## References

- https://developers.cloudflare.com/workers/static-assets/
- https://tailscale.com/docs/reference/tailscale-cli/serve
