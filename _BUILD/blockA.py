import json,sys
sys.path.insert(0,"/tmp/build")
from common import *
EAN=""
P=[]
# 03 Arachidi
P.append(prod("03_ARACHIDI_SGUSCIATE_AL_TARTUFO",
 L("Arachidi Sgusciate al Tartufo","Cacahuètes Décortiquées à la Truffe","Shelled Peanuts with Truffle","Gepelde Pinda's met Truffel"),
 EAN, TYP["veg_ns"], shelf("12 mesi","12 mois","12 months","12 maanden"),
 L("Vasetto in latta.","Pot en métal (boîte).","Tin jar.","Blikken potje."),
 "Reg. UE 1169/2011", GMO,
 L("ARACHIDI sgusciate tostate 92,5%; olio di girasole 5%; [sale, tartufo estivo (Tuber aestivum Vitt.) 1%, aromi] 2,5%.",
   "ARACHIDES décortiquées et grillées 92,5 % ; huile de tournesol 5 % ; [sel, truffe d'été (Tuber aestivum Vitt.) 1 %, arômes] 2,5 %.",
   "Toasted shelled PEANUTS 92.5%; sunflower oil 5%; [salt, summer truffle (Tuber aestivum Vitt.) 1%, flavourings] 2.5%.",
   "Gepelde geroosterde PINDA'S 92,5%; zonnebloemolie 5%; [zout, zomertruffel (Tuber aestivum Vitt.) 1%, aroma's] 2,5%."),
 L("Contiene ARACHIDI. Può contenere tracce di: SOIA, SEMI DI SESAMO, SENAPE, altra FRUTTA A GUSCIO e ANIDRIDE SOLFOROSA.",
   "Contient des ARACHIDES. Peut contenir des traces de : SOJA, GRAINES DE SÉSAME, MOUTARDE, autres FRUITS À COQUE et ANHYDRIDE SULFUREUX.",
   "Contains PEANUTS. May contain traces of: SOY, SESAME SEEDS, MUSTARD, other NUTS and SULPHUR DIOXIDE.",
   "Bevat PINDA'S. Kan sporen bevatten van: SOJA, SESAMZAAD, MOSTERD, andere NOTEN en ZWAVELDIOXIDE."),
 STOR["amb"], USE["consume"],
 {"energy":"2526 kJ / 610 kcal","fat":"51 g","sat":"7,7 g","carb":"12 g","sugar":"4,5 g","protein":"22 g","salt":"2,3 g","fibre":"7,6 g"},
 micro=MICRO["full"]))
# 04 Burro Bianchetto 6%
P.append(prod("04_BURRO_BIANCHETTO_6PCT",
 L("Condimento di Burro e Tartufo Bianchetto 6%","Préparation de Beurre et Truffe Bianchetto 6 %","Butter Condiment with Bianchetto Truffle 6%","Boterbereiding met Bianchetto-truffel 6%"),
 EAN, TYP["dairy_s"], shelf("36 mesi","36 mois","36 months","36 maanden"),
 L("Vasetto in vetro (80, 160, 450 g).","Pot en verre (80, 160, 450 g).","Glass jar (80, 160, 450 g).","Glazen pot (80, 160, 450 g)."),
 L("D.Lgs. 109/1992 e Reg. UE 1169/2011","D.Lgs. 109/1992 et Rég. UE 1169/2011","Italian Legislative Decree 109/1992 and EU Reg. 1169/2011","Wetsbesluit 109/1992 en EU-Verord. 1169/2011")["ITA"] if False else "D.Lgs. 109/1992 e Reg. UE 1169/2011", GMO,
 L("BURRO (LATTOSIO), tartufo bianchetto (Tuber borchii, Vittad.) 6%, sale, aroma.",
   "BEURRE (LACTOSE), truffe bianchetto (Tuber borchii, Vittad.) 6 %, sel, arôme.",
   "BUTTER (LACTOSE), bianchetto truffle (Tuber borchii, Vittad.) 6%, salt, flavouring.",
   "BOTER (LACTOSE), bianchetto-truffel (Tuber borchii, Vittad.) 6%, zout, aroma."),
 ALL["none_extra"], STOR["amb_fridge"], USE["ready"],
 {"energy":"3454 kJ / 840 kcal","fat":"91,70 g","sat":"57,40 g","carb":"0,50 g","sugar":"0,40 g","protein":"0,06 g","salt":"1,10 g"},
 micro=MICRO["noanae"]))
