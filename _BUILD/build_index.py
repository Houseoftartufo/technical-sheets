import argparse,base64,json,html as H
from pathlib import Path

from i18n import DATA_FILES, LANGS, load_products_file

ROOT=Path(__file__).resolve().parents[1]
BUILD=Path(__file__).resolve().parent
LOGO=base64.b64encode((ROOT/"house-of-tartufo-logo.png").read_bytes()).decode()
def esc(s): return H.escape(s,quote=True)
CSS="""@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Manrope:wght@400;500;600&display=swap');
:root{color-scheme:light;--hot-bg:#f6f2ea;--hot-bg-elevated:#fffdf8;--hot-panel:#fffdf9;--hot-panel-soft:#eee6da;--hot-ink:#2b211b;--hot-ink-muted:#75685f;--hot-ink-dim:#9a8b80;--hot-accent:#9b7446;--hot-accent-dark:#765131;--hot-primary:#5b4030;--hot-primary-hover:#493226;--hot-on-primary:#fffaf2;--hot-line:rgba(72,52,40,.12);--hot-line-strong:rgba(72,52,40,.23);--hot-radius:18px;--hot-radius-control:12px;--hot-pill:999px;--hot-shadow-panel:0 24px 70px rgba(72,52,40,.08);--hot-shadow-header:0 8px 28px rgba(72,52,40,.035);--hot-transition:160ms ease}
*{margin:0;padding:0;box-sizing:border-box}
body{min-height:100vh;padding:0 24px 28px;color:var(--hot-ink);font-family:'Manrope',system-ui,sans-serif;background:radial-gradient(circle at 84% 4%,rgba(185,154,113,.16),transparent 32rem),radial-gradient(circle at 12% 22%,rgba(214,199,180,.26),transparent 28rem),linear-gradient(180deg,#fbf8f2 0%,var(--hot-bg) 46rem,#f4efe7 100%)}
.wrap{width:min(1500px,100%);margin:0 auto}
.head{position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:22px;min-height:88px;margin-bottom:30px;padding:12px 0;background:rgba(251,248,242,.92);border-bottom:1px solid var(--hot-line);box-shadow:var(--hot-shadow-header);backdrop-filter:blur(18px) saturate(120%)}
.logo{width:124px;height:40px;flex:0 0 124px;background:url('data:image/png;base64,__L__') no-repeat center;background-size:contain}
.htxt{padding-left:22px;border-left:1px solid var(--hot-line-strong)}
.htxt h1{color:#30231c;font-family:'Cormorant Garamond',Georgia,serif;font-size:clamp(32px,4vw,48px);font-weight:500;line-height:.98;letter-spacing:-.025em}
.htxt p{margin:0 0 3px;color:var(--hot-accent-dark);font-size:10px;font-weight:600;letter-spacing:.18em;text-transform:uppercase}
.toolbar{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:14px;margin-bottom:8px}
.search{position:relative;flex:1;min-width:240px}
.search input{width:100%;min-height:50px;padding:12px 16px 12px 44px;border:1px solid rgba(72,52,40,.13);border-radius:var(--hot-radius-control);outline:0;background:rgba(255,253,249,.92);box-shadow:0 5px 18px rgba(72,52,40,.025);color:var(--hot-ink);font:500 14px 'Manrope',system-ui,sans-serif;transition:border-color var(--hot-transition),box-shadow var(--hot-transition)}
.search input::placeholder{color:var(--hot-ink-dim);font-weight:400}
.search input:focus{border-color:rgba(91,64,48,.38);box-shadow:0 0 0 3px rgba(155,116,70,.08)}
.search svg{position:absolute;left:15px;top:50%;width:17px;height:17px;transform:translateY(-50%);fill:var(--hot-accent-dark)}
.langsel{display:flex;gap:3px;padding:4px;border:1px solid var(--hot-line-strong);border-radius:var(--hot-pill);background:rgba(255,253,249,.58)}
.langsel button{min-width:48px;min-height:44px;padding:7px 12px;border:1px solid transparent;border-radius:var(--hot-pill);background:transparent;color:var(--hot-primary);font:600 11px 'Manrope',system-ui,sans-serif;cursor:pointer;transition:background var(--hot-transition),color var(--hot-transition),border-color var(--hot-transition)}
.langsel button:hover{background:#eee5d8}
.langsel button.active{background:var(--hot-primary);color:var(--hot-on-primary)}
.langsel button:focus-visible,.langs a:focus-visible{outline:3px solid rgba(155,116,70,.32);outline-offset:2px}
.count{margin:14px 0 22px;color:var(--hot-ink-muted);font-size:11px;font-weight:500;letter-spacing:.02em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:16px}
.card{min-width:0;padding:18px 20px;border:1px solid var(--hot-line);border-radius:var(--hot-radius);background:rgba(255,253,249,.88);box-shadow:var(--hot-shadow-panel);transition:transform var(--hot-transition),border-color var(--hot-transition),box-shadow var(--hot-transition)}
.card:hover{transform:translateY(-2px);border-color:var(--hot-line-strong);box-shadow:0 26px 72px rgba(72,52,40,.11)}
.card.duplicate{border-color:rgba(155,116,70,.55);box-shadow:0 0 0 3px rgba(155,116,70,.10),var(--hot-shadow-panel)}
.num{color:var(--hot-accent);font-size:10px;font-weight:700;letter-spacing:.16em}
.pname{min-height:46px;margin:5px 0 13px;color:var(--hot-ink);font-size:14px;font-weight:600;line-height:1.55}
.langs{display:flex;flex-wrap:wrap;gap:5px}
.langs a{display:inline-flex;min-width:48px;min-height:44px;align-items:center;justify-content:center;padding:6px 12px;border:1px solid rgba(91,64,48,.30);border-radius:var(--hot-pill);background:rgba(255,253,249,.48);color:var(--hot-primary);font-size:10px;font-weight:600;text-decoration:none;transition:background var(--hot-transition),color var(--hot-transition),border-color var(--hot-transition)}
.langs a.cur,.langs a:hover{border-color:var(--hot-primary);background:var(--hot-primary);color:var(--hot-on-primary)}
.nores{display:none;margin-top:14px;padding:36px;border:1px solid var(--hot-line);border-radius:var(--hot-radius);background:rgba(255,253,249,.70);color:var(--hot-ink-muted);font-size:13px;text-align:center}
.foot{margin-top:34px;padding:18px 8px 0;border-top:1px solid var(--hot-line);color:var(--hot-ink-dim);font-size:10px;line-height:1.7;text-align:center}
@media(max-width:760px){body{padding-inline:14px}.head{min-height:76px;margin-bottom:22px;gap:15px}.logo{width:104px;height:34px;flex-basis:104px}.htxt{padding-left:15px}.htxt h1{font-size:clamp(28px,7vw,38px)}.toolbar{align-items:stretch}.search{min-width:100%;flex-basis:100%}.langsel{justify-content:space-between;width:100%}.langsel button{flex:1;min-width:0}.grid{grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr))}}
@media(max-width:420px){body{padding-inline:10px}.head{gap:11px}.logo{width:82px;height:28px;flex-basis:82px}.htxt{padding-left:11px}.htxt h1{font-size:29px}.htxt p{font-size:8px;letter-spacing:.12em}.card{padding:16px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important;animation:none!important}}""".replace("__L__",LOGO)
JS_TEMPLATE="""var UI=__UI__;__SEARCH__
var q=document.getElementById('q'),cards=[].slice.call(document.querySelectorAll('.card')),grid=document.getElementById('grid'),shown=document.getElementById('shown'),nores=document.getElementById('nores');
var originalOrder=new Map(cards.map(function(card,index){return [card,index]}));
function setLang(L){cards.forEach(function(c){var p=c.querySelector('.pname');p.textContent=p.getAttribute('data-'+L.toLowerCase());c.querySelectorAll('.lang').forEach(function(a){a.classList.toggle('cur',a.textContent===L);});});document.getElementById('q').placeholder=UI[L][0];document.getElementById('counttxt').textContent=UI[L][1];document.getElementById('nores').textContent=UI[L][2];document.getElementById('subtitle').textContent=UI[L][3];document.documentElement.lang={ITA:'it',FR:'fr',ENG:'en',NL:'nl',DE:'de'}[L];}
function apply(){var t=q.value,n=0,ranked=cards.map(function(c){var names=JSON.parse(c.getAttribute('data-search'));return {card:c,score:ProductSearch.score(t,names),order:originalOrder.get(c)};});ranked.sort(function(a,b){return b.score-a.score||a.order-b.order;});ranked.forEach(function(item){var match=item.score>=0;item.card.style.display=match?'':'none';grid.appendChild(item.card);if(match)n++;});shown.textContent=n;nores.style.display=n?'none':'block';}
q.addEventListener('input',apply);document.getElementById('langsel').addEventListener('click',function(e){if(e.target.tagName!=='BUTTON')return;document.querySelectorAll('.langsel button').forEach(function(b){b.classList.remove('active')});e.target.classList.add('active');setLang(e.target.getAttribute('data-l'));});setLang('ITA');apply();"""


