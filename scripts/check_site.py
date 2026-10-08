"""Validate static site publication without third-party dependencies.

Run locally with Python 3.10+:
    python scripts/check_site.py
After deployment, also check real HTTP status codes:
    python scripts/check_site.py --base-url https://trinitrotorol.com
"""
from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
ORIGIN = "https://trinitrotorol.com"
APP_PATHS = {
    "/game-guide/exponential-idle-minigame-guide/",
    "/game-guide/mhwilds-inventory-checker/",
    "/game-guide/mhwilds-skill-sim/",
}
REMOTE_RESOURCES = {"/game-guide/mhwilds-skill-sim/release.json"}
INDEXED_APP_PATHS = {"/game-guide/exponential-idle-minigame-guide/"}
WILDS_ORIGIN = "https://mhwilds.trinitrotorol.com"
WILDS_PATHS = {"/skill-sim/", "/inventory/", "/skill-sim/release.json"}
ADS = b"google.com, pub-6343181736493400, DIRECT, f08c47fec0942fa0\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class Page(HTMLParser):
    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.ids: set[str] = set()
        self.duplicates: set[str] = set()
        self.title = ""
        self.h1_count = 0
        self.in_title = False
        self.script_type: str | None = None
        self.script_body = ""
        self.structured: list[dict] = []
        self.feed(text)
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        self.tags.append((tag, values))
        if element_id := values.get("id"):
            if element_id in self.ids:
                self.duplicates.add(element_id)
            self.ids.add(element_id)
        if tag == "h1":
            self.h1_count += 1
        if tag == "title":
            self.in_title = True
        if tag == "script":
            self.script_type = values.get("type") or ""
            self.script_body = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "script":
            if self.script_type == "application/ld+json":
                self.structured.append(json.loads(self.script_body))
            self.script_type = None

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        if self.script_type is not None:
            self.script_body += data

    def values(self, tag: str, match: str, value: str, result: str) -> list[str]:
        return [
            str(attrs[result])
            for name, attrs in self.tags
            if name == tag and attrs.get(match) == value and attrs.get(result)
        ]


def page_path(file: Path) -> str:
    relative = file.relative_to(PUBLIC).as_posix()
    return "/" + (relative[:-10] if relative.endswith("index.html") else relative)


def source_for(path: str) -> Path:
    return PUBLIC / (path.lstrip("/") + ("index.html" if path.endswith("/") else ""))


