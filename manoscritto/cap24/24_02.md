## 24.2 Funzioni sovraccaricate con `_Generic` e `inline`

In C non è possibile dichiarare due funzioni con lo stesso nome e parametri di tipo diverso: se vuoi calcolare il valore assoluto di un `int`, di un `long` e di un `double`, la libreria standard ti costringe a ricordare nomi distinti (`abs`, `labs`, `fabs`). Quando però progetti una libreria numerica o un modulo di utilità, avere un'interfaccia unica che si adatta al tipo dell'argomento rende il codice molto più leggibile e riduce gli errori di conversione implicita.

Combinando due strumenti che già conosci — la selezione generica `_Generic` (capitolo 15) e le funzioni `inline` (capitolo 19) — puoi simulare in C un **sovraccarico statico** basato sul tipo a costo zero a tempo di esecuzione.

### Selezionare la funzione dentro `_Generic`

Un errore frequente con `_Generic` consiste nello scrivere l'intera chiamata alla funzione all'interno di ciascun ramo:

<!-- cod: id=24.2-d tipo=frammento -->
```c
// SCONSIGLIATO: ogni ramo ripete la chiamata e tutti i rami devono tipare
#define ABS_FRAGILE(x) _Generic((x), int: abs_int(x), double: abs_dbl(x))
```

Questa forma ha un difetto importante: in C tutti i rami di `_Generic` devono essere sintatticamente validi e superare il controllo dei tipi anche quando non vengono selezionati. Se `x` è un `double`, il compilatore controlla comunque `abs_int(x)` e può emettere avvisi di conversione o errori veri e propri se i tipi sono incompatibili (ad esempio `struct` e `int`).

Lo schema corretto seleziona **solo il nome della funzione** dentro `_Generic` e applica la lista degli argomenti **all'esterno**:

<!-- cod: id=24.2-e tipo=frammento -->
```c
#define ABS_GEN(x) _Generic((x), \
    int: abs_int,                \
    long: abs_long,              \
    double: abs_double           \
)(x)
```

Questa forma offre tre vantaggi decisivi:

1. **Valutazione unica dell'argomento**: l'espressione di controllo `(x)` di `_Generic` non viene mai valutata a tempo di esecuzione; serve al compilatore esclusivamente per ricavarne il tipo. L'argomento `(x)` viene quindi valutato una sola volta quando viene passato al parametro della funzione selezionata, eliminando il tipico bug delle macro sugli effetti collaterali (come `ABS_GEN(prossimo_valore())`).
2. **Controllo rigoroso dei tipi**: soltanto la funzione scelta viene chiamata con `(x)`. Se il tipo di `x` non compare tra le associazioni e non è presente un ramo `default:`, il compilatore segnala subito un errore di compilazione invece di eseguire conversioni silenziose.
3. **Costo zero a tempo di esecuzione**: la scelta avviene interamente a tempo di compilazione; se le funzioni bersaglio sono `inline`, il compilatore può integrarne il corpo direttamente nel punto di chiamata.

### `static inline` contro `inline` + `extern inline`

Quando organizzi una libreria sovraccaricata su più file (un file di intestazione `.h` e uno o più file `.c`), devi decidere quale modello di collegamento dare alle funzioni di supporto:

- **`static inline` nell'header**: ogni unità di traduzione riceve una copia con collegamento interno. È la scelta più semplice per helper brevi e privati dell'header, come piccole funzioni di formattazione o ricerche lineari, di cui non serve garantire un unico indirizzo condiviso tra più file `.c`.
- **`inline` nell'header + `extern inline` in esattamente un file `.c`**: la definizione nell'header fornisce il corpo per l'inlining, mentre la dichiarazione `extern inline` in un solo file `.c` ordina al compilatore di emettere l'unica definizione con collegamento esterno del modulo. Questa scelta è preferibile per le funzioni pubbliche della libreria, perché garantisce che esista un solo simbolo nel programma anche quando il compilatore disattiva l'inlining (ad esempio con `-O0` in debug) o quando prendi l'indirizzo della funzione tramite un puntatore a funzione.

Secondo lo standard C23, questo modello di collegamento è completamente definito: omettere la dichiarazione `extern inline` per una funzione `inline` non-`static` usata con collegamento esterno provoca un errore del collegatore (simbolo non definito).

### Preservare la qualificazione `const`

Una delle applicazioni più eleganti di `_Generic` riguarda le funzioni di ricerca che accettano un puntatore a dati mutabili oppure a dati costanti e restituiscono un puntatore all'interno dello stesso buffer. Con una normale funzione C dovresti scrivere:

<!-- cod: id=24.2-f tipo=frammento -->
```c
const int *cerca(const int *arr, size_t n, int val);
```

In questo modo, anche passando un `int *` mutabile, il valore di ritorno diventa `const int *`, costringendoti a un cast esplicito se vuoi modificare l'elemento trovato. Con `_Generic` puoi distinguere i due rami `int *` e `const int *` e indirizzarli a due funzioni `static inline` dedicate:

