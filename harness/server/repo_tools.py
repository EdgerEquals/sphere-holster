import subprocess, re, datetime
REPO = "/home/git/sphere-holster.git"
ALLOW = ("reviews/", "docs/", "logs/", "DESIGN_STATE")
LIMIT = 50000
AWST = datetime.timezone(datetime.timedelta(hours=8))

def git(*a):
    r = subprocess.run(["git", "-c", "safe.directory=*", "--git-dir", REPO, *a], capture_output=True, text=True, timeout=30)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "git error")
    return r.stdout

def newest():
    return git("for-each-ref", "--sort=-committerdate", "--count=1", "--format=%(refname:short)", "refs/heads").strip()

def register(mcp):
    @mcp.tool()
    def get_latest(branch: str = "") -> str:
        """Read logs/LATEST.md from the server copy of sphere-holster (newest branch by default), stamped with commit and AWST time."""
        return read("logs/LATEST.md", branch, 0)

    @mcp.tool()
    def get_file(path: str = "", branch: str = "", offset: int = 0) -> str:
        """Read a file or list a folder in the server copy of sphere-holster. Allowed: reviews/, docs/, logs/, DESIGN_STATE*. Empty path lists the top level. Read-only."""
        return read(path, branch, offset)


def read(path="", branch="", offset=0):
    import datetime
    def run(*a):
        r = subprocess.run(["git", "-c", "safe.directory=*", "--git-dir", REPO, *a], capture_output=True, text=True, timeout=30)
        if r.returncode:
            raise RuntimeError(r.stderr.strip() or "git failed")
        return r.stdout
    def ok(p):
        return p.split("/")[0] in ("reviews", "docs", "logs") or p.startswith("DESIGN_STATE")
    try:
        spec = (path or "").strip().strip("/")
        if ".." in spec or (spec and not ok(spec)):
            return "Not allowed. Only reviews/, docs/, logs/ and DESIGN_STATE* can be read."
        if not branch:
            heads = run("for-each-ref", "--sort=-committerdate", "--format=%(refname:short)", "refs/heads").split()
            heads = [h for h in heads if h not in ("voice-notes", "claude-code")]
            if not heads:
                return "No branches on the server copy yet."
            branch = heads[0]
        sha, ts = run("log", "-1", "--format=%h %ct", branch, "--").split()
        awst = datetime.datetime.fromtimestamp(int(ts), datetime.timezone(datetime.timedelta(hours=8)))
        head = f"[{branch} @ {sha}, committed {awst:%Y-%m-%d %H:%M} AWST]\n\n"
        ref = f"{branch}:{spec}"
        if run("cat-file", "-t", ref).strip() == "tree":
            names = []
            for line in run("ls-tree", ref).splitlines():
                meta, name = line.split("\t", 1)
                full = f"{spec}/{name}" if spec else name
                if ok(full):
                    names.append(name + ("/" if meta.split()[1] == "tree" else ""))
            return head + ("\n".join(names) or "(nothing readable here)")
        text = run("show", ref)
        part = text[offset:offset + 20000]
        if offset + 20000 < len(text):
            part += f"\n\n[more: call again with offset={offset + 20000}; {len(text)} chars total]"
        return head + part
    except Exception as e:
        return f"Error reading {path or 'top level'}: {e}"


# --- post_to_bot: voice Claude -> bot notes, on the separate voice-notes branch ---
NOTES_BRANCH = "refs/heads/voice-notes"
NOTES_FILE = "from_voice.md"
NOTE_MAX = 8000

def _gitu(*a, inp=None):
    # Run git as the git user so the bare repo never gets root-owned objects.
    r = subprocess.run(["runuser", "-u", "git", "--", "git", "--git-dir", REPO, *a],
                       input=inp, capture_output=True, text=True, timeout=30,
                       env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "GIT_AUTHOR_NAME": "voice Claude",
                            "GIT_AUTHOR_EMAIL": "voice@harness", "GIT_COMMITTER_NAME": "harness",
                            "GIT_COMMITTER_EMAIL": "harness@vultr", "HOME": "/home/git"})
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "git failed")
    return r.stdout

