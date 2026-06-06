# MAPPATURA E REGOLE — House of Tartufo (macchina di generazione)

## Regole bloccate
1. Fonte autorevole = 27 PDF originali Sassone (radice cartella progetto).
2. Titoli fedeli al termine merceologico originale (Crema, Salsa, Burro/Condimento, Olio, Sale, Carpaccio...), tradotti correttamente nelle 4 lingue.
3. Valori nutrizionali VERBATIM, ogni decimale/millesimo, virgola IT/FR/NL, punto EN.
4. Allergeni: CORRETTI dove l'originale aveva errori copia-incolla (02 Anacardi e 11 Mandorle: "FRUTTA A GUSCIO" non "ARACHIDI").
5. Una sola lingua per file; sezioni pulite; design CSS invariato (logo HOT, colori truffle/oro).
6. Lingue: ITA, FR, ENG, NL.

## Correzioni applicate vs originale
- 12 Noci: titolo originale errato ("Arachidi/Peanuts") -> corretto "Noci al Tartufo".
- 02 Anacardi: allergene "ARACHIDI" -> "FRUTTA A GUSCIO (ANACARDI)".
- 11 Mandorle: allergene "ARACHIDI" -> "FRUTTA A GUSCIO (MANDORLE)".
- 15 Perle: formato originale non standard (g/l, no shelf life) -> gestito a parte.

## Output: HOUSE_OF_TARTUFO_PREMIUM/<NN_NOME>/<NN_NOME>_{ITA,FR,ENG,NL}.{html,pdf}
