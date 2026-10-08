# -*- coding: utf-8 -*-
import base64, os, sys
from pathlib import Path

from i18n import LANGS, load_products_file, localized
from pdf_backend import write_pdf


ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = ROOT / "HOT_logo_Full_Black.svg"
with open(LOGO_PATH, "rb") as f:
    LOGO_B64 = base64.b64encode(f.read()).decode()

L = {
    "html_lang": {"ITA": "it", "FR": "fr", "ENG": "en", "NL": "nl", "DE": "de"},
    "sheet_type": {"ITA": "SCHEDA TECNICA PRODOTTO", "FR": "FICHE TECHNIQUE PRODUIT",
                   "ENG": "PRODUCT TECHNICAL DATA SHEET", "NL": "TECHNISCHE PRODUCTFICHE", "DE": "TECHNISCHES PRODUKTDATENBLATT"},
    "finished": {"ITA": "PRODOTTO FINITO", "FR": "PRODUIT FINI", "ENG": "FINISHED PRODUCT", "NL": "EINDPRODUCT", "DE": "FERTIGPRODUKT"},
    "sec_general": {"ITA": "Informazioni Generali", "FR": "Informations Générales",
                    "ENG": "General Information", "NL": "Algemene Informatie", "DE": "Allgemeine Informationen"},
    "sec_ingr": {"ITA": "Ingredienti e Allergeni", "FR": "Ingrédients et Allergènes",
                 "ENG": "Ingredients & Allergens", "NL": "Ingredienten & Allergenen", "DE": "Zutaten und Allergene"},
    "sec_storage": {"ITA": "Conservazione e Modalità d'Uso", "FR": "Conservation et Mode d'Emploi",
                    "ENG": "Storage & Method of Use", "NL": "Bewaring & Gebruiksaanwijzing", "DE": "Lagerung und Verwendung"},
    "sec_nutri": {"ITA": "Valori Nutrizionali Medi (per 100 g)", "FR": "Valeurs Nutritionnelles Moyennes (pour 100 g)",
                  "ENG": "Average Nutritional Values (per 100 g)", "NL": "Gemiddelde Voedingswaarden (per 100 g)", "DE": "Durchschnittliche Nährwerte (pro 100 g)"},
    "sec_charact": {"ITA": "Caratteristiche Chimiche e Microbiologiche", "FR": "Caractéristiques Chimiques et Microbiologiques",
                    "ENG": "Chemical & Microbiological Characteristics", "NL": "Chemische & Microbiologische Kenmerken", "DE": "Chemische und mikrobiologische Eigenschaften"},
    "lbl_ean": {"ITA": "Codice EAN", "FR": "Code EAN", "ENG": "EAN Code", "NL": "EAN-code", "DE": "EAN-Code"},
    "lbl_typ": {"ITA": "Tipologia", "FR": "Typologie", "ENG": "Typology", "NL": "Typologie", "DE": "Produkttyp"},
    "lbl_label": {"ITA": "Etichettatura", "FR": "Étiquetage", "ENG": "Labelling", "NL": "Etikettering", "DE": "Kennzeichnung"},
    "lbl_gmo": {"ITA": "OGM e Irraggiamento", "FR": "OGM et Irradiation", "ENG": "GMO & Irradiation", "NL": "GGO & Bestraling", "DE": "GVO und Bestrahlung"},
    "lbl_shelf": {"ITA": "Shelf Life", "FR": "Durée de Conservation", "ENG": "Shelf Life", "NL": "Houdbaarheid", "DE": "Mindesthaltbarkeit"},
    "lbl_pack": {"ITA": "Confezione", "FR": "Conditionnement", "ENG": "Packaging", "NL": "Verpakking", "DE": "Verpackung"},
    "lbl_ingr": {"ITA": "Ingredienti", "FR": "Ingrédients", "ENG": "Ingredients", "NL": "Ingredienten", "DE": "Zutaten"},
    "lbl_all": {"ITA": "Allergeni", "FR": "Allergènes", "ENG": "Allergens", "NL": "Allergenen", "DE": "Allergene"},
    "lbl_storeinstr": {"ITA": "Istruzioni per la Conservazione", "FR": "Instructions de Conservation",
                       "ENG": "Storage Instructions", "NL": "Bewaarinstructies", "DE": "Lagerhinweise"},
    "lbl_method": {"ITA": "Modalità d'Uso", "FR": "Mode d'Emploi", "ENG": "Method of Use", "NL": "Gebruiksaanwijzing", "DE": "Verwendung"},
    "lbl_chem": {"ITA": "Caratteristiche Chimiche", "FR": "Caractéristiques Chimiques",
                 "ENG": "Chemical Characteristics", "NL": "Chemische Kenmerken", "DE": "Chemische Eigenschaften"},
    "lbl_micro": {"ITA": "Caratteristiche Microbiologiche", "FR": "Caractéristiques Microbiologiques",
                  "ENG": "Microbiological Characteristics", "NL": "Microbiologische Kenmerken", "DE": "Mikrobiologische Eigenschaften"},
    "th_param": {"ITA": "Parametro", "FR": "Paramètre", "ENG": "Parameter", "NL": "Parameter", "DE": "Parameter"},
    "th_value": {"ITA": "Valore", "FR": "Valeur", "ENG": "Value", "NL": "Waarde", "DE": "Wert"},
    "updated": {"ITA": "Aggiornato", "FR": "Mise à jour", "ENG": "Updated", "NL": "Bijgewerkt", "DE": "Aktualisiert"},
}

