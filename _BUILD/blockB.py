import json
from pathlib import Path
from common import *
EAN=""
# typologie extra
typ_truffle_past=L("Prodotto a base di tartufo, pastorizzato.","Produit à base de truffe, pasteurisé.","Truffle-based product, pasteurised.","Truffelproduct, gepasteuriseerd.")
typ_truffle_ns=L("Prodotto a base di tartufo, non sterilizzato.","Produit à base de truffe, non stérilisé.","Truffle-based product, not sterilised.","Truffelproduct, niet gesteriliseerd.")
stor_cool20=L("Conservare in luogo fresco (max 20°C) e asciutto.","Conserver dans un endroit frais (max 20°C) et sec.","Store in a cool (max 20°C) and dry place.","Bewaren op een koele (max 20°C) en droge plaats.")
stor_ketchup=L("Conservare in luogo fresco e asciutto, al riparo dalla luce solare diretta (8-15°C). Dopo l'apertura, conservare in frigorifero tra 0 e 4°C e consumare entro 4-5 giorni.",
 "Conserver dans un endroit frais et sec, à l'abri de la lumière directe du soleil (8-15°C). Après ouverture, conserver au réfrigérateur entre 0 et 4°C et consommer sous 4-5 jours.",
 "Store in a cool, dry place, away from direct sunlight (8-15°C). After opening, keep refrigerated between 0 and 4°C and consume within 4-5 days.",
 "Bewaren op een koele, droge plaats, beschermd tegen direct zonlicht (8-15°C). Na opening gekoeld bewaren tussen 0 en 4°C en binnen 4-5 dagen consumeren.")
micro_honey=L("Carica Batterica Totale (CBT): < 10 UFC/g; Muffe e lieviti: assenti; Salmonella: assente in 25 g.",
 "Flore aérobie mésophile totale : < 10 UFC/g ; Levures et moisissures : absentes ; Salmonelles : absentes dans 25 g.",
 "Total Bacterial Count (TBC): < 10 CFU/g; Yeasts and moulds: absent; Salmonella: absent in 25 g.",
 "Totaal kiemgetal (TBC): < 10 KVE/g; Gisten en schimmels: afwezig; Salmonella: afwezig in 25 g.")
def nuts(name_it,name_fr,name_en,name_nl):
    return L("Contiene FRUTTA A GUSCIO (%s). Può contenere tracce di: SOIA, SEMI DI SESAMO, SENAPE, altra FRUTTA A GUSCIO e ANIDRIDE SOLFOROSA."%name_it,
             "Contient des FRUITS À COQUE (%s). Peut contenir des traces de : SOJA, GRAINES DE SÉSAME, MOUTARDE, autres FRUITS À COQUE et ANHYDRIDE SULFUREUX."%name_fr,
             "Contains NUTS (%s). May contain traces of: SOY, SESAME SEEDS, MUSTARD, other NUTS and SULPHUR DIOXIDE."%name_en,
             "Bevat NOTEN (%s). Kan sporen bevatten van: SOJA, SESAMZAAD, MOSTERD, andere NOTEN en ZWAVELDIOXIDE."%name_nl)
P=[]
# 08 Crema Porcini
P.append(prod("08_CREMA_DI_FUNGHI_PORCINI_E_TARTUFO_NERO_ESTIVO",
 L("Crema di Porcini e Tartufo Nero Estivo","Crème de Cèpes et Truffe Noire d'Été","Porcini & Summer Black Truffle Cream","Crème van Eekhoorntjesbrood en Zwarte Zomertruffel"),
 EAN, TYP["veg_s"], shelf("36 mesi","36 mois","36 months","36 maanden"),
 L("Vasetto in vetro (80, 170 g).","Pot en verre (80, 170 g).","Glass jar (80, 170 g).","Glazen pot (80, 170 g)."),
 "Reg. UE 1169/2011", GMO,
 L("Funghi porcini (Boletus edulis), tartufo nero estivo (Tuber aestivum Vitt.) 5%, olio extravergine di oliva, sale, pepe, prezzemolo, aroma.",
   "Cèpes (Boletus edulis), truffe noire d'été (Tuber aestivum Vitt.) 5 %, huile d'olive extra vierge, sel, poivre, persil, arôme.",
   "Porcini mushrooms (Boletus edulis), summer black truffle (Tuber aestivum Vitt.) 5%, extra virgin olive oil, salt, pepper, parsley, flavouring.",
   "Eekhoorntjesbrood (Boletus edulis), zwarte zomertruffel (Tuber aestivum Vitt.) 5%, extra vierge olijfolie, zout, peper, peterselie, aroma."),
 ALL["none"], STOR["amb_fridge"], USE["ready"],
 {"energy":"815,2 kJ / 194,8 kcal","fat":"18,20 g","sat":"2,60 g","carb":"3,50 g","sugar":"0,90 g","protein":"2,00 g","salt":"1,1 g"},
 micro=MICRO["full"]))