def read_http(base: str, path: str) -> tuple[int, str, str]:
    request = Request(base.rstrip("/") + path, headers={"User-Agent": "trinitrotorol-site-check/1.0"})
    try:
        response = urlopen(request, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.read().decode("utf-8"), response.headers.get("Content-Type", "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", help="Optional deployed origin for read-only HTTP validation")
    args = parser.parse_args()
    files = sorted(PUBLIC.rglob("*.html"))
    pages = {page_path(file): Page(file.read_text(encoding="utf-8")) for file in files}
    require(len(pages) == 7, "Expected the six public content pages and one 404 page")
    titles: set[str] = set()
    descriptions: set[str] = set()
    for path, page in pages.items():
        require(page.h1_count == 1, f"{path}: expected exactly one H1")
        require(page.title and page.title not in titles, f"{path}: missing or duplicate title")
        titles.add(page.title)
        description = page.values("meta", "name", "description", "content")
        require(len(description) == 1 and description[0] not in descriptions, f"{path}: description")
        descriptions.add(description[0])
        require(not page.duplicates, f"{path}: duplicate IDs {page.duplicates}")
        require(("html", {"lang": "ja"}) in page.tags, f"{path}: Japanese language")
        require(page.values("link", "rel", "icon", "href") == ["/favicon.svg"], f"{path}: favicon")
        require(page.values("link", "rel", "stylesheet", "href") == ["/assets/site.css"], f"{path}: CSS")
        require(page.values("meta", "property", "og:title", "content") == [page.title], f"{path}: OG title")
        require(page.values("meta", "property", "og:url", "content") == [ORIGIN + path], f"{path}: OG URL")
        require(page.values("meta", "name", "google-adsense-account", "content") == ["ca-pub-6343181736493400"], f"{path}: publisher")
        robots = page.values("meta", "name", "robots", "content")
        if path == "/404.html":
            require(robots == ["noindex,follow"], "404 must be noindex")
            require(not page.values("link", "rel", "canonical", "href"), "404 must not canonicalize to home")
        else:
            require(robots == ["index,follow"], f"{path}: indexing")
            require(page.values("link", "rel", "canonical", "href") == [ORIGIN + path], f"{path}: canonical")
        for tag, attrs in page.tags:
            if tag == "script":
                require(attrs.get("type") == "application/ld+json" and "src" not in attrs, f"{path}: executable script")
            require(not any(name.startswith("on") for name in attrs), f"{path}: inline handler")
            for key in ("href", "src"):
                if raw := attrs.get(key):
                    url = urlsplit(urljoin(ORIGIN + path, raw))
                    require(url.scheme == "https", f"{path}: unexpected link scheme {raw}")
                    if url.netloc == "mhwilds.trinitrotorol.com":
                        require(url.path in WILDS_PATHS, f"{path}: invalid Wilds URL {raw}")
                    if url.netloc != "trinitrotorol.com":
                        continue
                    target = unquote(url.path)
                    if target in APP_PATHS - INDEXED_APP_PATHS:
                        require(url.query == "legacy=1", f"{path}: outdated Wilds link {raw}")
                    require(target in APP_PATHS | REMOTE_RESOURCES or source_for(target).is_file(), f"{path}: missing {raw}")
                    if url.fragment and target in pages:
                        require(unquote(url.fragment) in pages[target].ids, f"{path}: missing fragment {raw}")
        links = page.values("a", "href", "#main", "href")
        require(links == ["#main"] and "main" in page.ids, f"{path}: skip link")
        hrefs = {attrs.get("href") for tag, attrs in page.tags if tag == "a"}
        require({"/about/", "/contact/", "/privacy/"} <= hrefs, f"{path}: missing policy navigation")
        for schema in page.structured:
            require(schema["@type"] == "BreadcrumbList", f"{path}: unsupported structured data")
            items = schema["itemListElement"]
            require([item["position"] for item in items] == list(range(1, len(items) + 1)), f"{path}: breadcrumb order")
            require(items[-1]["item"] == ORIGIN + path, f"{path}: breadcrumb target")
    sitemap = ET.parse(PUBLIC / "sitemap.xml")
    locations = [item.text for item in sitemap.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    expected = {ORIGIN + path for path in set(pages) - {"/404.html"} | INDEXED_APP_PATHS}
    require(len(locations) == len(set(locations)) and set(locations) == expected, "Sitemap mismatch")
    require((PUBLIC / "ads.txt").read_bytes() == ADS, "ads.txt changed")
    config = json.loads((ROOT / "wrangler.jsonc").read_text(encoding="utf-8"))
    require(config["assets"]["not_found_handling"] == "404-page", "Real custom 404 handling required")
    require(config["routes"] == [{"pattern": "trinitrotorol.com", "custom_domain": True}], "Existing domain route changed")
    require(not any(source_for(path).exists() for path in APP_PATHS), "Root site must not shadow app assets")
    policy = (PUBLIC / "privacy/index.html").read_text(encoding="utf-8")
    for expected_link in ("https://policies.google.com/technologies/partner-sites?hl=ja", "https://adssettings.google.com/", "https://www.cloudflare.com/privacypolicy/", "https://docs.github.com/ja/site-policy/privacy-policies/github-general-privacy-statement"):
        require(expected_link in policy, f"Missing policy source: {expected_link}")
    require("現在、当サイトでは広告を配信していません。" in policy, "Current advertising status missing")
    require("mhwilds.trinitrotorol.com" in policy, "New storage origin missing from policy")
    migration = (PUBLIC / "game-guide/mhwilds-guide/index.html").read_text(encoding="utf-8")
    require('id="migration"' in migration and '?legacy=1' in migration, "Legacy inventory export instructions missing")
    ET.parse(PUBLIC / "favicon.svg")
    require("Sitemap: " + ORIGIN + "/sitemap.xml" in (PUBLIC / "robots.txt").read_text(), "robots sitemap missing")
    print(f"PASS: {len(pages)} HTML pages, links/fragments, unique metadata, JSON-LD, sitemap, ads.txt, policy links, custom404 config")
    if args.base_url:
        for path in sorted(set(pages) - {"/404.html"} | APP_PATHS | {"/ads.txt", "/sitemap.xml", "/assets/site.css", "/favicon.svg"}):
            status, body, content_type = read_http(args.base_url, path)
            require(status == 200, f"HTTP {status}: {path}")
            if path in pages:
                require(Page(body).title == pages[path].title, f"Deployed title differs: {path}")
            if path == "/ads.txt":
                require(body.encode() == ADS and "text/plain" in content_type, "Published ads.txt mismatch")
            print(f"PASS HTTP 200: {path}")
        for path in sorted(WILDS_PATHS):
            status, _, _ = read_http(WILDS_ORIGIN, path)
            require(status == 200, f"HTTP {status}: {WILDS_ORIGIN}{path}")
            print(f"PASS HTTP 200: {WILDS_ORIGIN}{path}")
        status, body, _ = read_http(args.base_url, "/__site-check-missing-20261007__/")
        require(status == 404, f"Unknown route returned {status}, not real404")
        require(Page(body).title == pages["/404.html"].title, "Custom404 content missing")
        require(Page(body).values("meta", "name", "robots", "content") == ["noindex,follow"], "Published404 noindex")
        print("PASS HTTP 404: unknown route with custom noindex page")


if __name__ == "__main__":
    main()
