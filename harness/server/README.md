# Harness server code

The MCP harness that voice Claude connects to runs on the Vultr server
(45.76.117.213) as the systemd service `harness`. This folder is the
source of truth for its code. Before 2026-10-22 the code lived only on
the server.

## What lives where

| What | Where |
|---|---|
| `server.py` (FastMCP app, Poe and DeepSeek tools) | here, deployed to `/opt/harness/server.py` |
| `repo_tools.py` (get_latest, get_file, post_to_bot, wait_for_reply, post_and_wait, post_to_code, wait_for_code_reply) | here, deployed to `/opt/harness/repo_tools.py` |
| `deploy.sh` (copies the two files above to the server) | here; run it from the bot's box |
| Python venv | server only: `/opt/harness/venv` |
| Secrets: `.env` (Poe, DeepSeek), `notify.env` (wake-up URL and key, ntfy topic), `claude.env` (Anthropic key) | **server only**, never in this repo |
| Backups of earlier live files | server only: `/opt/harness/<file>.revN` |
| Claude Code job log | server only: `/opt/harness/code_replies.md` |
| Public route | Caddy (`/etc/caddy/Caddyfile`), HTTPS with a secret path, proxied to `127.0.0.1:8000` |

The code only reads secrets from those files by path at run time. Never
copy their contents into this folder, a commit, a log or a chat.

## Waits

`wait_for_reply`, `post_and_wait` and `wait_for_code_reply` wait at most
25 s per call (`WAIT_MAX`), polling once a second. On timeout, or if
polling hits an unexpected error, they return a normal result starting
`no reply yet` that says how to call again (the `since` time or the job
id). They don't raise.

## Changing the harness

1. Edit the files here and commit them to the repo.
2. Wait for Danny's OK.
3. Run `harness/server/deploy.sh` from the bot's box. For each file it
   backs up the live copy to the next free `.revN` (it never overwrites
   one), uploads the repo copy, compiles it on the server (and puts the
   backup back if compiling fails), then restarts `harness` and shows
   its status.
4. Check the public route still works. If a tool's name, arguments or
   description changed, voice Claude needs a new chat to see it.

To roll back, copy the `.revN` backups from that run back over the live
files on the server and restart `harness`.
