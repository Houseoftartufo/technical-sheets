# House of Tartufo - Schede Tecniche Prodotti

Catalogo multilingue House of Tartufo, con schede generate dal motore ufficiale `_BUILD/engine.py` e indice creato da `_BUILD/build_index.py`.

## Caricamento nuove schede fornitori

1. Aggiungi il PDF, DOC o DOCX originale del fornitore direttamente nella cartella Drive **ELABORATE**. Questa è la lista autorevole dei prodotti pubblicati.
2. GitHub Actions controlla la cartella ogni 15 minuti. Puoi anche avviare **Run workflow**: la preview è la modalità predefinita e solo da `main` puoi scegliere esplicitamente la pubblicazione ufficiale.
3. Il job estrae e valida i dati, crea le cinque lingue e genera HTML/PDF con `_BUILD/engine.py` e lo stesso layout del catalogo. Le informazioni mancanti non vengono inventate.
4. Dopo preview e controlli, il workflow pubblica il bundle completo. Solo dopo il deploy ufficiale riuscito rinomina il documento in `CODICE_PRODOTTO__nome-originale.pdf` (o mantiene l'estensione Word), così resta ordinato in **ELABORATE**. Preview e run falliti non modificano Drive.

Per aggiornare un prodotto, sostituisci il suo originale in **ELABORATE** mantenendo il file. Per rimuoverlo, elimina l'originale da **ELABORATE**: dopo un deploy riuscito la scheda sparisce da indice e sito, e la cartella di output gestita viene spostata nel cestino Drive. I 27 output ufficiali iniziali restano byte per byte invariati al bootstrap. I documenti incompleti, ambigui, non mappati o duplicati bloccano/si segnalano senza pubblicare una scheda incompleta. Il report del job è disponibile come artifact GitHub Actions.

## Configurazione GitHub

In **Settings → Secrets and variables → Actions** configura:

**Secrets**
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON`: JSON completo del service account.
- `OPENAI_API_KEY`: chiave API usata per estrazione e traduzione.
- `VERCEL_TOKEN`: token Vercel con accesso al progetto catalogo.
- `GOOGLE_DRIVE_IMPERSONATED_USER`: opzionale, solo per delega Workspace in My Drive.

**Variables**
- `DRIVE_SOURCE_FOLDER_ID`: ID della cartella di ingresso facoltativa **DA ELABORARE**; i nuovi originali possono essere messi direttamente in ELABORATE.
- `DRIVE_PROCESSED_FOLDER_ID`: ID della cartella autorevole **ELABORATE** (`1RcuKuZrdGgQUOq-2j-Nr-tcdnGDsWhGX`).
- `DRIVE_CATALOG_FOLDER_ID`: ID della cartella **HOUSE_OF_TARTUFO_PREMIUM** sul Drive condiviso.
- `VERCEL_ORG_ID`: ID dell'organizzazione Vercel.
- `VERCEL_PROJECT_ID`: ID del progetto Vercel collegato al dominio ufficiale.

Condividi con l'indirizzo service account le cartelle **ELABORATE**, di ingresso (se usata) e del catalogo. La variabile `DRIVE_PROCESSED_FOLDER_ID` deve puntare alla cartella ELABORATE già esistente: il workflow non ne crea una seconda.

## Evitare deploy Git Vercel concorrenti

Il workflow pubblica il bundle completo attraverso Vercel CLI per mantenere online i prodotti ancora presenti in ELABORATE. I 27 prodotti storici vengono presi dal repository e conservati byte per byte al bootstrap. Si collega in modo non interattivo all'ID progetto e team configurati nelle variabili GitHub. In Vercel apri **Project → Settings → Build and Deployment → Ignored Build Step** e imposta `exit 0` per saltare i deploy avviati dai push Git. Il deploy ufficiale viene avviato dal workflow con Vercel CLI, non dai commit Git. Verifica una preview e un deploy CLI prima di affidarti alla sincronizzazione automatica; non disconnettere il repository.

## Integrità dei contenuti

- Codici lingua: ITA, FR, ENG, NL, DE.
- Le cartelle e gli URL delle schede storiche non vengono rinominati.
- I 27 prodotti storici vengono copiati byte per byte dal repository nel bundle iniziale; solo una modifica esplicita del relativo originale ne genera una nuova versione.
- EAN sconosciuti non vengono inventati; campi tecnici mancanti bloccano la pubblicazione.
- Carpaccio di tartufo estivo in olio è il prodotto 28, distinto dal carpaccio in acqua prodotto 06.
- Manifest e dati temporanei restano in Drive e nell'ambiente effimero di GitHub Actions, mai nei commit del catalogo.

## Generazione manuale locale

- Tutte le lingue: `python _BUILD/engine.py _BUILD/p01.json . 06/06/2026`
- Solo tedesco: `python _BUILD/engine.py _BUILD/p01.json . 06/06/2026 DE`
- Indice statico: `python _BUILD/build_index.py`
- Verifiche: `python -m unittest discover -s tests -v` e `node --test tests/search.test.js`
