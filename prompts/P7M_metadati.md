# P7M — Metadati del libro

**Modello:** Gemini 4 Hydrogen · **Sessione:** nuova · **Parametri:** nessuno

## Prima di tutto
Leggi `CONVENZIONI.md` per intero e `stato/macro_scaletta.json` (titolo, capitoli, obiettivi). Se
`apparati/metadati.json` esiste gia' ed e' incompleto, completalo.

## Output: `apparati/metadati.json` (JSON valido)

```json
{
  "titolo": "...",
  "sottotitolo": "...",
  "descrizione": "120-180 parole che presentano il libro a studenti e docenti",
  "parole_chiave": ["C", "programmazione", "..."],
  "livello": "dal principiante assoluto all'autonomia in C",
  "requisiti_software": "un compilatore C con supporto allo standard C23 (per esempio GCC 14 o successivo, Clang 18 o successivo) e un editor di testo o un IDE a scelta"
}
```

`parole_chiave`: da 8 a 12. Descrivi solo cio' che c'e' nella macro-scaletta: non inventare caratteristiche.

## Non fare
Non modificare altri file.

## Messaggio finale
Formato di `CONVENZIONI.md` §7.
