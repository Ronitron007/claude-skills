#!/usr/bin/env python3
"""Voiceover via Instinct on WhatsApp, through the Cadbury Matrix bridge.

Commands:
  check                      services, Synapse, WhatsApp login, Instinct room
  up                         start any Cadbury launchd service that is not running
  compose FILE [--tone T]    print the exact WhatsApp message (no send)
  send FILE [--tone T] [--name N] [--timeout S]
                             send the message, wait for Instinct's voice note(s),
                             download them into ~/Voiceovers/
"""
import argparse, json, os, re, sqlite3, subprocess, sys, time, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

REPO = Path.home() / "matrix-claude-bridge"
HS = "http://127.0.0.1:8008"
ME = "@rohan:cadbury.local"
INSTINCT_PN = "16508702892"
OUT_DIR = Path.home() / "Voiceovers"
SERVICES = ["synapse", "meta", "whatsapp", "listener"]
WA_DB = REPO / "bridges/whatsapp/bridge.db"

PREMISE = (
    "Voiceover request. I need voiceover work for a project. "
    "Please read the script below aloud and send it back as a voice note. "
    "Read it exactly as written: no intro, no outro, no commentary, no changes to the words.{tone}\n\n"
    "Script:\n{script}"
)


def token() -> str:
    return (REPO / "state/rohan_token.txt").read_text().strip()


def api(method: str, path: str, body: dict | None = None, raw: bool = False):
    req = urllib.request.Request(
        HS + path, method=method,
        headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body is not None else None,
    )
    with urllib.request.urlopen(req, timeout=30) as f:
        data = f.read()
    return data if raw else json.loads(data or b"{}")


def q(s: str) -> str:
    return urllib.parse.quote(s, safe="")


def instinct_ids() -> tuple[str, str]:
    """Return (room_id, instinct_ghost_mxid) resolved from the bridge DB."""
    db = sqlite3.connect(f"file:{WA_DB}?mode=ro", uri=True)
    row = db.execute("select lid from whatsmeow_lid_map where pn=?", (INSTINCT_PN,)).fetchone()
    if not row:
        sys.exit(f"Instinct (+{INSTINCT_PN}) not found in bridge contacts. Is WhatsApp logged in?")
    lid = row[0]
    room = db.execute("select mxid from portal where id=?", (f"{lid}@lid",)).fetchone()
    if not room or not room[0]:
        sys.exit("No Matrix room for the Instinct chat yet. Send it any message from the phone, then retry.")
    return room[0], f"@whatsapp_lid-{lid}:cadbury.local"


def running_services() -> dict[str, bool]:
    out = subprocess.run(["launchctl", "list"], capture_output=True, text=True).stdout
    state = {}
    for s in SERVICES:
        line = next((l for l in out.splitlines() if l.endswith(f"com.rohan.cadbury.{s}")), None)
        state[s] = bool(line) and line.split()[0] != "-"
    return state


def cmd_check(_: argparse.Namespace) -> int:
    ok = True
    for s, up in running_services().items():
        print(f"service {s:9} {'running' if up else 'DOWN'}")
        ok &= up
    try:
        api("GET", "/_matrix/client/versions")
        print("synapse   reachable")
    except Exception as e:
        print(f"synapse   UNREACHABLE ({e})"); return 1
    logins = sqlite3.connect(f"file:{WA_DB}?mode=ro", uri=True).execute("select count(*) from user_login").fetchone()[0]
    print(f"whatsapp  {'logged in' if logins else 'NOT LOGGED IN (DM @whatsappbot: login qr, scan in WhatsApp > Linked Devices)'}")
    ok &= bool(logins)
    if logins:
        room, ghost = instinct_ids()
        print(f"instinct  room {room}")
    return 0 if ok else 1


def cmd_up(_: argparse.Namespace) -> int:
    uid = os.getuid()
    for s, up in running_services().items():
        if up:
            continue
        label = f"com.rohan.cadbury.{s}"
        plist = Path.home() / f"Library/LaunchAgents/{label}.plist"
        r = subprocess.run(["launchctl", "kickstart", f"gui/{uid}/{label}"], capture_output=True, text=True)
        if r.returncode != 0:
            subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(plist)], capture_output=True, text=True)
        print(f"started {s}")
    for _ in range(30):
        try:
            api("GET", "/_matrix/client/versions"); break
        except Exception:
            time.sleep(2)
    return cmd_check(_)


def compose(script_file: str, tone: str | None) -> str:
    script = Path(script_file).read_text().strip()
    if not script:
        sys.exit("Script file is empty.")
    return PREMISE.format(script=script, tone=f" Tone and pace: {tone}." if tone else "")


def cmd_compose(a: argparse.Namespace) -> int:
    print(compose(a.file, a.tone))
    return 0


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "voiceover"


def cmd_send(a: argparse.Namespace) -> int:
    body = compose(a.file, a.tone)
    room, ghost = instinct_ids()
    since = int(time.time() * 1000)
    api("PUT", f"/_matrix/client/v3/rooms/{q(room)}/send/m.room.message/vo{since}", {"msgtype": "m.text", "body": body})
    print(f"sent to Instinct, waiting up to {a.timeout}s for voice notes...", flush=True)

    got: dict[str, dict] = {}
    last_new = None
    deadline = time.time() + a.timeout
    while time.time() < deadline:
        chunk = api("GET", f"/_matrix/client/v3/rooms/{q(room)}/messages?dir=b&limit=30")["chunk"]
        for e in chunk:
            c = e.get("content", {})
            if (e["type"] == "m.room.message" and e["sender"] == ghost and e["origin_server_ts"] > since
                    and c.get("msgtype") == "m.audio" and e["event_id"] not in got):
                got[e["event_id"]] = e
                last_new = time.time()
            elif (e["type"] == "m.room.message" and e["sender"] == ghost and e["origin_server_ts"] > since
                    and c.get("msgtype") == "m.text" and e["event_id"] not in got):
                got[e["event_id"]] = e
                print(f"instinct says: {c.get('body', '')[:300]}", flush=True)
        # long scripts may arrive as several notes: stop after 30s with no new audio
        if last_new and time.time() - last_new > 30:
            break
        time.sleep(4)

    audio = sorted((e for e in got.values() if e["content"].get("msgtype") == "m.audio"), key=lambda e: e["origin_server_ts"])
    if not audio:
        print("NO voice note received before timeout. Check the chat; Instinct may have replied in text.")
        return 2
    OUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = slug(a.name or Path(a.file).stem)
    for i, e in enumerate(audio, 1):
        server, mid = e["content"]["url"][6:].split("/", 1)
        part = f"-part{i}" if len(audio) > 1 else ""
        out = OUT_DIR / f"{stamp}-{base}{part}.ogg"
        out.write_bytes(api("GET", f"/_matrix/client/v1/media/download/{server}/{mid}", raw=True))
        secs = e["content"].get("info", {}).get("duration", 0) / 1000
        print(f"saved {out} ({secs:.0f}s)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("up")
    for name in ("compose", "send"):
        sp = sub.add_parser(name)
        sp.add_argument("file")
        sp.add_argument("--tone")
        if name == "send":
            sp.add_argument("--name")
            sp.add_argument("--timeout", type=int, default=300)
    a = p.parse_args()
    return {"check": cmd_check, "up": cmd_up, "compose": cmd_compose, "send": cmd_send}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