def load_static_titles(build_dir=BUILD):
    products = []
    for filename in DATA_FILES:
        products.extend(load_products_file(Path(build_dir) / filename))
    return {product["folder"]: product["title"] for product in products}


def load_dynamic_titles(path):
    if path is None:
        return {}
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("dynamic products metadata must be an object keyed by product folder")
    result = {}
    for folder, titles in value.items():
        if not isinstance(folder, str) or not folder or not isinstance(titles, dict):
            raise ValueError("invalid dynamic product metadata")
        missing = [language for language in LANGS if not isinstance(titles.get(language), str) or not titles[language].strip()]
        if missing:
            raise ValueError(f"{folder} has missing localized title(s): {', '.join(missing)}")
        result[folder] = {language: titles[language] for language in LANGS}
    return result


def build_index(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    parser.add_argument("--dynamic-products",type=Path)
    parser.add_argument("--static-products",type=Path,help="JSON list of static folders to include; omit to include the full legacy catalog")
    parser.add_argument("--site-root",type=Path,default=ROOT)
    args=parser.parse_args(argv)
    site_root=args.site_root.resolve()
    output=(args.output or site_root/"index.html").resolve()
    all_static_titles=load_static_titles()
    if args.static_products:
        selected=json.loads(args.static_products.read_text(encoding="utf-8"))
        if not isinstance(selected,list) or any(not isinstance(folder,str) for folder in selected):
            raise ValueError("static products metadata must be a JSON list of folder names")
        unknown=sorted(set(selected)-set(all_static_titles))
        if unknown:
            raise ValueError("static products metadata contains unknown folder(s): "+", ".join(unknown))
        static_titles={folder:all_static_titles[folder] for folder in selected}
    else:
        static_titles=all_static_titles
    dynamic_titles=load_dynamic_titles(args.dynamic_products)
    collisions=sorted(set(static_titles) & set(dynamic_titles))
    if collisions:
        raise ValueError("dynamic product folder collides with a static product: " + ", ".join(collisions))
    titles={**static_titles, **dynamic_titles}
    folders=sorted(titles)
    for folder in folders:
        if not (site_root/folder).is_dir():
            raise ValueError(f"product folder is missing from site root: {folder}")

    cards=[]
    for folder in folders:
        localized_titles=titles[folder]
        search=esc(json.dumps([localized_titles.get(language,"") for language in LANGS],ensure_ascii=False))
        data=" ".join('data-%s="%s"'%(language.lower(),esc(localized_titles.get(language,folder))) for language in LANGS)
        links="".join('<a class="lang" href="%s/%s_%s.pdf">%s</a>'%(folder,folder,language,language) for language in LANGS)
        cards.append('<div class="card" data-search="%s"><div class="num">%s</div><div class="pname" %s>%s</div><div class="langs">%s</div></div>'%(search,folder[:2],data,esc(localized_titles.get("ITA",folder)),links))
    count=len(folders)
    ui={"ITA":["Cerca un prodotto...",f"di {count} prodotti","Nessun prodotto trovato","Schede Tecniche Prodotti"],
        "FR":["Rechercher un produit...",f"sur {count} produits","Aucun produit trouve","Fiches Techniques Produits"],
        "ENG":["Search a product...",f"of {count} products","No product found","Product Technical Data Sheets"],
        "NL":["Zoek een product...",f"van {count} producten","Geen product gevonden","Technische Productfiches"],
        "DE":["Produkt suchen...",f"von {count} Produkten","Kein Produkt gefunden","Technische Produktdatenblätter"]}
    js=JS_TEMPLATE.replace("__UI__",json.dumps(ui,ensure_ascii=True)).replace("__SEARCH__",(BUILD/"search.js").read_text(encoding="utf-8"))
    html='<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>House of Tartufo - Schede Tecniche</title><style>'+CSS+'</style></head><body><div class="wrap"><div class="head"><div class="logo"></div><div class="htxt"><p class="eyebrow">HOUSE OF TARTUFO</p><h1 id="subtitle">Schede Tecniche Prodotti</h1></div></div><div class="toolbar"><div class="search"><svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 1 0-.7.7l.27.28v.79l5 5 1.5-1.5-5-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/></svg><input id="q" type="text" placeholder="Cerca un prodotto..." autocomplete="off"></div><div class="langsel" id="langsel"><button data-l="ITA" class="active">ITA</button><button data-l="FR">FR</button><button data-l="ENG">ENG</button><button data-l="NL">NL</button><button data-l="DE">DE</button></div></div><div class="count"><span id="shown">'+str(count)+'</span> <span id="counttxt">di '+str(count)+' prodotti</span></div><div class="grid" id="grid">'+"".join(cards)+'</div><div class="nores" id="nores">Nessun prodotto trovato</div><div class="foot">House of Tartufo SRL &middot; Avenue de la Liberté 175, 1080 Bruxelles - Belgium &middot; VAT BE1017314026 &middot; admin@houseoftartufo.com</div></div><script>'+js+'</script></body></html>'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(html,encoding="utf-8")
    print("INDEX ok -",count,"prodotti")
    return 0


if __name__ == "__main__":
    build_index()
