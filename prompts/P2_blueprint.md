# P2 — Blueprint tecnico-pedagogico dei capitoli

**Modello:** Gemini 4 Neon (ragionamento alto) · **Sessione:** nuova · **Parametri:** `CAPITOLI=lista` (es. `1-2`)

NN = N a due cifre (es. 03). N e' il capitolo in corso.

**Lavoro sui capitoli:** se `CAPITOLI` contiene piu' capitoli, lavorali UNO ALLA VOLTA nell'ordine: finisci e controlla un capitolo prima di passare al successivo e non rileggere i capitoli gia' chiusi. Lavori da solo: non delegare ad altri agenti.

Alla fine, nel messaggio finale, segnala gli elementi che avresti voluto usare ma non sono nel registro (decide l'utente).

## Istruzioni (per ogni capitolo N)

## Prima di tutto
1. Leggi `CONVENZIONI.md` per intero.
2. Leggi `stato/macro_scaletta.json`: la voce del capitolo N, il `registro`, il `glossario`, `non_trattati`.
3. Se `N > 1` leggi anche i blueprint dei capitoli precedenti gia' esistenti (`stato/blueprint/cap*.json`) per non
   ripetere concetti ed esercizi.
4. Se `stato/verifica_bp_capNN.json` esiste e contiene `errori` (rilancio dopo errori): modalita' correzione. Correggi
   SOLO gli errori elencati in `stato/blueprint/capNN.json` e vai al "Controllo finale".

## Obiettivo
Produrre `stato/blueprint/capNN.json`: la scheda tecnica del capitolo, da cui un altro modello scrivera' il testo.
Deve essere precisa: e' la fonte di verita' per definizioni, regole, firme delle funzioni ed esercizi.
Non scrivere nessun altro file.

## Formato (JSON valido, nessun testo fuori dal JSON)

```json
{
  "capitolo": 2,
  "titolo": "Variabili e tipi",
  "obiettivi": ["...", "...", "..."],
  "concetti_introdotti": [
    {"termine": "variabile", "definizione": "definizione formale e breve"},
    {"termine": "tipo", "definizione": "..."}
  ],
  "concetti_richiesti": ["compilare ed eseguire un programma"],
  "regole": [
    {"id": "2.R1", "enunciato": "Enunciato preciso della regola.", "nota_standard": "definito | dipendente dall'implementazione | indefinito: spiegazione"}
  ],
  "funzioni_usate": [
    {"nome": "printf", "firma": "int printf(const char *restrict format, ...);", "header": "stdio.h", "descrizione": "una riga"}
  ],
  "sotto_sezioni": [
    {
      "id": "2.1",
      "titolo": "Dichiarare una variabile",
      "contenuti": ["punto che la teoria deve coprire 1", "punto 2"],
      "esempio_guidato": "Descrizione dell'esempio da scrivere: cosa mostra e cosa stampa.",
      "approfondimento": "",
      "esercizio_id": "2.1"
    }
  ],
  "esercizi": [
    {
      "id": "2.1",
      "tipo": "esercizio",
      "titolo": "Il tuo profilo",
      "descrizione": "Testo completo dell'esercizio, almeno 40 caratteri, con tutti i requisiti.",
      "concetti_da_tenere_a_mente": ["concetto 1", "concetto 2"],
      "domande_guida": ["Quale tipo e' adatto a un'eta'?", "Dove dichiari la variabile?", "Come la stampi?"],
      "difficolta": 1,
      "verificabile": true,
      "esempi_io": [{"input": "", "output": "Eta': 17\n"}],
      "test": [{"input": "", "output": "Eta': 17\n"}],
      "soluzione_riferimento": "#include <stdio.h>\n\nint main(void) {\n    int eta = 17;\n    printf(\"Eta': %d\\n\", eta);\n    return 0;\n}\n"
    }
  ],
  "errori_comuni": ["errore tipico 1", "errore tipico 2", "errore tipico 3"],
  "differenze_python": ["(facoltativo) differenza rispetto a Python utile a chi lo conosce"]
}
```

(L'esempio e' abbreviato e semplificato: il tuo file deve rispettare tutti i vincoli qui sotto.)

## Vincoli

### Struttura
- `sotto_sezioni`: esattamente quelle della macro-scaletta (stessi `id`, stesso ordine). Ognuna ha `contenuti` (almeno 2
  punti), `esempio_guidato` (descrizione), `approfondimento` (testo, oppure stringa vuota) ed `esercizio_id`.
- `esercizi`: UNO per sotto-sezione, con `id` uguale a quello della sotto-sezione (`N.k`). Difficolta' crescente nel
  capitolo e nel libro: segui le fasce di difficolta' di `PROGRAMMA.md` (capitoli 1-7 da 1 a 3, 8-12 da 2 a 4, 13-21 da 3 a 5). Nel capitolo di progetto: le prime sotto-sezioni hanno esercizi `"tipo": "esercizio"` che
  preparano i pezzi; l'ultima ha `"tipo": "progetto"` con il campo `"fasi"` (lista di almeno 3 fasi con criterio di verifica).
- `concetti_introdotti`: SOLO i concetti nuovi di questo capitolo (almeno 2), con i termini ESATTI del glossario.
- `regole`: gli enunciati formali (almeno 1), corretti rispetto allo standard C23. In `nota_standard` dichiara se il
  comportamento e' definito, dipendente dall'implementazione o indefinito.
- `funzioni_usate`: ogni funzione/macro di libreria usata negli esempi e nelle soluzioni, con la firma ESATTA della
  libreria standard C23 e l'header. Ognuna deve essere nel `registro` con capitolo <= N.
- `errori_comuni`: almeno 3 errori realmente tipici dei principianti in questo argomento.

### Esercizi (qualita')
- Risolvibili SOLO con gli elementi del `registro` fino al capitolo N compreso. Niente di non ancora spiegato.
- `descrizione`: completa e non ambigua (input, output, casi particolari).
- `concetti_da_tenere_a_mente`: da 2 a 6. `domande_guida`: da 3 a 6, ognuna deve finire con `?`; guidano il
  ragionamento, NON contengono codice ne' il nome della soluzione.
- `esempi_io`: l'esempio (almeno uno) che comparira' nel libro. `test`: casi aggiuntivi di verifica (anche casi limite;
  puo' essere una lista vuota). `input` e `output` sono stringhe ESATTE: se il programma stampa un invito prima di
  leggere, quell'invito e' parte dell'`output`.
- `soluzione_riferimento`: programma C completo (con `main`), nello stile del libro (`CONVENZIONI.md` §4), massimo 60
  righe (150 dal capitolo 13, 900 per il progetto, anche su piu' file con `soluzione_file`). Non deve produrre warning con `-Wall -Wextra -Wpedantic -Werror`, deve essere
  deterministica e restituire 0.
- Soluzione su piu' file (dal capitolo 19 e nel progetto): al posto di `soluzione_riferimento` usa `"soluzione_file"`,
  un oggetto `{"nome.h": "codice", "nome.c": "codice", "main.c": "codice"}` (nomi con lettere, cifre, `_`, estensione `.c` o
  `.h`; almeno un `.c` con `main`). Lo script li scrive nella stessa cartella e li compila insieme.
- Dal capitolo 13 gli esercizi devono essere all'altezza del livello: programmi con logica non banale (strutture dati,
  puntatori, bit, errori da gestire), non variazioni di un esempio. I casi `test` devono includere casi limite
  (vuoto, un solo elemento, pieno, errore di allocazione simulato con dimensioni non valide, ecc.).
- La soluzione NON deve somigliare all'esempio guidato della stessa sotto-sezione: scegli un esercizio che applichi
  il concetto in un contesto diverso.
- Se un esercizio non e' verificabile automaticamente: `"verificabile": false` e `"motivo_non_verificabile"`.
  Per tutti gli altri `"verificabile": true` e sono obbligatori `soluzione_riferimento` (oppure `soluzione_file`), `esempi_io`, `test`.
- Il JSON deve escapare correttamente `\n`, `\"` e `\\` dentro le stringhe di codice.

## Controllo finale (obbligatorio)
1. Esegui `python3 scripts/libro.py controlla-bp N`: compila e testa le tue soluzioni. Leggi gli errori in
   `stato/verifica_bp_capNN.json` e correggi, riesegui (massimo 3 volte).
2. Non toccare gli altri capitoli.

## Non fare
Non scrivere testo del libro. Non modificare la macro-scaletta (se manca un elemento nel registro, segnalalo nel
messaggio finale: lo decide l'utente).

## Messaggio finale
Formato di `CONVENZIONI.md` §7. In DUBBI elenca ogni elemento che avresti voluto usare ma non e' nel registro.
