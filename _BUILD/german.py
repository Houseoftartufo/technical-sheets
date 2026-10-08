# -*- coding: utf-8 -*-
"""German B2B copy for the product technical sheets."""

VEG_NS = "Pflanzliches Erzeugnis, nicht sterilisiert."
VEG_S = "Pflanzliches Erzeugnis, sterilisiert."
DAIRY_S = "Milcherzeugnis, sterilisiert."
TRUFFLE = "Erzeugnis auf Trüffelbasis."
TRUFFLE_NS = "Erzeugnis auf Trüffelbasis, nicht sterilisiert."
TRUFFLE_PAST = "Erzeugnis auf Trüffelbasis, pasteurisiert."

EU_LABEL = "Verordnung (EU) Nr. 1169/2011"
IT_EU_LABEL = "Italienisches Gesetzesdekret 109/1992 und Verordnung (EU) Nr. 1169/2011"
GMO = "Nicht vorhanden"

NONE = "Keine."
NONE_EXTRA = (
    "Abgesehen von den im vorherigen Absatz in GROSSBUCHSTABEN angegebenen Allergenen "
    "enthält das Produkt keine weiteren allergenen Zutaten."
)
READY_USE = "Nach dem Öffnen ist das Produkt gebrauchsfertig."
READY_EAT = "Nach dem Öffnen ist das Produkt verzehrfertig."

CHEM = "Schwermetalle: < 0,10 ppm"
MICRO_FULL = (
    "Gesamtkeimzahl (GKZ): < 10 KBE/g; coliforme Keime: < 10 KBE/g; Hefen und "
    "Schimmelpilze: nicht nachweisbar; sulfitreduzierende Anaerobier: < 10 KBE/g; "
    "Listeria monocytogenes: in 25 g nicht nachweisbar; Salmonellen: in 25 g nicht nachweisbar."
)
MICRO_NO_ANAE = (
    "Gesamtkeimzahl (GKZ): < 10 KBE/g; coliforme Keime: < 10 KBE/g; Hefen und "
    "Schimmelpilze: nicht nachweisbar; Listeria monocytogenes: in 25 g nicht nachweisbar; "
    "Salmonellen: in 25 g nicht nachweisbar."
)
MICRO_BASIC = "Gesamtkeimzahl (GKZ): < 10 KBE/g; Hefen und Schimmelpilze: nicht nachweisbar."
MICRO_DRY = (
    "Gesamtkeimzahl (GKZ): < 10 KBE/g; Hefen und Schimmelpilze: nicht nachweisbar; "
    "Salmonellen: in 25 g nicht nachweisbar."
)

STORE_AMBIENT = "Bei Raumtemperatur vor Licht und Wärmequellen geschützt lagern."
STORE_AMBIENT_FRIDGE = (
    "Bei Raumtemperatur vor Licht und Wärmequellen geschützt lagern. Nach dem Öffnen bei "
    "0 bis 4 °C im Kühlschrank aufbewahren und innerhalb von 4-5 Tagen verbrauchen."
)
STORE_AMBIENT_ORIGINAL = (
    "Bei Raumtemperatur vor Licht und Wärmequellen geschützt lagern. Nach dem Öffnen das "
    "Produkt in der Originalverpackung vor direktem Licht und Wärme geschützt aufbewahren."
)
STORE_COOL_20 = "Kühl (max. 20 °C) und trocken lagern."
STORE_COOL_DRY = "Kühl und trocken lagern."
STORE_KETCHUP = (
    "Kühl und trocken, vor direkter Sonneneinstrahlung geschützt bei 8-15 °C lagern. Nach "
    "dem Öffnen bei 0 bis 4 °C im Kühlschrank aufbewahren und innerhalb von 4-5 Tagen verbrauchen."
)
STORE_RICE = (
    "Bei Raumtemperatur vor Licht und Wärmequellen geschützt lagern. Nach dem Öffnen das "
    "Produkt in der Originalverpackung vor direktem Licht und Wärme geschützt an einem gut "
    "belüfteten Ort aufbewahren."
)
STORE_SALT = (
    "Bei Raumtemperatur vor Licht und Wärmequellen geschützt lagern. Nach dem Öffnen das "
    "Produkt in der Originalverpackung vor direktem Licht geschützt an einem trockenen und "
    "gut belüfteten Ort aufbewahren."
)