def post_note(text):
    text = (text or "").strip()
    if not text:
        return "Nothing posted: the note was empty."
    if len(text) > NOTE_MAX:
        return f"Nothing posted: notes are limited to {NOTE_MAX} characters."
    now = datetime.datetime.now(AWST)
    try:
        old = _gitu("rev-parse", "--verify", "-q", NOTES_BRANCH).strip()
    except RuntimeError:
        old = ""
    body = ""
    if old:
        try:
            body = _gitu("show", f"{old}:{NOTES_FILE}")
        except RuntimeError:
            body = ""
    if not body:
        body = "# Notes from voice Claude\n\nAppended by post_to_bot. Newest at the bottom. Times are AWST.\n"
    body += f"\n## {now:%Y-%m-%d %H:%M} AWST\n\n{text}\n"
    blob = _gitu("hash-object", "-w", "--stdin", inp=body).strip()
    tree = _gitu("mktree", inp=f"100644 blob {blob}\t{NOTES_FILE}\n").strip()
    args = ["commit-tree", tree, "-m", f"voice note {now:%Y-%m-%d %H:%M} AWST"]
    if old:
        args += ["-p", old]
    commit = _gitu(*args).strip()
    _gitu("update-ref", NOTES_BRANCH, commit, old or "0" * 40)
    woke = wake_bot(commit[:7])
    return f"Posted to voice-notes @ {commit[:7]} at {now:%Y-%m-%d %H:%M} AWST ({woke}). The bot also checks every 15 minutes."

_register_orig = register
def register(mcp):
    _register_orig(mcp)
    @mcp.tool()
    def post_to_bot(text: str) -> str:
        """Leave a note for Danny's Stratified Sphere bot. Appended with an AWST timestamp to from_voice.md on the voice-notes branch of the server repo; the bot checks it every 15 minutes."""
        try:
            return post_note(text)
        except Exception as e:
            return f"Error posting note: {e}"


# --- wake-up, wait_for_reply and ntfy push (2026-10-22) ---
import threading, time, json, asyncio, urllib.request
NOTIFY_FILE = "/opt/harness/notify.env"
WORK_BRANCH = "holster-loop-2026-10-19"
TO_VOICE = "logs/to_voice.md"

def _notify_cfg():
    cfg = {}
    try:
        for line in open(NOTIFY_FILE):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    except OSError:
        pass
    return cfg

def _http_post(url, data, headers, timeout=8):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status

def wake_bot(commit):
    cfg = _notify_cfg()
    url, key = cfg.get("WAKE_URL", ""), cfg.get("WAKE_KEY", "")
    if not url or not key:
        return "wake-up not configured"
    if key.lower().startswith("authorization:"):
        key = key.split(":", 1)[1].strip()
    if not key.lower().startswith("bearer "):
        key = "Bearer " + key
    try:
        _http_post(url, json.dumps({"event": "voice-note", "commit": commit}).encode(),
                   {"Content-Type": "application/json", "Authorization": key})
        return "bot woken"
    except Exception as e:
        return f"wake-up failed ({type(e).__name__}); the 15-minute check will pick it up"

def _to_voice_entries():
    try:
        text = git("show", f"{WORK_BRANCH}:{TO_VOICE}")
    except Exception:
        return []
    out, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) AWST\s*$", line)
        if m:
            cur = [m.group(1), []]
            out.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return [(t, "\n".join(b).strip()) for t, b in out]

def _ntfy_watch():
    seen = None
    while True:
        try:
            n = len(_to_voice_entries())
            if seen is None:
                seen = n
            elif n > seen:
                seen = n
                topic = _notify_cfg().get("NTFY_TOPIC", "")
                if topic:
                    try:
                        _http_post("https://ntfy.sh/" + topic, b"bot replied", {"Title": "bot replied"})
                    except Exception:
                        pass
        except Exception:
            pass
        time.sleep(30)

WAIT_MAX = 25  # seconds per wait call; callers poll again with the returned since/job

def _cap(t):
    try:
        t = int(t)
    except Exception:
        t = WAIT_MAX
    return max(1, min(t, WAIT_MAX))

def _short(e):
    return (type(e).__name__ + ": " + str(e)).splitlines()[0][:200]

