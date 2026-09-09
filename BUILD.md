# Building the static website styles

The website serves ordinary HTML, images, and a precompiled stylesheet. It does
not need a browser-side Tailwind compiler, JavaScript framework, or Node.js on
the web server.

Install the pinned development dependency and rebuild the stylesheet:

```sh
npm ci
npm run build
```

Tailwind scans the complete class names in `index.html`, using the theme in
`tailwind.config.cjs` and the extra CSS in `styles/site.css`. The minified output
is `assets/site.css`. Rebuild it whenever those source files change. Include the
generated stylesheet with the website when deploying; do not deploy
`node_modules`.

For local editing, `npm run watch:css` rebuilds when the source changes. Run
`npm run build` once more before deployment to produce the minified stylesheet.

The page loads the result with this element in its `<head>`:

```html
<link rel="stylesheet" href="/assets/site.css" />
```

The build uses the official [Tailwind CSS 3 CLI](https://v3.tailwindcss.com/docs/installation)
with the exact dependency version and transitive dependencies recorded in
`package-lock.json`.
