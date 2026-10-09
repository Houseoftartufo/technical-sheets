# Design: ELABORATE come fonte autorevole del catalogo

## Obiettivo e vincoli

La cartella Drive `ELABORATE` deve contenere gli originali dei fornitori che governano le schede pubblicate. Aggiungere un originale avvia l'importazione con il motore esistente; rimuovere un originale rimuove dal catalogo la scheda associata dopo una sincronizzazione valida. Le 27 schede già pubblicate, i loro contenuti e l'archivio storico devono restare intatti durante la configurazione iniziale.

L'utente ha già copiato i 27 originali nell'attuale `ELABORATE`, lasciando intatto `ARCHIVIO_ORIGINALI_27`, e vi ha inserito anche il PDF del Carpaccio estivo in olio. La cartella contiene quindi 28 PDF: 27 corrispondenti ai prodotti esistenti e il prodotto 28. Il Carpaccio in olio resta distinto dal prodotto 06 in acqua.

## Stato osservato

- L'ID Drive della cartella attuale `ELABORATE` è `1RcuKuZrdGgQUOq-2j-Nr-tcdnGDsWhGX`.
- Gli originali storici sono ancora presenti in `ARCHIVIO_ORIGINALI_27`.
- Le cartelle prodotto numerate 01–27 sono già presenti nel catalogo e il prodotto 28 è già stato generato.
- Il manifest nel repository associa un solo file a `28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO`; non contiene le associazioni per i 27 originali appena copiati.
- Il flusso attuale cerca `ELABORATE` accanto alla cartella di ingresso. L'ultima esecuzione ha riportato un solo prodotto cambiato, non i 28 file attivi della cartella indicata sopra; il dato conferma che la cartella popolata non è quella letta dal workflow. L'esecuzione si è fermata prima del deploy e non ha finalizzato modifiche a Drive.
- `_BUILD/MAPPATURA.md` documenta correzioni rispetto ai PDF originali: nome del prodotto 12, allergeni dei prodotti 02 e 11 e una gestione specifica per il prodotto 15. La migrazione deve usare queste regole e non dedurre l'associazione dal solo nome del file.

## Architettura

1. Aggiungere una configurazione esplicita `DRIVE_PROCESSED_FOLDER_ID` e collegarla all'ID della cartella `ELABORATE` già popolata. L'ID non è una credenziale e va configurato come GitHub Actions variable. Il flusso non deve cercare o creare una cartella omonima parallela quando l'ID è configurato.
2. Mantenere la cartella d'ingresso separata. Gli originali vengono estratti, validati, tradotti e generati con `_BUILD/sync_drive.py`, `_BUILD/engine.py` e `_BUILD/build_index.py` come già previsto.
3. Usare il manifest Drive per associare ogni ID file stabile alla cartella prodotto numerata. La migrazione iniziale aggiunge le 27 associazioni mancanti e riallinea il record del prodotto 28 al file che si trova in `ELABORATE`; non rilancia estrazione, traduzione o generazione per i 27 prodotti già pubblicati.
4. Prima di applicare la migrazione, confrontare tutte le associazioni, il numero di originali e le cartelle catalogo. Una mappatura mancante, ambigua o in collisione blocca la sincronizzazione senza rimuovere prodotti.

## Identità, duplicati e nomi

- Il codice numerico e la cartella prodotto già presenti nel catalogo sono l'identità stabile. Il nome del file e il testo estratto sono evidenze di verifica, non l'unica chiave di associazione.
- La configurazione iniziale associa i 27 originali ai prodotti 01–27 usando le regole esistenti in `_BUILD/MAPPATURA.md` e i dati catalogo correnti. Il PDF 28 in `ELABORATE` è associato al prodotto in olio 28.
- Le copie identiche del PDF 28 presenti in altre cartelle d'ingresso sono riconosciute tramite impronta del contenuto. Non generano una seconda scheda e non vengono eliminate o spostate automaticamente; restano segnalate nel report finché non vengono riordinate.
- Ogni prodotto ha una sola sorgente attiva canonica in `ELABORATE` per questa versione. Una seconda scheda diversa che sembra riferirsi allo stesso prodotto viene segnalata e richiede classificazione, invece di sovrascrivere o creare una scheda duplicata.
- I file attivi sono rinominati secondo `NN_CARTELLA_PRODOTTO__NOME_ORIGINALE.ext`, per esempio `12_NOCI_AL_TARTUFO__Noci al Tartufo.pdf`. Il nome originale viene conservato nel manifest; il contenuto binario non viene modificato. L'impronta usata per rilevare modifiche deve ignorare il solo cambio di nome, così una rinomina non riavvia l'estrazione.

## Aggiunte e rimozioni

- Dopo l'importazione valida e il deploy previsto dal workflow, il sorgente viene spostato in `ELABORATE` e rinominato secondo la convenzione. La registrazione nel manifest usa il nome finale e l'identità del prodotto.
- L'elenco dei file supportati in `ELABORATE` determina i prodotti attivi. Quando un originale gestito non è più presente, il workflow rigenera l'indice senza quel prodotto e prepara la rimozione dei suoi output gestiti.
- Le rimozioni diventano effettive solo dopo test e deploy riusciti. In anteprima, in caso di errore di estrazione o di mapping ambiguo, Drive e sito ufficiale restano invariati.
- Sono rimovibili solo le cartelle prodotto registrate nel manifest come gestite dal sincronizzatore. Gli altri output e le cartelle storiche non vengono toccati.
- Il PDF originale nell'archivio storico non viene rinominato, spostato o cancellato dalla migrazione iniziale.

## Flusso di migrazione

1. Configurare `DRIVE_PROCESSED_FOLDER_ID` con l'ID della cartella attuale.
2. Verificare i 28 file, i 27 codici prodotto storici, il Carpaccio in olio 28 e l'assenza di collisioni o sorgenti mancanti.
3. Preparare un aggiornamento del manifest che colleghi i file alle cartelle prodotto già pubblicate e registri i nomi originali e canonici.
4. Eseguire un controllo in sola anteprima che dimostri zero rigenerazioni per i prodotti 01–27 e zero cambiamenti ai loro output.
5. Solo dopo il controllo, pubblicare la modifica del sincronizzatore tramite la pull request esistente e verificare la preview. La produzione continua a seguire il percorso approvato su `main`.

## Verifiche richieste

- La cartella configurata viene usata direttamente e non viene creata una cartella `ELABORATE` parallela.
- Il manifest iniziale contiene 28 associazioni valide; i 27 prodotti pubblicati conservano gli stessi file, hash e voci di indice.
- Il prodotto 28 rimane Carpaccio in olio e non collide con il prodotto 06 in acqua.
- Una rinomina senza modifica del contenuto non avvia una nuova estrazione.
- Un PDF nuovo crea una sola scheda con l'engine esistente; un file non riconoscibile o un conflitto blocca pubblicazione e finalizzazione Drive con un report utile.
- La rimozione di un file attivo produce una rimozione coordinata dal catalogo solo dopo una validazione e un deploy riusciti.
- Le prove di rimozione usano dati di test isolati e non cancellano gli output ufficiali esistenti.
- `git diff --check`, i test del sincronizzatore e il controllo delle 27 schede ufficiali passano prima della pull request.

## Fuori ambito

- Rigenerare o correggere contenuti delle 27 schede durante la sola migrazione delle associazioni.
- Eliminare o rinominare le copie dell'archivio storico.
- Combinare più schede di fornitori in un'unica scheda prodotto senza una regola esplicita di selezione.
- Pubblicare direttamente su `main` senza revisione della pull request e verifica della preview.
