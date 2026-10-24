"""Build the livstay.org static site into _site/.

Usage: python3 tools/build_site.py   (needs: pip install markdown)
Sources: site/index.html, site/style.css, site/CNAME, site/content/*.md, spec/livstay-0.1.md
"""
import re, markdown, html, os, shutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'_site'); O=os.path.join(OUT,'docs')
shutil.rmtree(OUT,ignore_errors=True); os.makedirs(O)
for f in ('index.html','style.css','CNAME'):
    shutil.copy(os.path.join(ROOT,'site',f),os.path.join(OUT,f))
SRC={'specification':os.path.join(ROOT,'spec','livstay-0.1.md')}
def source(slug): return SRC.get(slug,os.path.join(ROOT,'site','content',slug+'.md'))
REPO='https://github.com/livaroundltd/livstay'
pages=[('introduction','Introduction','Overview'),('specification','Specification 0.1','Overview'),
 ('guide-host-platforms','Host platforms','Guides'),('guide-agents','Agent builders','Guides'),
 ('path-to-1','Path to 1.0','Project'),('license','License','Project')]
desc={'introduction':'What LivStay is, how it extends the Personal Agent Protocol, and its four levels.',
 'specification':'LivStay draft 0.1: the normative specification of the livstay.org/stays extension.',
 'guide-host-platforms':'How a host platform goes from listed to bookable under LivStay.',
 'guide-agents':'How a personal agent finds, quotes, asks about and books a LivStay home.',
 'path-to-1':'How LivStay becomes stable, the feedback requested and the open topics.',
 'license':'LivStay is licensed under the Apache License 2.0.'}
for i,(slug,title,grp) in enumerate(pages):
    src=open(source(slug)).read()
    if slug=='specification':
        src=re.sub(r'## Contents\n.*?\n---\n','',src,flags=re.S)
    md=markdown.Markdown(extensions=['tables','fenced_code','toc','sane_lists'],extension_configs={'toc':{'toc_depth':'2'}})
    body=md.convert(src)
    body=re.sub(r'<table>(.*?)</table>',r'<div class="tbl"><table>\1</table></div>',body,flags=re.S)
    toc=md.toc_tokens[0]['children'] if md.toc_tokens and md.toc_tokens[0]['level']==1 else md.toc_tokens
    rail=[]; cur=None
    for s2,t2,g2 in pages:
        if g2!=cur:
            if cur: rail.append('</ul>')
            rail.append(f'<p class="grp">{g2}</p><ul>'); cur=g2
        ac=' aria-current="page"' if s2==slug else ''
        rail.append(f'<li><a href="{s2}.html"{ac}>{t2}</a></li>')
        if s2==slug and slug in('specification',) :
            rail.append('</ul><ul class="toc">'+''.join(f'<li><a href="#{h["id"]}">{html.escape(h["name"])}</a></li>' for h in toc)+'</ul><ul>')
    rail.append('</ul>')
    prev=pages[i-1] if i>0 else None; nxt=pages[i+1] if i+1<len(pages) else None
    pager='<nav class="pager" aria-label="Pages">'+(f'<a href="{prev[0]}.html"><small>Previous</small>{prev[1]}</a>' if prev else '<span></span>')+(f'<a href="{nxt[0]}.html" style="text-align:right"><small>Next</small>{nxt[1]}</a>' if nxt else '')+'</nav>'
    topcur=lambda k: ' aria-current="page"' if k==slug else ''
    out=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="claude:viewport-fit-sides" content="cover">
<title>{title} · LivStay</title><meta name="description" content="{desc[slug]}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&family=JetBrains+Mono:wght@400;600&display=swap">
<link rel="canonical" href="https://livstay.org/docs/{slug}.html">
<link rel="stylesheet" href="../style.css"></head><body>
<header class="bar"><div class="in">
<a class="mark" href="../index.html"><i aria-hidden="true"></i>LivStay</a>
<nav class="top" aria-label="Site"><a href="introduction.html"{topcur('introduction')}>Docs</a><a href="specification.html"{topcur('specification')}>Specification</a><a href="path-to-1.html"{topcur('path-to-1')}>Path to 1.0</a><a href="{REPO}">GitHub</a></nav>
<span class="status">Draft 0.1 · Poppy 0.2</span></div></header>
<div class="layout"><aside class="rail"><nav aria-label="Documentation">{''.join(rail)}</nav></aside>
<main id="main">{body}{pager}</main></div>
<footer class="foot"><div class="in"><span>LivStay · an open protocol started by LivAround Ltd</span><span><a href="license.html">Apache License 2.0</a> · <a href="{REPO}">GitHub</a> · Examples are fictional</span></div></footer>
</body></html>'''
    open(f'{O}/{slug}.html','w').write(out)
print('built', len(pages), 'pages into', OUT)
