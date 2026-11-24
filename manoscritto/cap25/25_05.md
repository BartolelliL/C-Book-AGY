## 25.5 Fuzzing a seme fisso e strumenti professionali di analisi

I test automatici scritti a mano controllano i casi a cui hai pensato tu. I difetti più subdoli, però, si nascondono spesso in combinazioni di operazioni a cui nessuno pensa: un inserimento seguito da tre rimozioni, un ridimensionamento esattamente sul bordo della capacità, un carattere inatteso dentro un parser. Per scoprire questi errori esiste una tecnica complementare chiamata **fuzzing** (*fuzzing*): una tecnica di verifica automatica che sottopone un programma a grandi quantità di input generati casualmente per scoprirne difetti.

In C la libreria standard `<stdlib.h>` fornisce un generatore di numeri pseudocasuali semplice e sempre disponibile:

- `void srand(unsigned int seed);` imposta il **seme** iniziale del generatore;
- `int rand(void);` restituisce l'intero pseudocasuale successivo nell'intervallo `[0, RAND_MAX]`, dove `RAND_MAX` è una costante garantita dallo standard pari ad almeno `32767` (puoi verificarlo con `static_assert(RAND_MAX >= 32767)`).

Due regole sono fondamentali quando usi `srand` e `rand` nel fuzzing:

1. **Usa sempre un seme fisso** (per esempio `srand(12345U)` oppure un seme passato da input). Se il fuzzer scopre un guasto al passo 1 842, rilanciare il programma con lo stesso seme sulla stessa piattaforma riproduce esattamente la stessa sequenza di operazioni, permettendoti di indagare il bug nel debugger.
2. **Non dipendere dalla sequenza numerica grezza di `rand()`**. Secondo lo standard C23, le funzioni `srand`, `rand` e il limite `RAND_MAX >= 32767` sono definiti, ma l'algoritmo interno del generatore e la sequenza prodotta per un dato seme sono **dipendenti dall'implementazione**: lo stesso seme produce numeri diversi su Linux, macOS e Windows. Inoltre `rand()` non va mai usato per scopi crittografici o di sicurezza.

Come fai a sapere se il tuo programma si è comportato bene su 5 000 operazioni casuali, se non conosci in anticipo il risultato di ogni passo? Si usano due strategie potentissime, che funzionano qualunque sia la sequenza prodotta da `rand()`:

- **Test differenziale con oracolo**: affianchi alla tua struttura dati veloce (per esempio una mappa ordinata o una tabella hash) un **oracolo** di riferimento elementare e ovvio — magari lento, basato su un piccolo array lineare — ma quasi impossibile da sbagliare. A ogni passo esegui la stessa operazione casuale su entrambi e controlli che i risultati coincidano esattamente.
- **Verifica continua degli invarianti**: scrivi una funzione dedicata (come `invariante_ok(struttura)`) che controlla a ogni singolo passo le proprietà strutturali (chiavi strettamente ordinate, `len <= cap`, assenza di cicli o puntatori incoerenti). Così intercetti l'errore esattamente nel passo in cui nasce, non migliaia di operazioni dopo.

Il fuzzing a seme fisso diventa ancora più efficace quando lo combini con la **cassetta degli attrezzi professionale** del programmatore C:

- **Avvisi severi del compilatore**: compila sempre con `-Wall -Wextra -Wpedantic` (e preferibilmente `-Werror`) per intercettare conversioni sospette, variabili non usate e violazioni dello standard.
- **Sanitizer durante il fuzzing**: eseguire il fuzzer con `-fsanitize=address,undefined` (AddressSanitizer e UndefinedBehaviorSanitizer, introdotti nei capitoli 11 e 21) trasforma ogni accesso fuori dai limiti, uso dopo la liberazione, perdita di memoria o overflow con segno in un arresto immediato con diagnosi precisa.
- **Debugger (`gdb` o `lldb`)**: una volta trovato un seme che fallisce, il debugger ti permette di fermarti esattamente sul passo incriminato e ispezionare variabili, puntatori e stack delle chiamate.
- **Profiler**: prima di ottimizzare a intuito un programma funzionante, usa un profiler del tuo sistema operativo per misurare dove il programma spende davvero il tempo di CPU.

