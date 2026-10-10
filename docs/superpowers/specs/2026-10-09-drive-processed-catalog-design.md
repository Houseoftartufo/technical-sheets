# Catalogo Drive processato come fonte del sito

**Stato:** progetto approvato in chat; in attesa di revisione della specifica scritta  
**Data:** 09/10/2026

## Obiettivo

Caricare gli originali dei fornitori in «DA_ELABORARE». Dopo estrazione, validazione, traduzione e generazione, il sistema sposta l'originale in «ELABORATE». Quest'ultima cartella diventa la fonte del catalogo attivo: aggiunte, sostituzioni e rimozioni aggiornano il catalogo ufficiale su Drive e il sito Vercel di produzione.

Si continua a usare _BUILD/engine.py per HTML/PDF e _BUILD/build_index.py per l'indice. Le 27 schede storiche restano byte per byte intatte e protette.

## Cartelle e identità

Tutte le cartelle sono sorelle nella radice del Drive condiviso già configurata:

- **DA_ELABORARE**: coda di originali nuovi o sostitutivi. In caso di errore l'originale resta qui.
- **ELABORATE**: originali approvati e sorgenti attive. La loro presenza mantiene attivo il prodotto.
- **HOUSE_OF_TARTUFO_PREMIUM**: output ufficiali HTML/PDF nelle cartelle prodotto.
- **ARCHIVIO_ORIGINALI_27**: archivio legacy escluso dalle scansioni e dalle rimozioni.

L'ID Drive dell'originale, non il suo nome, collega il file al manifest e al prodotto. Sorgenti non identificabili univocamente o in collisione bloccano il job e richiedono revisione; niente output incompleti o ambigui.

## Aggiunta e modifica

1. Un workflow schedulato e avviabile manualmente legge PDF e Word supportati dalle sole cartelle DA_ELABORARE ed ELABORATE.
2. Confronta ID e impronta del file con un manifest autorevole conservato sul Drive condiviso; gli invariati non vengono rielaborati.
3. Estrae e valida i campi richiesti e crea i dati nel formato già usato da _BUILD, con traduzioni ITA, FR, ENG, NL e DE.
4. _BUILD/engine.py genera gli output. Si controllano conteggi, apertura e pagine dei PDF, indice, link e git diff --check.
5. Un assemblatore crea un bundle completo e temporaneo: sito statico versionato, schede dinamiche attive e indice aggiornato. Si verifica una preview Vercel.
6. Dopo l'aggiornamento di Vercel e della cartella prodotto su Drive, l'originale viene spostato da DA_ELABORARE a ELABORATE mantenendo lo stesso ID.
7. Un report Actions registra aggiunte, modifiche, rimozioni, controlli, pubblicazioni, errori e stato dello spostamento.

Una sostituzione aggiorna la scheda associata senza duplicati. Un errore di estrazione, validazione, generazione o preview lascia l'originale in DA_ELABORARE e non pubblica risultati parziali. Una copia byte-per-byte già presente in ELABORATE viene invece spostata lì e rinominata `ERRORE: DUPLICATO - …`: non genera una seconda scheda e viene ignorata nelle sincronizzazioni successive. Le collisioni con contenuto diverso restano in ingresso per revisione.

## Rimozione

La presenza in ELABORATE mantiene attivo il prodotto. Se una sorgente gestita viene rimossa da ELABORATE, il job toglie il prodotto dall'indice e dal bundle Vercel e sposta nel Cestino di Drive la sola cartella prodotto generata associata. Ripristinando l'originale e rimettendolo in ELABORATE, la sincronizzazione successiva lo ripubblica.

Solo ID sorgente e cartelle registrate nel manifest possono essere rimossi. L'assenza da DA_ELABORARE non significa rimozione; solo l'assenza da ELABORATE disattiva una sorgente già approvata. Le 27 cartelle storiche e i prodotti non gestiti sono esclusi.

## Pubblicazione, manifest e retry

I file generati non vengono committati su GitHub: un bundle completo viene pubblicato in produzione tramite Vercel CLI. GitHub Actions richiede VERCEL_TOKEN, VERCEL_ORG_ID e VERCEL_PROJECT_ID. Il manifest autorevole e idempotente risiede nella radice tecnica del catalogo Drive, fuori dalle cartelle prodotto; il report è conservato come artifact Actions. Le esecuzioni sono serializzate.

Il deploy Git di Vercel basato solo su main non contiene i prodotti dinamici. Quindi i deploy automatici Git che possono sovrascrivere il catalogo vanno disabilitati o instradati nello stesso workflow. Anche ogni aggiornamento del codice su main deve generare e pubblicare il bundle completo, composto da legacy statici e prodotti attivi su Drive.

Ogni passaggio è ripetibile: una nuova esecuzione riconcilia Drive, sito e manifest dopo un errore di rete senza duplicare output. La migrazione iniziale registra l'originale di Carpaccio in olio e i suoi file già esistenti senza riestrarli né rigenerarli inutilmente; non tocca i 27 legacy.

## Componenti coinvolti

- .github/workflows/sync-drive.yml: scansione, serializzazione, bundle e deploy completo.
- _BUILD/sync_drive.py e _BUILD/drive_sync_state.py: sorgenti, manifest, rimozioni e retry.
- _BUILD/engine.py e _BUILD/build_index.py: schede e indice nel layout attuale; l'indice accetta il catalogo legacy e i metadati dinamici e scrive nella directory di bundle indicata, senza cambiare il comportamento di build esistente.
- _BUILD/publish_drive.py: upsert e rimozione limitati ai prodotti gestiti.
- Nuovo assemblatore bundle; README e istruzioni per cartelle, credenziali, controlli e ripristino.

## Criteri di accettazione

- Una scheda valida passa da DA_ELABORARE a ELABORATE con ID conservato, e appare su Drive e sul sito in tutte le cinque lingue; una non valida resta in ingresso e dà un errore leggibile.
- Una sostituzione aggiorna prodotto, link e PDF senza duplicati o cambi di URL non necessari.
- Rimuovere da ELABORATE toglie il prodotto dal sito e mette nel Cestino solo la relativa cartella generata; il ripristino lo riattiva.
- Retry dopo errori tra deploy, pubblicazione Drive, spostamento o manifest converge senza perdita dell'originale o duplicati.
- Una sincronizzazione senza variazioni non rigenera prodotti e lascia i 27 legacy byte per byte identici.
- Ogni deploy da main o Drive include tutti i legacy e tutte le sorgenti gestite attive, e un deploy Git non può sovrascrivere il catalogo con un indice incompleto.
- I test verificano conteggi e pagine PDF, indice, link, preview e report.

## Fuori ambito

Aggiornare o cancellare i 27 originali storici; cambiare design o contenuti non coinvolti; salvare HTML/PDF generati nel repository; pubblicare dati incompleti.

