# DAVEFLIX

A local personal video library for Windows. No npm packages, account, cloud service or subscription required.

## Start on your PC

1. Install Python 3.11 or newer from https://www.python.org/downloads/windows/ if it is not already installed. Enable “Add Python to PATH” during installation.
2. Clone this repository into D:\DAVEFLIX using the commands below.
3. Double-click START_DAVEFLIX.bat. Keep the command window open.
4. Your browser opens http://127.0.0.1:8787. Click “Connect your library” and enter the full path to your video folder, for example D:\Videos.
5. Click “Scan library”. Click a title to play it.

To stop, close the command window. To restart, double-click the batch file again.

## Clone from GitHub

Run in PowerShell (if D:\DAVEFLIX does not already contain a checkout):

```powershell
git clone https://github.com/imdavidj13-droid/daveflix.git D:\DAVEFLIX
Set-Location D:\DAVEFLIX
.\START_DAVEFLIX.bat
```

For future updates, stop the server, open PowerShell in D:\DAVEFLIX and run `git pull --ff-only`, then start it again. Keep your videos outside the repository. The database and video files are excluded from Git.

## File naming

Movies can have any filename. Series episodes should use Show Name S01E01.mp4, Show Name S01E02.mp4, etc. Nested folders are scanned. Use one parent video folder containing your whole collection. Changing the configured root replaces the visible library. Rescan after adding or removing files; saved progress for files at the same path is preserved.

Matching WebVTT subtitle sidecars are supported: Show Name S01E01.vtt beside Show Name S01E01.mp4. Select subtitles in the native browser player. Embedded subtitles and embedded audio-track selection are not implemented.

MP4 with H.264 video and AAC audio is the recommended format. MKV, AVI, MOV and other codecs may not work in your browser. This version does not transcode. Convert incompatible files externally, then rescan. No files are moved, deleted or changed by scanning.

## Included

Dark red DAVEFLIX interface, responsive browsing rows, search, movie/series filters, episode lists, My List, native fullscreen video controls, seeking via HTTP ranges, progress saved every five seconds in SQLite, Continue Watching, and a next-episode button after playback ends.

The initial artwork consists of designed title cards, not downloaded posters. Profiles, metadata/poster fetching, transcoding and automatic next-episode countdown are future features, not included functionality. Progress and My List currently belong to one shared user.

## Privacy and devices

The server listens only on 127.0.0.1. Only this PC can connect. No internet upload occurs. Other-device streaming is intentionally not enabled in this version; it needs a later LAN configuration and access controls. Do not expose the server to the internet. Videos remain in your chosen folder; settings and watch history are stored in daveflix.db next to server.py. Back up that database to preserve your history.

## Verification

Server syntax and HTTP library, scan, saved-list and partial-stream operations were tested in the build environment. Windows launch, actual codec playback and visual browser QA need verification on your PC with your videos.
