import argparse,base64,json,html as H
from pathlib import Path

from i18n import DATA_FILES, LANGS, load_products_file

ROOT=Path(__file__).resolve().parents[1]
BUILD=Path(__file__).resolve().parent
LOGO=base64.b64encode((ROOT/"house-of-tartufo-logo.png").read_bytes()).decode()
def esc(s): return H.escape(s,quote=True)
CSS="""*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',-apple-system,sans-serif;color:#1a1a1a;background:#faf9f6;padding:40px 24px}.wrap{max-width:1100px;margin:0 auto}.head{display:flex;align-items:center;gap:24px;border-bottom:3px solid #856244;padding-bottom:24px;margin-bottom:20px}.logo{width:248px;height:78px;background:url('data:image/png;base64,__L__') no-repeat center;background-size:contain;flex:0 0 248px}.htxt h1{font-size:24px;color:#0f0902}.htxt p{font-size:12px;color:#856244;letter-spacing:1px;text-transform:uppercase;margin-top:4px}.toolbar{display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;margin-bottom:8px}.search{flex:1;min-width:240px;position:relative}.search input{width:100%;padding:11px 14px 11px 38px;font-size:14px;border:1px solid #e8c897;border-radius:8px;background:#fff;outline:none}.search input:focus{border-color:#856244}.search svg{position:absolute;left:12px;top:50%;transform:translateY(-50%);width:16px;height:16px;fill:#856244}.langsel{display:flex;gap:6px}.langsel button{font-size:12px;font-weight:600;color:#856244;background:#fff;border:1px solid #856244;border-radius:6px;padding:8px 14px;cursor:pointer;transition:.15s}.langsel button:hover{background:#f1e9df}.langsel button.active{background:#856244;color:#fff}.count{font-size:11px;color:#888;margin:14px 0 24px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}.card{background:#fff;border:1px solid #e8c897;border-radius:10px;padding:16px 18px;box-shadow:0 2px 6px rgba(0,0,0,.05)}.card.duplicate{border-color:#8eb9e8;box-shadow:0 0 12px rgba(73,145,220,.42)}.num{font-size:10px;color:#c9b896;font-weight:700}.pname{font-size:14px;font-weight:700;color:#0f0902;margin:4px 0 10px;min-height:38px}.langs a{display:inline-block;font-size:11px;font-weight:600;color:#856244;text-decoration:none;border:1px solid #856244;border-radius:6px;padding:4px 10px;margin:2px 4px 2px 0;transition:.15s}.langs a.cur{background:#856244;color:#fff}.langs a:hover{background:#856244;color:#fff}.nores{display:none;text-align:center;color:#999;font-size:13px;padding:40px}.foot{margin-top:32px;text-align:center;font-size:10px;color:#999;border-top:1px solid #ddd;padding-top:16px}""".replace("__L__",LOGO)
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
    html='<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>House of Tartufo - Schede Tecniche</title><style>'+CSS+'</style></head><body><div class="wrap"><div class="head"><div class="logo"></div><div class="htxt"><h1>House of Tartufo</h1><p id="subtitle">Schede Tecniche Prodotti</p></div></div><div class="toolbar"><div class="search"><svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 1 0-.7.7l.27.28v.79l5 5 1.5-1.5-5-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/></svg><input id="q" type="text" placeholder="Cerca un prodotto..." autocomplete="off"></div><div class="langsel" id="langsel"><button data-l="ITA" class="active">ITA</button><button data-l="FR">FR</button><button data-l="ENG">ENG</button><button data-l="NL">NL</button><button data-l="DE">DE</button></div></div><div class="count"><span id="shown">'+str(count)+'</span> <span id="counttxt">di '+str(count)+' prodotti</span></div><div class="grid" id="grid">'+"".join(cards)+'</div><div class="nores" id="nores">Nessun prodotto trovato</div><div class="foot">House of Tartufo SRL &middot; Avenue de la Liberté 175, 1080 Bruxelles - Belgium &middot; VAT BE1017314026 &middot; admin@houseoftartufo.com</div></div><script>'+js+'</script></body></html>'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(html,encoding="utf-8")
    print("INDEX ok -",count,"prodotti")
    return 0


if __name__ == "__main__":
    build_index()
