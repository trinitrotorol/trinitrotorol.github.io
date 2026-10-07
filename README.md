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
