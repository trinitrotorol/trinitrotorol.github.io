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
