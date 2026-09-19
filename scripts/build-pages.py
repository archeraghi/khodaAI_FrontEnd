#!/usr/bin/env python3
"""Build six public HTML pages from reviewed EN/DE/ZH company copy."""
from html import escape as e
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = "https://khoda.ai"
COPY = json.loads((ROOT / "content/site.json").read_text())
LANGUAGES = {"en": "English", "de": "Deutsch", "zh": "简体中文"}


def path(lang, platform=False):
    return ("/" if lang == "en" else f"/{lang}/") + ("lifetoy/" if platform else "")


def paragraphs(items):
    return "\n".join(f'<p class="mt-5 text-lg leading-relaxed text-kh-mute">{e(text)}</p>' for text in items)


def cards(items, columns="md:grid-cols-2"):
    return f'<div class="mt-10 grid {columns} gap-6">' + "".join(
        f'<article class="rounded-2xl border border-black/10 bg-white p-6"><h3 class="text-xl font-semibold">{e(title)}</h3><p class="mt-3 leading-relaxed text-kh-mute">{e(body)}</p></article>'
        for title, body in items) + '</div>'


def store_status(t):
    # Informative text only: there are no public store listing URLs yet.
    return '<div class="mt-6 flex flex-wrap gap-3">' + ''.join(
        f'<span class="rounded-xl border border-black/10 bg-white px-4 py-3 text-sm font-semibold">{e(t[key])}</span>'
        for key in ('appStoreStatus', 'googlePlayStatus')) + '</div>'


def section(title, body, id="", pale=False, wide=False):
    return f'<section{f" id={chr(34)}{id}{chr(34)}" if id else ""} class="py-16 sm:py-20{ " bg-kh-blush/30" if pale else ""}"><div class="mx-auto {"max-w-6xl" if wide else "max-w-3xl"} px-5 sm:px-8"><h2 class="text-3xl font-bold leading-tight">{e(title)}</h2>{body}</div></section>'


def image_block(title, texts, alt, image):
    return f'<section id="lifetoy" class="bg-kh-blush/30 py-16 sm:py-20"><div class="mx-auto max-w-6xl px-5 sm:px-8 grid md:grid-cols-2 gap-10 items-center"><img src="/images/{image}.webp" alt="{e(alt)}" width="1024" height="1024" loading="lazy" decoding="async" class="mx-auto w-full max-w-sm h-auto rounded-3xl"/><div><h2 class="text-3xl font-bold leading-tight">{e(title)}</h2>{texts}</div></div></section>'


