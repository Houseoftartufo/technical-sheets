# Google Drive push tramite Cloudflare

## Obiettivo

Quando un fornitore aggiunge, modifica o rimuove un file nel Drive condiviso del catalogo, avviare automaticamente la sincronizzazione GitHub esistente. Il workflow `_BUILD/sync_drive.py` resta l'autorità per l'estrazione e la riconciliazione; `_BUILD/engine.py`, l'anteprima Vercel e i controlli prima della pubblicazione restano invariati. Il polling GitHub ogni cinque minuti rimane come recupero per notifiche mancate.

## Disegno

Google Drive `changes.watch` osserva il Drive condiviso che contiene `DA_ELABORARE` ed `ELABORATE`. Il canale invia notifiche a un Cloudflare Worker pubblico HTTPS. Il Worker convalida un token casuale nel header `X-Goog-Channel-Token` e accoda l'evento a un Durable Object SQLite che raggruppa gli eventi vicini; il Durable Object avvia `workflow_dispatch` su `main` passando `publish_to_production=true` e ritenta in caso di errore. Nessuno dei due riceve, scarica o conserva documenti.

La sincronizzazione esistente scansiona le cartelle autorevoli, confronta i contenuti e mantiene idempotenti le modifiche. Le notifiche Drive non contengono il dettaglio dei file e possono essere duplicate o aggregate: il workflow continuerà a ricavare lo stato reale interrogando Drive. Il workflow aggiorna il canale prima della scadenza, usando `DRIVE_WATCH_STATE` come variabile di repository; il token del webhook viene mantenuto identico tra i canali durante la rotazione. L'intervallo di rinnovo è un giorno prima della scadenza richiesta a sei giorni, sotto il limite documentato di sette giorni per i cambiamenti.

## Sicurezza

- Cloudflare Worker conserva come secret `DRIVE_WEBHOOK_TOKEN` e `GITHUB_DISPATCH_TOKEN`.
- Il Durable Object usa storage SQLite per raggruppare le notifiche per 20 secondi e conservare i retry; non archivia file o dati prodotto.
- `DRIVE_WEBHOOK_TOKEN` è generato casualmente, verificato in tempo costante e non compare nei log o nel repository.
- `GITHUB_DISPATCH_TOKEN` è un token fine-grained limitato al repository `Houseoftartufo/technical-sheets` con il solo permesso Actions: write.
- `CLOUDFLARE_API_TOKEN` è un secret GitHub Actions limitato al singolo account Cloudflare e ai permessi necessari per deployare il Worker.
- Le credenziali Google e OpenAI restano esclusivamente nei GitHub Secrets esistenti; Cloudflare non riceve accesso a Drive.
- Le richieste non valide vengono respinte senza dispatch. Il Worker risponde con errore temporaneo se GitHub non accetta il dispatch, così Google può ritentare; il polling periodico recupera comunque l'evento.
- Il Worker invia solo l'evento di avvio e non contiene contenuti o metadati dei prodotti.

## Rinnovo e recupero

Al primo run dopo aver configurato `DRIVE_WEBHOOK_URL` e `DRIVE_WEBHOOK_TOKEN`, il workflow ottiene il `driveId` dalla cartella di ingresso, recupera un token di pagina condiviso e crea un canale `changes.watch`. Il workflow salva ID, resource ID e scadenza in una singola variabile GitHub. Durante il rinnovo crea e salva il nuovo canale prima di fermare il precedente; se lo stato non si aggiorna, il vecchio canale resta attivo fino alla scadenza naturale. Il cron ogni cinque minuti rimane attivo come fallback.

## Configurazione una tantum

GitHub repository secret `CLOUDFLARE_API_TOKEN` (permesso Cloudflare Workers Edit), repository variable `CLOUDFLARE_ACCOUNT_ID`, GitHub repository secret `GITHUB_DISPATCH_TOKEN` (Actions: write, repository-only), e un `DRIVE_WEBHOOK_TOKEN` casuale creato localmente e salvato direttamente come secret GitHub. Il workflow installa quest'ultimo e `GITHUB_DISPATCH_TOKEN` sul Worker, verifica `/health` e salva `DRIVE_WEBHOOK_URL`. Il canale viene attivato dal successivo run schedulato o manuale. `DRIVE_WATCH_STATE` è gestito dal workflow e non va inserito a mano.

## Criteri di accettazione

| Requisito | Evidenza attesa |
|---|---|
| Upload produce un evento di attivazione | Test Worker, debounce e dispatch GitHub verificato con API response 204 |
| Richiesta senza token o con token errato non avvia job | Test HTTP 401/403 e nessuna chiamata a GitHub |
| Evento `sync` iniziale non avvia una pubblicazione | Test HTTP 204 senza dispatch |
| Canale si crea sul Drive condiviso corretto | Test API mock con `driveId` derivato dalla cartella di ingresso |
| Canale viene rinnovato prima della scadenza | Test che verifica nessun rinnovo oltre soglia e rinnovo sotto 24 ore |
| Errore di rinnovo o dispatch non perde il polling | Workflow cron resta ogni cinque minuti e report diagnostico |
| Catalogo pubblico e prodotti esistenti restano intatti | Nessun cambiamento al generatore; invarianti suite esistente e nessun PDF rigenerato in sync senza modifiche |
| Deploy Cloudflare automatizzato | Workflow deploy condizionato ai secrets e URL Worker registrato come repository variable |

## Limiti operativi

Cloudflare non è collegato in questo ambiente e il repository non ha ancora un Cloudflare API token né un GitHub token fine-grained Actions: write. La parte software può essere implementata e testata qui; il canale non può ricevere eventi reali finché quei due accessi non sono creati nei rispettivi secret. Nessun valore segreto va inviato in chat.