NUT = {
    "energy": {"ITA": "Valore energetico", "FR": "Valeur énergétique", "ENG": "Energy value", "NL": "Energetische waarde", "DE": "Energie"},
    "fat": {"ITA": "Grassi", "FR": "Matières grasses", "ENG": "Fat", "NL": "Vetten", "DE": "Fett"},
    "sat": {"ITA": "di cui acidi grassi saturi", "FR": "dont acides gras saturés", "ENG": "of which saturates", "NL": "waarvan verzadigde vetzuren", "DE": "davon gesättigte Fettsäuren"},
    "carb": {"ITA": "Carboidrati", "FR": "Glucides", "ENG": "Carbohydrate", "NL": "Koolhydraten", "DE": "Kohlenhydrate"},
    "sugar": {"ITA": "di cui zuccheri", "FR": "dont sucres", "ENG": "of which sugars", "NL": "waarvan suikers", "DE": "davon Zucker"},
    "protein": {"ITA": "Proteine", "FR": "Protéines", "ENG": "Protein", "NL": "Eiwitten", "DE": "Eiweiß"},
    "salt": {"ITA": "Sale", "FR": "Sel", "ENG": "Salt", "NL": "Zout", "DE": "Salz"},
    "fibre": {"ITA": "Fibre", "FR": "Fibres", "ENG": "Fibre", "NL": "Vezels", "DE": "Ballaststoffe"},
}
NUT_ORDER = ["energy", "fat", "sat", "carb", "sugar", "protein", "salt", "fibre"]