def generate(lang, platform):
    t = COPY[lang]
    url = ORIGIN + path(lang, platform)
    home = path(lang)
    product = path(lang, True)
    lifetoy = 'https://lifetoy.ai' + home
    title = t['productTitle' if platform else 'homeTitle']
    description = t['productDescription' if platform else 'homeDescription']
    alternates = {language: ORIGIN + path(language, platform) for language in LANGUAGES}
    alternates['x-default'] = alternates['en']
    alternate_tags = '\n'.join(f'<link rel="alternate" hreflang="{key}" href="{href}"/>' for key, href in alternates.items())
    graph = [
        {"@type": "Organization", "@id": ORIGIN + "/#organization", "name": "Khoda AI", "legalName": "Khoda AI LLC", "url": ORIGIN + "/", "logo": {"@type": "ImageObject", "url": ORIGIN + "/images/logo.png", "width": 1024, "height": 1024}, "email": "info@khoda.ai", "founder": {"@id": ORIGIN + "/#founder"}, "brand": {"@type": "Brand", "name": "LifeToy", "url": "https://lifetoy.ai/"}},
        {"@type": "Person", "@id": ORIGIN + "/#founder", "name": "Dr. Ahmad Reza Cheraghi", "url": ORIGIN + "/#founder", "image": ORIGIN + "/images/me.jpg"},
        {"@type": "WebSite", "@id": ORIGIN + "/#website", "name": "Khoda AI", "url": ORIGIN + "/", "inLanguage": list(LANGUAGES), "publisher": {"@id": ORIGIN + "/#organization"}},
        {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": title, "description": description, "inLanguage": lang, "isPartOf": {"@id": ORIGIN + "/#website"}, "about": {"@id": ORIGIN + "/#organization"}}
    ]
    if platform:
        graph[-1]['breadcrumb'] = {"@id": url + "#breadcrumb"}
        graph.append({"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Khoda AI", "item": ORIGIN + home}, {"@type": "ListItem", "position": 2, "name": "LifeToy", "item": url}]})
    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2).replace('<', '\\u003c')
    languages = ' '.join(f'<a href="{path(code, platform)}" hreflang="{code}" lang="{code}"{ " aria-current=\"page\"" if code == lang else ""} class="rounded-md px-2 py-1 hover:bg-kh-blush{ " font-semibold text-kh-bright bg-kh-blush/50" if code == lang else ""}">{label}</a>' for code, label in LANGUAGES.items())
    nav = ''.join(f'<a href="{href}" class="hover:text-kh-bright">{e(label)}</a>' for href, label in zip([home, product, home + '#founder', '#contact'], t['nav']))
    eyebrow = t['platformEyebrow' if platform else 'companyEyebrow']
    heading = t['platformHeading' if platform else 'companyHeading']
    intro = t['platformIntro' if platform else 'companyIntro']
    second = t['platformSecond' if platform else 'companySecond']
    primary_href = lifetoy if platform else product
    primary = t['platformPrimary' if platform else 'primary']
    hero_image = 'bearie' if platform else 'logo'
    hero_alt = t['bearAlt' if platform else 'logoAlt']
    content = f'''<section id="top" class="bg-kh-blush/30 py-16 sm:py-20"><div class="mx-auto max-w-6xl px-5 sm:px-8 grid lg:grid-cols-2 gap-8 items-center"><div><p class="text-sm font-semibold text-kh-bright">{e(eyebrow)}</p><h1 class="mt-4 text-4xl sm:text-5xl font-extrabold leading-tight">{e(heading)}</h1>{paragraphs([intro, second])}<div class="mt-8 flex flex-wrap gap-3"><a href="{primary_href}" class="rounded-xl bg-kh-bright px-5 py-3 text-white font-semibold hover:bg-kh-base">{e(primary)}</a><a href="#contact" class="rounded-xl border border-kh-mute px-5 py-3 font-semibold hover:bg-white">{e(t['secondary'])}</a></div></div><img src="/images/{hero_image}.webp" alt="{e(hero_alt)}" width="1024" height="1024" fetchpriority="high" class="mx-auto w-full max-w-xs sm:max-w-md h-auto rounded-3xl"/></div></section>'''
    if platform:
        breadcrumb_label = {'en': 'Breadcrumb', 'de': 'Brotkrumennavigation', 'zh': '面包屑导航'}[lang]
        content = f'<nav aria-label="{breadcrumb_label}" class="mx-auto max-w-6xl px-5 sm:px-8 py-4 text-sm"><ol class="flex flex-wrap gap-3"><li><a href="{home}" class="underline hover:text-kh-bright">Khoda AI</a></li><li aria-hidden="true">/</li><li aria-current="page">LifeToy</li></ol></nav>' + content
        content += section(t['meaningTitle'], paragraphs(t['meaning']))
        content += section(t['layersTitle'], paragraphs([t['layersIntro']]) + cards(t['layers']), wide=True)
        content += image_block(t['bearTitle'], paragraphs(t['bear']), t['bearAlt'], 'bearie')
        app_detail_link = f'<a href="{lifetoy}#app" class="mt-6 inline-block font-semibold underline text-kh-bright">{e(t["appLink"])}</a>'
        content += section(t['appTitle'], paragraphs(t['app']) + store_status(t) + app_detail_link, id='app')
        marketplace_link = f'<a href="{lifetoy}#marketplace" class="mt-6 inline-block font-semibold underline text-kh-bright">{e(t["marketplaceLink"])}</a>'
        content += section(t['marketplaceTitle'], paragraphs(t['marketplace']) + marketplace_link, id='marketplace', pale=True)
        content += section(t['planningTitle'], cards(t['planning']), wide=True)
        faqs = ''.join(f'<details class="border-b border-black/10 py-5"><summary class="cursor-pointer text-lg font-semibold">{e(question)}</summary><p class="mt-3 text-kh-mute leading-relaxed">{e(answer)}</p></details>' for question, answer in t['faqs'])
        guides = ''.join(f'<a href="{lifetoy}{slug}" class="underline hover:text-kh-bright">{e(label)}</a>' for slug, label in zip(['ai-toys', 'ai-plushies'], t['guideLinks']))
        content += section(t['faqTitle'], f'<div class="mt-6">{faqs}</div><div class="mt-8 flex flex-wrap gap-5">{guides}</div>')
    else:
        content += section(t['missionTitle'], paragraphs(t['mission']), id='mission')
        product_text = paragraphs(t['homeProduct']) + f'<a href="{product}" class="mt-6 inline-block font-semibold underline text-kh-bright">{e(t["homeProductLink"])}</a>'
        content += image_block(t['homeProductTitle'], product_text, t['bearAlt'], 'bearie')
        app_link = f'<a href="{product}#app" class="mt-6 inline-block font-semibold underline text-kh-bright">{e(t["homeAppLink"])}</a>'
        content += section(t['homeAppTitle'], paragraphs(t['homeApp']) + store_status(t) + app_link, id='app')
        content += section(t['visionTitle'], paragraphs(t['vision']), id='vision')
        content += section(t['companyCardsTitle'], cards(t['companyCards'], 'md:grid-cols-3'), id='approach', wide=True)
        content += f'<section id="founder" class="py-16 sm:py-20"><div class="mx-auto max-w-6xl px-5 sm:px-8 grid md:grid-cols-2 gap-10 items-center"><img src="/images/me.webp" width="1320" height="1287" loading="lazy" decoding="async" alt="{e(t["founderAlt"])}" class="w-full h-auto rounded-3xl"/><div><h2 class="text-3xl font-bold leading-tight">{e(t["founderTitle"])}</h2>{paragraphs(t["founder"])}</div></div></section>'
    content += section(t['contactTitle'], paragraphs([t['contact']]) + f'<div class="mt-8 flex flex-wrap gap-4"><a href="mailto:info@khoda.ai" class="rounded-xl bg-kh-bright px-5 py-3 font-semibold text-white hover:bg-kh-base">{e(t["email"])}</a><a href="{lifetoy}" class="rounded-xl border border-kh-mute px-5 py-3 font-semibold hover:bg-white">{e(t["visit"])}</a></div>', id='contact', pale=True)
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{e(title)}</title>
<meta name="description" content="{e(description)}"/>
<link rel="canonical" href="{url}"/>
{alternate_tags}
<meta name="robots" content="index, follow, max-image-preview:large"/>
<meta name="theme-color" content="#C62832"/>
<meta property="og:type" content="website"/>
<meta property="og:site_name" content="Khoda AI"/>
<meta property="og:locale" content="{t['locale']}"/>
<meta property="og:url" content="{url}"/>
<meta property="og:title" content="{e(title)}"/>
<meta property="og:description" content="{e(description)}"/>
<meta property="og:image" content="{ORIGIN}/images/logo.png"/>
<meta property="og:image:type" content="image/png"/>
<meta property="og:image:width" content="1024"/>
<meta property="og:image:height" content="1024"/>
<meta property="og:image:alt" content="{e(t['logoAlt'])}"/>
<meta name="twitter:card" content="summary"/>
<meta name="twitter:title" content="{e(title)}"/>
<meta name="twitter:description" content="{e(description)}"/>
<meta name="twitter:image" content="{ORIGIN}/images/logo.png"/>
<meta name="twitter:image:alt" content="{e(t['logoAlt'])}"/>
<script type="application/ld+json">{schema}</script>
<link rel="stylesheet" href="/assets/site.css"/>
<link rel="preload" href="/fonts/inter-latin-wght-400-800.woff2" as="font" type="font/woff2" crossorigin/>
<link rel="icon" type="image/png" sizes="96x96" href="/favicon.png"/>
</head>
<body class="font-sans text-kh-ink bg-white">
<a href="#content" class="skip-link">{e(t['skip'])}</a>
<header class="border-b border-black/5 bg-white"><div class="mx-auto max-w-6xl px-5 sm:px-8 py-4"><div class="flex flex-wrap gap-3 items-center justify-between"><a href="{home}" class="flex items-center gap-2 font-semibold text-lg"><img src="/images/logo.webp" width="1024" height="1024" alt="" class="w-12 h-12"/>Khoda <span class="text-kh-bright">AI</span></a><nav aria-label="{e(t['languageLabel'])}" class="flex flex-wrap gap-1 text-sm">{languages}</nav></div><nav aria-label="{e(t['nav'][0])}" class="mt-3 flex flex-wrap gap-x-6 gap-y-3 text-sm font-medium">{nav}</nav></div></header>
<main id="content">{content}</main>
<footer class="border-t border-black/10"><div class="mx-auto max-w-6xl px-5 sm:px-8 py-8"><div class="flex flex-wrap gap-x-6 gap-y-3 text-sm">{nav}</div><p class="mt-5 text-sm text-kh-mute">© 2026 {e(t['footer'])}</p></div></footer>
</body>
</html>
'''


def main():
    urls = []
    for lang in LANGUAGES:
        for platform in (False, True):
            relative = path(lang, platform).strip('/')
            destination = ROOT / relative / 'index.html'
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(generate(lang, platform))
            alternates = {code: ORIGIN + path(code, platform) for code in LANGUAGES}
            alternates['x-default'] = alternates['en']
            links = ''.join(f'<xhtml:link rel="alternate" hreflang="{code}" href="{url}"/>' for code, url in alternates.items())
            urls.append(f'  <url><loc>{ORIGIN}{path(lang, platform)}</loc>{links}</url>')
    (ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + '\n'.join(urls) + '\n</urlset>\n')
    print(f'Built {len(urls)} static pages and sitemap.xml')


if __name__ == '__main__':
    main()
