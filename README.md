# House of Tartufo - Schede Tecniche Prodotti

Catalogo multilingue House of Tartufo, con schede generate dal motore ufficiale `_BUILD/engine.py` e indice creato da `_BUILD/build_index.py`.

## Caricamento nuove schede fornitori

1. Aggiungi il PDF, DOC o DOCX originale del fornitore in **DA_ELABORARE**. Dopo estrazione, validazione, traduzione, anteprima e pubblicazione, il workflow lo sposta in **ELABORATE**, la lista autorevole dei prodotti pubblicati. È possibile aggiungere direttamente in ELABORATE solo un originale già approvato.
2. Dopo la configurazione del webhook Cloudflare, le modifiche su Drive avviano la sincronizzazione in pochi secondi; gli eventi vicini vengono raggruppati. GitHub Actions continua anche a controllare la cartella ogni 5 minuti come recupero automatico. Puoi avviare **Run workflow** manualmente: la preview è la modalità predefinita.
3. Il job estrae e valida i dati, crea le cinque lingue e genera HTML/PDF con `_BUILD/engine.py` e lo stesso layout del catalogo. Le informazioni mancanti non vengono inventate.
4. Dopo preview e controlli, il workflow pubblica il bundle completo. Solo dopo il deploy ufficiale riuscito rinomina il documento in `CODICE_PRODOTTO__nome-originale.pdf` (o mantiene l'estensione Word), così resta ordinato in **ELABORATE**. Preview e run falliti non modificano Drive.

Per aggiornare un prodotto, sostituisci il suo originale in **ELABORATE** mantenendo il file. Per rimuoverlo, elimina l'originale da **ELABORATE**: dopo un deploy riuscito la scheda sparisce da indice e sito, e la cartella di output gestita viene spostata nel cestino Drive. I 27 output ufficiali iniziali restano byte per byte invariati al bootstrap. Un duplicato identico viene archiviato in **ELABORATE** con nome `ERRORE: DUPLICATO - …`, senza rigenerare la scheda; i file incompleti, ambigui, non mappati o diversi ma in collisione restano in ingresso e bloccano la pubblicazione per revisione. Il report del job è disponibile come artifact GitHub Actions.

## Configurazione GitHub

In **Settings → Secrets and variables → Actions** configura:

**Secrets**
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON`: JSON completo del service account.
- `OPENAI_API_KEY`: chiave API usata per estrazione e traduzione.
- `GOOGLE_DRIVE_IMPERSONATED_USER`: opzionale, solo per delega Workspace in My Drive.
- `CLOUDFLARE_API_TOKEN`: token Cloudflare con permesso **Workers Edit**, limitato all'account usato per il Worker.
- `DRIVE_DISPATCH_TOKEN`: token fine-grained limitato a questa repository con il solo permesso **Actions: write**; il workflow lo installa nel Worker con il binding interno `GITHUB_DISPATCH_TOKEN`.
- `DRIVE_WEBHOOK_TOKEN`: valore casuale di almeno 32 byte, condiviso solo tra il canale Drive e il Worker; viene caricato sul Worker dal workflow di deploy.

**Variables**
- `DRIVE_SOURCE_FOLDER_ID`: ID della cartella di ingresso facoltativa **DA ELABORARE**; i nuovi originali possono essere messi direttamente in ELABORATE.
- `DRIVE_PROCESSED_FOLDER_ID`: ID della cartella autorevole **ELABORATE** (`1RcuKuZrdGgQUOq-2j-Nr-tcdnGDsWhGX`).
- `DRIVE_CATALOG_FOLDER_ID`: ID della cartella **HOUSE_OF_TARTUFO_PREMIUM** sul Drive condiviso.
- `CLOUDFLARE_ACCOUNT_ID`: ID dell'account Cloudflare che ospita il Worker.
- `DRIVE_WEBHOOK_URL`: viene salvato automaticamente dopo che il deploy del Worker supera il controllo HTTPS `/health`.
- `DRIVE_WATCH_STATE`: stato del canale Drive, gestito e rinnovato automaticamente dal workflow.

Condividi con l'indirizzo service account le cartelle **ELABORATE**, di ingresso (se usata) e del catalogo. La variabile `DRIVE_PROCESSED_FOLDER_ID` deve puntare alla cartella ELABORATE già esistente: il workflow non ne crea una seconda.

## Attivazione immediata Drive con Cloudflare

Il workflow `Deploy Drive webhook` crea un endpoint HTTPS Cloudflare Worker. Un Durable Object raggruppa notifiche ravvicinate e ritenta il dispatch se GitHub non è momentaneamente disponibile. Il Worker riceve solo gli header di notifica; non accede ai documenti né alle credenziali Google/OpenAI. La sincronizzazione continua a confrontare lo stato reale del Drive e passa sempre dal motore e dai controlli esistenti.

Per attivarlo una volta sola:

1. In GitHub aggiungi i tre secret Cloudflare/GitHub elencati sopra e la variabile `CLOUDFLARE_ACCOUNT_ID`.
2. Crea `DRIVE_WEBHOOK_TOKEN` localmente (per esempio con `python -c "import secrets; print(secrets.token_urlsafe(48))"`) e inseriscilo direttamente come secret GitHub. Non inviarlo in chat né inserirlo nei file del repository.
3. Avvia **Actions → Deploy Drive webhook → Run workflow** su `main`. Il workflow installa i due secret nel Worker, verifica il suo endpoint e salva `DRIVE_WEBHOOK_URL`.
4. Al successivo controllo automatico (entro 5 minuti) il workflow registra il canale Google Drive e salva `DRIVE_WATCH_STATE`. Da quel momento gli upload e le rimozioni generano l'avvio automatico; il polling rimane attivo come rete di sicurezza.

Google fa scadere i canali `changes` entro sette giorni: il workflow li rinnova un giorno prima della scadenza, senza richiedere interventi periodici. Il report di ogni sincronizzazione indica lo stato del canale. Se mancano i secret, il deploy automatico viene saltato in modo visibile e il polling continua.

Il token fine-grained GitHub può avere una data di scadenza: prima che scada, rinnovalo e aggiorna il secret GitHub `DRIVE_DISPATCH_TOKEN`. Il workflow di deploy successivo aggiornerà il binding `GITHUB_DISPATCH_TOKEN` sul Worker.

## Pubblicazione e anteprima

La repo è già collegata a Vercel tramite GitHub. Il workflow crea un branch temporaneo, attende che Vercel completi la preview, controlla il bundle e solo dopo aggiorna `main`; Vercel pubblica quindi il nuovo catalogo sul dominio ufficiale. Una esecuzione manuale resta in preview per impostazione predefinita. Il job verifica che indice e PDF siano effettivamente visibili sul sito ufficiale prima di rinominare gli originali o aggiornare il manifest Drive. Non servono Vercel CLI, token, permessi GitHub aggiuntivi o modifiche a **Ignored Build Step**. Mantieni attiva l'integrazione GitHub già collegata al progetto Vercel.

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
