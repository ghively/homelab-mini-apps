# TODO

Outstanding work after the redesign + Media app changes (branch `claude/redesign-yeo98r`).

## Deploy / configuration

- [ ] Set `JELLYFIN_API_KEY` (and `JELLYFIN_URL` if not `http://100.116.139.100:8096`) in the container env — the Media app returns 503 until it's set.
- [ ] Add the two Jellyfin vars to `docker-compose.yml` / deployment secrets.
- [ ] Rebuild the image: the Dockerfile no longer installs the 1Password CLI (app removed), so the image should shrink.

## Media app — verify against real services

- [ ] **Casting network path**: `/api/media/play` hands the cast target a direct Jellyfin stream URL (`/Videos/{id}/stream?api_key=…`). The player device (Chromecast/TV) must be able to reach Jellyfin on that URL. If cast targets sit on a VLAN that can't reach gh-media, switch to HA's Jellyfin integration media-source IDs (`media-source://jellyfin/...`) instead.
- [ ] Confirm the Jellyfin `/Items` queries behave as expected on the real server (episode→series collapse uses `SeriesId` de-dup; `GroupItems` param may be redundant).
- [ ] Poster proxy has no backend cache — every client fetch hits Jellyfin. Consider a small in-memory LRU if it matters.
- [ ] Nice-to-haves: continue-watching row, season/episode browsing, pause/stop controls on the player list.

## Known frontend gaps

- [ ] `wiki.js` `readLocalFile()` calls `fetch()` without the `tma` Authorization header (pre-existing bug) — search-result file opens will 401 against the real backend. Route it through `api()`.
- [ ] Poster blob object-URLs are cached per session and never revoked (minor, bounded by library size).
- [ ] Verify the new UI inside real Telegram clients (iOS/Android/Desktop): light theme via `tg-theme` vars, safe-area top inset with the new sticky top bar, and `@property --pct` gauge animation on older webviews (falls back to a jump, not broken).

## Housekeeping

- [ ] `frontend/packages/design-system/` (TypeScript token/web-component package) is not consumed by the runtime app at all — either wire it in or remove it to avoid drift.
- [ ] Backend tests only cover auth (`tests/test_auth.py`); `media.py` and the other routers have no coverage. At minimum add tests for media input validation (`entity_id`/`item_id` checks) and the fail-closed error paths.
- [ ] CORS middleware only allows `GET` methods; POST endpoints work because the app is same-origin. Fine as-is, but revisit if the frontend is ever served from another origin.
- [ ] README screenshots: the docs describe the new design but have no images — add real captures from Telegram once deployed.
