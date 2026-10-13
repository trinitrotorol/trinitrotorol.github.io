# trinitrotorol.github.io

This repository uses `main` for both Cloudflare Workers and GitHub Pages.

Production URL:
https://trinitrotorol.com/

- `public/` is the Cloudflare Workers publish directory.
- Cloudflare Workers production branch: `main`.
- Cloudflare Workers build output directory: `public`.
- `docs/` is only for redirecting `trinitrotorol.github.io` to `trinitrotorol.com`.
- GitHub Pages source: `main` branch, `/docs` folder.
- Do not set a custom domain on GitHub Pages.
- Do not add a `CNAME` file.

## AdSense site verification

`public/ads.txt` and the non-executing `google-adsense-account` meta tag in
`public/index.html` identify publisher `pub-6343181736493400` for the
`trinitrotorol.com` AdSense site review. They do not load advertising scripts or
enable ad display. Approval and ad serving are separate steps in AdSense.

## Content and verification

The site consists of static HTML with shared CSS in `public/assets/`. Most
pages are in Japanese; the MHWILDS guide also has a complete English version
at `/en/game-guide/mhwilds-guide/`. Both guides have self-canonical URLs,
reciprocal language links and `hreflang`, and are listed in the sitemap.
Keep the UI labels and migration/backup instructions aligned in both versions.
The guides do not automatically change the tools' saved language setting.
Each content page has its own title, description, canonical URL, Open Graph
metadata, and navigation to the operator, contact, and privacy pages. The
MHWILDS guide describes the currently deployed browser implementation.

Exponential Idle remains on its existing path. The Wilds tools are served at
https://mhwilds.trinitrotorol.com/skill-sim/ and /inventory/ by their existing
Worker. Its old root-domain paths redirect to the new site, with `?legacy=1`
retained for browser-local JSON export; the guide documents migration.
Each host publishes a sitemap containing its own canonical URLs. Do not
copy those apps into this repository or broaden their routes. Root
`assets.not_found_handling: "404-page"` serves `public/404.html` with HTTP 404;
it does not redirect unknown URLs to the homepage.

Run `python scripts/check_site.py` with Python 3.10+ for dependency-free static
validation. After deployment, use
`python scripts/check_site.py --base-url https://trinitrotorol.com` to verify
published pages, the unchanged tool entrances, ads.txt, and real HTTP 404.
Also check narrow viewports, keyboard focus, and browser accessibility tooling.
The static checks do not establish search ranking or AdSense approval.

Before enabling ads, review the privacy page, consent settings, ad placement,
and each application's CSP and network checks together. The current pages do
not claim ads or a consent banner are live. Root/guide Web Analytics remains
enabled through Cloudflare; the existing MHWILDS path exclusions remain separate.

## Site Metrics application information

`/site-metrics/`, `/site-metrics/privacy/`, and `/site-metrics/terms/` describe
the operator-only `trinitrotorol Site Metrics` CLI for Google OAuth branding.
These static pages explain read-only AdSense and Search Console access,
private local reports, and operator-directed analysis in Codex; they
do not provide public account sign-in. Keep their exact URLs aligned with
the OAuth branding configuration. They use `noindex,follow` and are omitted
from the sitemap. Do not publish credentials, account/client identifiers,
or private revenue/search performance reports in these pages or their assets.

References: [Digital Agency design system](https://design.digital.go.jp/dads/),
[Google Search basics](https://developers.google.com/search/docs/fundamentals/get-started-developers),
[AdSense privacy disclosures](https://support.google.com/adsense/answer/1348695?hl=ja),
[Cloudflare custom404](https://developers.cloudflare.com/workers/static-assets/routing/static-site-generation/).
