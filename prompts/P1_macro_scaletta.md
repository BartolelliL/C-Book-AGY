# P1 — Macro-scaletta del libro

**Modello:** Gemini 4 Neon (ragionamento alto) · **Sessione:** nuova · **Parametri:** nessuno
(la critica indipendente della macro-scaletta la fa un altro modello con P1R)

## Istruzioni

## Prima di tutto
1. Leggi `CONVENZIONI.md` per intero.
2. Leggi `PROGRAMMA.md` (proposta dei capitoli) e `config.json` (limiti: numero di capitoli e di sotto-sezioni).
3. Se `stato/verifica_p1.json` esiste e contiene `errori` (rilancio dopo errori): modalita' correzione. Apri
   `stato/macro_scaletta.json`, correggi SOLO gli errori elencati e vai al "Controllo finale".

## Obiettivo
Produrre `stato/macro_scaletta.json`: il "contratto" dell'intero libro. Ogni errore qui si propaga a tutti i
capitoli, quindi lavora con cura. Non scrivere nessun altro file.

## Cosa deve contenere (JSON valido, nessun testo fuori dal JSON)

```json
{
  "titolo": "Imparare il C con gli esercizi",
  "destinatari": "una frase sui lettori",
  "capitoli": [
    {
      "n": 1,
      "titolo": "Il primo programma",
      "tipo": "teoria",
      "obiettivi": ["Compilare ed eseguire un programma C", "Spiegare la struttura di un programma", "Usare printf per stampare testo"],
      "argomenti": ["struttura di un programma", "printf", "errori del compilatore"],
      "prerequisiti": [],
      "sotto_sezioni": [
        {"id": "1.1", "titolo": "Dal sorgente all'eseguibile"},
        {"id": "1.2", "titolo": "La struttura di un programma"},
        {"id": "1.3", "titolo": "Stampare con printf"}
      ]
    }
  ],
  "registro": [
    {"nome": "printf", "categoria": "funzione", "capitolo": 1},
    {"nome": "stdio.h", "categoria": "header", "capitolo": 1},
    {"nome": "int", "categoria": "parola chiave", "capitolo": 1}
  ],
  "non_trattati": ["register", "stdbool.h", "threads.h"],
  "glossario": [
    {"termine": "variabile", "definizione": "una riga chiara", "capitolo": 2, "sinonimi_vietati": ["contenitore"]}
  ]
}
```

(L'esempio e' abbreviato: il tuo file deve essere completo.)

### Regole per i capitoli
- Il numero di capitoli sta nei limiti di `config.json` (`capitoli_min`-`capitoli_max`); segui ordine e traguardo di
  `PROGRAMMA.md` (compresa la tabella hash generica come concetto di riferimento) salvo motivi didattici. L'ULTIMO capitolo ha
  `"tipo": "progetto"`, tutti gli altri `"teoria"`.
- `n` consecutivo da 1. `prerequisiti` contiene solo numeri di capitoli PRECEDENTI.
- Almeno 3 `obiettivi` per capitolo, formulati come cose che il lettore sa fare (verbi: scrivere, spiegare, prevedere
  l'output di, correggere, scegliere...).
- Da 3 a 6 `sotto_sezioni` per capitolo (limiti in `config.json`; i capitoli piu' densi, come puntatori e memoria, ne hanno di piu'), con `id` esatti `N.1`, `N.2`, ... Ogni sotto-sezione tratta UN concetto e avra'
  un esercizio. Nel capitolo di progetto le prime sotto-sezioni preparano i pezzi del progetto e l'ULTIMA contiene il
  progetto completo (diviso in fasi).
- Il progetto usa SOLO concetti dei capitoli precedenti.

### Regole per il `registro` (il punto piu' importante)
Il registro elenca **ogni** elemento del linguaggio o della libreria standard che comparira' nel codice del libro, con il
capitolo in cui viene introdotto per la prima volta:
- `categoria` puo' essere solo: `parola chiave`, `header`, `funzione`, `tipo`, `costante`, `sintassi`, `concetto`.
- Nomi esatti: `printf`, `fgets`, `stdio.h` (header SENZA `<` `>`), `size_t`, `NULL`, `nullptr`, `for`, `struct`...
- Includi tutte le parole chiave del C23 che userai, tutte le funzioni (`printf`, `fgets`, `strlen`, `malloc`, ...),
  tutti gli header, i tipi (`size_t`, `FILE`...) e le costanti (`NULL`, `EOF`, `INT_MAX`, `stdin`...).
- Un elemento si introduce nel capitolo dove viene SPIEGATO, non dove compare per caso. Quando un esempio ha bisogno di
  qualcosa che non e' ancora stato spiegato, o sposti l'introduzione prima, o cambi l'ordine dei capitoli.
- Almeno `registro_min` elementi in totale (vedi `config.json`: con un corso fino all'autonomia sono parecchi: tutte le
  parole chiave, le funzioni, i tipi, le costanti e gli header che userai).
- Elementi che NON userai mai nel libro (es. `register`, `stdbool.h`, `threads.h`; `stdbool.h` perche' in C23 `bool` e' una
  parola chiave) vanno in `non_trattati`: i controlli automatici segnaleranno ogni uso.
- **Tutto cio' che `PROGRAMMA.md` richiede va nel registro, mai in `non_trattati`** (per esempio `goto`, `volatile`, `inline`,
  `restrict`, `extern`, `setjmp`/`longjmp`, `offsetof`, `_Generic`, `static_assert`, `errno`, funzioni variadiche). In
  `non_trattati` mettici solo cio' che il libro non usera' davvero (di solito poche voci).
- Rispetta le regole sul codice di `CONVENZIONI.md` §4 (per esempio, niente `scanf("%s")`; l'ordine di introduzione
  delle funzioni di input deve essere coerente con `PROGRAMMA.md`).

### Regole per il `glossario`
- Almeno `glossario_min` termini tecnici (vedi `config.json`): ogni termine nuovo che il lettore incontra (compilatore, variabile, tipo, operatore,
  puntatore, ...), con `definizione` di una riga, `capitolo` di introduzione, `sinonimi_vietati` (lista, anche vuota)
  di sinonimi o traduzioni che nel libro NON si devono usare (per evitare incoerenze come "indirizzatore" per
  "puntatore").
- Termini unici (nessun duplicato).
- Preferisci la terminologia italiana consolidata; il termine inglese tra parentesi sta nel testo del libro, non qui.

### Lingua
Scrivi TUTTI i testi del JSON (titoli, obiettivi, definizioni, termini del glossario) in italiano corretto con le lettere
accentate (è, é, à, ì, ò, ù): mai l'apostrofo al posto dell'accento (`perche'`, `visibilita'`) e mai termini senza accento
(`visibilita`, `complessita`). I termini del glossario sono quelli che finiranno nel libro e nell'indice analitico.

## Controllo finale (obbligatorio)
1. Rileggi il JSON: nessuna virgola finale, nessun commento.
2. Esegui `python3 scripts/libro.py controlla-macro`. Se segnala errori, correggili e riesegui (massimo 3 volte).
3. Non approvare nulla: l'approvazione e' dell'utente.

## Non fare
- Non scrivere capitoli, esercizi o codice. Non creare altri file. Non modificare file esistenti oltre al tuo output.

## Messaggio finale
Usa il formato di `CONVENZIONI.md` §7 e aggiungi: numero di capitoli, e le tre scelte didattiche piu' discutibili
che l'utente dovrebbe controllare con attenzione.
