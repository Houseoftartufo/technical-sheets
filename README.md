# House of Tartufo - Schede Tecniche Prodotti

Catalogo multilingue House of Tartufo, con schede generate dal motore ufficiale `_BUILD/engine.py` e indice creato da `_BUILD/build_index.py`.

## Caricamento nuove schede fornitori

1. Carica il PDF, DOC o DOCX originale nella cartella Drive **DA ELABORARE**.
2. Il workflow GitHub Actions la controlla ogni 15 minuti. **Run workflow** avvia un collaudo preview-only per impostazione predefinita; da `main` puoi scegliere esplicitamente `publish_to_production` dopo aver controllato la preview.
3. Il job estrae e valida i dati, crea le cinque lingue e genera HTML/PDF usando lo stesso motore e lo stesso layout del catalogo. Fibre, caratteristiche chimiche e microbiologiche sono incluse solo se presenti nella scheda originale.
4. Pubblica prima una preview Vercel e verifica l'indice e ogni PDF attivo; poi pubblica lo stesso bundle sul sito ufficiale.
5. Solo dopo il deploy ufficiale riuscito sposta il file originale, mantenendo il suo ID, da **DA ELABORARE** a **ELABORATE**. I collaudi preview-only non spostano né modificano file Drive. Le schede generate e i PDF restano nel Drive catalogo, nelle cartelle prodotto.
6. I dati obbligatori mancanti o ambigui, le collisioni e i formati non supportati bloccano il job; il file resta nella cartella d'ingresso. Fibre e caratteristiche chimiche/microbiologiche mancanti vengono omesse, mai inventate o copiate da un altro prodotto. Il report è disponibile come artifact del run.

Per aggiornare un prodotto sostituisci il documento sorgente già in **ELABORATE** mantenendolo nella cartella. Per rimuovere un prodotto gestito, elimina la sua scheda da **ELABORATE**: solo la cartella prodotto registrata nel manifest viene spostata nel cestino Drive. Le cartelle storiche e non gestite sono escluse dalle rimozioni.

## Configurazione GitHub

In **Settings → Secrets and variables → Actions** configura:

**Secrets**
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON`: JSON completo del service account.
- `OPENAI_API_KEY`: chiave API usata per estrazione e traduzione.
- `VERCEL_TOKEN`: token Vercel con accesso al progetto catalogo.
- `GOOGLE_DRIVE_IMPERSONATED_USER`: opzionale, solo per delega Workspace in My Drive.

**Variables**
- `DRIVE_SOURCE_FOLDER_ID`: ID della cartella **DA ELABORARE**.
- `DRIVE_CATALOG_FOLDER_ID`: ID della cartella **HOUSE_OF_TARTUFO_PREMIUM** sul Drive condiviso.
- `VERCEL_ORG_ID`: ID dell'organizzazione Vercel.
- `VERCEL_PROJECT_ID`: ID del progetto Vercel collegato al dominio ufficiale.

Condividi le cartelle Drive pertinenti con l'indirizzo service account. Il catalogo ufficiale e la cartella di input devono essere scrivibili; la cartella **ELABORATE** viene individuata o creata come sorella di **DA ELABORARE**.

## Evitare deploy Git Vercel concorrenti

Il workflow pubblica il bundle completo attraverso Vercel CLI per mantenere online insieme le 27 schede storiche e i prodotti gestiti da Drive. In Vercel apri **Project → Settings → Build and Deployment → Ignored Build Step** e imposta `exit 0` per saltare i deploy avviati dai push Git. Il deploy ufficiale viene avviato dal workflow con Vercel CLI, non dai commit Git. Verifica una preview e un deploy CLI prima di affidarti alla sincronizzazione automatica; non disconnettere il repository.

## Integrità dei contenuti

- Codici lingua: ITA, FR, ENG, NL, DE.
- Cartelle e URL dei prodotti esistenti non vengono rinominati o rigenerati dal sync.
- I 27 prodotti storici vengono copiati byte per byte nel bundle.
- EAN sconosciuti non vengono inventati; campi tecnici mancanti bloccano la pubblicazione.
- Carpaccio di tartufo estivo in olio è il prodotto 28, distinto dal carpaccio in acqua prodotto 06.
- Manifest e dati temporanei restano in Drive e nell'ambiente effimero di GitHub Actions, mai nei commit del catalogo.

## Generazione manuale locale

- Tutte le lingue: `python _BUILD/engine.py _BUILD/p01.json . 06/06/2026`
- Solo tedesco: `python _BUILD/engine.py _BUILD/p01.json . 06/06/2026 DE`
- Indice statico: `python _BUILD/build_index.py`
- Verifiche: `python -m unittest discover -s tests -v` e `node --test tests/search.test.js`
