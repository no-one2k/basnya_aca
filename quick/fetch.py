#!/usr/bin/env python3
"""Шаг 2: цитаты с 20 страниц ru.wikiquote и мемы Lurkmore -> quick/quotes.jsonl."""
import collections, html, json, re, time, urllib.parse, urllib.request
from pathlib import Path

UA = "basnya-aca/0.1 (none.from.nowhere@gmail.com)"
WQ, LM = "https://ru.wikiquote.org/w/api.php", "https://lurkmore.media/api.php"
OUT = Path(__file__).with_name("quotes.jsonl")
PAGES = """Брат (фильм); Брат 2; Мастер и Маргарита; Двенадцать стульев; Золотой телёнок;
Иван Васильевич меняет профессию; Бриллиантовая рука;
Кавказская пленница, или Новые приключения Шурика; Джентльмены удачи;
Белое солнце пустыни; Собачье сердце; Горе от ума; Ирония судьбы, или С лёгким паром!;
Служебный роман; Место встречи изменить нельзя; Козьма Прутков;
Понедельник начинается в субботу; Кин-дза-дза!; Тот самый Мюнхгаузен; Generation «П»"""
SKIP = {"См. также", "Ссылки", "Примечания", "Источники"}
Q_RE = re.compile(r"\{\{\s*[Qq]\s*\|")
TAGS = r"</?(?:small|big|span|div|poem|center|i|b|u|s|sup|sub|font|blockquote|p|nowiki|code|tt)\b[^>]*>"

def api(base, **q):
    url = base + "?" + urllib.parse.urlencode({**q, "format": "json", "formatversion": 2})
    for _ in range(3):
        time.sleep(1)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return json.load(r)
        except OSError as e:
            err = e
    raise err

def close(w, i):
    """Индекс сразу за "}}", парным к "{{" в позиции i."""
    depth = 0
    for m in re.finditer(r"\{\{|\}\}", w[i:]):
        depth += 1 if m.group() == "{{" else -1
        if depth == 0:
            return i + m.end()
    return len(w)

def split_params(body):
    """Делит тело шаблона по | только на верхнем уровне {{ }} и [[ ]]."""
    parts, cur, depth = [], "", 0
    for tok in re.split(r"(\{\{|\}\}|\[\[|\]\]|\|)", body):
        if tok in ("{{", "[["):
            depth += 1
        elif tok in ("}}", "]]"):
            depth -= 1
        elif tok == "|" and depth == 0:
            parts, cur = parts + [cur], ""
            continue
        cur += tok
    return parts + [cur]

def parse_q(body):
    """(текст, автор) из {{Q|...}}: Цитата=/Автор= или позиционные; прочие именованные пропускаются."""
    named, pos = {}, []
    for p in split_params(body)[1:]:
        m = re.match(r"\s*([A-Za-zА-Яа-яЁё]\w{0,15}|\d)\s*=(?!=)", p)
        named.update({m[1]: p[m.end():]}) if m else pos.append(p)
    pos += [""] * 2
    return named.get("Цитата") or named.get("1") or pos[0], named.get("Автор") or named.get("2") or pos[1]

def clean(s):
    s = re.sub(r"<ref[^>]*/>|<ref.*?</ref>|<!--.*?-->", "", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    prev = None
    while prev != s:  # шаблоны изнутри наружу; {{comment|видимое|подсказка}} -> видимое
        prev = s
        s = re.sub(r"\{\{\s*comment\s*\|([^{}|]*)[^{}]*\}\}", r"\1", s, flags=re.I)
        s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"\[\[(?:Файл|File|Изображение|Image):[^\]]*\]\]", "", s, flags=re.I)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", s)
    s = html.unescape(re.sub(TAGS, "", re.sub(r"'{2,}", "", s), flags=re.I))
    lines = (re.sub(r"\s+", " ", ln).strip(" :*") for ln in s.split("\n"))
    return " / ".join(ln for ln in lines if ln)

def quotes(w, stars):
    """(section, text, author) для каждого {{Q}} и, если stars, строки "*" (не "**")."""
    qs, flat, pos = [], "", 0
    while m := Q_RE.search(w, pos):
        end = close(w, m.start())
        qs.append(w[m.start() + 2:end - 2])
        flat, pos = flat + w[pos:m.start()] + f"\0{len(qs) - 1}\0", end
    section, skip = "", False
    for line in (flat + w[pos:]).split("\n"):
        if h := re.match(r"(=+)\s*(.*?)\s*\1\s*$", line):
            section = clean(h[2])
            skip = section in SKIP
        elif skip:
            continue
        elif ids := re.findall(r"\0(\d+)\0", line):
            for i in ids:
                text, author = parse_q(qs[int(i)])
                yield section, clean(text), clean(author)
        elif stars and re.match(r"\*(?!\*)", line):
            yield section, clean(line[1:]), ""

def rec(text, work, section, author, url, source, kind, backlinks):
    return dict(text=text, work=work, section=section, author=author,
                url=url + urllib.parse.quote(work.removeprefix("Lurkmore: ").replace(" ", "_")),
                source=source, kind=kind, backlinks=backlinks)

rows = []
for page in (p.strip() for p in PAGES.replace("\n", " ").split(";")):
    p = api(WQ, action="parse", page=page, prop="wikitext", redirects=1)["parse"]
    recs = [rec(t, p["title"], s, "", "https://ru.wikiquote.org/wiki/", "wikiquote", "quote", None)
            for s, t, _ in quotes(p["wikitext"], stars=True) if len(t) >= 15]
    print(f"{p['title']} → {len(recs)}", flush=True)
    rows += recs

links = api(LM, action="parse", page="Мем", prop="links")["parse"]["links"]
seen = set()
for link in (x["title"] for x in links if x["ns"] == 0 and x.get("exists")):
    d = api(LM, action="parse", page=link, prop="wikitext", redirects=1)
    if "parse" not in d or d["parse"]["title"] in seen:
        print(f"{link}: пропуск ({d.get('error') or 'дубль'})", flush=True)
        continue
    title, w = d["parse"]["title"], d["parse"]["wikitext"]
    seen.add(title)
    bl = len(api(LM, action="query", list="backlinks", bltitle=title, blnamespace=0, bllimit=500)["query"]["backlinks"])
    lm = lambda t, a, k: rec(t, f"Lurkmore: {title}", "", a, "https://lurkmore.media/", "lurkmore", k, bl)
    recs = [lm(title, "", "meme")] + [lm(t, a, "meme_quote") for _, t, a in quotes(w, stars=False) if len(t) >= 15]
    print(f"{title} → {len(recs)} (backlinks {bl})", flush=True)
    rows += recs

OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
print("итого:", dict(collections.Counter(r["source"] for r in rows)), "мемов:", sum(r["kind"] == "meme" for r in rows))