CSS = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        @page { size: A4; margin: 15mm 15mm 20mm 15mm; }
        body { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; color: #1a1a1a; line-height: 1.6; }
        .container { background: white; position: relative; }
        .header { display: grid; grid-template-columns: 130px 1fr; gap: 25px; margin-bottom: 30px; padding-bottom: 25px; border-bottom: 3px solid #856244; align-items: flex-start; }
        .logo-container { display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f9f7f4, #faf9f6); border: 2px solid #e8c897; border-radius: 12px; padding: 15px; min-height: 145px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .logo { width: 110px; height: 110px; background: url('data:image/svg+xml;base64,__LOGO__') no-repeat center; background-size: contain; }
        .company-info { display: flex; flex-direction: column; justify-content: center; padding-top: 8px; }
        .company-name { font-size: 16px; font-weight: 700; color: #0f0902; margin-bottom: 8px; }
        .company-details { font-size: 9px; color: #555; line-height: 1.6; }
        .title-section { text-align: center; margin: 35px 0 35px; }
        .sheet-type { font-size: 10px; letter-spacing: 1.5px; color: #856244; font-weight: 600; text-transform: uppercase; margin-bottom: 10px; }
        .product-title { font-size: 25px; font-weight: 700; color: #0f0902; margin-bottom: 5px; }
        .product-subtitle { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.8px; }
        .section { margin-bottom: 22px; }
        .section-title { font-size: 11px; font-weight: 700; color: #0f0902; text-transform: uppercase; letter-spacing: 0.8px; padding-bottom: 8px; border-bottom: 1.5px solid #856244; margin-bottom: 12px; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 15px; margin-bottom: 8px; }
        .info-row { display: flex; flex-direction: column; }
        .info-label { font-size: 8.5px; font-weight: 600; color: #856244; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
        .info-value { font-size: 10px; color: #333; line-height: 1.5; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 9px; }
        thead { background: linear-gradient(135deg, #856244, #c9b896); color: white; }
        th { padding: 8px 6px; text-align: left; font-weight: 600; letter-spacing: 0.3px; }
        td { padding: 8px 6px; border-bottom: 1px solid #e8c897; }
        tbody tr:nth-child(odd) { background-color: #faf9f6; }
        .footer { margin-top: 35px; padding-top: 15px; border-top: 1px solid #ddd; text-align: center; font-size: 8px; color: #888; }
        .footer-company { font-weight: 600; color: #856244; margin-bottom: 3px; }
""".replace("__LOGO__", LOGO_B64)

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def fmt_num(s, lang):
    if lang == "ENG":
        return s.replace(",", ".")
    return s

def render(prod, lang, date_str):
    t = lambda k: L[k][lang]
    title = prod["title"][lang]
    g = prod["general"]
    info = []
    def row(label, val):
        info.append('<div class="info-row"><span class="info-label">%s</span><span class="info-value">%s</span></div>' % (esc(label), esc(val)))
    if g.get("ean"): row(t("lbl_ean"), g["ean"])
    row(t("lbl_typ"), g["typology"][lang])
    row(t("lbl_shelf"), g["shelf"][lang])
    row(t("lbl_pack"), g["packaging"][lang])
    row(t("lbl_label"), localized(g["labelling"], lang))
    row(t("lbl_gmo"), g["gmo"][lang])
    general_html = '<div class="section"><div class="section-title">%s</div><div class="info-grid">%s</div></div>' % (t("sec_general"), "".join(info))

    ia = prod["ingredients"]
    ingr_html = ('<div class="section"><div class="section-title">%s</div>'
                 '<div class="info-row" style="margin-bottom:10px;"><span class="info-label">%s</span><span class="info-value">%s</span></div>'
                 '<div class="info-row"><span class="info-label">%s</span><span class="info-value">%s</span></div></div>') % (
        t("sec_ingr"), t("lbl_ingr"), esc(ia["ingredients"][lang]), t("lbl_all"), esc(ia["allergens"][lang]))

    st = prod["storage"]
    storage_html = ('<div class="section"><div class="section-title">%s</div>'
                    '<div class="info-row" style="margin-bottom:10px;"><span class="info-label">%s</span><span class="info-value">%s</span></div>'
                    '<div class="info-row"><span class="info-label">%s</span><span class="info-value">%s</span></div></div>') % (
        t("sec_storage"), t("lbl_storeinstr"), esc(st["instructions"][lang]), t("lbl_method"), esc(st["method"][lang]))

    nut = prod["nutrition"]
    nrows = []
    for k in NUT_ORDER:
        if k in nut:
            nrows.append("<tr><td>%s</td><td>%s</td></tr>" % (esc(NUT[k][lang]), esc(fmt_num(nut[k], lang))))
    nutri_html = ('<div class="section"><div class="section-title">%s</div>'
                  '<table><thead><tr><th>%s</th><th>%s</th></tr></thead><tbody>%s</tbody></table></div>') % (
        t("sec_nutri"), t("th_param"), t("th_value"), "".join(nrows))

    charact_html = ""
    ch = prod.get("characteristics", {})
    crows = []
    if ch.get("chemical"):
        crows.append("<tr><td>%s</td><td>%s</td></tr>" % (esc(t("lbl_chem")), esc(ch["chemical"][lang])))
    if ch.get("micro"):
        crows.append("<tr><td>%s</td><td>%s</td></tr>" % (esc(t("lbl_micro")), esc(ch["micro"][lang])))
    if crows:
        charact_html = ('<div class="section"><div class="section-title">%s</div>'
                        '<table><thead><tr><th>%s</th><th>%s</th></tr></thead><tbody>%s</tbody></table></div>') % (
            t("sec_charact"), t("th_param"), t("th_value"), "".join(crows))

    html = """<!DOCTYPE html>
<html lang="%s">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%s - %s</title>
    <style>%s</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo-container"><div class="logo"></div></div>
            <div class="company-info">
                <div class="company-name">House of Tartufo SRL</div>
                <div class="company-details">
                    Avenue de la Liberte 175<br>
                    1080 Bruxelles - Belgium<br>
                    VAT: BE1017314026<br>
                    admin@houseoftartufo.com
                </div>
            </div>
        </div>
        <div class="title-section">
            <div class="sheet-type">%s</div>
            <div class="product-title">%s</div>
            <div class="product-subtitle">%s</div>
        </div>
        %s
        %s
        %s
        %s
        %s
        <div class="footer">
            <div class="footer-company">House of Tartufo SRL</div>
            Avenue de la Liberte 175 &bull; 1080 Bruxelles - Belgium &bull; VAT: BE1017314026<br>
            admin@houseoftartufo.com &bull; %s: %s
        </div>
    </div>
</body>
</html>""" % (L["html_lang"][lang], esc(title), t("sheet_type"), CSS,
              t("sheet_type"), esc(title), t("finished"),
              general_html, ingr_html, storage_html, nutri_html, charact_html,
              t("updated"), date_str)
    return html

if __name__ == "__main__":
    data_file = sys.argv[1]; out_dir = sys.argv[2]
    date_str = sys.argv[3] if len(sys.argv) > 3 else "06/06/2026"
    requested_langs = sys.argv[4].split(",") if len(sys.argv) > 4 else list(LANGS)
    unknown_langs = [lang for lang in requested_langs if lang not in LANGS]
    if unknown_langs:
        raise SystemExit("Unknown language code(s): %s" % ", ".join(unknown_langs))
    products = load_products_file(data_file)
    for prod in products:
        folder = os.path.join(out_dir, prod["folder"])
        os.makedirs(folder, exist_ok=True)
        for lang in requested_langs:
            html = render(prod, lang, date_str)
            base = "%s_%s" % (prod["folder"], lang)
            with open(os.path.join(folder, base + ".html"), "w", encoding="utf-8") as f:
                f.write(html)
            write_pdf(html, os.path.join(folder, base + ".pdf"))
        print("OK", prod["folder"])
