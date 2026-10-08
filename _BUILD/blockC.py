import json
from pathlib import Path
from common import *
EAN=""
stor_riso=L("Conservare a temperatura ambiente, al riparo dalla luce e da fonti di calore. Dopo l'apertura, conservare il prodotto nella confezione originale, al riparo dalla luce diretta e dal calore, in un luogo ben ventilato.",
 "Conserver à température ambiante, à l'abri de la lumière et des sources de chaleur. Après ouverture, conserver le produit dans son emballage d'origine, à l'abri de la lumière directe et de la chaleur, dans un endroit bien ventilé.",
 "Store at room temperature, away from light and heat sources. After opening, keep the product in its original packaging, away from direct light and heat, in a well-ventilated place.",
 "Bewaren op kamertemperatuur, beschermd tegen licht en warmtebronnen. Na opening het product in de originele verpakking bewaren, beschermd tegen direct licht en warmte, op een goed geventileerde plaats.")
micro_drygoods=L("Carica Batterica Totale (CBT): < 10 UFC/g; Muffe e lieviti: assenti; Salmonella: assente in 25 g.",
 "Flore aérobie mésophile totale : < 10 UFC/g ; Levures et moisissures : absentes ; Salmonelles : absentes dans 25 g.",
 "Total Bacterial Count (TBC): < 10 CFU/g; Yeasts and moulds: absent; Salmonella: absent in 25 g.",
 "Totaal kiemgetal (TBC): < 10 KVE/g; Gisten en schimmels: afwezig; Salmonella: afwezig in 25 g.")
oil_pack=L("Bottiglia di vetro (60, 100, 250, 500, 1000 ml); lattina di metallo (5 L).",
 "Flacon en verre (60, 100, 250, 500, 1000 ml) ; bidon métallique (5 L).",
 "Glass bottle (60, 100, 250, 500, 1000 ml); metal tin (5 L).",
 "Glazen fles (60, 100, 250, 500, 1000 ml); metalen blik (5 L).")
oil_ingr=L("Olio extravergine di oliva, aroma.","Huile d'olive extra vierge, arôme.","Extra virgin olive oil, flavouring.","Extra vierge olijfolie, aroma.")
P=[]
# 13 Olio bianco
P.append(prod("13_OLIO_EXTRA_VERGINE_DOLIVA_AL_TARTUFO_BIANCO",
 L("Olio Extra Vergine di Oliva all'Aroma di Tartufo Bianco","Huile d'Olive Extra Vierge à l'Arôme de Truffe Blanche","Extra Virgin Olive Oil with White Truffle Flavour","Extra Vierge Olijfolie met Witte Truffelaroma"),
 EAN, TYP["veg_ns"], shelf("24 mesi","24 mois","24 months","24 maanden"),
 oil_pack, "Reg. UE 1169/2011", GMO, oil_ingr, ALL["none"], STOR["amb_open_orig"], USE["ready"],
 {"energy":"3690 kJ / 868 kcal","fat":"99,74 g","sat":"14,44 g","carb":"0,00 g","sugar":"0,00 g","protein":"0,00 g","salt":"0,00 g"},
 micro=MICRO["full"]))
# 14 Olio nero
P.append(prod("14_OLIO_EXTRAVERGINE_DOLIVA_AL_TARTUFO_NERO_ESTIVO",
 L("Olio Extra Vergine di Oliva all'Aroma di Tartufo Nero Estivo","Huile d'Olive Extra Vierge à l'Arôme de Truffe Noire d'Été","Extra Virgin Olive Oil with Summer Black Truffle Flavour","Extra Vierge Olijfolie met Zwarte Zomertruffelaroma"),
 EAN, TYP["veg_ns"], shelf("24 mesi","24 mois","24 months","24 maanden"),
 oil_pack, "Reg. UE 1169/2011", GMO, oil_ingr, ALL["none"], STOR["amb_open_orig"], USE["ready"],
 {"energy":"3696 kJ / 899 kcal","fat":"99,90 g","sat":"14,46 g","carb":"0,00 g","sugar":"0,00 g","protein":"0,00 g","salt":"0,00 g"},
 micro=MICRO["full"]))
