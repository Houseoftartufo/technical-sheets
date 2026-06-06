import json,sys
sys.path.insert(0,"/tmp/build")
from common import *
EAN=""
typ_truffle=L("Prodotto a base di tartufo.","Produit à base de truffe.","Truffle-based product.","Truffelproduct.")
typ_truffle_ns=L("Prodotto a base di tartufo, non sterilizzato.","Produit à base de truffe, non stérilisé.","Truffle-based product, not sterilised.","Truffelproduct, niet gesteriliseerd.")
stor_cool_dry=L("Conservare in luogo fresco e asciutto.","Conserver dans un endroit frais et sec.","Store in a cool, dry place.","Bewaren op een koele, droge plaats.")
stor_ketchup=L("Conservare in luogo fresco e asciutto, al riparo dalla luce solare diretta (8-15°C). Dopo l'apertura, conservare in frigorifero tra 0 e 4°C e consumare entro 4-5 giorni.",
 "Conserver dans un endroit frais et sec, à l'abri de la lumière directe du soleil (8-15°C). Après ouverture, conserver au réfrigérateur entre 0 et 4°C et consommer sous 4-5 jours.",
 "Store in a cool, dry place, away from direct sunlight (8-15°C). After opening, keep refrigerated between 0 and 4°C and consume within 4-5 days.",
 "Bewaren op een koele, droge plaats, beschermd tegen direct zonlicht (8-15°C). Na opening gekoeld bewaren tussen 0 en 4°C en binnen 4-5 dagen consumeren.")
micro_drygoods=L("Carica Batterica Totale (CBT): < 10 UFC/g; Muffe e lieviti: assenti; Salmonella: assente in 25 g.",
 "Flore aérobie mésophile totale : < 10 UFC/g ; Levures et moisissures : absentes ; Salmonelles : absentes dans 25 g.",
 "Total Bacterial Count (TBC): < 10 CFU/g; Yeasts and moulds: absent; Salmonella: absent in 25 g.",
 "Totaal kiemgetal (TBC): < 10 KVE/g; Gisten en schimmels: afwezig; Salmonella: afwezig in 25 g.")
P=[]
# 23 Salsa Bianca
P.append(prod("23_SALSA_TARTUFATA_BIANCA_AL_TARTUFO",
 L("Salsa Tartufata Bianca al Tartufo","Sauce Tartufata Blanche à la Truffe","White Tartufata Sauce with Truffle","Witte Tartufata-saus met Truffel"),
 EAN, TYP["veg_s"], shelf("36 mesi","36 mois","36 months","36 maanden"),
 L("Vasetto in vetro (80, 170, 500 g).","Pot en verre (80, 170, 500 g).","Glass jar (80, 170, 500 g).","Glazen pot (80, 170, 500 g)."),
 "Reg. UE 1169/2011", GMO,
 L("Funghi prataioli coltivati (Agaricus bisporus), olio di semi di girasole, tartufo bianchetto (Tuber borchii, Vittad.), farina di riso, sale, aroma.",
   "Champignons de Paris cultivés (Agaricus bisporus), huile de graines de tournesol, truffe bianchetto (Tuber borchii, Vittad.), farine de riz, sel, arôme.",
   "Cultivated champignon mushrooms (Agaricus bisporus), sunflower seed oil, bianchetto truffle (Tuber borchii, Vittad.), rice flour, salt, flavouring.",
   "Gekweekte champignons (Agaricus bisporus), zonnebloemzaadolie, bianchetto-truffel (Tuber borchii, Vittad.), rijstmeel, zout, aroma."),
 ALL["none"], STOR["amb_fridge"], USE["ready"],
 {"energy":"831 kJ / 202 kcal","fat":"18,50 g","sat":"2,00 g","carb":"4,20 g","sugar":"0,80 g","protein":"2,20 g","salt":"1,20 g"},
 micro=MICRO["full"]))
# 24 Taralli
P.append(prod("24_TARALLI_AL_TARTUFO",
 L("Taralli al Tartufo","Taralli à la Truffe","Taralli with Truffle","Taralli met Truffel"),
 EAN, typ_truffle, shelf("36 mesi","36 mois","36 months","36 maanden"),
 L("Sacchetto di plastica per uso alimentare (200 g).","Sachet plastique de qualité alimentaire (200 g).","Food-grade plastic bag (200 g).","Plastic zak voor levensmiddelen (200 g)."),
 "Reg. UE 1169/2011", GMO,
 L("Farina di GRANO tenero tipo 0, vino bianco (SOLFITI), olio di girasole alto oleico, olio extravergine di oliva, grano saraceno, sale, acqua, tartufo estivo (Tuber aestivum Vitt.) 1,2%, aroma naturale.",
   "Farine de BLÉ tendre type 0, vin blanc (SULFITES), huile de tournesol à haute teneur en acide oléique, huile d'olive extra vierge, sarrasin, sel, eau, truffe d'été (Tuber aestivum Vitt.) 1,2 %, arôme naturel.",
   "Soft WHEAT flour type 0, white wine (SULPHITES), high-oleic sunflower oil, extra virgin olive oil, buckwheat, salt, water, summer truffle (Tuber aestivum Vitt.) 1.2%, natural flavouring.",
   "Zachte TARWEbloem type 0, witte wijn (SULFIETEN), zonnebloemolie met hoog oliezuurgehalte, extra vierge olijfolie, boekweit, zout, water, zomertruffel (Tuber aestivum Vitt.) 1,2%, natuurlijk aroma."),
 ALL["none_extra"], stor_cool_dry, USE["ready"],
 {"energy":"1545 kJ / 368 kcal","fat":"15,00 g","sat":"1,60 g","carb":"47,00 g","sugar":"1,10 g","protein":"7,20 g","salt":"1,20 g"},
 micro=MICRO["full"]))
