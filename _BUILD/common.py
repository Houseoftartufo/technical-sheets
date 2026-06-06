# Frasi comuni riutilizzabili (4 lingue) - traduzioni professionali B2B
def L(it,fr,en,nl): return {"ITA":it,"FR":fr,"ENG":en,"NL":nl}

TYP = {
 "veg_ns": L("Prodotto a base vegetale, non sterilizzato.","Produit d'origine végétale, non stérilisé.","Plant-based product, not sterilised.","Plantaardig product, niet gesteriliseerd."),
 "veg_s": L("Prodotto a base vegetale, sterilizzato.","Produit d'origine végétale, stérilisé.","Plant-based product, sterilised.","Plantaardig product, gesteriliseerd."),
 "dairy_s": L("Prodotto lattiero-caseario, sterilizzato.","Produit laitier, stérilisé.","Dairy product, sterilised.","Zuivelproduct, gesteriliseerd."),
}
STOR = {
 "amb": L("Conservare a temperatura ambiente, al riparo dalla luce e da fonti di calore.",
          "Conserver à température ambiante, à l'abri de la lumière et des sources de chaleur.",
          "Store at room temperature, away from light and heat sources.",
          "Bewaren op kamertemperatuur, beschermd tegen licht en warmtebronnen."),
 "amb_fridge": L("Conservare a temperatura ambiente, al riparo dalla luce e da fonti di calore. Dopo l'apertura, conservare in frigorifero tra 0 e 4°C e consumare entro 4-5 giorni.",
          "Conserver à température ambiante, à l'abri de la lumière et des sources de chaleur. Après ouverture, conserver au réfrigérateur entre 0 et 4°C et consommer sous 4-5 jours.",
          "Store at room temperature, away from light and heat sources. After opening, keep refrigerated between 0 and 4°C and consume within 4-5 days.",
          "Bewaren op kamertemperatuur, beschermd tegen licht en warmtebronnen. Na opening gekoeld bewaren tussen 0 en 4°C en binnen 4-5 dagen consumeren."),
 "amb_open_orig": L("Conservare a temperatura ambiente, al riparo dalla luce e da fonti di calore. Dopo l'apertura, conservare il prodotto nella confezione originale, al riparo dalla luce diretta e dal calore.",
          "Conserver à température ambiante, à l'abri de la lumière et des sources de chaleur. Après ouverture, conserver le produit dans son emballage d'origine, à l'abri de la lumière directe et de la chaleur.",
          "Store at room temperature, away from light and heat sources. After opening, keep the product in its original packaging, away from direct light and heat.",
          "Bewaren op kamertemperatuur, beschermd tegen licht en warmtebronnen. Na opening het product in de originele verpakking bewaren, beschermd tegen direct licht en warmte."),
}
USE = {
 "ready": L("Una volta aperto, il prodotto è pronto per essere utilizzato.","Une fois ouvert, le produit est prêt à l'emploi.","Once opened, the product is ready to use.","Eenmaal geopend is het product klaar voor gebruik."),
 "consume": L("Una volta aperto, il prodotto è pronto per essere consumato.","Une fois ouvert, le produit est prêt à être consommé.","Once opened, the product is ready to be consumed.","Eenmaal geopend is het product klaar voor consumptie."),
}
ALL = {
 "none_extra": L("Oltre a quanto dichiarato in MAIUSCOLO nel paragrafo precedente, il prodotto non contiene ulteriori ingredienti ad azione allergizzante.",
          "Hormis les allergènes indiqués en MAJUSCULES dans le paragraphe précédent, le produit ne contient aucun autre ingrédient allergène.",
          "Apart from the allergens stated in CAPITAL LETTERS in the paragraph above, the product does not contain any other allergenic ingredients.",
          "Naast de in HOOFDLETTERS vermelde allergenen in de vorige alinea bevat het product geen andere allergene ingrediënten."),
 "none": L("Nessuno.","Aucun.","None.","Geen."),
}
GMO = L("Assenti","Absents","None","Geen")
CHEM = L("Metalli pesanti: < 0,10 ppm","Métaux lourds : < 0,10 ppm","Heavy metals: < 0.10 ppm","Zware metalen: < 0,10 ppm")
MICRO = {
 "full": L("Carica Batterica Totale (CBT): < 10 UFC/g; Coliformi: < 10 UFC/g; Muffe e lieviti: assenti; Anaerobi solfito-riduttori: < 10 UFC/g; Listeria monocytogenes: assente in 25 g; Salmonella: assente in 25 g.",
          "Flore aérobie mésophile totale : < 10 UFC/g ; Coliformes : < 10 UFC/g ; Levures et moisissures : absentes ; Anaérobies sulfito-réducteurs : < 10 UFC/g ; Listeria monocytogenes : absente dans 25 g ; Salmonelles : absentes dans 25 g.",
          "Total Bacterial Count (TBC): < 10 CFU/g; Coliforms: < 10 CFU/g; Yeasts and moulds: absent; Sulphite-reducing anaerobes: < 10 CFU/g; Listeria monocytogenes: absent in 25 g; Salmonella: absent in 25 g.",
          "Totaal kiemgetal (TBC): < 10 KVE/g; Coliformen: < 10 KVE/g; Gisten en schimmels: afwezig; Sulfietreducerende anaeroben: < 10 KVE/g; Listeria monocytogenes: afwezig in 25 g; Salmonella: afwezig in 25 g."),
 "noanae": L("Carica Batterica Totale (CBT): < 10 UFC/g; Coliformi: < 10 UFC/g; Muffe e lieviti: assenti; Listeria monocytogenes: assente in 25 g; Salmonella: assente in 25 g.",
          "Flore aérobie mésophile totale : < 10 UFC/g ; Coliformes : < 10 UFC/g ; Levures et moisissures : absentes ; Listeria monocytogenes : absente dans 25 g ; Salmonelles : absentes dans 25 g.",
          "Total Bacterial Count (TBC): < 10 CFU/g; Coliforms: < 10 CFU/g; Yeasts and moulds: absent; Listeria monocytogenes: absent in 25 g; Salmonella: absent in 25 g.",
          "Totaal kiemgetal (TBC): < 10 KVE/g; Coliformen: < 10 KVE/g; Gisten en schimmels: afwezig; Listeria monocytogenes: afwezig in 25 g; Salmonella: afwezig in 25 g."),
 "basic": L("Carica Batterica Totale (CBT): < 10 UFC/g; Muffe e lieviti: assenti.",
          "Flore aérobie mésophile totale : < 10 UFC/g ; Levures et moisissures : absentes.",
          "Total Bacterial Count (TBC): < 10 CFU/g; Yeasts and moulds: absent.",
          "Totaal kiemgetal (TBC): < 10 KVE/g; Gisten en schimmels: afwezig."),
}
def shelf(it,fr,en,nl): return L(it,fr,en,nl)
def prod(folder,title,ean,typ,shelf_,pack,label,gmo,ingr,allg,stor,use,nut,chem=CHEM,micro=None):
    d={"folder":folder,"title":title,"general":{"ean":ean,"typology":typ,"shelf":shelf_,"packaging":pack,"labelling":label,"gmo":gmo},
       "ingredients":{"ingredients":ingr,"allergens":allg},"storage":{"instructions":stor,"method":use},"nutrition":nut,
       "characteristics":{"chemical":chem,"micro":micro}}
    return d
