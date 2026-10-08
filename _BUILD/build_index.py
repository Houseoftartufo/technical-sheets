import argparse,base64,json,html as H
from pathlib import Path

from i18n import LANGS, load_all_products

ROOT=Path(__file__).resolve().parents[1]
BUILD=Path(__file__).resolve().parent
LOGO=base64.b64encode((ROOT/"house-of-tartufo-logo.png").read_bytes()).decode()
titles={p["folder"]:p["title"] for p in load_all_products(BUILD)}
folders=sorted(d.name for d in ROOT.iterdir() if d.name[0].isdigit() and d.is_dir())
def esc(s): return H.escape(s,quote=True)
cards=[]
for d in folders:
    tt=titles.get(d,{})
    product_meta = next((p for p in load_all_products(BUILD) if p["folder"] == d), {})
    duplicate_class = " duplicate" if product_meta.get("duplicate_of") else ""
    search=esc(json.dumps([tt.get(L,"") for L in LANGS],ensure_ascii=False))
    data=" ".join('data-%s="%s"'%(L.lower(),esc(tt.get(L,d))) for L in LANGS)
    links="".join('<a class="lang" href="%s/%s_%s.pdf">%s</a>'%(d,d,L,L) for L in LANGS)
    cards.append('<div class="card%s" data-search="%s"><div class="num">%s</div><div class="pname" %s>%s</div><div class="langs">%s</div></div>'%(duplicate_class,search,d[:2],data,esc(tt.get("ITA",d)),links))
UI={"ITA":["Cerca un prodotto...","di %d prodotti"%len(folders),"Nessun prodotto trovato","Schede Tecniche Prodotti"],
    "FR":["Rechercher un produit...","sur %d produits"%len(folders),"Aucun produit trouve","Fiches Techniques Produits"],
    "ENG":["Search a product...","of %d products"%len(folders),"No product found","Product Technical Data Sheets"],
    "NL":["Zoek een product...","van %d producten"%len(folders),"Geen product gevonden","Technische Productfiches"],
    "DE":["Produkt suchen...","von %d Produkten"%len(folders),"Kein Produkt gefunden","Technische Produktdatenblätter"]}
