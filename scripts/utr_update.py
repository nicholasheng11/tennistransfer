#!/usr/bin/env python3
"""
utr_update.py — refresh UTR ratings in transfers.js from your premium UTR account.

Talks to the same private API the UTR website uses, authenticated with the `jwt`
token from your logged-in browser session (see scripts/.env.example). Your password
is never stored. Run it on your own machine, on demand.

USAGE (run from the repo root):
    python scripts/utr_update.py test "Calin Stirbu"   # verify token + see candidates for one name
    python scripts/utr_update.py match                  # one-time: link players -> UTR ids + set current UTR
    python scripts/utr_update.py match --auto           # only auto-accept confident matches, skip the rest
    python scripts/utr_update.py refresh                # re-update UTRs for already-linked players
    python scripts/utr_update.py refresh --dry-run      # show what WOULD change, write nothing

Matching uses NAME + UTR-PROXIMITY: UTR has duplicate profiles (some unrated), and
profiles show country, not college — so the reliable signal is "the rated profile
whose UTR is closest to your existing snapshot." Confident matches are auto-accepted;
the rest are listed for you to pick (unless --auto).

After any run, review with `git diff transfers.js`, then commit + push yourself.
"""

import json
import re
import sys
import os
import time
import datetime
import urllib.request
import urllib.parse
import urllib.error
import http.client
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TRANSFERS = os.path.join(REPO, "transfers.js")
ENV = os.path.join(HERE, ".env")

DELAY_SECONDS = 0.6        # be polite to the API — small pause between calls
AUTO_UTR_TOLERANCE = 1.5   # auto-accept a rated name-match if its UTR is within this of your snapshot