# 15 Perle (speciale)
P.append(prod("15_PERLE",
 L("Perle di Aceto Balsamico al Tartufo","Perles de Vinaigre Balsamique à la Truffe","Balsamic Vinegar Pearls with Truffle","Parels van Balsamicoazijn met Truffel"),
 EAN, TYP["veg_ns"], shelf("24 mesi","24 mois","24 months","24 maanden"),
 L("Vasetto in vetro (50 g).","Pot en verre (50 g).","Glass jar (50 g).","Glazen pot (50 g)."),
 "Reg. UE 1169/2011", GMO,
 L("Aceto Balsamico di Modena IGP 60% min. (aceto di vino, mosto d'uva cotto), acqua, gelificanti: gomma di cellulosa, cloruro di calcio, alginato di sodio, tartufo estivo (Tuber aestivum) 0,1%, aroma. Contiene SOLFITI.",
   "Vinaigre balsamique de Modène IGP 60 % min. (vinaigre de vin, moût de raisin cuit), eau, gélifiants : gomme de cellulose, chlorure de calcium, alginate de sodium, truffe d'été (Tuber aestivum) 0,1 %, arôme. Contient des SULFITES.",
   "Balsamic Vinegar of Modena PGI 60% min. (wine vinegar, cooked grape must), water, gelling agents: cellulose gum, calcium chloride, sodium alginate, summer truffle (Tuber aestivum) 0.1%, flavouring. Contains SULPHITES.",
   "Balsamicoazijn van Modena BGA 60% min. (wijnazijn, gekookte druivenmost), water, geleermiddelen: cellulosegom, calciumchloride, natriumalginaat, zomertruffel (Tuber aestivum) 0,1%, aroma. Bevat SULFIETEN."),
 ALL["none_extra"],
 L("Conservare al riparo dal sole e dalla luce diretta (10-20°C). Dopo l'apertura, conservare in frigorifero e consumare entro 10 giorni.",
   "Conserver à l'abri du soleil et de la lumière directe (10-20°C). Après ouverture, conserver au réfrigérateur et consommer sous 10 jours.",
   "Store away from sunlight and direct light (10-20°C). After opening, keep refrigerated and consume within 10 days.",
   "Beschermd tegen zon en direct licht bewaren (10-20°C). Na opening gekoeld bewaren en binnen 10 dagen consumeren."),
 USE["ready"],
 {"energy":"602 kJ / 141 kcal","fat":"0 g","sat":"0 g","carb":"33 g","sugar":"33 g","protein":"0,1 g","salt":"0,03 g"},
 chem=L("Zuccheri totali: 210-230 g/l; Anidride solforosa totale: max 100 mg/l; pH: 3-4,5.",
        "Sucres totaux : 210-230 g/l ; Anhydride sulfureux total : max 100 mg/l ; pH : 3-4,5.",
        "Total sugars: 210-230 g/l; Total sulphur dioxide: max 100 mg/l; pH: 3-4.5.",
        "Totale suikers: 210-230 g/l; Totaal zwaveldioxide: max 100 mg/l; pH: 3-4,5."),
 micro=L("Conta batterica totale: < 100 UFC/ml; Lieviti: < 50 UFC/ml; Muffe: < 10 UFC/ml; Coliformi: assenti; Salmonella: assente; Germi patogeni: assenti.",
         "Flore totale : < 100 UFC/ml ; Levures : < 50 UFC/ml ; Moisissures : < 10 UFC/ml ; Coliformes : absents ; Salmonelles : absentes ; Germes pathogènes : absents.",
         "Total count: < 100 CFU/ml; Yeasts: < 50 CFU/ml; Moulds: < 10 CFU/ml; Coliforms: absent; Salmonella: absent; Pathogens: absent.",
         "Totaal kiemgetal: < 100 KVE/ml; Gisten: < 50 KVE/ml; Schimmels: < 10 KVE/ml; Coliformen: afwezig; Salmonella: afwezig; Pathogenen: afwezig.")))
# 16 Polenta
P.append(prod("16_POLENTA_AL_TARTUFO",
 L("Polenta al Tartufo Estivo","Polenta à la Truffe d'Été","Polenta with Summer Truffle","Polenta met Zomertruffel"),
 EAN, TYP["veg_ns"], shelf("18 mesi","18 mois","18 months","18 maanden"),
 L("Sacchetto di plastica per uso alimentare (125 g).","Sachet plastique de qualité alimentaire (125 g).","Food-grade plastic bag (125 g).","Plastic zak voor levensmiddelen (125 g)."),
 "Reg. UE 1169/2011", GMO,
 L("Farina di mais, farina di grano saraceno, aroma, tartufo estivo essiccato (Tuber aestivum, Vitt.) 0,2%.",
   "Farine de maïs, farine de sarrasin, arôme, truffe d'été séchée (Tuber aestivum, Vitt.) 0,2 %.",
   "Corn flour, buckwheat flour, flavouring, dried summer truffle (Tuber aestivum, Vitt.) 0.2%.",
   "Maïsmeel, boekweitmeel, aroma, gedroogde zomertruffel (Tuber aestivum, Vitt.) 0,2%."),
 ALL["none"], STOR["amb_open_orig"], USE["ready"],
 {"energy":"1469 kJ / 346 kcal","fat":"1,25 g","sat":"0,26 g","carb":"74,33 g","sugar":"0,59 g","protein":"8,22 g","salt":"0,14 g"},
 micro=micro_drygoods))
# 17 Riso
P.append(prod("17_RISO_TARTUFO_ESTIVO_G_170_1000___170G",
 L("Riso al Tartufo Estivo","Riz à la Truffe d'Été","Rice with Summer Truffle","Rijst met Zomertruffel"),
 EAN, TYP["veg_ns"], shelf("18 mesi","18 mois","18 months","18 maanden"),
 L("Sacchetto di plastica per uso alimentare (170 g).","Sachet plastique de qualité alimentaire (170 g).","Food-grade plastic bag (170 g).","Plastic zak voor levensmiddelen (170 g)."),
 "Reg. UE 1169/2011", GMO,
 L("Riso Carnaroli, funghi essiccati (Agaricus bisporus), tartufo estivo essiccato (Tuber aestivum, Vitt.) 0,3%, aroma.",
   "Riz Carnaroli, champignons séchés (Agaricus bisporus), truffe d'été séchée (Tuber aestivum, Vitt.) 0,3 %, arôme.",
   "Carnaroli rice, dried mushrooms (Agaricus bisporus), dried summer truffle (Tuber aestivum, Vitt.) 0.3%, flavouring.",
   "Carnaroli-rijst, gedroogde champignons (Agaricus bisporus), gedroogde zomertruffel (Tuber aestivum, Vitt.) 0,3%, aroma."),
 ALL["none"], stor_riso, USE["ready"],
 {"energy":"1463 kJ / 345 kcal","fat":"1,62 g","sat":"0,52 g","carb":"74,90 g","sugar":"0,60 g","protein":"7,15 g","salt":"0,00 g"},
 micro=micro_drygoods))
json.dump(P,open(Path(__file__).with_suffix(".json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("blockC.json:",len(P))
