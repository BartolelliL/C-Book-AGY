# Digest — Capitolo 8: Array

## Termini definiti e glossario
- **Array** (*array*): sequenza contigua in memoria di un numero fissato di elementi tutti dello stesso tipo, accessibili tramite indice.
- **Indice** (*index*): valore intero non negativo che identifica la posizione di un elemento in un array a partire da `0`.
- **Accesso fuori dai limiti** (*out-of-bounds access*): qualsiasi lettura o scrittura di un array con un indice negativo o maggiore o uguale alla sua lunghezza (comportamento indefinito).
- Altri termini del glossario usati: *array a lunghezza variabile* (VLA), inizializzatore designato, capacità fisica, lunghezza effettiva, array bidimensionale, *row-major order* (per righe), ricerca lineare, ricerca binaria, ordinamento per selezione, ordinamento per inserzione, invariante di ciclo, comportamento indefinito, valutazione a corto circuito.

## Concetti spiegati
- Dichiarazione `tipo nome[N];` con `N` costante (`constexpr` C23 o letterale; VLA vietati nel libro).
- Inizializzazione: lista completa, lunghezza dedotta (`int b[] = {...}`), parziale (`{0}` azzera tutto), inizializzatore designato (`{[i] = v}`); array locale non inizializzato contiene valori indeterminati (comportamento indefinito alla lettura).
- Lunghezza con `sizeof(a) / sizeof(a[0])` di tipo `size_t` (solo nella stessa visibilità della dichiarazione).
- Divieto di copia/confronto diretto (`a = b` errore, `a == b` non confronta elementi): serve un ciclo elemento per elemento.
- Accessi fuori dai limiti: errori off-by-one (`<= n`, `a[i + 1]` con `i < n`, underflow `i - 1` su `size_t`), distinzione tra capacità fisica e lunghezza effettiva `n`, controllo dei limiti a sinistra di `&&` per corto circuito.
- Passaggio di array a funzioni: `tipo a[]` (adattato a puntatore al primo elemento) + parametro `size_t n` obbligatorio (dentro la funzione `sizeof(a)` non dà la dimensione dell'array); `const tipo a[]` per sola lettura; modifica e riorganizzazione sul posto.
- Array bidimensionali `tipo m[RIGHE][COLONNE]`: memorizzazione contigua per righe (*row-major order*), cicli annidati con righe all'esterno per località dei dati, seconda dimensione costante obbligatoria nei parametri (`m[][COLONNE]`).
- Algoritmi elementari e idea di costo: ricerca lineare ($n$), ricerca binaria ($\log_2 n$, su array ordinato, intervallo semiaperto `[sinistra, destra)` su `size_t`, `medio = sinistra + (destra - sinistra) / 2`), ordinamento per selezione ($n(n-1)/2$) e per inserzione (lineare nel caso migliore, quadratico nel peggiore).

## Esempi e scenari
- **8.1**: vendite settimanali di una libreria (`vendite`, `sconti`, `giorni`, `giorno_migliore`).
- **8.2**: interrogazioni su letture di temperatura (`letture`, `CAPACITA = 8`, `usati = 5`, `richieste`).
- **8.3**: elaborazione prezzi (`prezzi`, `calcola_media`, `indice_massimo`, `scala_valori`, `stampa_array`).
- **8.4**: temperature di 3 stazioni in 4 fasce (`temp[3][4]`, `stampa_tabella`, `media_stazione`, `fascia_piu_calda`).
- **8.5**: confronto ricerca lineare, `ordina_selezione` e ricerca binaria su array `codici`.

## Esercizi
- **8.1 — Istogramma delle valutazioni con inizializzatore designato**: contare frequenze voti `1..5` in `frequenze[6]`, mappare gradimento con `punti[6]` designato, stampare istogramma a `*` e statistiche. Difficoltà: 2/5.
- **8.2 — Interrogazioni su sotto-intervalli con controlli sui limiti**: leggere `n` misure in array `MAX_STAZIONI = 20`, validare coppie `inizio fine` prima di calcolare min/max/media sul sotto-intervallo. Difficoltà: 2/5.
- **8.3 — Saturazione e inversione di un segnale con funzioni su array**: `satura_array`, `inverti_array`, `stampa_array` su `MAX_CAMPIONI = 30`. Difficoltà: 3/5.
- **8.4 — Somme per righe, colonne e trasposta di una matrice**: `stampa_matrice`, `somma_riga`, `trasponi` su matrice `MAX_DIM = 6`. Difficoltà: 3/5.
- **8.5 — Ordinamento per inserzione e confronto tra ricerca lineare e binaria**: `ordina_inserzione` (contando spostamenti), `ricerca_lineare` e `ricerca_binaria` (prima occorrenza con `[sinistra, destra)`). Difficoltà: 4/5.

## Rinvii
- Richiami ai capitoli precedenti: cap. 2, 4, 6, 7 in apertura; cap. 4 (corto circuito `&&`); cap. 5 (`char riga[128]` e `fgets`); cap. 6 (cicli annidati, invariante di ciclo).
- Rinvii in avanti: cap. 9 (stringhe in array di `char`); cap. 10 (puntatori, perché `a == b` non confronta elementi e adattamento di `tipo a[]`); cap. 11 (memoria dinamica al posto dei VLA, sanitizer e stack); cap. 16 (`qsort`); cap. 19 (`#define`); cap. 23 (notazione O); cap. 25 (località dei dati).

## Affermazioni forti
- Mai usare VLA (array a lunghezza variabile) in questo libro.
- Passare sempre esplicitamente `size_t n` alle funzioni che ricevono un array; mai usare `sizeof(a) / sizeof(a[0])` dentro la funzione.
- Usare sempre `const tipo a[]` nei parametri array di sola lettura.
- Nella ricerca binaria su `size_t` usare sempre `[sinistra, destra)` e `sinistra + (destra - sinistra) / 2`.
- Negli array bidimensionali nei parametri di funzione indicare sempre la seconda dimensione costante (`m[][COLONNE]`).

## Stile del codice
- Standard C23 (`constexpr`, `size_t` con `%zu` in `printf`, `<stddef.h>` in `08_01`–`08_02`, `<stdio.h>` in `08_03`–`08_05`).
- Costanti in MAIUSCOLO (`CAPACITA`, `MAX_DIM`), prototipi prima di `main`, identificatori `snake_case` italiano.