# 05 Burro Estivo 3%
P.append(prod("05_BURRO_ESTIVO_3PCT",
 L("Condimento di Burro e Tartufo Estivo 3%","Préparation de Beurre et Truffe d'Été 3 %","Butter Condiment with Summer Truffle 3%","Boterbereiding met Zomertruffel 3%"),
 EAN, TYP["dairy_s"], shelf("36 mesi","36 mois","36 months","36 maanden"),
 L("Vasetto in vetro (80, 160, 450 g).","Pot en verre (80, 160, 450 g).","Glass jar (80, 160, 450 g).","Glazen pot (80, 160, 450 g)."),
 "Reg. UE 1169/2011", GMO,
 L("BURRO (LATTOSIO), tartufo estivo (Tuber aestivum, Vittad.) 3%, sale, aroma.",
   "BEURRE (LACTOSE), truffe d'été (Tuber aestivum, Vittad.) 3 %, sel, arôme.",
   "BUTTER (LACTOSE), summer truffle (Tuber aestivum, Vittad.) 3%, salt, flavouring.",
   "BOTER (LACTOSE), zomertruffel (Tuber aestivum, Vittad.) 3%, zout, aroma."),
 ALL["none_extra"], STOR["amb_fridge"], USE["ready"],
 {"energy":"3554 kJ / 864 kcal","fat":"94,50 g","sat":"59,20 g","carb":"0,60 g","sugar":"0,50 g","protein":"0,50 g","salt":"1,20 g"},
 micro=MICRO["noanae"]))
# 06 Carpaccio
P.append(prod("06_CARPACCIO_DI_TARTUFO_IN_ACQUA",
 L("Carpaccio di Tartufo Estivo in Acqua","Carpaccio de Truffe d'Été dans l'Eau","Summer Truffle Carpaccio in Water","Carpaccio van Zomertruffel in Water"),
 EAN, TYP["veg_s"], shelf("36 mesi","36 mois","36 months","36 maanden"),
 L("Vasetto in vetro (80, 170, 500 g).","Pot en verre (80, 170, 500 g).","Glass jar (80, 170, 500 g).","Glazen pot (80, 170, 500 g)."),
 "D.Lgs. 109/1992 e Reg. UE 1169/2011", GMO,
 L("Tartufo estivo (Tuber aestivum, Vittad.) 60%, acqua, aroma.",
   "Truffe d'été (Tuber aestivum, Vittad.) 60 %, eau, arôme.",
   "Summer truffle (Tuber aestivum, Vittad.) 60%, water, flavouring.",
   "Zomertruffel (Tuber aestivum, Vittad.) 60%, water, aroma."),
 ALL["none"], STOR["amb_fridge"], USE["ready"],
 {"energy":"259 kJ / 62 kcal","fat":"0,36 g","sat":"0,06 g","carb":"2,85 g","sugar":"0,47 g","protein":"2,42 g","salt":"1,25 g"},
 micro=MICRO["full"]))
# 07 Crema Balsamica
P.append(prod("07_CREMA_ALLACETO_BALSAMICO_AL_TARTUFO",
 L("Crema all'Aceto Balsamico di Modena all'Aroma di Tartufo","Crème de Vinaigre Balsamique de Modène à l'Arôme de Truffe","Modena Balsamic Glaze with Truffle Flavour","Crème van Balsamicoazijn van Modena met Truffelaroma"),
 EAN, TYP["veg_ns"], shelf("18 mesi","18 mois","18 months","18 maanden"),
 L("Bottiglia di vetro, 100 ml.","Flacon en verre, 100 ml.","Glass bottle, 100 ml.","Glazen fles, 100 ml."),
 "Reg. UE 1169/2011", GMO,
 L("Succo d'uva concentrato, aceto balsamico di Modena IGP 35% (aceto di vino, mosto d'uva concentrato, colorante E150d), sciroppo di glucosio-fruttosio, aceto di vino, amido modificato, colorante E150d, aroma. Contiene SOLFITI.",
   "Jus de raisin concentré, vinaigre balsamique de Modène IGP 35 % (vinaigre de vin, moût de raisin concentré, colorant E150d), sirop de glucose-fructose, vinaigre de vin, amidon modifié, colorant E150d, arôme. Contient des SULFITES.",
   "Concentrated grape juice, Balsamic Vinegar of Modena PGI 35% (wine vinegar, concentrated grape must, colour E150d), glucose-fructose syrup, wine vinegar, modified starch, colour E150d, flavouring. Contains SULPHITES.",
   "Geconcentreerd druivensap, balsamicoazijn van Modena BGA 35% (wijnazijn, geconcentreerde druivenmost, kleurstof E150d), glucose-fructosestroop, wijnazijn, gemodificeerd zetmeel, kleurstof E150d, aroma. Bevat SULFIETEN."),
 ALL["none_extra"], STOR["amb_fridge"], USE["ready"],
 {"energy":"942 kJ / 222 kcal","fat":"0,41 g","sat":"0,06 g","carb":"53,09 g","sugar":"45,37 g","protein":"1,46 g","salt":"0,24 g"},
 micro=MICRO["basic"]))
json.dump(P,open("/tmp/build/blockA.json","w"),ensure_ascii=False,indent=1)
print("blockA.json:",len(P),"prodotti")
