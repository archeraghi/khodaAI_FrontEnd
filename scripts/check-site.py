#!/usr/bin/env python3
"""Check generated crawlable pages, link targets, languages and deployment coverage."""
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = 'https://khoda.ai'


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.alternates, self.schemas = [], set(), {}, []
        self.canonical, self.lang, self.h1 = None, None, 0
        self.title, self.description, self.og_url = '', '', ''
        self.in_schema = self.in_title = False
        self.schema_text = ''
        self.feed(source)

    def handle_starttag(self, tag, attributes):
        a = dict(attributes)
        if a.get('id'):
            assert a['id'] not in self.ids, f'Duplicate id {a["id"]}'
            self.ids.add(a['id'])
        if tag == 'html': self.lang = a.get('lang')
        if tag == 'h1': self.h1 += 1
        if tag == 'title': self.in_title = True
        if tag == 'meta' and a.get('name') == 'description': self.description = a.get('content')
        if tag == 'meta' and a.get('property') == 'og:url': self.og_url = a.get('content')
        if tag == 'meta' and a.get('name') == 'robots': assert 'noindex' not in a.get('content', '')
        if tag == 'link' and a.get('rel') == 'canonical':
            assert self.canonical is None, 'Duplicate canonical'
            self.canonical = a.get('href')
        if tag == 'link' and a.get('rel') == 'alternate': self.alternates[a['hreflang']] = a['href']
        if tag in ('a', 'link') and a.get('href'): self.links.append(a['href'])
        if tag == 'img':
            assert all(k in a for k in ('alt', 'width', 'height'))
            self.links.append(a['src'])
        if tag == 'script' and a.get('type') == 'application/ld+json': self.in_schema = True

    def handle_data(self, data):
        if self.in_schema: self.schema_text += data
        if self.in_title: self.title += data

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == 'script' and self.in_schema:
            self.schemas.append(json.loads(self.schema_text))
            self.in_schema, self.schema_text = False, ''


def main():
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
    entries = ET.parse(ROOT / 'sitemap.xml').getroot().findall('s:url', ns)
    pages = {}
    for entry in entries:
        url = entry.findtext('s:loc', namespaces=ns)
        filename = ROOT / urlsplit(url).path.strip('/') / 'index.html'
        assert filename.is_file(), url
        page = pages[url] = Page(filename.read_text())
        assert page.canonical == page.og_url == url, url
        assert page.h1 == 1 and page.title and page.description, url
        assert set(page.alternates) == {'en', 'de', 'zh', 'x-default'}, url
        assert page.alternates[page.lang] == url, url
        assert page.alternates['x-default'] == page.alternates['en'], url
        assert {a.attrib['hreflang']: a.attrib['href'] for a in entry.findall('x:link', ns)} == page.alternates
        graph = page.schemas[0]['@graph']
        webpage = next(item for item in graph if item['@type'] == 'WebPage')
        assert webpage['url'] == url and webpage['inLanguage'] == page.lang
        assert webpage['name'] == page.title and webpage['description'] == page.description
        assert not any(item['@type'] in ('Product', 'Review', 'AggregateRating') for item in graph)
    assert len(pages) == 6
    assert len({p.title for p in pages.values()}) == len(pages)
    for url, page in pages.items():
        for alternate in page.alternates.values():
            assert pages[alternate].alternates == page.alternates, f'Non-reciprocal: {url}'
        for link in page.links:
            parts = urlsplit(link)
            if parts.scheme == 'mailto' or parts.netloc and parts.netloc != 'khoda.ai': continue
            pathname = parts.path or urlsplit(url).path
            target = ROOT / pathname.lstrip('/')
            if target.is_dir(): target /= 'index.html'
            assert target.is_file(), f'Broken local link {url} -> {link}'
            if parts.fragment:
                linked = pages.get(ORIGIN + pathname)
                assert linked and parts.fragment in linked.ids, f'Missing fragment {url} -> {link}'
    spec = importlib.util.spec_from_file_location('deploy', ROOT / 'deploy/deploy.py')
    deploy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(deploy)
    for url in pages:
        assert urlsplit(url).path.lstrip('/') + 'index.html' in deploy.PUBLIC_FILES
    for asset in deploy.PUBLIC_FILES: deploy.regular_file(ROOT, asset)
    assert (ROOT / 'google0cbd976d77731379.html').read_text().strip() == 'google-site-verification: google0cbd976d77731379.html'
    assert 'https://khoda.ai/sitemap.xml' in (ROOT / 'robots.txt').read_text()
    print(f'Checked {len(pages)} pages: unique metadata, reciprocal hreflang, sitemap, links, schema and {len(deploy.PUBLIC_FILES)} deploy assets')


if __name__ == '__main__':
    main()