# 25 Tartufata Piccante
P.append(prod("25_TARTUFATA_PICCANTE_AL_TARTUFO",
 L("Salsa Tartufata Piccante al Tartufo","Sauce Tartufata Piquante à la Truffe","Spicy Tartufata Sauce with Truffle","Pikante Tartufata-saus met Truffel"),
 EAN, TYP["veg_s"], shelf("36 mesi","36 mois","36 months","36 maanden"),
 L("Vasetto in vetro (80, 180 g).","Pot en verre (80, 180 g).","Glass jar (80, 180 g).","Glazen pot (80, 180 g)."),
 "Reg. UE 1169/2011", GMO,
 L("Funghi champignon, tartufo nero estivo (Tuber aestivum Vitt.), olio extravergine di oliva, olive nere, paprika, peperoncino piccante, aromi di tartufo, sale, prezzemolo.",
   "Champignons, truffe noire d'été (Tuber aestivum Vitt.), huile d'olive extra vierge, olives noires, paprika, piment fort, arômes de truffe, sel, persil.",
   "Champignon mushrooms, summer black truffle (Tuber aestivum Vitt.), extra virgin olive oil, black olives, paprika, hot chilli pepper, truffle flavourings, salt, parsley.",
   "Champignons, zwarte zomertruffel (Tuber aestivum Vitt.), extra vierge olijfolie, zwarte olijven, paprika, hete chilipeper, truffelaroma's, zout, peterselie."),
 ALL["none"], STOR["amb_fridge"], USE["ready"],
 {"energy":"869,9 kJ / 207,9 kcal","fat":"14,00 g","sat":"2,10 g","carb":"12,50 g","sugar":"3,20 g","protein":"4,50 g","salt":"1,20 g"},
 micro=MICRO["full"]))
# 26 Maionese
P.append(prod("26_MAIONESE_AL_TARTUFO",
 L("Maionese al Tartufo","Mayonnaise à la Truffe","Truffle Mayonnaise","Truffelmayonaise"),
 EAN, typ_truffle_ns, shelf("18 mesi","18 mois","18 months","18 maanden"),
 L("Vasetto in vetro (120 g).","Pot en verre (120 g).","Glass jar (120 g).","Glazen pot (120 g)."),
 "D.Lgs. 109/1992 e Reg. UE 1169/2011", GMO,
 L("Olio di semi di girasole, UOVO pastorizzato, aceto di vino, olio extravergine di oliva, tartufo estivo (Tuber aestivum Vitt.), sale, aroma.",
   "Huile de graines de tournesol, ŒUF pasteurisé, vinaigre de vin, huile d'olive extra vierge, truffe d'été (Tuber aestivum Vitt.), sel, arôme.",
   "Sunflower seed oil, pasteurised EGG, wine vinegar, extra virgin olive oil, summer truffle (Tuber aestivum Vitt.), salt, flavouring.",
   "Zonnebloemzaadolie, gepasteuriseerd EI, wijnazijn, extra vierge olijfolie, zomertruffel (Tuber aestivum Vitt.), zout, aroma."),
 ALL["none_extra"], stor_ketchup, USE["ready"],
 {"energy":"2906 kJ / 721 kcal","fat":"79,00 g","sat":"9,50 g","carb":"0,00 g","sugar":"0,00 g","protein":"2,50 g","salt":"0,79 g"},
 micro=MICRO["noanae"]))
# 27 Pesto
P.append(prod("27_PESTO_AL_TARTUFO",
 L("Pesto Genovese al Tartufo Bianco","Pesto Genovese à la Truffe Blanche","Genovese Pesto with White Truffle","Genovese Pesto met Witte Truffel"),
 EAN, TYP["veg_s"], shelf("36 mesi","36 mois","36 months","36 maanden"),
 L("Vasetto in vetro (80 g).","Pot en verre (80 g).","Glass jar (80 g).","Glazen pot (80 g)."),
 "D.Lgs. 109/1992 e Reg. UE 1169/2011", GMO,
 L("Olio di oliva, basilico genovese, ANACARDI, olio extravergine di oliva, sale, pinoli, tartufo bianco (Tuber magnatum Pico), aroma.",
   "Huile d'olive, basilic génois, NOIX DE CAJOU, huile d'olive extra vierge, sel, pignons de pin, truffe blanche (Tuber magnatum Pico), arôme.",
   "Olive oil, Genovese basil, CASHEWS, extra virgin olive oil, salt, pine nuts, white truffle (Tuber magnatum Pico), flavouring.",
   "Olijfolie, Genovese basilicum, CASHEWNOTEN, extra vierge olijfolie, zout, pijnboompitten, witte truffel (Tuber magnatum Pico), aroma."),
 L("Contiene FRUTTA A GUSCIO (ANACARDI). Può contenere tracce di altra FRUTTA A GUSCIO e ARACHIDI.",
   "Contient des FRUITS À COQUE (NOIX DE CAJOU). Peut contenir des traces d'autres FRUITS À COQUE et d'ARACHIDES.",
   "Contains NUTS (CASHEWS). May contain traces of other NUTS and PEANUTS.",
   "Bevat NOTEN (CASHEWNOTEN). Kan sporen bevatten van andere NOTEN en PINDA'S."),
 STOR["amb_fridge"], USE["ready"],
 {"energy":"2482 kJ / 602 kcal","fat":"60,00 g","sat":"9,00 g","carb":"8,30 g","sugar":"3,00 g","protein":"5,80 g","salt":"3,30 g"},
 micro=micro_drygoods))
json.dump(P,open("/tmp/build/blockE.json","w"),ensure_ascii=False,indent=1)
print("blockE.json:",len(P))
