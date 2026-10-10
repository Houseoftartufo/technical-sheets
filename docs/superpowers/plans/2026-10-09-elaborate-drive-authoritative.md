# Piano di implementazione: catalogo Drive ELABORATE autorevole

> **For Codex:** Implementare questo piano in ordine, in modalità nativa nel checkout corrente. Scrivere prima i test, eseguire il test mirato e poi l’intera suite pertinente. Non eseguire modifiche remote su Drive durante lo sviluppo; rinomina e spostamenti restano dietro la finalize post-deploy già prevista.

**Obiettivo:** adottare gli originali già caricati nella cartella ELABORATE come registro dei prodotti, associare in sicurezza i 28 documenti ai codici di catalogo, rinominare gli originali solo dopo deploy valido e rendere le successive aggiunte/modifiche/rimozioni idempotenti, senza alterare i 27 prodotti online esistenti durante la migrazione iniziale.

**Architettura:** il workflow riceve un ID esplicito `DRIVE_PROCESSED_FOLDER_ID`; il bootstrap associa con mapping verificato i 27 originali storici ai codici statici e crea il manifest senza estrarli né rigenerarli. Il ventottesimo originale, Carpaccio in olio, è un nuovo prodotto distinto dal Carpaccio in acqua e viene tradotto/generato una volta con il motore ufficiale. L’impronta segue i byte (MD5 Drive), non nome/data: la rinomina gestionale non provoca reimportazione. Il bundle conserva dal repository i prodotti ufficiali ancora attivi; le rimozioni in ELABORATE escludono il prodotto statico dal bundle e dall’indice. I prodotti nuovi o modificati usano `_BUILD/engine.py` e `_BUILD/build_index.py`. La finalize post-produzione aggiorna manifest e nomi.

**Tecnologie:** Python 3, GitHub Actions, Google Drive API, JSON, suite `unittest` esistente.

## Vincoli globali

- Nessun PDF/HTML esistente dei 27 prodotti può cambiare durante il bootstrap; registrare gli SHA-256 prima e confrontarli dopo.
- Nessuna chiamata di scrittura a Google Drive durante sviluppo, test o deploy preview. Rinomine, spostamenti e rimozioni sono ammesse solo nella finalize già subordinata al successo della pubblicazione ufficiale.
- Non eliminare gli originali d’archivio in `ARCHIVIO_ORIGINALI_27`; non toccare duplicati fuori dalle due cartelle configurate.
- `ELABORATE` è la fonte autorevole. Un documento ambiguo, incompleto, duplicato o non mappato blocca il piano prima di qualsiasi pubblicazione.
- Non modificare il motore PDF o il layout. Nessun output gestito può sovrapporsi silenziosamente a una scheda statica.
- Conservare cambi preesistenti e non stage/commit di file `work/`.

## Punti di revisione

- Mapping iniziale: esattamente 28 nomi sorgente attesi; i 27 originali storici sono associati uno a uno ai codici statici, Carpaccio in olio al nuovo codice 28; nessun mapping euristico.
- Bootstrap: niente estrazione o rigenerazione iniziale dei 27 prodotti statici. Il prodotto 28 viene estratto e generato una volta, con validazione completa.
- Bundle: i 27 prodotti ufficiali attivi vengono presi byte per byte dal repository, senza sovrascriverli con vecchi output Drive. Una fonte rimossa dal manifest esclude la relativa cartella statica dal bundle e dall’indice.
- Nuove revisioni di un prodotto esistente: overlay consentito solo quando il piano include un output generato valido; il prodotto resta una sola card nell’indice.
- Fonte rimossa: eliminazione dal catalogo solo dopo build, smoke test e deploy produzione riusciti; manifest scritto per ultimo.
- Identificativo ELABORATE fornito: `1RcuKuZrdGgQUOq-2j-Nr-tcdnGDsWhGX`. Usare variabile GitHub non sensibile `DRIVE_PROCESSED_FOLDER_ID`, senza creare cartelle omonime automatiche.
- Verificare che token Vercel non fallisca; il log precedente indicava `User not found (404)` e non va dichiarato risolto senza prova.

## Attività

### 1. Impronte stabili e metadati di provenienza

**File:** `_BUILD/drive_sync_state.py`, `tests/test_drive_sync_state.py`.

- [x] Aggiungere test che una modifica a `name` o `modifiedTime` con MD5 invariato non cambia l’impronta, mentre MD5/size/MIME diversi la cambiano.
- [x] Aggiungere test di manifest per conservare nome originale e nome gestionale canonico separatamente.
- [x] Implementare impronta content-based, includendo fallback prudente per metadati senza MD5 (scaricare/hashare contenuto nel flusso Drive prima di classificare unchanged).
- [x] Estendere le entry manifest senza rompere il caricamento dei manifest v1/v2.
- [x] Eseguire `python -m unittest tests.test_drive_sync_state -v`.

### 2. Mapping deterministico e bootstrap dei 28 originali

**File:** `_BUILD/drive_baseline_mapping.json` (nuovo), `_BUILD/drive_bootstrap.py` (nuovo), `tests/test_drive_bootstrap.py` (nuovo), `_BUILD/sync_drive.py`.

