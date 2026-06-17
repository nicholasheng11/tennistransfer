#!/usr/bin/env python3
"""
utr_update.py — refresh UTR ratings in transfers.js from your premium UTR account.

This talks to the same private API the UTR website uses, authenticated with the
`jwt` token from your logged-in browser session (see scripts/.env.example).
Nothing here stores your password. Run it on your own machine, on demand.

USAGE (run from the repo root):
    python scripts/utr_update.py test "Calin Stirbu"   # verify token + see API shape for one name
    python scripts/utr_update.py match                  # one-time: link players -> UTR ids (interactive)
    python scripts/utr_update.py match --auto           # only auto-accept confident matches, skip the rest
    python scripts/utr_update.py refresh                # update every player's utr by their stored utrId
    python scripts/utr_update.py refresh --dry-run      # show what WOULD change, write nothing

After match/refresh, review with `git diff transfers.js`, then commit + push yourself.
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

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TRANSFERS = os.path.join(REPO, "transfers.js")
ENV = os.path.join(HERE, ".env")

# Be polite to the API — small pause between calls so we never look like a hammer.
DELAY_SECONDS = 0.6


# ----------------------------------------------------------------------------- env + http
def load_env():
    cfg = {}
    if not os.path.exists(ENV):
        die(f"No .env file found at {ENV}\n"
            f"Copy scripts/.env.example to scripts/.env and paste your UTR_JWT token.")
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


def api_get(cfg, path, params=None):
    """GET a UTR API path. Returns parsed JSON (or raises on a hard failure)."""
    url = cfg["UTR_API_BASE"].rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    token = cfg["UTR_JWT"]
    req = urllib.request.Request(url, headers={
        # Send the token both ways — different UTR endpoints accept one or the other.
        "Authorization": "Bearer " + token,
        "Cookie": "jwt=" + token,
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, body
    except urllib.error.URLError as e:
        die(f"Network error hitting {url}: {e}")


def search_players(cfg, name, top=20):
    status, raw = api_get(cfg, "/v2/search/players",
                          {"query": name, "top": top, "skip": 0})
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


def get_player_utr(cfg, utr_id):
    """Return (singlesUtr_float_or_None, raw_status)."""
    status, raw = api_get(cfg, f"/v1/player/{utr_id}")
    if status == 401:
        die("401 Unauthorized — your UTR_JWT token is missing/expired. Grab a fresh one and retry.")
    if status != 200:
        return None, status
    try:
        data = json.loads(raw)
    except ValueError:
        return None, status
    return pick_singles_utr(data), status


# ----------------------------------------------------------------------------- JSON shape helpers
# These are written defensively because the UTR API wrapper shape has changed over time.
def extract_hits(data):
    """Find the list of player hits in a v2 search response, tolerating shape changes."""
    if isinstance(data, dict):
        players = data.get("players")
        if isinstance(players, dict) and isinstance(players.get("hits"), list):
            return players["hits"]
        if isinstance(players, list):
            return players
        if isinstance(data.get("hits"), list):
            return data["hits"]
    if isinstance(data, list):
        return data
    return []


def normalize_candidate(hit):
    """Pull a flat {id, name, college, gender, utr} out of one search hit, whatever its nesting."""
    src = hit.get("source", hit) if isinstance(hit, dict) else {}
    pid = src.get("id") or hit.get("id")
    name = src.get("displayName") or src.get("name") or ""
    gender = (src.get("gender") or "")[:1].upper()
    # College / club — try the common spots
    college = ""
    pc = src.get("playerClubs") or src.get("clubs") or []
    if isinstance(pc, list) and pc:
        college = (pc[0].get("name") or pc[0].get("displayName") or "") if isinstance(pc[0], dict) else ""
    if not college:
        loc = src.get("location") or {}
        if isinstance(loc, dict):
            college = loc.get("display") or loc.get("displayName") or ""
    return {
        "id": str(pid) if pid is not None else "",
        "name": name,
        "gender": gender,
        "college": college,
        "utr": pick_singles_utr(src),
    }


def pick_singles_utr(obj):
    if not isinstance(obj, dict):
        return None
    for key in ("singlesUtr", "myUtrSingles", "threeMonthRating", "singlesUtrDisplay"):
        v = obj.get(key)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
        if isinstance(v, str):
            try:
                f = float(v)
                if f > 0:
                    return f
            except ValueError:
                pass
    return None


# ----------------------------------------------------------------------------- transfers.js parsing
FIELD_RE = lambda key: re.compile(key + r':\s*"([^"]*)"')


def read_records():
    text = open(TRANSFERS, encoding="utf-8").read()
    lines = text.split("\n")
    recs = []
    for i, line in enumerate(lines):
        if line.strip().startswith("{ id:"):
            recs.append(i)
    last = recs[-1] if recs else None
    return lines, recs, last


def get_field(line, key):
    m = FIELD_RE(key).search(line)
    return m.group(1) if m else None


def set_field(line, key, value, after="utr"):
    """Replace key's value if present, else insert `, key: "value"` right after the `after` field."""
    pat = FIELD_RE(key)
    if pat.search(line):
        return pat.sub(f'{key}: "{value}"', line, count=1)
    anchor = FIELD_RE(after).search(line)
    if anchor:
        insert = anchor.group(0) + f', {key}: "{value}"'
        return line[:anchor.start()] + insert + line[anchor.end():]
    # fallback: before closing brace
    idx = line.rfind("}")
    return line[:idx].rstrip() + f', {key}: "{value}" ' + line[idx:]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# ----------------------------------------------------------------------------- commands