_register_prev = register
def register(mcp):
    _register_prev(mcp)
    threading.Thread(target=_ntfy_watch, daemon=True).start()

    @mcp.tool()
    async def wait_for_reply(since: str = "", timeout: int = 60) -> str:
        """Wait for the bot's reply in logs/to_voice.md (server copy of the working branch). Returns entries newer than `since` ("YYYY-MM-DD HH:MM" AWST; empty means now), or "no reply yet" after `timeout` seconds (max 25; call again with the `since` it gives if nothing yet). `since` may be "YYYY-MM-DD HH:MM" or "YYYY-MM-DD HH:MM:SS"; entries in the same minute count as new. Meant for quick acknowledgements; replies that need Danny's decision come later."""
        base = None
        if not since:
            since = datetime.datetime.now(AWST).strftime("%Y-%m-%d %H:%M")
            base = len(_to_voice_entries())
        since = since.replace("T", " ").replace(" AWST", "").strip()[:16]
        end = time.monotonic() + _cap(timeout)
        again = f'call wait_for_reply(since="{since}") again'
        try:
            while True:
                ents = _to_voice_entries()
                new = ents[base:] if base is not None else [(t, b) for t, b in ents if t >= since]
                if new:
                    return "\n\n".join(f"## {t} AWST\n\n{b}" for t, b in new)
                if time.monotonic() >= end:
                    return f"no reply yet (nothing in {TO_VOICE} newer than {since} AWST); {again}"
                await asyncio.sleep(1)
        except Exception as e:
            return f"no reply yet (error: {_short(e)}); {again}"

# --- Claude Code bridge + post_and_wait (added 2026-10-22, backup repo_tools.py.rev8) ---
import os, pwd, shutil
CODE_USER = "claudecode"
CODE_CLONE = "/home/claudecode/sphere-holster"
CODE_ENV = "/opt/harness/claude.env"
CODE_BRANCH = "claude-code"
CODE_REPLIES = "/opt/harness/code_replies.md"
CODE_TOOLS = "Read,Edit,Write,Grep,Glob,Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git add:*),Bash(git commit:*)"
CODE_TIMEOUT = 900
RUNUSER = "/usr/sbin/runuser"
_code_lock = threading.Lock()
_code_jobs = {}

def _code_missing():
    m = []
    try:
        pwd.getpwnam(CODE_USER)
    except KeyError:
        m.append(f"user {CODE_USER}")
    if not (shutil.which("claude", path="/usr/local/bin:/usr/bin:/bin")):
        m.append("claude CLI")
    if not os.path.isfile(CODE_ENV):
        m.append(CODE_ENV)
    return m

def _code_env():
    env = {"HOME": f"/home/{CODE_USER}", "USER": CODE_USER, "PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"}
    for line in open(CODE_ENV):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.strip().split("=", 1)
            if k == "ANTHROPIC_API_KEY":
                env[k] = v.strip().strip('"')
    return env

def _rootgit(*a, cwd=None):
    r = subprocess.run(["git", "-c", "safe.directory=*", *a], cwd=cwd, capture_output=True, text=True, timeout=60)
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[-500:])
    return r.stdout.strip()

def _prep_clone():
    if not os.path.isdir(CODE_CLONE + "/.git"):
        _rootgit("clone", "--no-hardlinks", REPO, CODE_CLONE)
        _rootgit("checkout", "-B", CODE_BRANCH, f"origin/{WORK_BRANCH}", cwd=CODE_CLONE)
        _rootgit("config", "user.name", "Claude Code (server)", cwd=CODE_CLONE)
        _rootgit("config", "user.email", "claudecode@sphere-holster.local", cwd=CODE_CLONE)
    else:
        _rootgit("fetch", "-q", "origin", cwd=CODE_CLONE)
    subprocess.run(["chown", "-R", f"{CODE_USER}:{CODE_USER}", CODE_CLONE], check=True)

def _publish_clone():
    head = _rootgit("rev-parse", "HEAD", cwd=CODE_CLONE)
    try:
        cur = git("rev-parse", f"refs/heads/{CODE_BRANCH}")
    except Exception:
        cur = ""
    if head == cur:
        return ""
    _rootgit("--git-dir", REPO, "fetch", "-q", CODE_CLONE, f"+{CODE_BRANCH}:refs/heads/{CODE_BRANCH}")
    subprocess.run(["chown", "-R", "git:git", REPO], check=True)
    return head[:7]