<!-- cod: id=24.2-g tipo=frammento -->
```c
#define CERCA_INT(arr, n, val) _Generic((arr), \
    const int *: cerca_int_const,              \
    int *: cerca_int_mut                       \
)((arr), (n), (val))
```

In questo modo la macro preserva fedelmente la qualificazione `const`: se passi un array mutabile ottieni un `int *`, se passi un `const int *` ottieni un `const int *`, senza mai rimuovere `const` con cast pericolosi.

> **C23** — Lo standard C23 ha adottato proprio questa tecnica (chiamata *qualificazione preservata*) per funzioni storiche di `<string.h>` e `<stdlib.h>` come `strchr`, `memchr` e `bsearch`: in C23, chiamare `strchr` su un `const char *` restituisce `const char *`, mentre chiamarla su un `char *` restituisce `char *`. Nei compilatori precedenti (C11/C17) queste funzioni restituivano sempre `char *` o `void *`, perdendo la protezione di `const`.

> **Se vieni da Python** — In Python il polimorfismo e il sovraccarico vengono risolti dinamicamente a tempo di esecuzione sugli oggetti; in C `_Generic` abbinato a funzioni `inline` seleziona la funzione esatta a tempo di compilazione senza alcun sovraccarico a tempo di esecuzione.

### Esempio guidato

Il modulo seguente, diviso in `stampa_gen.h`, `stampa_gen.c` e `main.c`, definisce funzioni `inline` (con `extern inline` in `stampa_gen.c`) per calcolare il valore assoluto e stampare valori di tipo `int`, `long`, `double` e `const char *`. Le macro `ABS_GEN(x)` e `MOSTRA(x)` usano `_Generic` per selezionare la funzione corretta; in `main.c` la funzione `prossimo_int` verifica che l'argomento di `ABS_GEN` venga valutato una sola volta.

<!-- cod: id=24.2-a tipo=programma gruppo=stampa_gen file=stampa_gen.h -->
```c
#ifndef STAMPA_GEN_H
#define STAMPA_GEN_H

#include <stdio.h>

inline int abs_int(int x) { return (x < 0) ? -x : x; }
inline long abs_long(long x) { return (x < 0L) ? -x : x; }
inline double abs_double(double x) { return (x < 0.0) ? -x : x; }

inline void mostra_int(int x) { printf("int: %d\n", x); }
inline void mostra_long(long x) { printf("long: %ld\n", x); }
inline void mostra_double(double x) { printf("double: %.2f\n", x); }
inline void mostra_str(const char *s) { printf("str: %s\n", s); }

#define ABS_GEN(x) _Generic((x), \
    int: abs_int,                \
    long: abs_long,              \
    double: abs_double           \
)(x)

#define MOSTRA(x) _Generic((x), \
    int: mostra_int,            \
    long: mostra_long,          \
    double: mostra_double,      \
    const char *: mostra_str,   \
    char *: mostra_str          \
)(x)

#endif
```

<!-- cod: id=24.2-b tipo=programma gruppo=stampa_gen file=stampa_gen.c -->
```c
#include "stampa_gen.h"

extern inline int abs_int(int x);
extern inline long abs_long(long x);
extern inline double abs_double(double x);
extern inline void mostra_int(int x);
extern inline void mostra_long(long x);
extern inline void mostra_double(double x);
extern inline void mostra_str(const char *s);
```

<!-- cod: id=24.2-c tipo=programma gruppo=stampa_gen file=main.c -->
```c
#include <stdio.h>
#include "stampa_gen.h"

static int prossimo_int(int *chiamate, int valore) {
    ++(*chiamate);
    return valore;
}

int main(void) {
    int chiamate = 0;
    int a = ABS_GEN(prossimo_int(&chiamate, -18));
    long b = ABS_GEN(-500000L);
    double c = ABS_GEN(-3.75);
    char etichetta[] = "C23";

    MOSTRA(a);
    MOSTRA(b);
    MOSTRA(c);
    MOSTRA(etichetta);
    MOSTRA("testo costante");
    printf("Valutazioni di prossimo_int: %d\n", chiamate);
    return 0;
}
```

```output
int: 18
long: 500000
double: 3.75
str: C23
str: testo costante
Valutazioni di prossimo_int: 1
```

Osserva i dettagli fondamentali del modulo:

- In `stampa_gen.h` tutte le funzioni sono dichiarate `inline`; in `stampa_gen.c` le corrispondenti dichiarazioni `extern inline` emettono le definizioni esterne una sola volta per l'intero eseguibile.
- Nella macro `MOSTRA(x)` sono presenti sia `const char *` sia `char *`: in C sia un array `char etichetta[]` sia un letterale stringa come `"testo costante"` decadono a `char *` (a differenza del C++, in C i letterali stringa non sono `const` nel tipo, pur essendo comportamento indefinito modificarli), mentre un puntatore a caratteri costanti ha tipo `const char *`; coprire entrambi i rami rende la macro sicura con qualsiasi stringa.
- L'output conferma che `prossimo_int` è stata invocata una sola volta (`Valutazioni di prossimo_int: 1`), dimostrando che `(x)` dentro `_Generic((x), ...)` non è valutato.