def cmd_test(cfg, args):
    if not args:
        die('Usage: python scripts/utr_update.py test "Player Name"')
    name = args[0]
    print(f"Searching UTR for: {name!r}\n")
    status, raw = api_get(cfg, "/v2/search/players", {"query": name, "top": 10, "skip": 0})
    print(f"HTTP {status}\n")
    if status == 200:
        try:
            data = json.loads(raw)
            cands = [normalize_candidate(h) for h in extract_hits(data)]
            print(f"Parsed {len(cands)} candidate(s):")
            for c in cands:
                print(f"  id={c['id']:>10}  {c['name']:<28} {c['gender']:<2} UTR={c['utr']}  {c['college']}")
            print("\n--- raw JSON (first 2500 chars, so we can confirm field names) ---")
            print(json.dumps(data, indent=2)[:2500])
        except ValueError:
            print("Response was not JSON:\n", raw[:2000])
    else:
        print(raw[:2000])


def cmd_match(cfg, args):
    auto = "--auto" in args
    lines, recs, last = read_records()
    changed = 0
    skipped = []
    for i in recs:
        line = lines[i]
        if get_field(line, "utrId"):
            continue  # already linked
        name = get_field(line, "name") or ""
        gender = get_field(line, "gender") or ""
        prev = get_field(line, "previousSchool") or ""
        new = get_field(line, "newSchool") or ""
        schools = {norm(s) for chunk in (prev, new) for s in chunk.split(",") if s.strip()}
        cands = search_players(cfg, name, top=20)
        time.sleep(DELAY_SECONDS)
        # gender filter when known
        if gender:
            g = [c for c in cands if not c["gender"] or c["gender"] == gender]
            cands = g or cands
        # score: strong = a candidate whose college matches one of the player's schools
        def school_hit(c):
            cn = norm(c["college"])
            return any(s and (s in cn or cn in s) for s in schools) if cn else False
        strong = [c for c in cands if school_hit(c)]
        chosen = None
        if len(strong) == 1:
            chosen = strong[0]
        elif not auto:
            chosen = prompt_pick(name, prev, new, cands)
        if chosen and chosen["id"]:
            lines[i] = set_field(line, "utrId", chosen["id"])
            tag = "auto" if (len(strong) == 1) else "you"
            print(f"  linked  {name:<26} -> utrId {chosen['id']} ({tag}; UTR {chosen['utr']}, {chosen['college']})")
            changed += 1
        else:
            skipped.append(name)
    if changed:
        open(TRANSFERS, "w", encoding="utf-8").write("\n".join(lines))
    print(f"\nLinked {changed} player(s). Skipped {len(skipped)}.")
    if skipped:
        print("Unmatched (run without --auto to pick manually, or they may not be in UTR):")
        for n in skipped:
            print("   -", n)
    print("\nReview with:  git diff transfers.js")


def prompt_pick(name, prev, new, cands):
    if not cands:
        print(f"  no UTR results for {name!r} — skipping")
        return None
    print(f"\n{name}  ({prev} -> {new})")
    for n, c in enumerate(cands[:8]):
        print(f"   [{n}] {c['name']:<26} UTR {str(c['utr']):<6} {c['college']}")
    ans = input("   pick number, or Enter to skip: ").strip()
    if ans.isdigit() and int(ans) < len(cands):
        return cands[int(ans)]
    return None


def cmd_refresh(cfg, args):
    dry = "--dry-run" in args
    lines, recs, last = read_records()
    today = datetime.date.today().isoformat()
    changed = 0
    no_id = 0
    for i in recs:
        line = lines[i]
        utr_id = get_field(line, "utrId")
        if not utr_id:
            no_id += 1
            continue
        name = get_field(line, "name") or ""
        old = get_field(line, "utr") or ""
        val, status = get_player_utr(cfg, utr_id)
        time.sleep(DELAY_SECONDS)
        if val is None:
            print(f"  ? {name:<26} no rating (HTTP {status}) — left as {old or 'blank'}")
            continue
        new_utr = f"{val:.2f}"
        if new_utr == old:
            continue  # unchanged, don't touch the line
        if not dry:
            line = set_field(line, "utr", new_utr)
            line = set_field(line, "utrUpdated", today, after="utr")
            lines[i] = line
        print(f"  {'(dry) ' if dry else ''}{name:<26} {old or 'blank':>6} -> {new_utr}")
        changed += 1
    if changed and not dry:
        open(TRANSFERS, "w", encoding="utf-8").write("\n".join(lines))
    print(f"\n{'Would update' if dry else 'Updated'} {changed} rating(s). "
          f"{no_id} player(s) have no utrId yet (run `match` first).")
    if changed and not dry:
        print("Review with:  git diff transfers.js")


def die(msg):
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd, rest = sys.argv[1], sys.argv[2:]
    cfg = load_env()
    if cmd == "test":
        cmd_test(cfg, rest)
    elif cmd == "match":
        cmd_match(cfg, rest)
    elif cmd == "refresh":
        cmd_refresh(cfg, rest)
    else:
        die(f"Unknown command {cmd!r}. Use: test | match | refresh")


if __name__ == "__main__":
    main()
