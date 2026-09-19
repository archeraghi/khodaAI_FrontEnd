# Building the static website

The site serves ordinary HTML, images and a precompiled stylesheet. No browser
framework, JavaScript compiler or Node.js runtime is required on the web server.

```sh
npm ci
npm run build
```

The build runs `scripts/build-pages.py`, compiles Tailwind CSS and runs
`scripts/check-site.py`. Python 3.12+ and Node.js are build-time dependencies.

## Editing content

Edit the reviewed English, German and Simplified Chinese copy in
`content/site.json` and the shared HTML layout in `scripts/build-pages.py`.
The six generated public pages are:

- `/` and `/lifetoy/`
- `/de/` and `/de/lifetoy/`
- `/zh/` and `/zh/lifetoy/`

The generator writes their `index.html` files and `sitemap.xml`. It supplies
page-specific metadata, self-canonicals, reciprocal language alternates and
Organization, Person, WebSite and WebPage structured data. The platform pages
also include breadcrumbs. Do not edit the generated HTML directly.

Tailwind scans all six HTML pages using `tailwind.config.cjs` and
`styles/site.css`. The compiled output is `assets/site.css`. Commit generated
HTML, the sitemap and CSS together with their sources. `npm run check` verifies
metadata, language groups, local links and anchors, sitemap coverage, structured
data, ownership verification and the deployment allowlist.

`npm run watch:css` watches CSS changes during local editing. Run
`npm run build:pages` after a content change and `npm run build` before release.
For a loopback preview, run `python3 -m http.server 8879 --bind 127.0.0.1`.

## Deploying

Use the existing DigitalOcean/Nginx deployment flow in `deploy/deploy.py`.
The helper copies only its 20 allowlisted public assets, including all six
pages and the unchanged Google ownership file. It validates the expected host
configuration, atomically switches releases and rolls back on failure. Run
its dry run against the actual host before publishing a pinned revision.
The repository's old Azure workflow is not the current production path.

Do not deploy `node_modules`, content sources, build scripts or evidence files.
Production uses only the generated public artifacts. See
`docs/SEO-2026-09-19.md` for this release's scope and remaining live checks.