def _run_code(jid, text):
    j = _code_jobs[jid]
    with _code_lock:
        j["status"] = "running"
        try:
            _prep_clone()
            r = subprocess.run([RUNUSER, "-u", CODE_USER, "--", "claude", "-p", text,
                                "--allowedTools", CODE_TOOLS, "--permission-mode", "acceptEdits",
                                "--output-format", "text"],
                               cwd=CODE_CLONE, env=_code_env(), capture_output=True, text=True, timeout=CODE_TIMEOUT)
            out = (r.stdout or "").strip() or ("(no output) " + (r.stderr or "")[-1500:])
            pushed = _publish_clone()
            j["reply"] = out[:20000] + (f"\n\n[committed to branch {CODE_BRANCH} @ {pushed}]" if pushed else "")
            j["status"] = "done"
        except subprocess.TimeoutExpired:
            j["status"], j["reply"] = "timeout", f"Claude Code timed out after {CODE_TIMEOUT} s."
        except Exception as e:
            j["status"], j["reply"] = "error", f"Claude Code error: {e}"
        j["finished"] = datetime.datetime.now(AWST).strftime("%H:%M:%S")
        try:
            with open(CODE_REPLIES, "a") as f:
                f.write(f"\n## job {jid} ({j['status']}, finished {j['finished']} AWST)\n\nAsked: {text[:300]}\n\n{j['reply']}\n")
        except Exception:
            pass

async def _await_job(jid, timeout):
    end = time.monotonic() + _cap(timeout)
    again = f'call wait_for_code_reply(job="{jid}") again'
    try:
        while True:
            j = _code_jobs.get(jid)
            if j is None:
                return f"No Claude Code job {jid} (jobs are forgotten on a harness restart; see {CODE_REPLIES})."
            if j["status"] in ("done", "timeout", "error"):
                return f"[job {jid}, {j['status']}, finished {j['finished']} AWST]\n\n{j['reply']}"
            if time.monotonic() >= end:
                return f"no reply yet (Claude Code job {jid} is still {j['status']}); {again}"
            await asyncio.sleep(1)
    except Exception as e:
        return f"no reply yet (error: {_short(e)}); {again}"

_register_prev2 = register
def register(mcp):
    _register_prev2(mcp)

    @mcp.tool()
    async def post_to_code(text: str, wait: int = 25) -> str:
        """Send a task to headless Claude Code on the server ("ping code"). It works in its own clone of sphere-holster and may read, edit and commit there (no push, no shell beyond git status/diff/log/add/commit); commits are published to the claude-code branch. Waits up to `wait` seconds (max 25) for the answer; if it isn't done, returns a job id for wait_for_code_reply. One job runs at a time."""
        missing = _code_missing()
        if missing:
            return "Claude Code isn't set up on the server yet. Missing: " + ", ".join(missing)
        if len(text) > 8000:
            return "Task too long (max 8000 characters)."
        jid = datetime.datetime.now(AWST).strftime("%H%M%S")
        while jid in _code_jobs:
            jid += "b"
        _code_jobs[jid] = {"status": "queued", "reply": "", "finished": ""}
        threading.Thread(target=_run_code, args=(jid, text), daemon=True).start()
        return await _await_job(jid, wait)

    @mcp.tool()
    async def wait_for_code_reply(job: str = "", timeout: int = 25) -> str:
        """Wait up to `timeout` seconds (max 25) for a Claude Code job started with post_to_code. Empty `job` means the most recent one."""
        if not job:
            if not _code_jobs:
                return "No Claude Code jobs since the last harness restart."
            job = list(_code_jobs)[-1]
        return await _await_job(job, timeout)

    @mcp.tool()
    async def post_and_wait(text: str, timeout: int = 25) -> str:
        """post_to_bot and wait_for_reply in one call: leaves the note for the bot, then waits up to `timeout` seconds (max 25) for the bot's reply in logs/to_voice.md. Test pings are usually answered in about 6 s; anything needing Danny's decision comes later (call wait_for_reply)."""
        base = len(_to_voice_entries())
        since = datetime.datetime.now(AWST).strftime("%Y-%m-%d %H:%M")
        try:
            posted = await asyncio.to_thread(post_note, text)
        except Exception as e:
            return f"Error posting note: {_short(e)}"
        end = time.monotonic() + _cap(timeout)
        again = f'call wait_for_reply(since="{since}")'
        try:
            while True:
                new = _to_voice_entries()[base:]
                if new:
                    return posted + "\n\n" + "\n\n".join(f"## {t} AWST\n\n{b}" for t, b in new)
                if time.monotonic() >= end:
                    return posted + f"\n\nno reply yet; {again}"
                await asyncio.sleep(1)
        except Exception as e:
            return posted + f"\n\nno reply yet (error: {_short(e)}); {again}"
