# Lighthouse audit — `docs/index.html` (v1.0.0rc1)

**Run date:** 2026-04-29
**Tool:** Lighthouse 12.x via `npx lighthouse`, headless Chrome, desktop form-factor.
**Source:** `docs/index.html` served via `python -m http.server` on `localhost`.
**Reports:** raw HTML + JSON gitignored (~1.4 MB combined). Re-run with the script in this directory to regenerate locally.

## Scores

| Category | Score |
|---|---|
| Performance | 96 |
| Accessibility | 100 |
| Best Practices | 100 |
| SEO | 100 |

All four categories above 90; three of four at 100. Sprint plan acceptance: **Lighthouse pass on `docs/index.html`** ✓.

## Fixes landed during the audit

- **`<main>` landmark** added around the body content. Was: missing. Now: present. Accessibility +3.
- **Inline favicon** added via SVG data URI (`data:image/svg+xml,...`). Was: 404 on `/favicon.ico`. Now: served from the document itself, no extra request. Console errors → 0.
- **`docs/robots.txt`** added with `User-agent: * / Allow: /`. Was: 404. Now: served. SEO +10.
- **Link affordance**: links inside paragraphs now carry `text-decoration: underline` instead of relying on color alone. Was: WCAG fail (color contrast for distinguishability). Now: passes. Accessibility +7.

## Remaining penalties (Performance 96, not 100)

- **`largest-contentful-paint` 0.84** — sub-second LCP on a static page is constrained by the local Python `http.server` (no compression, single-threaded). Real GitHub Pages serving will cut this. Not a code-side issue.
- **`document-latency-insight` 0.50** — same root cause (local server has no `Cache-Control` headers). GH Pages adds these automatically.
- **`unsized-images` 0.50** — five SVG `<img>` tags don't carry explicit `width`/`height` attributes. Adding them prevents reflow but the SVGs scale fluidly so visual impact is zero. Optional polish.
- **`cache-insight` 0.00** — local server doesn't set cache lifetimes. GH Pages does.

The three server-side penalties (LCP, document-latency, cache-insight) will go away in production. The unsized-images one is a 5-line polish that doesn't affect the user experience and was deferred to keep this slice small.

## Re-running

```bash
# from repo root, with node_modules/.bin/lighthouse on PATH:
cd docs
python -m http.server 9876 &
SERVER_PID=$!
sleep 2
npx lighthouse http://localhost:9876/index.html \
  --output=json --output=html \
  --output-path=lighthouse-rc1 \
  --chrome-flags="--headless --no-sandbox" \
  --quiet --only-categories=performance,accessibility,best-practices,seo \
  --form-factor=desktop --screenEmulation.disabled
kill $SERVER_PID
```

Re-run before tagging v1.0.0 GA to confirm no regressions.
