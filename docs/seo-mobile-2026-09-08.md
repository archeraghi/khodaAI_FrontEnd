# Khoda AI SEO, Google registration, and mobile performance

Completed on September 8, 2026 (Europe/Berlin).

## Published website

The existing https://khoda.ai/ website now has descriptive company/product
metadata and headings, one canonical homepage, Open Graph/Twitter previews,
Organization/Person/WebSite/WebPage JSON-LD, a real favicon, robots.txt, and
sitemap.xml. The company mission and visual identity remain present.

The page uses precompiled Tailwind CSS and a locally hosted Inter font; no
external JavaScript or Google Fonts request is required to render it. WebP
images replace the large originals for visible content. Image dimensions reserve
layout space; the hero loads eagerly and below-fold images load lazily. The
mobile menu has an accessible label and closes on section selection. Section
anchors clear the sticky header, and the founder markup is balanced.

Original visible image files totalled 4,122,235 bytes. Their WebP equivalents
total 271,708 bytes (93.4% smaller). CSS is 11,323 bytes before gzip; the locally
hosted font is 48,432 bytes. The original images remain available for existing
links and structured/social metadata.

## Measured mobile performance

Google PageSpeed Insights used the same emulated Moto G Power, Slow 4G,
Lighthouse 13.4.1 setup for both runs.

| Metric | Before | Published release |
| --- | ---: | ---: |
| Performance | 50 | 98 |
| Accessibility | 85 | 100 |
| Best practices | 100 | 100 |
| SEO automated checks | 100 | 100 |
| First Contentful Paint | 3.7 s | 1.2 s |
| Largest Contentful Paint | 24.5 s | 2.2 s |
| Total Blocking Time | 0 ms | 0 ms |
| Cumulative Layout Shift | 0.325 | 0.007 |
| Speed Index | 4.0 s | 3.0 s |

- [Before report](https://pagespeed.web.dev/analysis/https-khoda-ai/o2pyr6w105?form_factor=mobile)
- [Published report](https://pagespeed.web.dev/analysis/https-khoda-ai/axnx4f07th?form_factor=mobile)

These are individual lab measurements, not field Core Web Vitals. Google showed
no real-user field data. Automated SEO scores do not measure search ranking.

## Google Search Console

Property: https://khoda.ai/ (HTTPS URL prefix).

Google confirmed ownership through its downloaded HTML file,
`google0cbd976d77731379.html`, which remains in source and the live release.
The sitemap submission succeeded; the table showed **Success**, one discovered
page, and a September 8 last-read date. Homepage inspection showed **URL is on
Google** and **Page is indexed** before requesting a fresh crawl.

Google then confirmed **Indexing requested** and added the updated homepage to
a priority crawl queue. The new release is submitted for recrawling; this does
not establish that Google has already refreshed its stored page or ranking.
[Open Khoda URL Inspection](https://search.google.com/search-console/inspect?resource_id=https%3A%2F%2Fkhoda.ai%2F&id=P9L6lKo2GFbpuhwjN0rgbg).

## Deployment and recovery

Source revision: `55473d35f847e9b36588df192fbd232f333ac564`, pushed on
`codex/khoda-seo` in the existing public GitHub repository. The old Azure workflow
was not used; the actual host is the existing DigitalOcean Nginx server at
165.22.147.34. Deployment used its signed-in web console and the pinned public
GitHub archive. No SSH key or additional server credential was created.

Archive SHA-256:
`9b1d896292ec6b4397ea3c3172fd41c892aa9564ab5235c2522daeb02ca2daae`.

Active release:
`/var/www/khoda-ai/releases/20260907T221520Z-seo-55473d35f847`.

Previous release:
`/var/www/khoda-ai/releases/d4d126fbc222-20260722T070533Z`.

Config/deployment backup:
`/var/www/khoda-ai/deploy-backups/20260907T221520Z-seo-55473d35f847/`.

The deployment script only copies allowlisted public files. It validates the
existing layout and configuration, preserves TLS and previous static assets,
runs nginx validation before activation, changes the release symlink atomically,
and rolls back configuration and symlink if activation or acceptance fails.
Its dry run was reviewed against the real host before publishing. A temporary
local fixture also proved rollback after an injected acceptance failure.

HTTPS www/nip aliases redirect to the canonical domain; explicit /index.html
redirects to / while preserving query strings. Unknown URLs still return real
404 responses. HTML and CSS are served with gzip; CSS and fonts receive cache
headers. The rest of the server configuration remains intact.

All 15 deployed public files were checked over external HTTPS and match the
committed source byte for byte. Redirects, headers, error status, local desktop
and mobile navigation, and the live mobile homepage were checked. The live
browser reported no errors or horizontal overflow.

Detailed local evidence is in the ignored `build/seo-evidence/` directory.
Use `npm ci && npm run build` before future releases; see BUILD.md. Google
verification must remain accessible in future deployments.

## Reference guidance

- [Google SEO starter guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
- [Organization structured data](https://developers.google.com/search/docs/appearance/structured-data/organization)
- [Site names](https://developers.google.com/search/docs/appearance/site-names)