# ----------------------------------------------------------------------------- env + http
def load_env():
    if not os.path.exists(ENV):
        die(f"No .env file at {ENV}\nCopy scripts/.env.example to scripts/.env and paste your UTR_JWT token.")
    cfg = {}
    with open(ENV, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    if not cfg.get("UTR_JWT") or cfg["UTR_JWT"].startswith("paste-"):
        die("UTR_JWT is not set in scripts/.env — paste your jwt token first.")
    cfg.setdefault("UTR_API_BASE", "https://api.utrsports.net")
    return cfg


def api_get(cfg, path, params=None, retries=4):
    url = cfg["UTR_API_BASE"].rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    token = cfg["UTR_JWT"]
    headers = {
        "Authorization": "Bearer " + token,
        "Cookie": "jwt=" + token,
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")  # a real HTTP response (e.g. 401) — return it
        except (urllib.error.URLError, http.client.HTTPException, OSError) as e:
            last_err = e
            time.sleep(1.0 * (attempt + 1))  # transient (dropped connection / timeout) — back off and retry
    print(f"  ! network error (gave up after {retries} tries): {last_err}", file=sys.stderr)
    return 0, ""


def search_players(cfg, name, top=30):
    status, raw = api_get(cfg, "/v2/search/players", {"query": name, "top": top, "skip": 0})
    if status == 401:
        die("401 Unauthorized — your UTR_JWT token is missing/expired. Grab a fresh one and retry.")
    if status != 200:
        print(f"  ! search for {name!r} returned HTTP {status}", file=sys.stderr)
        return []
    try:
        data = json.loads(raw)
    except ValueError:
        print(f"  ! search for {name!r} returned non-JSON", file=sys.stderr)
        return []
    return [normalize_candidate(h) for h in extract_hits(data)]


# ----------------------------------------------------------------------------- JSON shape helpers
def extract_hits(data):
    if isinstance(data, dict):
        if isinstance(data.get("hits"), list):
            return data["hits"]
        players = data.get("players")
        if isinstance(players, dict) and isinstance(players.get("hits"), list):
            return players["hits"]
        if isinstance(players, list):
            return players
    if isinstance(data, list):
        return data
    return []


def normalize_candidate(hit):
    src = hit.get("source", hit) if isinstance(hit, dict) else {}
    pid = src.get("id") or hit.get("id")
    name = src.get("displayName") or src.get("name") or ""
    gender = (src.get("gender") or "")[:1].upper()  # "Male"->"M", "Female"->"F"
    loc = src.get("location") or {}
    where = ""
    if isinstance(loc, dict):
        where = loc.get("display") or loc.get("displayName") or ""
    return {
        "id": str(pid) if pid is not None else "",
        "name": name,
        "gender": gender,
        "where": where,
        "utr": pick_singles_utr(src),
    }


def pick_singles_utr(obj):
    if not isinstance(obj, dict):
        return None
    for key in ("singlesUtr", "myUtrSingles", "threeMonthRating"):
        v = obj.get(key)
        try:
            f = float(v)
            if f > 0:
                return f
        except (TypeError, ValueError):
            pass
    return None


# ----------------------------------------------------------------------------- transfers.js parsing
def FIELD_RE(key):
    return re.compile(key + r':\s*"([^"]*)"')


def read_records():
    text = open(TRANSFERS, encoding="utf-8").read()
    lines = text.split("\n")
    recs = [i for i, l in enumerate(lines) if l.strip().startswith("{ id:")]
    return lines, recs, (recs[-1] if recs else None)


def get_field(line, key):
    m = FIELD_RE(key).search(line)
    return m.group(1) if m else None


def get_utr(line):
    try:
        return float(get_field(line, "utr"))
    except (TypeError, ValueError):
        return None


def set_field(line, key, value, after="utr"):
    """Replace key's value if present, else insert `, key: "value"` right after the `after` field."""
    pat = FIELD_RE(key)
    if pat.search(line):
        return pat.sub(f'{key}: "{value}"', line, count=1)
    anchor = FIELD_RE(after).search(line)
    if anchor:
        return line[:anchor.end()] + f', {key}: "{value}"' + line[anchor.end():]
    idx = line.rfind("}")
    return line[:idx].rstrip() + f', {key}: "{value}" ' + line[idx:]


def name_tokens(s):
    # Strip accents so "Niccolò"/"Prachař"/"López" match their ASCII spellings in our data.
    flat = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+", flat.lower()))


def target_gender(g):
    return "F" if g == "W" else g  # our data uses W; UTR uses Female->F


# ----------------------------------------------------------------------------- commands
def cmd_test(cfg, args):
    if not args:
        die('Usage: python scripts/utr_update.py test "Player Name"')
    name = args[0]
    print(f"Searching UTR for: {name!r}\n")
    status, raw = api_get(cfg, "/v2/search/players", {"query": name, "top": 10, "skip": 0})
    print(f"HTTP {status}\n")
    if status != 200:
        print(raw[:1500]); return
    try:
        data = json.loads(raw)
    except ValueError:
        print("Not JSON:\n", raw[:1500]); return
    cands = [normalize_candidate(h) for h in extract_hits(data)]
    print(f"Parsed {len(cands)} candidate(s):")
    for c in cands:
        print(f"  id={c['id']:>9}  {c['name']:<28} {c['gender']:<2} UTR={c['utr']}  {c['where']}")


def cmd_match(cfg, args):
    auto = "--auto" in args
    loose = "--loose" in args  # also accept surname-only matches (for nicknames), still gated by UTR proximity
    lines, recs, last = read_records()
    today = datetime.date.today().isoformat()
    changed = 0
    skipped = []
    try:
        for i in recs:
            line = lines[i]
            if get_field(line, "utrId"):
                continue  # already linked (lets a re-run resume where a previous one stopped)
            name = get_field(line, "name") or ""
            try:
                our_utr = get_utr(line)
                tg = target_gender(get_field(line, "gender") or "")
                cands = search_players(cfg, name, top=30)
                time.sleep(DELAY_SECONDS)
                if tg:
                    g = [c for c in cands if not c["gender"] or c["gender"] == tg]
                    cands = g or cands
                nt = name_tokens(name)
                named = [c for c in cands if nt and nt <= name_tokens(c["name"])]
                if loose and not named:
                    sn = name_tokens(name.split()[-1]) if name.split() else set()
                    named = [c for c in cands if sn and sn <= name_tokens(c["name"])]
                rated = [c for c in named if c["utr"] is not None]
                chosen, how = None, ""
                if our_utr is not None and rated:
                    best = min(rated, key=lambda c: abs(c["utr"] - our_utr))
                    if abs(best["utr"] - our_utr) <= AUTO_UTR_TOLERANCE:
                        chosen, how = best, ("loose~UTR" if loose and nt - name_tokens(best["name"]) else "auto~UTR")
                if not chosen and our_utr is None and len(rated) == 1:
                    chosen, how = rated[0], "auto-1rated"
                if not chosen and not auto:
                    chosen = prompt_pick(name, our_utr, named or cands)
                    how = "picked"
                if chosen and chosen["id"]:
                    line = set_field(line, "utrId", chosen["id"])
                    if chosen["utr"] is not None:
                        line = set_field(line, "utr", f"{chosen['utr']:.2f}")
                        line = set_field(line, "utrUpdated", today, after="utr")
                    lines[i] = line
                    print(f"  linked {name:<24} -> {chosen['name']:<26} UTR {chosen['utr']}  ({how})")
                    changed += 1
                else:
                    skipped.append(name)
            except Exception as e:
                print(f"  ! skipped {name}: {e}", file=sys.stderr)
                skipped.append(name)
    finally:
        # Always persist progress — even if interrupted — so a re-run continues, not restarts.
        if changed:
            open(TRANSFERS, "w", encoding="utf-8").write("\n".join(lines))
    print(f"\nLinked {changed} player(s) this run. Skipped {len(skipped)}.")
    if skipped:
        print("Unmatched (re-run WITHOUT --auto to pick manually, or they're not in UTR):")
        for n in skipped:
            print("   -", n)
    print("\nReview with:  git diff transfers.js")


def prompt_pick(name, our_utr, cands):
    if not cands:
        print(f"  no UTR name-match for {name!r} — skipping")
        return None
    print(f"\n{name}   (your snapshot: UTR {our_utr})")
    shown = cands[:10]
    for n, c in enumerate(shown):
        star = "*" if c["utr"] is not None else " "
        print(f"   [{n}]{star} {c['name']:<26} UTR {str(c['utr']):<6} {c['where']}")
    ans = input("   pick number (* = rated), or Enter to skip: ").strip()
    return shown[int(ans)] if ans.isdigit() and int(ans) < len(shown) else None


def cmd_refresh(cfg, args):
    dry = "--dry-run" in args
    lines, recs, last = read_records()
    today = datetime.date.today().isoformat()
    changed = no_id = unread = 0
    for i in recs:
        line = lines[i]
        utr_id = get_field(line, "utrId")
        if not utr_id:
            no_id += 1
            continue
        name = get_field(line, "name") or ""
        old = get_field(line, "utr") or ""
        cands = search_players(cfg, name, top=40)
        time.sleep(DELAY_SECONDS)
        match = next((c for c in cands if c["id"] == utr_id), None)
        if not match or match["utr"] is None:
            print(f"  ? {name:<26} couldn't read current UTR — left as {old or 'blank'}")
            unread += 1
            continue
        new = f"{match['utr']:.2f}"
        if new == old:
            continue
        if not dry:
            if old:
                line = set_field(line, "utrPrev", old, after="utr")  # stash prior value for trend arrows
            line = set_field(line, "utr", new)
            line = set_field(line, "utrUpdated", today, after="utr")
            lines[i] = line
        print(f"  {'(dry) ' if dry else ''}{name:<26} {old or 'blank':>6} -> {new}")
        changed += 1
    if changed and not dry:
        open(TRANSFERS, "w", encoding="utf-8").write("\n".join(lines))
    print(f"\n{'Would update' if dry else 'Updated'} {changed} rating(s). "
          f"{no_id} not linked yet (run `match`), {unread} couldn't be read.")
    if changed and not dry:
        print("Review with:  git diff transfers.js")


def die(msg):
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(1)


def main():
    # Windows consoles default to cp1252 and crash printing accented names (č, š, ł…).
    # Force UTF-8 output so prints never abort the run; the file write is already UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd, rest = sys.argv[1], sys.argv[2:]
    cfg = load_env()
    {"test": cmd_test, "match": cmd_match, "refresh": cmd_refresh}.get(
        cmd, lambda *_: die(f"Unknown command {cmd!r}. Use: test | match | refresh"))(cfg, rest)


if __name__ == "__main__":
    main()
