# House of Tartufo - Schede Tecniche Prodotti

Schede tecniche professionali multilingue (ITA / FR / ENG / NL / DE) per 27 prodotti,
ricostruite dai testi originali italiani Sassone con traduzioni B2B e dati verbatim.

## Contenuto
- 27 cartelle prodotto, ciascuna con 5 PDF + 5 HTML (ITA, FR, ENG, NL, DE) = 135 schede per formato.
- index.html - indice navigabile con link a tutte le lingue.
- _BUILD/ - motore di generazione (engine.py), dati (blockA-E.json, p01/p02),
  riferimento valori nutrizionali e MAPPATURA.md (regole + correzioni applicate).

## Deploy su Vercel
- Framework Preset: Other
- Build Command: lasciare vuoto
- Output Directory: lasciare vuoto o `.`
- Install Command: lasciare vuoto

## Note
- Nuovo logo House of Tartufo in PNG trasparente, senza riquadro o sfondo; colori e struttura delle schede invariati.
- Valori nutrizionali trascritti verbatim dalle schede originali (ogni decimale).
- Correzioni allergeni/titoli vs originale: vedi _BUILD/MAPPATURA.md.
- Codice EAN: placeholder originale Sassone (80582 6513), da sostituire con EAN reali.

## Rigenerazione
- Un dataset, tutte le lingue: `python _BUILD/engine.py _BUILD/p01.json . 06/06/2026`
- Un dataset, solo tedesco: `python _BUILD/engine.py _BUILD/p01.json . 06/06/2026 DE`
- Per rigenerare l'intero catalogo, ripetere il comando per `p02.json` e `blockA.json`-`blockE.json`.
- Indice: `python _BUILD/build_index.py`
- I PDF sono generati con WeasyPrint; in assenza delle librerie native viene usato Chrome/Edge in modalità headless.

## Schede originali fornitori
- Cartella Drive sorgente: [SCHEDE ORIGINALI FORNITORI - DA ELABORARE](https://drive.google.com/drive/folders/1Y1qgl2rih8Ikbjf6ch4CgG5Qtwg6k6hS).
- Il workflow `.github/workflows/sync-drive.yml` legge PDF/DOCX, estrae i campi con OCR, traduce nelle cinque lingue e passa i dati a `_BUILD/engine.py`.
- Configurare i secret GitHub `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` e `OPENAI_API_KEY`, oltre alle variabili `DRIVE_SOURCE_FOLDER_ID` (cartella input) e `DRIVE_CATALOG_FOLDER_ID` (cartella catalogo ufficiale; `1vEyctBT3z9F5-hFM-DeTWEsjaY2I8drb`).
- Condividere la cartella sorgente con l'indirizzo email del service account indicato nel JSON GitHub.
- Un prodotto già presente viene pubblicato come `DUPLICATE_...` con evidenziazione blu nell'indice; i campi assenti restano vuoti.
- La sincronizzazione automatica avviene ogni 15 minuti e aggiorna `main` solo dopo validazione.
- Dopo la validazione il job carica/aggiorna in Drive le cartelle prodotto con tutti gli HTML/PDF generati; le rimozioni vengono spostate nel cestino Drive.

Aggiornato: 06/06/2026