### Esempio guidato

Il programma seguente applica il fuzzing differenziale a una funzione `ordina_inserzione` su `int32_t`. Fissa il seme `12345U`, genera 200 array di lunghezza casuale tra `0` e `64` con valori positivi e negativi, li ordina sia con `ordina_inserzione` sia con l'oracolo `qsort` della libreria standard, verifica che l'array risultante sia ordinato e che i due risultati coincidano byte per byte tramite `memcmp`. L'output stampa solo il seme, il numero di prove e il numero di errori (`0`), restando identico su qualsiasi implementazione di `rand()`.

<!-- cod: id=25.5-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static_assert(RAND_MAX >= 32767);

static void ordina_inserzione(int32_t *a, size_t n) {
    for (size_t i = 1; i < n; ++i) {
        int32_t chiave = a[i];
        size_t j = i;
        while (j > 0 && a[j - 1] > chiave) {
            a[j] = a[j - 1];
            --j;
        }
        a[j] = chiave;
    }
}

static int confronta_i32(const void *p1, const void *p2) {
    int32_t a = *(const int32_t *)p1;
    int32_t b = *(const int32_t *)p2;
    return (a > b) - (a < b);
}

static bool invariante_ordinato(const int32_t *a, size_t n) {
    for (size_t i = 1; i < n; ++i) {
        if (a[i - 1] > a[i]) {
            return false;
        }
    }
    return true;
}