# 09 Ketchup
P.append(prod("09_KETCHUP_TARTUFATO",
 L("Ketchup al Tartufo","Ketchup à la Truffe","Truffle Ketchup","Truffelketchup"),
 EAN, typ_truffle_past, shelf("24 mesi","24 mois","24 months","24 maanden"),
 L("Vasetto in vetro (85 g).","Pot en verre (85 g).","Glass jar (85 g).","Glazen pot (85 g)."),
 "D.Lgs. 109/1992 e Reg. UE 1169/2011", GMO,
 L("Pomodoro (148 g per 100 g di prodotto), aceto di alcool, tartufo estivo (Tuber aestivum Vitt.) 1%, zucchero, sale, spezie ed estratti di erbe aromatiche (contiene SEDANO), spezie, aroma.",
   "Tomate (148 g pour 100 g de produit), vinaigre d'alcool, truffe d'été (Tuber aestivum Vitt.) 1 %, sucre, sel, épices et extraits de plantes aromatiques (contient du CÉLERI), épices, arôme.",
   "Tomato (148 g per 100 g of product), spirit vinegar, summer truffle (Tuber aestivum Vitt.) 1%, sugar, salt, spices and aromatic herb extracts (contains CELERY), spices, flavouring.",
   "Tomaat (148 g per 100 g product), alcoholazijn, zomertruffel (Tuber aestivum Vitt.) 1%, suiker, zout, specerijen en aromatische kruidenextracten (bevat SELDERIJ), specerijen, aroma."),
 ALL["none_extra"], stor_ketchup, USE["ready"],
 {"energy":"445 kJ / 105 kcal","fat":"0,90 g","sat":"0,00 g","carb":"23,00 g","sugar":"22,00 g","protein":"1,20 g","salt":"1,80 g"},
 micro=MICRO["noanae"]))
# 10 Miele
P.append(prod("10_MIELE_AL_TARTUFO",
 L("Miele al Tartufo Bianchetto","Miel à la Truffe Bianchetto","Honey with Bianchetto Truffle","Honing met Bianchetto-truffel"),
 EAN, typ_truffle_ns, shelf("24 mesi","24 mois","24 months","24 maanden"),
 L("Vasetto in vetro (100, 170, 500 g).","Pot en verre (100, 170, 500 g).","Glass jar (100, 170, 500 g).","Glazen pot (100, 170, 500 g)."),
 "Reg. UE 1169/2011", GMO,
 L("Miele d'acacia, tartufo bianchetto (Tuber borchii Vitt.) 0,5% (2% in origine), aroma.",
   "Miel d'acacia, truffe bianchetto (Tuber borchii Vitt.) 0,5 % (2 % à l'origine), arôme.",
   "Acacia honey, bianchetto truffle (Tuber borchii Vitt.) 0.5% (2% originally), flavouring.",
   "Acaciahoning, bianchetto-truffel (Tuber borchii Vitt.) 0,5% (2% oorspronkelijk), aroma."),
 ALL["none"], STOR["amb_open_orig"], USE["ready"],
 {"energy":"1429 kJ / 336 kcal","fat":"0,08 g","sat":"0,01 g","carb":"83,68 g","sugar":"77,55 g","protein":"0,12 g","salt":"0,00 g"},
 micro=micro_honey))
# 11 Mandorle (allergene corretto)
P.append(prod("11_MANDORLE",
 L("Mandorle al Tartufo","Amandes à la Truffe","Almonds with Truffle","Amandelen met Truffel"),
 EAN, TYP["veg_ns"], shelf("12 mesi","12 mois","12 months","12 maanden"),
 L("Vasetto in latta.","Pot en métal (boîte).","Tin jar.","Blikken potje."),
 "Reg. UE 1169/2011", GMO,
 L("MANDORLE sgusciate tostate 92,5%; olio di girasole 5%; [sale, tartufo estivo (Tuber aestivum Vitt.) 1%, aromi] 2,5%.",
   "AMANDES décortiquées et grillées 92,5 % ; huile de tournesol 5 % ; [sel, truffe d'été (Tuber aestivum Vitt.) 1 %, arômes] 2,5 %.",
   "Toasted shelled ALMONDS 92.5%; sunflower oil 5%; [salt, summer truffle (Tuber aestivum Vitt.) 1%, flavourings] 2.5%.",
   "Gepelde geroosterde AMANDELEN 92,5%; zonnebloemolie 5%; [zout, zomertruffel (Tuber aestivum Vitt.) 1%, aroma's] 2,5%."),
 nuts("MANDORLE","AMANDES","ALMONDS","AMANDELEN"), stor_cool20, USE["consume"],
 {"energy":"2534 kJ / 613 kcal","fat":"54 g","sat":"4,2 g","carb":"7,9 g","sugar":"4,3 g","protein":"19 g","salt":"2,3 g","fibre":"9,8 g"},
 micro=MICRO["full"]))
# 12 Noci (titolo corretto + allergene)
P.append(prod("12_NOCI_AL_TARTUFO",
 L("Noci al Tartufo","Noix à la Truffe","Walnuts with Truffle","Walnoten met Truffel"),
 EAN, TYP["veg_ns"], shelf("12 mesi","12 mois","12 months","12 maanden"),
 L("Vasetto in latta.","Pot en métal (boîte).","Tin jar.","Blikken potje."),
 "Reg. UE 1169/2011", GMO,
 L("NOCI sgusciate tostate 95%; olio di girasole 3,4%; [sale, tartufo estivo (Tuber aestivum Vitt.) 1%, aromi] 1,6%.",
   "NOIX décortiquées et grillées 95 % ; huile de tournesol 3,4 % ; [sel, truffe d'été (Tuber aestivum Vitt.) 1 %, arômes] 1,6 %.",
   "Toasted shelled WALNUTS 95%; sunflower oil 3.4%; [salt, summer truffle (Tuber aestivum Vitt.) 1%, flavourings] 1.6%.",
   "Gepelde geroosterde WALNOTEN 95%; zonnebloemolie 3,4%; [zout, zomertruffel (Tuber aestivum Vitt.) 1%, aroma's] 1,6%."),
 nuts("NOCI","NOIX","WALNUTS","WALNOTEN"), STOR["amb"], USE["consume"],
 {"energy":"2932 kJ / 710 kcal","fat":"65 g","sat":"6,0 g","carb":"14 g","sugar":"3,0 g","protein":"14 g","salt":"1,5 g","fibre":"6,4 g"},
 micro=MICRO["full"]))
json.dump(P,open(Path(__file__).with_suffix(".json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("blockB.json:",len(P))