> **Approfondimento — Conversioni di tipo nell'espressione di controllo di `_Generic`**
> Nell'espressione di controllo di `_Generic((x), ...)`, il compilatore applica la conversione *lvalue* (rimuovendo qualificatori di alto livello come `const` sul valore stesso, non sul tipo puntato) e il decadimento di array e funzioni a puntatori. Per questo un array `int a[4]` combacia con `int *` e non con `int[4]`, mentre un letterale carattere come `'a'` in C ha tipo `int` (non `char`) e quindi seleziona il ramo `int`. Quando progetti una macro sovraccaricata, verifica sempre quali tipi risultano dopo queste conversioni.

### Esercizio 24.2 — Libreria numerica sovraccaricata su più file con `_Generic`, `inline`/`extern inline` e `const`-preservation

**Descrizione**

Realizza su tre file (`num_gen.h`, `num_gen.c`, `main.c`) una mini-libreria numerica con funzioni sovraccaricate tramite `_Generic` e `inline`. (1) In `num_gen.h` (protetto da `NUM_GEN_H`) definisci `typedef struct vec2 { double x; double y; } vec2_t;` e fornisci otto funzioni `inline` (senza `static`) per i quattro tipi `int32_t`, `int64_t`, `double` e `vec2_t`: `limita_i32`, `limita_i64`, `limita_dbl`, `limita_vec2` (limita ciascuna componente in `[lo, hi]`) e `somma_sat_i32`, `somma_sat_i64` (somma con `ckd_add` che satura a `INT32_MAX`/`INT32_MIN` o `INT64_MAX`/`INT64_MIN` senza overflow indefinito), `somma_dbl` e `somma_vec2`. Definisci inoltre quattro helper `static inline` di formattazione (`fmt_i32`, `fmt_i64`, `fmt_dbl` con `%.2f`, `fmt_vec2` con `(%.2f,%.2f)`) e due helper `static inline` di ricerca (`cerca_i32_const` su `const int32_t *` e `cerca_i32_mut` su `int32_t *`). Esponi le quattro macro `_Generic`: `SOMMA(a, b)`, `LIMITA(x, lo, hi)`, `FORMATTA(x, buf, cap)` e `CERCA_I32(arr, n, val)` (che preserva `const` restituendo `const int32_t *` o `int32_t *` in base al puntatore di ingresso). (2) In `num_gen.c` emetti le definizioni esterne `extern inline` per tutte e otto le funzioni `inline` dell'header. (3) In `main.c` usa un helper `int32_t traccia_eval(int *c, int32_t v)` per dimostrare che `LIMITA(traccia_eval(&evals, s), lo, hi)` valuta il primo argomento una sola volta (`evals == 1`), gestisci da `stdin` i comandi `I32 <a> <b> <lo> <hi>`, `I64 <a> <b> <lo> <hi>`, `DBL <a> <b> <lo> <hi>`, `VEC <ax> <ay> <bx> <by> <lox> <loy> <hix> <hiy>` e `FIND <val>` (cercando in `{10, 20, 30, 40, 50}` sia su puntatore mutabile sia su `const int32_t *` e verificando il tipo del puntatore restituito con `_Generic`), riproducendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- selezione statica del nome della funzione dentro `_Generic` con applicazione degli argomenti all'esterno
- valutazione unica degli argomenti con effetti collaterali grazie al passaggio alla funzione `inline` selezionata
- modello di collegamento `inline` nell'header affiancato da `extern inline` in un solo file `.c`
- preservazione della qualificazione `const` tramite associazioni separate `T *` e `const T *` in `_Generic`

**Domande guida**

1. Perché chiamare `LIMITA(traccia_eval(&evals, s), lo, hi)` incrementa `evals` una sola volta invece di due, nonostante `traccia_eval(&evals, s)` compaia sia in `_Generic` sia nella chiamata?
2. Che errore rischia il collegatore se dichiari `inline int32_t limita_i32(...)` in `num_gen.h` senza fornire `extern inline int32_t limita_i32(...)` in `num_gen.c`?
3. Come fa `CERCA_I32(arr, n, val)` a restituire `int32_t *` quando riceve un array mutabile e `const int32_t *` quando riceve un puntatore a dati costanti senza mai rimuovere `const`?
4. Perché nelle funzioni `somma_sat_i32` e `somma_sat_i64` conviene rilevare l'overflow con `ckd_add` prima di saturare al massimo o al minimo?

**Esempio di esecuzione**

```input
I32 2000000000 500000000 -100 1000
I64 -9223372036854775800 -100 -500 500
DBL 1.25 2.50 0.0 3.0
VEC 1.5 -2.0 2.0 0.5 0.0 -1.0 3.0 1.0
FIND 30
FIND 99
```

```output
I32: somma=2147483647 clamp=1000 evals=1
I64: somma=-9223372036854775808 clamp=-500
DBL: somma=3.75 clamp=3.00
VEC: somma=(3.50,-1.50) clamp=(3.00,-1.00)
FIND(30): idx=2 mut=int32_t* cst=const int32_t*
FIND(99): ASSENTE mut=int32_t* cst=const int32_t*
```