int main(void) {
    constexpr unsigned int SEME = 12345U;
    constexpr size_t PROVE = 200;
    constexpr size_t MAX_N = 64;

    srand(SEME);
    size_t errori = 0;

    for (size_t t = 0; t < PROVE; ++t) {
        size_t n = (size_t)(rand() % (int)(MAX_N + 1));
        int32_t a[MAX_N] = {};
        int32_t oracolo[MAX_N] = {};

        for (size_t i = 0; i < n; ++i) {
            int32_t val = (int32_t)(rand() % 1001) - 500;
            a[i] = val;
            oracolo[i] = val;
        }

        ordina_inserzione(a, n);
        qsort(oracolo, n, sizeof(int32_t), confronta_i32);

        bool inv_ok = invariante_ordinato(a, n);
        bool uguali = (n == 0) || (memcmp(a, oracolo, n * sizeof(int32_t)) == 0);
        if (!inv_ok || !uguali) {
            ++errori;
        }
    }

    printf("Fuzzing ordinamento (seme=%u): prove=%zu errori=%zu\n",
           SEME, PROVE, errori);
    return (errori == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
```

```output
Fuzzing ordinamento (seme=12345): prove=200 errori=0
```

Osserva come l'esempio mette insieme tutte le buone pratiche viste nel capitolo:

- `confronta_i32` usa `(a > b) - (a < b)` invece di `a - b` per evitare qualsiasi rischio di overflow con segno.
- Ogni prova controlla sia l'invariante (`invariante_ordinato`) sia la coincidenza esatta con l'oracolo (`memcmp` dopo `qsort`), gestendo in modo sicuro anche il caso limite `n == 0`.
- Anche se `rand()` genera numeri diversi su piattaforme diverse, la proprietà verificata (`ordina_inserzione` coincide con `qsort`) è universale e l'esito finale è sempre `errori=0`.

> **Approfondimento — La regola d'oro delle prestazioni in C**
> Prima scrivi codice chiaro, modulare e privo di comportamento indefinito, protetto da test automatici, fuzzing e sanitizer. Solo quando tutto funziona correttamente usa un profiler per individuare i veri colli di bottiglia: nella maggior parte dei programmi reali circa il 90% del tempo viene speso nel 10% del codice. Ottimizzare a caso il restante 90% complica il sorgente senza benefici apprezzabili; concentrare miglioramenti algoritmici e di località dei dati sul 10% caldo produce invece guadagni concreti e misurabili.

### Esercizio 25.5 — Fuzzer differenziale a seme fisso (srand/rand) con oracolo e verifica di invarianti per una mappa ordinata

**Descrizione**

Realizza su tre file (`mappa_ord.h`, `mappa_ord.c`, `main.c`) un motore di **fuzzing** differenziale a seme fisso (`srand`/`rand` di `<stdlib.h>`) che mette alla prova una mappa ordinata dinamica contro un oracolo di riferimento elementare. (1) In `mappa_ord.h` (protetto da `MAPPA_ORD_H`) dichiara il **tipo opaco** `mappa_ord_t` con `mappa_ord_t *mappa_crea(void);`, `void mappa_distruggi(mappa_ord_t *m);`, `bool mappa_put(mappa_ord_t *m, int32_t chiave, int32_t valore, bool *aggiornato);` (usa ricerca binaria `O(log n)`, sposta con `memmove` e cresce raddoppiando con `ckd_mul` e `realloc`), `bool mappa_get(const mappa_ord_t *m, int32_t chiave, int32_t *val_out);`, `bool mappa_del(mappa_ord_t *m, int32_t chiave);`, `size_t mappa_len(const mappa_ord_t *m);` e `bool mappa_invariante_ok(const mappa_ord_t *m);` (verifica `len <= cap` e ordine strettamente crescente delle chiavi). (2) In `main.c` verifica `static_assert(RAND_MAX >= 32767)` e implementa un oracolo diretto su array di `64` posizioni (`bool pres[64]`, `int32_t val[64]`). Leggi da `stdin` i comandi `FUZZ <seme> <passi> <max_k>` (`1 <= passi <= 5000`, `1 <= max_k <= 64`): fissa `srand((unsigned int)seme)`, genera `<passi>` operazioni pseudocasuali con `rand()` (`PUT`, `DEL`, `GET` su chiavi in `[0, max_k)` e valori con segno), confronta a ogni passo il risultato e la lunghezza di `mappa_ord` con l'oracolo e controlla `mappa_invariante_ok(m)`. Al termine esegue una scansione completa di tutte le `max_k` chiavi verificando la coincidenza finale con l'oracolo, libera la mappa e stampa `FUZZ(seme=<seme>, passi=<passi>, k=<max_k>): ok=<passi>/<passi> errori=0 inv_ok=1` esattamente come nell'esempio.

**Concetti da tenere a mente**

- inizializzazione del generatore pseudocasuale con `srand(seme)` e uso di `rand()` con `static_assert(RAND_MAX >= 32767)`
- test differenziale contro un oracolo elementare per individuare discrepanze su migliaia di sequenze casuali
- verifica continua degli invarianti strutturali (ordine stretto delle chiavi e coerenza della lunghezza) a ogni passo
- portabilità dell'esito del fuzzing indipendente dall'implementazione specifica di `rand()`

**Domande guida**

1. Perché l'esito del fuzzer differenziale (`errori=0` e `inv_ok=1`) resta identico su sistemi operativi diversi anche se l'algoritmo interno di `rand()` dipende dall'implementazione?
2. Qual è il vantaggio di confrontare `mappa_ord` con un oracolo banale indicizzato direttamente per chiave rispetto a scrivere a mano dieci test statici?
3. Perché conviene chiamare `mappa_invariante_ok(m)` a ogni singolo passo del fuzzing invece che soltanto alla fine dei 5000 passi?
4. Come mai nel fuzzing professionale si combina l'esecuzione con AddressSanitizer e UndefinedBehaviorSanitizer?

**Esempio di esecuzione**

```input
FUZZ 42 500 16
FUZZ 1337 2000 64
FUZZ 7 300 1
```

```output
FUZZ(seme=42, passi=500, k=16): ok=500/500 errori=0 inv_ok=1
FUZZ(seme=1337, passi=2000, k=64): ok=2000/2000 errori=0 inv_ok=1
FUZZ(seme=7, passi=300, k=1): ok=300/300 errori=0 inv_ok=1
```