CSS="""*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',-apple-system,sans-serif;color:#1a1a1a;background:#faf9f6;padding:40px 24px}.wrap{max-width:1100px;margin:0 auto}.head{display:flex;align-items:center;gap:24px;border-bottom:3px solid #856244;padding-bottom:24px;margin-bottom:20px}.logo{width:248px;height:78px;background:url('data:image/png;base64,__L__') no-repeat center;background-size:contain;flex:0 0 248px}.htxt h1{font-size:24px;color:#0f0902}.htxt p{font-size:12px;color:#856244;letter-spacing:1px;text-transform:uppercase;margin-top:4px}.toolbar{display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;margin-bottom:8px}.search{flex:1;min-width:240px;position:relative}.search input{width:100%;padding:11px 14px 11px 38px;font-size:14px;border:1px solid #e8c897;border-radius:8px;background:#fff;outline:none}.search input:focus{border-color:#856244}.search svg{position:absolute;left:12px;top:50%;transform:translateY(-50%);width:16px;height:16px;fill:#856244}.langsel{display:flex;gap:6px}.langsel button{font-size:12px;font-weight:600;color:#856244;background:#fff;border:1px solid #856244;border-radius:6px;padding:8px 14px;cursor:pointer;transition:.15s}.langsel button:hover{background:#f1e9df}.langsel button.active{background:#856244;color:#fff}.count{font-size:11px;color:#888;margin:14px 0 24px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}.card{background:#fff;border:1px solid #e8c897;border-radius:10px;padding:16px 18px;box-shadow:0 2px 6px rgba(0,0,0,.05)}.card.duplicate{border-color:#8eb9e8;box-shadow:0 0 12px rgba(73,145,220,.42)}.num{font-size:10px;color:#c9b896;font-weight:700}.pname{font-size:14px;font-weight:700;color:#0f0902;margin:4px 0 10px;min-height:38px}.langs a{display:inline-block;font-size:11px;font-weight:600;color:#856244;text-decoration:none;border:1px solid #856244;border-radius:6px;padding:4px 10px;margin:2px 4px 2px 0;transition:.15s}.langs a.cur{background:#856244;color:#fff}.langs a:hover{background:#856244;color:#fff}.nores{display:none;text-align:center;color:#999;font-size:13px;padding:40px}.foot{margin-top:32px;text-align:center;font-size:10px;color:#999;border-top:1px solid #ddd;padding-top:16px}""".replace("__L__",LOGO)
JS="""var UI=__UI__;__SEARCH__
var q=document.getElementById('q'),cards=[].slice.call(document.querySelectorAll('.card')),grid=document.getElementById('grid'),shown=document.getElementById('shown'),nores=document.getElementById('nores');
var originalOrder=new Map(cards.map(function(card,index){return [card,index]}));
function setLang(L){cards.forEach(function(c){var p=c.querySelector('.pname');p.textContent=p.getAttribute('data-'+L.toLowerCase());c.querySelectorAll('.lang').forEach(function(a){a.classList.toggle('cur',a.textContent===L);});});document.getElementById('q').placeholder=UI[L][0];document.getElementById('counttxt').textContent=UI[L][1];document.getElementById('nores').textContent=UI[L][2];document.getElementById('subtitle').textContent=UI[L][3];document.documentElement.lang={ITA:'it',FR:'fr',ENG:'en',NL:'nl',DE:'de'}[L];}
function apply(){var t=q.value,n=0,ranked=cards.map(function(c){var names=JSON.parse(c.getAttribute('data-search'));return {card:c,score:ProductSearch.score(t,names),order:originalOrder.get(c)};});ranked.sort(function(a,b){return b.score-a.score||a.order-b.order;});ranked.forEach(function(item){var match=item.score>=0;item.card.style.display=match?'':'none';grid.appendChild(item.card);if(match)n++;});shown.textContent=n;nores.style.display=n?'none':'block';}
q.addEventListener('input',apply);document.getElementById('langsel').addEventListener('click',function(e){if(e.target.tagName!=='BUTTON')return;document.querySelectorAll('.langsel button').forEach(function(b){b.classList.remove('active')});e.target.classList.add('active');setLang(e.target.getAttribute('data-l'));});setLang('ITA');apply();"""
JS=JS.replace("__UI__",json.dumps(UI,ensure_ascii=True)).replace("__SEARCH__",(BUILD/"search.js").read_text(encoding="utf-8"))
html='<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>House of Tartufo - Schede Tecniche</title><style>'+CSS+'</style></head><body><div class="wrap"><div class="head"><div class="logo"></div><div class="htxt"><h1>House of Tartufo</h1><p id="subtitle">Schede Tecniche Prodotti</p></div></div><div class="toolbar"><div class="search"><svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 1 0-.7.7l.27.28v.79l5 5 1.5-1.5-5-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/></svg><input id="q" type="text" placeholder="Cerca un prodotto..." autocomplete="off"></div><div class="langsel" id="langsel"><button data-l="ITA" class="active">ITA</button><button data-l="FR">FR</button><button data-l="ENG">ENG</button><button data-l="NL">NL</button><button data-l="DE">DE</button></div></div><div class="count"><span id="shown">'+str(len(folders))+'</span> <span id="counttxt">di '+str(len(folders))+' prodotti</span></div><div class="grid" id="grid">'+"".join(cards)+'</div><div class="nores" id="nores">Nessun prodotto trovato</div><div class="foot">House of Tartufo SRL &middot; Avenue de la Liberté 175, 1080 Bruxelles - Belgium &middot; VAT BE1017314026 &middot; admin@houseoftartufo.com</div></div><script>'+JS+'</script></body></html>'
parser=argparse.ArgumentParser()
parser.add_argument("--output",type=Path,default=ROOT/"index.html")
args=parser.parse_args()
args.output.write_text(html,encoding="utf-8")
print("INDEX ok -",len(folders),"prodotti")
