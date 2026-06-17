# UTR auto-update tool

Refreshes the `utr` values in `transfers.js` from your **premium UTR account**, on demand.

It uses the same private API the UTR website uses, authenticated with the `jwt`
token from your logged-in browser session — so your password is never stored, and
it keeps working even when UTR changes their login flow. You stay in control: the
script edits `transfers.js`, you review the diff and push.

> ⚠️ This reads a paywalled service via its private API. Keep it gentle (the script
> already paces itself) and on-demand. Don't share your token.

## One-time setup

1. `copy scripts\.env.example scripts\.env`
2. Get your token: log in at https://app.utrsports.net → DevTools (F12) →
   **Application → Cookies** → copy the value of the `jwt` cookie.
3. Paste it into `scripts/.env` as `UTR_JWT=...`. (`.env` is gitignored.)

Tokens expire after a while. When a run says **401 Unauthorized**, just grab a fresh
`jwt` and paste it again.

## Usage (run from the repo root)

```bash
# 0. Sanity check — confirms your token works and shows results for one player
python scripts/utr_update.py test "Calin Stirbu"

# 1. One-time: link each player to their UTR id (stored as a new utrId field).
#    Auto-accepts a candidate whose UTR college matches the player's school;
#    prompts you to pick for the ambiguous ones.
python scripts/utr_update.py match
python scripts/utr_update.py match --auto    # only auto matches, skip the rest for now

# 2. Anytime after: refresh every linked player's UTR.
python scripts/utr_update.py refresh --dry-run   # preview, writes nothing
python scripts/utr_update.py refresh             # apply

# 3. Review + ship
git diff transfers.js
git add transfers.js && git commit -m "data: refresh UTRs" && git push
```

## What it writes to each player record

- `utrId` — the player's UTR id (set once by `match`; makes future refreshes exact).
- `utr` — updated to the current singles UTR (2 decimals).
- `utrUpdated` — date of the refresh. The card tooltip shows "UTR x.xx as of <utrUpdated>"
  (falls back to `dateUpdated` for players not yet refreshed). `dateUpdated` itself is
  **not** touched, so card sort order / commitment bubbling are unaffected.

## Notes

- If the API base URL ever moves, change `UTR_API_BASE` in `.env`.
- `refresh` only rewrites a line when the rating actually changed, so diffs stay small.
- Players UTR can't find (or not yet matched) are listed and simply left as-is.