def entry(title, typology, months, packaging, ingredients, allergens=NONE,
          storage=STORE_AMBIENT, method=READY_USE, labelling=EU_LABEL,
          chemical=CHEM, micro=MICRO_FULL):
    return {
        "title": title,
        "general": {
            "typology": typology,
            "shelf": f"{months} Monate",
            "packaging": packaging,
            "labelling": labelling,
            "gmo": GMO,
        },
        "ingredients": {"ingredients": ingredients, "allergens": allergens},
        "storage": {"instructions": storage, "method": method},
        "characteristics": {"chemical": chemical, "micro": micro},
    }


NUT_ALLERGEN = (
    "Enthält SCHALENFRÜCHTE ({name}). Kann Spuren von SOJA, SESAMSAMEN, SENF, anderen "
    "SCHALENFRÜCHTEN und SCHWEFELDIOXID enthalten."
)

DE_TRANSLATIONS = {
    "01_ACETO_BALSAMICO_SPRAY": entry(
        "Balsamico-Essig aus Modena mit Trüffelaroma", VEG_NS, 18,
        "Glasflasche mit Sprühkopf, 100 ml.",
        "Konzentrierter Traubenmost, Balsamico-Essig aus Modena g.g.A. (Weinessig, "
        "konzentrierter Traubenmost, Farbstoff E150d), Weinessig, Farbstoff E150d, Aroma. "
        "Enthält SULFITE.",
        NONE_EXTRA, STORE_AMBIENT_ORIGINAL, micro=MICRO_BASIC,
    ),
    "02_ANACARDI_SGUSCIATI_AL_TARTUFO": entry(
        "Geschälte Cashewkerne mit Trüffel", VEG_NS, 12, "Metalldose.",
        "Geröstete geschälte CASHEWKERNE 92,5 %; Sonnenblumenöl 5 %; [Salz, Sommertrüffel "
        "(Tuber aestivum Vitt.) 1 %, Aromen] 2,5 %.",
        NUT_ALLERGEN.format(name="CASHEWKERNE"), STORE_COOL_20, READY_EAT,
    ),
    "03_ARACHIDI_SGUSCIATE_AL_TARTUFO": entry(
        "Geschälte Erdnüsse mit Trüffel", VEG_NS, 12, "Metalldose.",
        "Geröstete geschälte ERDNÜSSE 92,5 %; Sonnenblumenöl 5 %; [Salz, Sommertrüffel "
        "(Tuber aestivum Vitt.) 1 %, Aromen] 2,5 %.",
        "Enthält ERDNÜSSE. Kann Spuren von SOJA, SESAMSAMEN, SENF, anderen "
        "SCHALENFRÜCHTEN und SCHWEFELDIOXID enthalten.",
        STORE_AMBIENT, READY_EAT,
    ),
    "04_BURRO_BIANCHETTO_6PCT": entry(
        "Butterzubereitung mit Bianchetto-Trüffel 6 %", DAIRY_S, 36,
        "Glasgefäß (80, 160, 450 g).",
        "BUTTER (LAKTOSE), Bianchetto-Trüffel (Tuber borchii, Vittad.) 6 %, Salz, Aroma.",
        NONE_EXTRA, STORE_AMBIENT_FRIDGE, labelling=IT_EU_LABEL, micro=MICRO_NO_ANAE,
    ),
    "05_BURRO_ESTIVO_3PCT": entry(
        "Butterzubereitung mit Sommertrüffel 3 %", DAIRY_S, 36,
        "Glasgefäß (80, 160, 450 g).",
        "BUTTER (LAKTOSE), Sommertrüffel (Tuber aestivum, Vittad.) 3 %, Salz, Aroma.",
        NONE_EXTRA, STORE_AMBIENT_FRIDGE, micro=MICRO_NO_ANAE,
    ),
    "06_CARPACCIO_DI_TARTUFO_IN_ACQUA": entry(
        "Sommertrüffel-Carpaccio in Wasser", VEG_S, 36,
        "Glasgefäß (80, 170, 500 g).",
        "Sommertrüffel (Tuber aestivum, Vittad.) 60 %, Wasser, Aroma.",
        NONE, STORE_AMBIENT_FRIDGE, labelling=IT_EU_LABEL,
    ),
    "07_CREMA_ALLACETO_BALSAMICO_AL_TARTUFO": entry(
        "Creme aus Balsamico-Essig aus Modena mit Trüffelaroma", VEG_NS, 18,
        "Glasflasche, 100 ml.",
        "Konzentrierter Traubensaft, Balsamico-Essig aus Modena g.g.A. 35 % (Weinessig, "
        "konzentrierter Traubenmost, Farbstoff E150d), Glukose-Fruktose-Sirup, Weinessig, "
        "modifizierte Stärke, Farbstoff E150d, Aroma. Enthält SULFITE.",
        NONE_EXTRA, STORE_AMBIENT_FRIDGE, micro=MICRO_BASIC,
    ),
    "08_CREMA_DI_FUNGHI_PORCINI_E_TARTUFO_NERO_ESTIVO": entry(
        "Steinpilzcreme mit schwarzem Sommertrüffel", VEG_S, 36,
        "Glasgefäß (80, 170 g).",
        "Steinpilze (Boletus edulis), schwarzer Sommertrüffel (Tuber aestivum Vitt.) 5 %, "
        "natives Olivenöl extra, Salz, Pfeffer, Petersilie, Aroma.",
        storage=STORE_AMBIENT_FRIDGE,
    ),
    "09_KETCHUP_TARTUFATO": entry(
        "Trüffel-Ketchup", TRUFFLE_PAST, 24, "Glasgefäß (85 g).",
        "Tomaten (148 g je 100 g Produkt), Branntweinessig, Sommertrüffel (Tuber aestivum "
        "Vitt.) 1 %, Zucker, Salz, Gewürze und Kräuterextrakte (enthält SELLERIE), Gewürze, Aroma.",
        NONE_EXTRA, STORE_KETCHUP, labelling=IT_EU_LABEL, micro=MICRO_NO_ANAE,
    ),
    "10_MIELE_AL_TARTUFO": entry(
        "Akazienhonig mit Bianchetto-Trüffel", TRUFFLE_NS, 24,
        "Glasgefäß (100, 170, 500 g).",
        "Akazienhonig, Bianchetto-Trüffel (Tuber borchii Vitt.) 0,5 % (ursprünglich 2 %), Aroma.",
        storage=STORE_AMBIENT_ORIGINAL, micro=MICRO_DRY,
    ),
    "11_MANDORLE": entry(
        "Mandeln mit Trüffel", VEG_NS, 12, "Metalldose.",
        "Geröstete geschälte MANDELN 92,5 %; Sonnenblumenöl 5 %; [Salz, Sommertrüffel "
        "(Tuber aestivum Vitt.) 1 %, Aromen] 2,5 %.",
        NUT_ALLERGEN.format(name="MANDELN"), STORE_COOL_20, READY_EAT,
    ),
    "12_NOCI_AL_TARTUFO": entry(
        "Walnüsse mit Trüffel", VEG_NS, 12, "Metalldose.",
        "Geröstete geschälte WALNÜSSE 95 %; Sonnenblumenöl 3,4 %; [Salz, Sommertrüffel "
        "(Tuber aestivum Vitt.) 1 %, Aromen] 1,6 %.",
        NUT_ALLERGEN.format(name="WALNÜSSE"), STORE_AMBIENT, READY_EAT,
    ),
    "13_OLIO_EXTRA_VERGINE_DOLIVA_AL_TARTUFO_BIANCO": entry(
        "Natives Olivenöl extra mit weißem Trüffelaroma", VEG_NS, 24,
        "Glasflasche (60, 100, 250, 500, 1000 ml); Metalldose (5 l).",
        "Natives Olivenöl extra, Aroma.", storage=STORE_AMBIENT_ORIGINAL,
    ),
    "14_OLIO_EXTRAVERGINE_DOLIVA_AL_TARTUFO_NERO_ESTIVO": entry(
        "Natives Olivenöl extra mit schwarzem Sommertrüffelaroma", VEG_NS, 24,
        "Glasflasche (60, 100, 250, 500, 1000 ml); Metalldose (5 l).",
        "Natives Olivenöl extra, Aroma.", storage=STORE_AMBIENT_ORIGINAL,
    ),
    "15_PERLE": entry(
        "Perlen aus Balsamico-Essig mit Trüffel", VEG_NS, 24,
        "Glasgefäß (50 g).",
        "Balsamico-Essig aus Modena g.g.A. mind. 60 % (Weinessig, eingekochter Traubenmost), "
        "Wasser, Geliermittel: Cellulosegummi, Calciumchlorid, Natriumalginat, Sommertrüffel "
        "(Tuber aestivum) 0,1 %, Aroma. Enthält SULFITE.",
        NONE_EXTRA,
        "Vor Sonne und direktem Licht geschützt bei 10-20 °C lagern. Nach dem Öffnen im "
        "Kühlschrank aufbewahren und innerhalb von 10 Tagen verbrauchen.",
        chemical="Gesamtzucker: 210-230 g/l; Gesamtschwefeldioxid: max. 100 mg/l; pH-Wert: 3-4,5.",
        micro=("Gesamtkeimzahl: < 100 KBE/ml; Hefen: < 50 KBE/ml; Schimmelpilze: < 10 KBE/ml; "
               "coliforme Keime: nicht nachweisbar; Salmonellen: nicht nachweisbar; pathogene "
               "Keime: nicht nachweisbar."),
    ),
    "16_POLENTA_AL_TARTUFO": entry(
        "Polenta mit Sommertrüffel", VEG_NS, 18,
        "Lebensmittelechter Kunststoffbeutel (125 g).",
        "Maismehl, Buchweizenmehl, Aroma, getrockneter Sommertrüffel (Tuber aestivum, Vitt.) 0,2 %.",
        storage=STORE_AMBIENT_ORIGINAL, micro=MICRO_DRY,
    ),
    "17_RISO_TARTUFO_ESTIVO_G_170_1000___170G": entry(
        "Carnaroli-Reis mit Sommertrüffel", VEG_NS, 18,
        "Lebensmittelechter Kunststoffbeutel (170 g).",
        "Carnaroli-Reis, getrocknete Champignons (Agaricus bisporus), getrockneter "
        "Sommertrüffel (Tuber aestivum, Vitt.) 0,3 %, Aroma.",
        storage=STORE_RICE, micro=MICRO_DRY,
    ),
    "18_SALE_GRIGIO": entry(
        "Graues Salz mit Trüffel", VEG_NS, 24, "Glasgefäß.",
        "Graues Salz, getrockneter Sommertrüffel (Tuber aestivum, Vittad.) 2 %, Aroma.",
        storage=STORE_SALT, micro=MICRO_NO_ANAE,
    ),
    "19_SALE_ROSA": entry(
        "Rosa Himalayasalz mit Trüffel", VEG_NS, 24, "Glasgefäß.",
        "Rosa Himalayasalz, getrockneter Sommertrüffel (Tuber aestivum, Vittad.) 2 %, Aroma.",
        storage=STORE_SALT, micro=MICRO_NO_ANAE,
    ),
    "20_SALE_CON_TARTUFO_BIANCO": entry(
        "Salz mit weißem Trüffel", VEG_NS, 24, "Glasgefäß.",
        "Graues Salz, getrockneter weißer Trüffel (Tuber magnatum, Pico.) 1 %, Aroma.",
        storage=STORE_SALT, micro=MICRO_NO_ANAE,
    ),
    "21_SALE_CON_TARTUFO_NERO": entry(
        "Salz mit Sommertrüffel", VEG_NS, 24, "Glasgefäß.",
        "Salz, getrockneter Sommertrüffel (Tuber aestivum, Vittad.) 2 %, Aroma.",
        storage=STORE_SALT, micro=MICRO_NO_ANAE,
    ),
    "22_SALSA_TARTUFATA_AL_TARTUFO_ESTIVO": entry(
        "Tartufata-Sauce mit Sommertrüffel", VEG_S, 36,
        "Glasgefäß (80, 170, 500 g).",
        "Kulturchampignons (Agaricus bisporus), Sonnenblumenöl, Sommertrüffel (Tuber "
        "aestivum, Vittad.), schwarze Oliven, Salz, Aroma, Knoblauch, Petersilie.",
        storage=STORE_AMBIENT_FRIDGE,
    ),
    "23_SALSA_TARTUFATA_BIANCA_AL_TARTUFO": entry(
        "Weiße Tartufata-Sauce mit Trüffel", VEG_S, 36,
        "Glasgefäß (80, 170, 500 g).",
        "Kulturchampignons (Agaricus bisporus), Sonnenblumenöl, Bianchetto-Trüffel "
        "(Tuber borchii, Vittad.), Reismehl, Salz, Aroma.",
        storage=STORE_AMBIENT_FRIDGE,
    ),
    "24_TARALLI_AL_TARTUFO": entry(
        "Taralli mit Trüffel", TRUFFLE, 36,
        "Lebensmittelechter Kunststoffbeutel (200 g).",
        "WEIZENMEHL Type 0, Weißwein (SULFITE), High-Oleic-Sonnenblumenöl, natives Olivenöl "
        "extra, Buchweizen, Salz, Wasser, Sommertrüffel (Tuber aestivum Vitt.) 1,2 %, natürliches Aroma.",
        NONE_EXTRA, STORE_COOL_DRY,
    ),
    "25_TARTUFATA_PICCANTE_AL_TARTUFO": entry(
        "Scharfe Tartufata-Sauce mit Trüffel", VEG_S, 36,
        "Glasgefäß (80, 180 g).",
        "Champignons, schwarzer Sommertrüffel (Tuber aestivum Vitt.), natives Olivenöl extra, "
        "schwarze Oliven, Paprika, scharfe Chilischote, Trüffelaromen, Salz, Petersilie.",
        storage=STORE_AMBIENT_FRIDGE,
    ),
    "26_MAIONESE_AL_TARTUFO": entry(
        "Trüffelmayonnaise", TRUFFLE_NS, 18, "Glasgefäß (120 g).",
        "Sonnenblumenöl, pasteurisiertes EI, Weinessig, natives Olivenöl extra, Sommertrüffel "
        "(Tuber aestivum Vitt.), Salz, Aroma.",
        NONE_EXTRA, STORE_KETCHUP, labelling=IT_EU_LABEL, micro=MICRO_NO_ANAE,
    ),
    "27_PESTO_AL_TARTUFO": entry(
        "Pesto Genovese mit weißem Trüffel", VEG_S, 36, "Glasgefäß (80 g).",
        "Olivenöl, Genoveser Basilikum, CASHEWKERNE, natives Olivenöl extra, Salz, Pinienkerne, "
        "weißer Trüffel (Tuber magnatum Pico), Aroma.",
        "Enthält SCHALENFRÜCHTE (CASHEWKERNE). Kann Spuren von anderen SCHALENFRÜCHTEN "
        "und ERDNÜSSEN enthalten.",
        STORE_AMBIENT_FRIDGE, labelling=IT_EU_LABEL, micro=MICRO_DRY,
    ),
}