- [x] Scrivere test per 28 fonti attese, cartelle univoche, documento mancante, filename duplicato, documento inatteso e cartella non presente nel catalogo.
- [x] Inserire il mapping esplicito dei 27 originali corrispondenti ai codici ufficiali più Carpaccio in olio come nuovo prodotto `28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO`.
- [x] Creare bootstrap puro che registra 27 fonti statiche senza estrazione AI né override e segnala Carpaccio in olio come nuova fonte da elaborare; usare i titoli statici ITA/FR/ENG/NL/DE già presenti.
- [x] Quando non esiste manifest Drive, richiedere corrispondenza esatta del mapping e bloccare in presenza di ambiguità invece di inferire dall’AI. (Implementato; mapping con 28 originali verificati.)
- [x] Produrre un piano di rinomina canonico `CODICE__nome-originale.ext`, mantenendo il nome originale nel manifest.
- [x] Eseguire `python -m unittest tests.test_drive_bootstrap tests.test_sync_drive -v`.

### 3. ID esplicito, duplicati e finalize idempotente

**File:** `_BUILD/sync_drive.py`, `_BUILD/publish_drive.py`, `_BUILD/finalize_drive_sync.py`, `tests/test_sync_drive.py`, `tests/test_publish_drive.py`.

- [x] Testare che `DRIVE_PROCESSED_FOLDER_ID` venga validato e usato direttamente, senza creare cartelle sorelle; ID mancante/non-folder deve fallire in modo esplicito.
- [x] Archiviare una copia intake identica già presente in ELABORATE con prefisso `ERRORE: DUPLICATO -`, senza reimportare la scheda; ignorare il duplicato archiviato nelle sincronizzazioni successive e registrarlo nel report.
- [x] Registrare nel piano le rinomine sorgente e i cambiamenti da finalizzare; nessuna rinomina nel `prepare`.
- [x] Applicare la rinomina canonica e l’eventuale trasferimento solo in finalize dopo deploy produzione; operazione idempotente, controllo collisioni prima di mutare Drive e manifest scritto per ultimo.
- [x] In caso di errore durante finalize, conservare il report diagnostico senza fingere che il manifest sia aggiornato.
- [x] Eseguire `python -m unittest tests.test_sync_drive tests.test_publish_drive -v`.

### 4. Bundle iniziale senza alterare i 27 prodotti online

**File:** `_BUILD/build_site_bundle.py`, `tests/test_build_site_bundle.py`, eventuale piccolo adattamento `_BUILD/build_index.py` e `tests/test_build_index.py` solo se necessario.

- [x] Testare bootstrap gestito per prodotti statici 01–27: confronto completo dei 10 file per prodotto con Drive e riuso byte-identico degli output repository; nessun duplicato di cartella/card.
- [x] Testare che i prodotti statici attivi vengano copiati byte per byte dal repository e quelli rimossi non compaiano più, senza richiedere la presenza di vecchi PDF nel Drive catalog.
- [x] Testare prodotto 28 dinamico: collegamenti ITA/FR/ENG/NL/DE validi e una sola card.
- [x] Testare un prodotto statico realmente rigenerato: l’output generato può sostituire la copia statica nel bundle soltanto per quel prodotto, senza duplicare la card; gli altri prodotti attivi restano identici.
- [x] Eseguire `python -m unittest tests.test_build_site_bundle tests.test_build_index -v`.

### 5. Workflow, report e istruzioni operative

**File:** `.github/workflows/sync-drive.yml`, `_BUILD/sync_drive.py`, README e documentazione di mapping.

- [x] Passare `vars.DRIVE_PROCESSED_FOLDER_ID` sia al prepare sia alla finalize e impedire creazione implicita di una seconda `ELABORATE`.
- [x] Verificare il flusso manifest-only del bootstrap: salta il generatore quando non ci sono prodotti da tradurre, ma costruisce, controlla e distribuisce il bundle di anteprima; finalize resta limitata alla produzione riuscita.
- [x] Rendere il report leggibile e includere nomi associati, rinomine previste/eseguite, duplicati, aggiunti/modificati/rimossi, errori e URL deploy.
- [x] Documentare mapping iniziale, variabili/secrets, convenzione nome e flusso additions/edits/removals.
- [x] Aggiungere/aggiornare test di configurazione workflow per tutte le variabili richieste e la guardia `main` + opt-in produzione.
- [x] Eseguire `python -m unittest discover -s tests -v`, `git diff --check` e validazione YAML.

### 6. Verifiche, PR e attivazione controllata

- [x] Prima del bootstrap, salvare SHA-256 dei 270 PDF/HTML statici esistenti (27×5×2) e conservarli nel report locale di lavoro, non committare file temporanei. (Verificati: 270/270 invariati.)
- [x] Eseguire prove simulate per 28 fonti, nuova fonte, modifica, duplicato, documento incompleto e rimozione; nessuna mutazione Drive nei test.
- [x] Dopo bundle di migrazione simulato, richiedere uguaglianza SHA-256 per i 270 file e 28 schede uniche nell’indice.
- [ ] Pubblicare branch/PR per revisione e attendere CI/preview verificati prima di qualunque merge; il token Vercel non valido resta un errore operativo da riportare, non bypassare.
- [ ] Dopo merge/produzione riuscita, la workflow finalize rinomina i 28 originali e aggiorna manifest. Verificare il log e i nomi in Drive prima di dichiarare attivo il flusso.

## Revisione del piano

- Il mapping esatto e l’errore su contenuti statici divergenti evitano associazioni errate e preservano il sito ufficiale.
- Le scritture Drive sono separate dal piano di prepare e restano dopo il deploy produzione.
- Le integrazioni rispettano il motore e l’indice già in uso.
- Il piano richiede una variabile GitHub pubblica con l’ID della cartella ELABORATE; non inserisce credenziali nel repository.
- Nessun nuovo servizio di storage o motore PDF.
