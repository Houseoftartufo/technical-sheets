import json
from pathlib import Path
from common import *
EAN=""
stor_salt=L("Conservare a temperatura ambiente, al riparo dalla luce e da fonti di calore. Dopo l'apertura, conservare il prodotto nella confezione originale, al riparo dalla luce diretta, in luogo asciutto e ben ventilato.",
 "Conserver à température ambiante, à l'abri de la lumière et des sources de chaleur. Après ouverture, conserver le produit dans son emballage d'origine, à l'abri de la lumière directe, dans un endroit sec et bien ventilé.",
 "Store at room temperature, away from light and heat sources. After opening, keep the product in its original packaging, away from direct light, in a dry and well-ventilated place.",
 "Bewaren op kamertemperatuur, beschermd tegen licht en warmtebronnen. Na opening het product in de originele verpakking bewaren, beschermd tegen direct licht, op een droge en goed geventileerde plaats.")
jar=L("Vasetto in vetro.","Pot en verre.","Glass jar.","Glazen pot.")
P=[]
def salt(folder,title,ingr,nut):
    return prod(folder,title,EAN,TYP["veg_ns"],shelf("24 mesi","24 mois","24 months","24 maanden"),
                jar,"Reg. UE 1169/2011",GMO,ingr,ALL["none"],stor_salt,USE["ready"],nut,micro=MICRO["noanae"])
# 18 Sale Grigio
P.append(salt("18_SALE_GRIGIO",
 L("Sale Tartufato Grigio","Sel Gris à la Truffe","Grey Salt with Truffle","Grijs Zout met Truffel"),
 L("Sale grigio, tartufo estivo essiccato (Tuber aestivum, Vittad.) 2%, aroma.",
   "Sel gris, truffe d'été séchée (Tuber aestivum, Vittad.) 2 %, arôme.",
   "Grey salt, dried summer truffle (Tuber aestivum, Vittad.) 2%, flavouring.",
   "Grijs zout, gedroogde zomertruffel (Tuber aestivum, Vittad.) 2%, aroma."),
 {"energy":"41 kJ / 10 kcal","fat":"0,40 g","sat":"0,06 g","carb":"0,74 g","sugar":"0,06 g","protein":"0,48 g","salt":"97,61 g"}))
# 19 Sale Rosa
P.append(salt("19_SALE_ROSA",
 L("Sale Rosa Himalaya al Tartufo","Sel Rose de l'Himalaya à la Truffe","Himalayan Pink Salt with Truffle","Himalaya Roze Zout met Truffel"),
 L("Sale Rosa dell'Himalaya, tartufo estivo essiccato (Tuber aestivum, Vittad.) 2%, aroma.",
   "Sel rose de l'Himalaya, truffe d'été séchée (Tuber aestivum, Vittad.) 2 %, arôme.",
   "Himalayan pink salt, dried summer truffle (Tuber aestivum, Vittad.) 2%, flavouring.",
   "Himalaya roze zout, gedroogde zomertruffel (Tuber aestivum, Vittad.) 2%, aroma."),
 {"energy":"41 kJ / 10 kcal","fat":"0,40 g","sat":"0,06 g","carb":"0,74 g","sugar":"0,06 g","protein":"0,48 g","salt":"97,61 g"}))
# 20 Sale Tartufo Bianco (corretto: bianco/Magnatum)
P.append(salt("20_SALE_CON_TARTUFO_BIANCO",
 L("Sale al Tartufo Bianco","Sel à la Truffe Blanche","Salt with White Truffle","Zout met Witte Truffel"),
 L("Sale grigio, tartufo bianco essiccato (Tuber magnatum, Pico.) 1%, aroma.",
   "Sel gris, truffe blanche séchée (Tuber magnatum, Pico.) 1 %, arôme.",
   "Grey salt, dried white truffle (Tuber magnatum, Pico.) 1%, flavouring.",
   "Grijs zout, gedroogde witte truffel (Tuber magnatum, Pico.) 1%, aroma."),
 {"energy":"19 kJ / 5 kcal","fat":"0,31 g","sat":"0,05 g","carb":"0,03 g","sugar":"0,03 g","protein":"0,24 g","salt":"98,61 g"}))
# 21 Sale Tartufo Estivo
P.append(salt("21_SALE_CON_TARTUFO_NERO",
 L("Sale al Tartufo Estivo","Sel à la Truffe d'Été","Salt with Summer Truffle","Zout met Zomertruffel"),
 L("Sale, tartufo estivo essiccato (Tuber aestivum, Vittad.) 2%, aroma.",
   "Sel, truffe d'été séchée (Tuber aestivum, Vittad.) 2 %, arôme.",
   "Salt, dried summer truffle (Tuber aestivum, Vittad.) 2%, flavouring.",
   "Zout, gedroogde zomertruffel (Tuber aestivum, Vittad.) 2%, aroma."),
 {"energy":"29 kJ / 7 kcal","fat":"0,40 g","sat":"0,06 g","carb":"0,06 g","sugar":"0,06 g","protein":"0,48 g","salt":"97,61 g"}))
# 22 Salsa Tartufata Estivo
P.append(prod("22_SALSA_TARTUFATA_AL_TARTUFO_ESTIVO",
 L("Salsa Tartufata al Tartufo Estivo","Sauce Tartufata à la Truffe d'Été","Tartufata Sauce with Summer Truffle","Tartufata-saus met Zomertruffel"),
 EAN, TYP["veg_s"], shelf("36 mesi","36 mois","36 months","36 maanden"),
 L("Vasetto in vetro (80, 170, 500 g).","Pot en verre (80, 170, 500 g).","Glass jar (80, 170, 500 g).","Glazen pot (80, 170, 500 g)."),
 "Reg. UE 1169/2011", GMO,
 L("Funghi prataioli coltivati (Agaricus bisporus), olio di semi di girasole, tartufo estivo (Tuber aestivum, Vittad.), olive nere, sale, aroma, aglio, prezzemolo.",
   "Champignons de Paris cultivés (Agaricus bisporus), huile de graines de tournesol, truffe d'été (Tuber aestivum, Vittad.), olives noires, sel, arôme, ail, persil.",
   "Cultivated champignon mushrooms (Agaricus bisporus), sunflower seed oil, summer truffle (Tuber aestivum, Vittad.), black olives, salt, flavouring, garlic, parsley.",
   "Gekweekte champignons (Agaricus bisporus), zonnebloemzaadolie, zomertruffel (Tuber aestivum, Vittad.), zwarte olijven, zout, aroma, knoflook, peterselie."),
 ALL["none"], STOR["amb_fridge"], USE["ready"],
 {"energy":"927 kJ / 225 kcal","fat":"20,00 g","sat":"2,5 g","carb":"5,00 g","sugar":"1,00 g","protein":"2,00 g","salt":"1,00 g"},
 micro=MICRO["full"]))
json.dump(P,open(Path(__file__).with_suffix(".json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("blockD.json:",len(P))
