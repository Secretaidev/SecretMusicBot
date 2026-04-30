<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=700&size=28&duration=3000&pause=1000&color=00D9FF&center=true&vCenter=true&width=800&lines=Secret+Music+Bot;The+Most+Advanced+Telegram+Music+Bot" alt="Secret Music Bot">
</p>

<p align="center">
  <b>Stream high-quality music in Telegram voice chats from YouTube, Spotify, JioSaavn, SoundCloud & Live Radio — no cookies, no API keys required.</b>
</p>

<p align="center">
  <a href="https://github.com/Secretaidev/SecretMusicBot/stargazers"><img src="https://img.shields.io/github/stars/Secretaidev/SecretMusicBot?style=flat-square&color=00d9ff" alt="Stars"></a>
  <a href="https://github.com/Secretaidev/SecretMusicBot/network/members"><img src="https://img.shields.io/github/forks/Secretaidev/SecretMusicBot?style=flat-square&color=00d9ff" alt="Forks"></a>
  <a href="https://github.com/Secretaidev/SecretMusicBot/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Secretaidev/SecretMusicBot?style=flat-square&color=00d9ff" alt="License"></a>
  <a href="https://t.me/SecretzBots"><img src="https://img.shields.io/badge/Channel-Telegram-00d9ff?style=flat-square&logo=telegram" alt="Channel"></a>
</p>

---

## ✨ Features

**Multi-Platform Streaming** — YouTube · Spotify · JioSaavn · SoundCloud · Live Radio · Audio Files

| | Feature | Details |
|:--|:--------|:--------|
| 🎧 | **Voice Chat Streaming** | High-quality audio/video streaming with auto-retry & reconnection |
| 🎛 | **Audio Effects** | Bass Boost, Nightcore, Vaporwave, 8D Audio, Speed Control |
| 📜 | **Queue System** | 300-track queue with shuffle, swap, remove, pagination |
| 🔁 | **Playback Modes** | Loop One, Loop All, Shuffle, Volume 1–200% |
| ❤️ | **Personal Library** | Favourites, Play History, Custom Playlists |
| 📥 | **Downloads** | Download songs (320kbps) and videos directly to chat |
| 🔍 | **Inline Search** | Search from any chat with `@botname song name` |
| 📻 | **Live Radio** | 8 preset stations + custom stream URLs |
| ⚙️ | **Group Settings** | Per-chat quality, autoplay, auto-leave, announcements |
| 🖼 | **Now Playing Cards** | Album art, progress bar, artist info — auto-generated |
| 👮 | **Admin Tools** | Auth users, block, broadcast, sudo, maintenance mode |
| 📊 | **Statistics** | Live system stats, uptime, active streams, group count |

---

## 🚀 Quick Deploy

### Railway (Recommended)

<a href="https://railway.app/new/template?template=https://github.com/Secretaidev/SecretMusicBot"><img src="https://railway.app/button.svg" alt="Deploy on Railway"></a>

### Manual

```bash
git clone https://github.com/Secretaidev/SecretMusicBot
cd SecretMusicBot
pip install -r requirements.txt
cp .env.example .env   # fill in your credentials
python main.py
```

### Required Variables

| Variable | Description |
|:---------|:------------|
| `API_ID` | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | Telegram API Hash |
| `BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `SESSION_STRING` | Pyrogram session string (run `python generate_session.py`) |

### Optional Variables

| Variable | Description |
|:---------|:------------|
| `MONGO_DB_URI` | MongoDB URI for persistent data |
| `SPOTIFY_CLIENT_ID` | Spotify Developer Client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify Developer Secret |
| `LOG_CHANNEL` | Channel ID for bot logs |
| `MUST_JOIN` | Force-join channel username |
| `OWNER_ID` | Your Telegram user ID |

---

## 📋 Commands

<details>
<summary><b>🎵 Play</b></summary>

```
/play <name|url>     Play from YouTube
/vplay <name|url>    Play video stream
/saavn <name>        Play from JioSaavn
/spotify <name>      Search Spotify
/cplay <name>        Play from SoundCloud
/radio [station]     Stream live radio
/song <name>         Download as MP3
/video <name>        Download as video
```
</details>

<details>
<summary><b>🎮 Controls</b></summary>

```
/pause               Pause stream
/resume              Resume stream
/skip                Skip track
/stop                Stop & clear queue
/volume <1-200>      Set volume
/loop                Cycle loop mode
/shuffle             Shuffle queue
/nowplaying          Current track info
```
</details>

<details>
<summary><b>🎛 Effects</b></summary>

```
/effects             Interactive effects panel
/bass                Toggle bass boost
/nightcore           Toggle nightcore
/vaporwave           Toggle vaporwave
/8d                  Toggle 8D audio
/speed <0.5-2.0>     Playback speed
```
</details>

<details>
<summary><b>📜 Queue & Playlists</b></summary>

```
/queue               View queue (paginated)
/queue remove <n>    Remove by position
/queue swap <a> <b>  Swap tracks
/like                Like current song
/favourite           View liked songs
/history             Play history
/lyrics [name]       Find lyrics
/playlist            Manage playlists
```
</details>

<details>
<summary><b>👮 Admin</b></summary>

```
/auth                Authorise user
/unauth              Remove auth
/block / /unblock    Block from bot
/settings            Group settings panel
/joinvc / /leavevc   VC management
/broadcast           Send to all chats
/restart             Restart bot
/logs                Get log file
```
</details>

---

## 📂 Project Structure

```
├── main.py                    Entry point
├── config.py                  Configuration
├── client/
│   └── client.py              Bot + Assistant + PyTgCalls
├── plugins/                   16 command handlers
│   ├── play.py                Multi-source play engine
│   ├── controls.py            Player panel & controls
│   ├── effects.py             Audio effects panel
│   ├── queue.py               Queue management
│   ├── radio.py               Live radio streaming
│   └── ...                    start, admin, sudo, etc.
├── utils/                     11 utility modules
│   ├── yt_utils.py            YouTube (cookie-free)
│   ├── jiosaavn.py            JioSaavn API
│   ├── spotify.py             Spotify resolver
│   ├── database.py            MongoDB + fallback
│   ├── queue_manager.py       Queue engine
│   └── ...                    cache, helpers, etc.
└── requirements.txt
```

---

## 🔧 Technical Details

- **Framework:** Pyrogram 2.0 + PyTgCalls (modern MediaStream API)
- **Streaming:** Cookie-free, API-key-free — uses `yt-dlp` with `android_music` player client
- **Database:** MongoDB with automatic in-memory fallback
- **Audio:** FFmpeg transcoding, 128/192/320 kbps quality options
- **Reliability:** 3-attempt stream retry, auto-reconnect, graceful degradation

---

<p align="center">
  <b>Developed by <a href="https://t.me/its_me_secret">SECRET</a></b><br>
  <a href="https://t.me/SecretzBots">Updates</a> · <a href="https://t.me/SecretSupportChat">Support</a> · <a href="https://github.com/Secretaidev">GitHub</a>
</p>
