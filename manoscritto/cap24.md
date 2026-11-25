# Capitolo 24 — Tecniche avanzate del linguaggio

> **In questo capitolo imparerai a:**
> - Scrivere macro robuste con `do-while(0)`, macro variadiche (`__VA_ARGS__`, `__VA_OPT__`) e X-macro
> - Simulare il sovraccarico di funzioni combinando `_Generic` e funzioni `inline`
> - Gestire uscite non locali in sicurezza con `setjmp` e `longjmp` conoscendo i vincoli su `volatile`
> - Implementare liste intrusive con `offsetof`, macchine a stati con tabelle di funzioni e formati binari con campi di bit

> **Ti servono:** i campi di bit, le unioni e `offsetof` (capitolo 13), `_Generic` e `static_assert` (capitolo 15), i puntatori a funzione (capitolo 16), le liste concatenate (capitolo 17), i programmi su più file e `inline` (capitolo 19), le macro con argomenti e `volatile` (capitolo 21).

Dopo aver costruito strutture dati complesse e analizzato la loro complessità nel capitolo precedente, conosci ormai l'intero nucleo del linguaggio C. Tuttavia, quando si legge il codice di compilatori, sistemi operativi, interpreti o librerie ad alte prestazioni, si incontrano schemi ricorrenti che sfruttano in modo combinato il preprocessore, il sistema dei tipi, il layout in memoria e il controllo di flusso. Questi idiomi non sono trucchi fini a sé stessi: nascono per risolvere problemi concreti come eliminare la duplicazione di codice, azzerare il costo delle astrazioni, gestire errori in ricorsioni profonde senza inquinare ogni firma o ridurre al minimo le allocazioni dinamiche.

In questo capitolo raccogliamo sei tecniche avanzate del C23 che completano la tua cassetta degli attrezzi. Vedrai come generare enumerazioni, tabelle e funzioni sincronizzate da un'unica fonte con le X-macro, come offrire interfacce polimorfiche a costo zero con `_Generic` e `inline`, e come usare `setjmp` e `longjmp` rispettando i vincoli rigorosi dello standard su sintassi, `volatile` e risorse allocate.

Nella seconda metà del capitolo applicherai queste conoscenze a tre problemi di architettura: le liste intrusive basate su `offsetof`, che permettono a un oggetto di appartenere a più liste senza nodi aggiuntivi; le macchine a stati finiti guidate da tabelle bidimensionali di puntatori a funzione; e i formati binari compatti, in cui i campi di bit e le unioni etichettate convivono con codec portabili indipendenti dall'architettura.

## 24.1 Macro avanzate: `do-while(0)`, macro variadiche e X-macro

Nel capitolo 21 hai incontrato le macro con argomenti e hai visto perché vadano usate con cautela rispetto alle funzioni `static inline`. Esistono però situazioni in cui una funzione non basta: generare nuovi identificatori, convertire nomi del codice in stringhe, accettare un numero variabile di argomenti mantenendo il controllo dei tipi del compilatore, oppure mantenere allineate più tabelle a partire da un'unica definizione. In questi casi il preprocessore diventa uno strumento di generazione del codice a tempo di compilazione, purché si rispettino alcuni idiomi consolidati.

### Macro multi-istruzione sicure con `do { ... } while (0)`

Supponi di voler scrivere una macro che esegue due o più istruzioni, ad esempio scambiare due variabili o aggiornare due contatori. L'istinto iniziale porta a racchiudere le istruzioni tra parentesi graffe:

<!-- cod: id=24.1-b tipo=frammento -->
```c
// ATTENZIONE: macro fragile, non scrivere così
#define RESETTA(a, b) { (a) = 0; (b) = 0; }
```

A prima vista questa definizione sembra corretta, ma si rompe non appena la macro viene invocata nel ramo `if` di un costrutto `if-else`:

<!-- cod: id=24.1-c tipo=frammento -->
```c
if (errore)
    RESETTA(x, y);
else
    continua();
```

Dopo la sostituzione del preprocessore, il punto e virgola che chiude `RESETTA(x, y);` diventa un'istruzione vuota che termina l'`if`, lasciando il ramo `else` orfano e provocando un errore di compilazione. Se togliessi le graffe dalla macro, la seconda istruzione verrebbe eseguita sempre fuori dall'`if`.

La soluzione standard del linguaggio C consiste nel racchiudere le istruzioni in un ciclo `do { ... } while (0)` **senza punto e virgola finale**:

<!-- cod: id=24.1-d tipo=frammento -->
```c
#define RESETTA(a, b) \
    do {              \
        (a) = 0;      \
        (b) = 0;      \
    } while (0)
```

Il costrutto `do { ... } while (0)` richiede esattamente un punto e virgola al termine: quello fornito dal chiamante quando scrive `RESETTA(x, y);`. Il corpo viene eseguito esattamente una volta, crea un proprio blocco per eventuali variabili temporanee locali e si comporta come una singola istruzione sintattica in ogni contesto, incluso un `if-else` privo di graffe. I compilatori moderni eliminano completamente il test costante `while (0)` senza alcun costo a tempo di esecuzione.

### Stringificazione (`#`), concatenazione (`##`) e doppio livello di espansione

Il preprocessore fornisce due operatori speciali utilizzabili nel corpo delle macro con argomenti:

- L'operatore `#` (**stringificazione**) trasforma il testo grezzo di un parametro della macro in un letterale stringa C racchiuso tra virgolette, eseguendo automaticamente l'escape di eventuali virgolette o barre rovesciate interne.
- L'operatore `##` (**concatenazione di token**) fonde i token alla sua sinistra e alla sua destra in un unico token, ad esempio per costruire nomi di costanti o funzioni come `e_colore_##nome`.

Secondo lo standard C23, entrambi gli operatori sono completamente definiti, ma produrre con `##` una sequenza di caratteri che non costituisce un token valido del preprocessore provoca **comportamento indefinito**. Inoltre, sia `#` sia `##` inibiscono la normale espansione delle macro presenti nei propri operandi diretti: se passi un'altra macro come argomento, il preprocessore usa il nome letterale della macro invece del suo valore. Per forzare l'espansione prima di applicare `#` o `##` si utilizza la tecnica del **doppio livello di espansione**:

<!-- cod: id=24.1-e tipo=frammento -->
```c
#define STR_IMPL(x) #x
#define STR(x) STR_IMPL(x)

#define UNISCI_IMPL(a, b) a##b
#define UNISCI(a, b) UNISCI_IMPL(a, b)
```

Quando invochi `STR(x)`, il preprocessore espande prima `x` (perché nella definizione di `STR` il parametro `x` non è adiacente a `#`) e solo dopo passa il risultato già espanso a `STR_IMPL`, che lo trasforma in stringa. Lo stesso meccanismo vale per `UNISCI` e `UNISCI_IMPL`.

### Macro variadiche: `__VA_ARGS__` e l'operatore C23 `__VA_OPT__`

Una macro può accettare un numero variabile di argomenti terminando la lista dei parametri con i tre punti `...`. Nel corpo della macro, l'identificatore predefinito `__VA_ARGS__` rappresenta l'intera sequenza degli argomenti variadici passati dal chiamante.

Uno schema molto comune consiste nell'avvolgere `printf` o `snprintf` per aggiungere un prefisso fisso:

<!-- cod: id=24.1-f tipo=frammento -->
```c
#define LOG_ERR(fmt, ...) fprintf(stderr, "[ERR] " fmt "\n", __VA_ARGS__)
```

Questa versione funziona se passi almeno un argomento dopo `fmt`, ma fallisce se scrivi `LOG_ERR("Avvio fallito")`, perché la virgola prima di `__VA_ARGS__` resta appesa e produce un errore di compilazione (`fprintf(stderr, "[ERR] Avvio fallito\n", )`).

Il C23 risolve definitivamente questo problema in modo portabile con l'operatore `__VA_OPT__(contenuto)`, che emette `contenuto` solo se la lista degli argomenti variadici contiene almeno un token:

<!-- cod: id=24.1-g tipo=frammento -->
```c
#define STAMPA_LOG(liv, fmt, ...) \
    printf("[%s] " fmt "\n", (liv) __VA_OPT__(,) __VA_ARGS__)
```

Se invochi `STAMPA_LOG("INFO", "Pronto")`, `__VA_ARGS__` è vuoto e `__VA_OPT__(,)` non emette nulla; se invochi `STAMPA_LOG("DATI", "val=%d", 42)`, `__VA_OPT__(,)` inserisce la virgola necessaria prima di `42`.

> **C23** — L'operatore `__VA_OPT__` è una novità dello standard C23. Con compilatori precedenti (C11/C17) si ricorreva all'estensione non standard `##__VA_ARGS__` (supportata da GCC e Clang ma non portabile) oppure si passava la stringa di formato dentro `...` (evitando parametri fissi prima dei tre punti). In C23 `__VA_OPT__` è standard e compila senza avvisi con `-Wpedantic`.

### Il modello X-macro

In molti programmi occorre mantenere sincronizzate più rappresentazioni degli stessi elementi: una `enum` per i codici simbolici, un array di struct con nomi leggibili e parametri, e magari una serie di funzioni di utilità. Se mantieni questi elenchi separati, aggiungere o riordinare una voce in un solo punto introduce facilmente bug silenziosi.

Una **X-macro** è una tecnica del preprocessore che definisce una sola volta una lista tabellare di voci come macro parametrica `LISTA(X)` e la espande più volte con definizioni diverse della macro `X` per generare in modo sincronizzato enumerazioni, tabelle e funzioni. Dopo ogni espansione si rimuove la macro temporanea con `#undef`, lasciando pulito lo spazio dei nomi del preprocessore.

Riassumiamo le regole chiave di questa sotto-sezione:

- Racchiudi sempre una macro multi-istruzione in `do { ... } while (0)` senza punto e virgola finale.
- Usa `#` per stringificare, `##` per concatenare token validi e un doppio livello di espansione (`STR`/`STR_IMPL`, `UNISCI`/`UNISCI_IMPL`) quando gli argomenti possono essere a loro volta macro.
- Usa `...`, `__VA_ARGS__` e `__VA_OPT__(...)` (C23) per scrivere macro variadiche portabili che accettano zero o più argomenti extra.
- Usa una X-macro `LISTA(X)` quando enum, tabelle e funzioni devono restare sempre sincronizzati, verificando comunque le dimensioni con `static_assert`.

### Esempio guidato

Il programma seguente definisce un'unica X-macro `LISTA_COLORI(X)` e la espande tre volte: per generare l'enumerazione `colore_t`, la tabella costante `COLORI[]` (usando `#` per il nome testuale) e quattro funzioni predicato tramite `##`. Mostra inoltre la macro `AGGIORNA_ESTREMI` protetta con `do-while(0)` usata dentro un `if-else` e la macro variadica `STAMPA_LOG` con `__VA_OPT__`, chiamata sia con zero sia con due argomenti variadici.

<!-- cod: id=24.1-a tipo=programma -->
```c
#include <limits.h>
#include <stddef.h>
#include <stdio.h>

#define LISTA_COLORI(X) \
    X(ROSSO, 220, 40, 40) \
    X(VERDE, 40, 180, 60) \
    X(BLU, 30, 90, 210) \
    X(AMBRA, 240, 170, 20)

#define GEN_ENUM(nome, r, g, b) COL_##nome,
typedef enum colore {
    LISTA_COLORI(GEN_ENUM)
    COL_CONTEGGIO
} colore_t;
#undef GEN_ENUM

typedef struct info_colore {
    const char *nome;
    int r;
    int g;
    int b;
} info_colore_t;

#define STR_IMPL(x) #x
#define STR(x) STR_IMPL(x)

#define GEN_TAB(nome, r, g, b) {STR(nome), (r), (g), (b)},
static const info_colore_t COLORI[] = {
    LISTA_COLORI(GEN_TAB)
};
#undef GEN_TAB

static_assert(sizeof(COLORI) / sizeof(COLORI[0]) == COL_CONTEGGIO);

#define DEF_PRED(nome, r, g, b) \
    [[maybe_unused]] static bool e_colore_##nome(colore_t c) { return c == COL_##nome; }
LISTA_COLORI(DEF_PRED)
#undef DEF_PRED

#define AGGIORNA_ESTREMI(val, min_v, max_v) \
    do {                                    \
        int _v = (val);                     \
        if (_v < (min_v)) { (min_v) = _v; } \
        if (_v > (max_v)) { (max_v) = _v; } \
    } while (0)

#define STAMPA_LOG(liv, fmt, ...) \
    printf("[%s] " fmt "\n", (liv) __VA_OPT__(,) __VA_ARGS__)

int main(void) {
    STAMPA_LOG("INFO", "Tavolozza pronta");
    int min_r = INT_MAX;
    int max_r = INT_MIN;

    for (size_t i = 0; i < COL_CONTEGGIO; ++i) {
        printf("%zu: %s rgb(%d,%d,%d)\n", i, COLORI[i].nome,
               COLORI[i].r, COLORI[i].g, COLORI[i].b);
        if (COLORI[i].r >= 0)
            AGGIORNA_ESTREMI(COLORI[i].r, min_r, max_r);
        else
            STAMPA_LOG("WARN", "Valore negativo");
    }

    STAMPA_LOG("DATI", "Canale rosso: min=%d max=%d", min_r, max_r);
    printf("e_colore_AMBRA(COL_AMBRA) = %d\n", e_colore_AMBRA(COL_AMBRA) ? 1 : 0);
    printf("e_colore_AMBRA(COL_BLU) = %d\n", e_colore_AMBRA(COL_BLU) ? 1 : 0);
    return 0;
}
```

```output
[INFO] Tavolozza pronta
0: ROSSO rgb(220,40,40)
1: VERDE rgb(40,180,60)
2: BLU rgb(30,90,210)
3: AMBRA rgb(240,170,20)
[DATI] Canale rosso: min=30 max=240
e_colore_AMBRA(COL_AMBRA) = 1
e_colore_AMBRA(COL_BLU) = 0
```

Osserva come interagiscono le tecniche nell'esempio:

- `LISTA_COLORI(X)` è l'unica fonte di verità: se aggiungi un quinto colore in quell'elenco, vengono aggiornati in automatico l'enumerazione `colore_t`, il conteggio `COL_CONTEGGIO`, la tabella `COLORI[]` e le funzioni `e_colore_*`.
- L'attributo C23 `[[maybe_unused]]` sulle funzioni generate da `DEF_PRED` evita avvisi del compilatore per i predicati non chiamati direttamente in `main`.
- La macro `AGGIORNA_ESTREMI` copia `val` nella variabile locale `_v` per valutarlo una sola volta e usa `do { ... } while (0)` per funzionare senza errori nel ramo `if` seguito da `else`.
- `STAMPA_LOG` funziona con la stessa definizione sia senza argomenti extra (`"Tavolozza pronta"`) sia con due argomenti (`min_r, max_r`), grazie a `__VA_OPT__(,)`.

> **Approfondimento — Perché `#` e `##` richiedono il doppio livello di espansione**
> Le regole di sostituzione del preprocessore stabiliscono che un parametro adiacente a `#` o `##` non viene espanso prima dell'operazione. Se definisci `#define VERSIONE 23` e `#define STR_DIRETTA(x) #x`, allora `STR_DIRETTA(VERSIONE)` produce la stringa `"VERSIONE"`, non `"23"`. Interponendo `#define STR(x) STR_DIRETTA(x)`, il parametro `x` non tocca `#`: il preprocessore sostituisce prima `VERSIONE` con `23`, poi passa `23` a `STR_DIRETTA`, ottenendo `"23"`. Lo stesso principio vale per `##` quando uno dei due operandi è a sua volta una macro (come `__LINE__`).

### Esercizio 24.1 — Registro diagnostico generato con X-macro, `do-while(0)`, `#`/`##` e `__VA_OPT__`

**Descrizione**

Realizza su due file (`codici_x.h` e `main.c`) un registro di diagnostica interamente pilotato da una **X-macro** senza duplicare mai nomi o codici. (1) In `codici_x.h` (protetto da `CODICI_X_H`) definisci la X-macro `LISTA_CODICI(X)` con cinque voci `(nome, num, liv, peso)`: `(OK, 0, "INFO", 0)`, `(DISCO_PIENO, 101, "ERR", 5)`, `(IO_TIMEOUT, 102, "WARN", 3)`, `(CHECKSUM_KO, 201, "CRIT", 10)` e `(PERM_NEGATO, 202, "ERR", 4)`. Da `LISTA_CODICI(X)` genera l'enumerazione `codice_diag_t` (`COD_OK`, ..., `COD_PERM_NEGATO`, `COD_CONTEGGIO`), le macro a doppio livello `STR(x)` (`#`) e `UNISCI(a, b)` (`##`), la macro `DEF_PRED_CODICE(nome, num, liv, peso)` che usa `##` per generare le cinque funzioni `static bool e_codice_<nome>(codice_diag_t c)`, la macro multi-istruzione `AGGIORNA_STAT(st, idx, molt)` protetta con `do { ... } while (0)` (aggiorna `conteggi[idx]`, `totale` e `gravita_tot += TABELLA_CODICI[idx].peso * molt`), e la macro variadica C23 `FORMATTA_DIAG(buf, cap, tag, fmt, ...)` basata su `snprintf` e `__VA_OPT__(,)` che accetta sia zero sia più argomenti variadici. (2) In `main.c` genera `static const info_codice_t TABELLA_CODICI[]` da `LISTA_CODICI` (usando `#nome` per il simbolo testuale) e verifica con `static_assert` che la sua lunghezza coincida con `COD_CONTEGGIO`. Leggi da `stdin` comandi fino a fine input: `REG <num> <molt>` (`1 <= molt <= 10`, aggiorna le statistiche con `AGGIORNA_STAT` e stampa il messaggio creato con `FORMATTA_DIAG` con argomenti variadici, oppure `CODICE_IGNOTO: <num>`), `PING <tag>` (invoca `FORMATTA_DIAG` con zero argomenti variadici per verificare `__VA_OPT__`), `IS_CRIT <num>` (verifica se il codice corrisponde a `CHECKSUM_KO` tramite la funzione generata `e_codice_CHECKSUM_KO`), `TAB` e `STATS`, producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- espansione multipla della stessa X-macro `LISTA_CODICI(X)` per enum, tabella di metadati e funzioni predicato
- operatori `#` (stringificazione) e `##` (concatenazione di token) con macro di appoggio per l'espansione
- protezione di macro multi-istruzione tramite `do { ... } while (0)` senza punto e virgola finale
- macro variadiche C23 con `__VA_ARGS__` e `__VA_OPT__(,)` per gestire sia 0 sia N argomenti

**Domande guida**

1. Quale errore di sintassi o di flusso di controllo si verifica se una macro multi-istruzione viene racchiusa tra semplici graffe `{ ... }` anziché in `do { ... } while (0)` e viene usata nel ramo `if` di un `if-else`?
2. In che modo la X-macro `LISTA_CODICI(X)` elimina il rischio che l'enum `codice_diag_t` e l'array `TABELLA_CODICI` vadano fuori sincronia?
3. Quale problema della macro variadica `snprintf(buf, cap, fmt, __VA_ARGS__)` risolve in modo standard l'operatore C23 `__VA_OPT__(,)` quando non viene passato alcun argomento dopo `fmt`?
4. Perché per generare il nome `e_codice_CHECKSUM_KO` da una voce della X-macro occorre usare l'operatore `##`?

**Esempio di esecuzione**

```input
TAB
REG 101 2
REG 201 1
REG 999 1
PING SYS
IS_CRIT 201
IS_CRIT 102
STATS
```

```output
0: OK num=0 liv=INFO peso=0
1: DISCO_PIENO num=101 liv=ERR peso=5
2: IO_TIMEOUT num=102 liv=WARN peso=3
3: CHECKSUM_KO num=201 liv=CRIT peso=10
4: PERM_NEGATO num=202 liv=ERR peso=4
[ERR] DISCO_PIENO(#101) x2
[CRIT] CHECKSUM_KO(#201) x1
CODICE_IGNOTO: 999
[SYS] battito regolare
IS_CRIT(201): 1
IS_CRIT(102): 0
STATS: tot=2 gravita=20 [OK=0 DISCO_PIENO=1 IO_TIMEOUT=0 CHECKSUM_KO=1 PERM_NEGATO=0]
```

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

Quando organizzi una libreria sovraccaricata su più file, scegli il modello di collegamento tra i due introdotti nella sotto-sezione 19.3: usa **`static inline`** nell'header per piccoli helper privati di cui non serve un simbolo condiviso, oppure **`inline` nell'header + `extern inline` in un solo `.c`** per le funzioni pubbliche della libreria (garantendo un unico simbolo esterno anche con `-O0` o quando si usa un puntatore a funzione). Come ricordato nel capitolo 19, in C23 omettere `extern inline` per una funzione `inline` non-`static` usata con collegamento esterno provoca un errore del collegatore.

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

> **Approfondimento — Dettagli sulle conversioni nell'espressione di controllo di `_Generic`**
> Oltre alla conversione *lvalue* e al decadimento degli array già visti nella sotto-sezione 15.4 (per cui `int a[4]` combacia con `int *` e non con `int[4]`), ricorda un dettaglio tipico del C quando progetti macro sovraccaricate: un letterale carattere come `'a'` ha tipo `int` (non `char`) e seleziona quindi il ramo `int`. Verifica sempre quali tipi risultano dopo queste conversioni.

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

## 24.3 Salti non locali con `setjmp` e `longjmp`

L'istruzione `goto` vista nel capitolo 21 permette di saltare soltanto a un'etichetta nella **stessa funzione**. In un parser ricorsivo profondo o in un interprete, però, un errore di sintassi o un overflow può verificarsi dieci chiamate ricorsive più in basso: propagare un codice di errore attraverso ogni singolo livello con decine di `if` appesantisce il codice e rende facile dimenticare un controllo.

Per questi scenari mirati la libreria standard C fornisce `<setjmp.h>`, che consente un **salto non locale** (*non-local jump*): il trasferimento del controllo eseguito con `longjmp` verso un punto salvato in precedenza da `setjmp`, attraversando più chiamate di funzione sullo stack.

### Come funzionano `jmp_buf`, `setjmp` e `longjmp`

L'intestazione `<setjmp.h>` definisce il tipo `jmp_buf` (un tipo array che conserva lo stato dei registri e dello stack necessario a riprendere l'esecuzione) e due operazioni complementari:

- `int setjmp(jmp_buf env);` (una macro) salva il contesto corrente in `env` e restituisce `0` alla chiamata diretta.
- `[[noreturn]] void longjmp(jmp_buf env, int val);` ripristina il contesto salvato in `env`, scartando tutti i frame intermedi dello stack, e fa sembrare che la chiamata originaria a `setjmp(env)` ritorni una seconda volta con valore `val` (se passi `val == 0`, `setjmp` restituisce comunque `1` per non confondere il ripristino con la chiamata iniziale). `longjmp` non ritorna mai al proprio chiamante.

Lo schema d'uso tipico è un `if`:

<!-- cod: id=24.3-b tipo=frammento -->
```c
jmp_buf env;
if (setjmp(env) == 0) {
    // Percorso normale: qui una funzione chiamata può invocare longjmp(env, 1)
    analizza_tutto(&env);
} else {
    // Blocco di recupero: raggiunto solo dopo un longjmp
    gestisci_errore();
}
```

### Vincoli rigorosi dello standard C23

Poiché `setjmp` e `longjmp` manipolano direttamente lo stato basso-livello della CPU e dello stack, lo standard C23 impone vincoli severi la cui violazione provoca **comportamento indefinito**:

1. **Contesti sintattici ammessi per `setjmp`**: `setjmp` può comparire **soltanto** come intera espressione di controllo di `if`, `switch`, `while`, `do-while` o `for` — direttamente, oppure confrontata con una costante intera tramite un operatore relazionale o di uguaglianza (es. `if (setjmp(env) == 0)`), oppure come operando di `!` (sempre come intera espressione di controllo) — oppure come intera espressione di un'istruzione il cui valore viene scartato. Scrivere `int rc = setjmp(env);` è vietato dallo standard e provoca comportamento indefinito. Se vuoi sapere quale errore si è verificato, memorizza il codice e la posizione in una `struct` di contesto prima di chiamare `longjmp(env, 1)`.
2. **Validità del frame di destinazione**: è vietato chiamare `longjmp` verso un `jmp_buf` salvato da una funzione che è già ritornata. Quel frame dello stack non esiste più e saltarci dentro corrompe immediatamente il programma.
3. **Regola di `volatile` per le variabili locali**: quando il compilatore ottimizza la funzione che chiama `setjmp`, può tenere le variabili automatiche locali nei registri della CPU; al momento del `longjmp`, i registri vengono ripristinati allo stato che avevano al momento di `setjmp`. Pertanto, **qualunque variabile automatica locale non-`volatile` nella funzione che ha invocato `setjmp`, se viene modificata tra `setjmp` e `longjmp`, assume valore indeterminato dopo il salto** e leggerla provoca comportamento indefinito. Ogni variabile locale che modifichi dopo `setjmp` e leggi nel blocco di recupero va qualificata `volatile`.

### Gestione delle risorse e frame annidati

A differenza delle eccezioni di altri linguaggi, `longjmp` non esegue alcun codice di pulizia nei frame attraversati: se una funzione profonda ha allocato memoria con `malloc` o aperto un `FILE *` e poi viene eseguito un `longjmp`, quel puntatore viene perso per sempre causando una perdita di memoria o una perdita di descrittori.

Per usare `setjmp`/`longjmp` senza perdite esistono due strategie affidabili:

- Allocare tutte le strutture temporanee in un **allocatore ad arena** (capitolo 22) passato nel contesto e azzerare l'arena nel blocco di recupero.
- Registrare ogni allocazione dinamica in un piccolo elenco dentro la struttura di contesto del frame di errore, così che il gestore possa chiamare `free` su tutte le risorse tracciate sia sul percorso normale sia dopo `longjmp`.

Collegando tra loro più strutture di contesto tramite un puntatore `prec` (una pila di frame di errore) si possono anche annidare blocchi di recupero, in modo che un gestore interno intercetti errori specifici e rilanci quelli non gestiti al frame esterno dopo aver eseguito `pop` e rilasciato le proprie risorse.

> **Se vieni da Python** — In Python le eccezioni (`try`/`except`/`finally`) eseguono automaticamente la pulizia delle risorse tramite i context manager (`with`); in C `longjmp` salta direttamente i frame dello stack senza eseguire alcuna pulizia automatica, rendendo indispensabile il tracciamento esplicito delle risorse.

### Esempio guidato

Il programma seguente simula un parser di configurazione su tre livelli di chiamata (`esegui_parse` → `analizza_sezione` → `analizza_coppia`). Un contesto `ctx_parser_t` contiene `jmp_buf`, codice d'errore, riga incriminata e il puntatore a un buffer dinamico allocato durante il parsing. Quando il livello più profondo incontra un valore negativo o una riga malformata, invoca `segnala_errore` (`longjmp`), risalendo direttamente al chiamante `esegui_parse`, dove la variabile `volatile int fase` mantiene il proprio valore aggiornato e il buffer tracciato viene sempre liberato.

<!-- cod: id=24.3-a tipo=programma -->
```c
#include <setjmp.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct ctx_parser {
    jmp_buf env;
    const char *messaggio;
    int riga;
    char *buf_lavoro;
} ctx_parser_t;

[[noreturn]] static void segnala_errore(ctx_parser_t *ctx, const char *msg, int riga) {
    ctx->messaggio = msg;
    ctx->riga = riga;
    longjmp(ctx->env, 1);
}

static void analizza_coppia(ctx_parser_t *ctx, const char *testo, int riga) {
    int valore = 0;
    char chiave[16];
    if (sscanf(testo, "%15[^=]=%d", chiave, &valore) != 2) {
        segnala_errore(ctx, "formato chiave=valore non valido", riga);
    }
    if (valore < 0) {
        segnala_errore(ctx, "valore negativo non ammesso", riga);
    }
    printf("  riga %d OK: %s = %d\n", riga, chiave, valore);
}

static void analizza_sezione(ctx_parser_t *ctx, const char *const *righe, size_t n) {
    ctx->buf_lavoro = malloc(64);
    if (ctx->buf_lavoro == nullptr) {
        segnala_errore(ctx, "memoria esaurita", 0);
    }
    for (size_t i = 0; i < n; ++i) {
        snprintf(ctx->buf_lavoro, 64, "%s", righe[i]);
        analizza_coppia(ctx, ctx->buf_lavoro, (int)(i + 1));
    }
}

static void esegui_parse(ctx_parser_t *ctx, const char *nome,
                         const char *const *righe, size_t n) {
    ctx->messaggio = nullptr;
    ctx->riga = 0;
    ctx->buf_lavoro = nullptr;
    volatile int fase = 0;

    printf("Analisi %s:\n", nome);
    if (setjmp(ctx->env) == 0) {
        fase = 1;
        analizza_sezione(ctx, righe, n);
        fase = 2;
        free(ctx->buf_lavoro);
        printf("Esito %s: COMPLETATO (fase=%d)\n", nome, fase);
    } else {
        free(ctx->buf_lavoro);
        printf("Esito %s: ERRORE alla riga %d (fase=%d): %s\n",
               nome, ctx->riga, fase, ctx->messaggio);
    }
}

int main(void) {
    const char *ok_cfg[] = {"porta=8080", "timeout=30"};
    const char *ko_cfg[] = {"porta=8080", "timeout=-5", "retry=3"};
    ctx_parser_t ctx = {};

    esegui_parse(&ctx, "cfg_valida", ok_cfg, 2);
    esegui_parse(&ctx, "cfg_errata", ko_cfg, 3);
    return 0;
}
```

```output
Analisi cfg_valida:
  riga 1 OK: porta = 8080
  riga 2 OK: timeout = 30
Esito cfg_valida: COMPLETATO (fase=2)
Analisi cfg_errata:
  riga 1 OK: porta = 8080
Esito cfg_errata: ERRORE alla riga 2 (fase=1): valore negativo non ammesso
```

Nota come ogni regola dello standard è rispettata:

- `setjmp(ctx->env)` appare nella forma ammessa `if (setjmp(ctx->env) == 0)`.
- `fase` è qualificata `volatile int` perché viene modificata (`fase = 1;`) dopo `setjmp` e riletta nel ramo `else` dopo `longjmp`.
- `ctx` è definita in `main` e passata per puntatore a `esegui_parse` (quindi non è un oggetto automatico locale della funzione che chiama `setjmp`): i suoi campi modificati prima del salto (`ctx->buf_lavoro`, `ctx->riga`, `ctx->messaggio`) restano definiti dopo `longjmp`, e `free(ctx->buf_lavoro)` nel ramo `else` rilascia il blocco allocato dentro `analizza_sezione` senza alcuna perdita di memoria.
- La terza riga di `cfg_errata` (`retry=3`) non viene mai eseguita: il salto non locale interrompe immediatamente l'intera catena di chiamate.

> **Approfondimento — Quando preferire codici di ritorno e `goto cleanup`**
> Nella quasi totalità del codice C, i codici di ritorno espliciti abbinati allo schema `goto cleanup` (capitolo 21) sono più leggibili, più facili da seguire con il debugger e meno esposti a errori di gestione delle risorse. Riserva `setjmp`/`longjmp` ai casi in cui il guadagno di chiarezza è reale — come parser ricorsivi profondi o motori di interpretazione — e solo quando ogni allocazione temporanea è protetta da un'arena o da un registro esplicito di risorse.

### Esercizio 24.3 — Valutatore ricorsivo di espressioni con frame annidati `setjmp`/`longjmp`, `volatile` e pulizia risorse

**Descrizione**

Realizza su tre file (`errore_jmp.h`, `errore_jmp.c`, `main.c`) un meccanismo di recupero da errori profondi basato su **salti non locali** (`setjmp`/`longjmp`) annidati con tracciamento delle risorse dinamiche, applicato a un valutatore ricorsivo di espressioni intere a 64 bit (`+`, `-`, `*`, `/`, `-` unario e parentesi `(...)`, profondità massima di parentesi `8`). (1) In `errore_jmp.h` (protetto da `ERRORE_JMP_H`) definisci `cod_errore_t` (`ERR_NESSUNO`, `ERR_SINTASSI`, `ERR_PARENTESI`, `ERR_DIV_ZERO`, `ERR_OVERFLOW`, `ERR_PROFONDITA`, `ERR_MEMORIA`) e `typedef struct frame_err { jmp_buf env; struct frame_err *prec; cod_errore_t codice; size_t pos; void *risorse[8]; size_t n_risorse; } frame_err_t;`, e dichiara `void err_push(frame_err_t *f);`, `void err_pop(frame_err_t *f);`, `bool err_traccia(void *ptr);`, `void err_rilascia_risorse(frame_err_t *f);`, `[[noreturn]] void err_lancia(cod_errore_t cod, size_t pos);` e `const char *err_nome(cod_errore_t cod);`. (2) In `errore_jmp.c` gestisci una pila collegata di `frame_err_t`: `err_lancia` registra `cod` e `pos` nel frame corrente ed esegue `longjmp(top->env, 1)` (chiamando `abort()` se la pila è vuota). (3) In `main.c` usa sempre `setjmp` nei soli contesti ammessi dallo standard C23 (`if (setjmp(f.env) == 0)`), alloca dinamicamente una copia di lavoro dell'espressione registrandola con `err_traccia` così che venga sempre liberata anche dopo un `longjmp`, e usa variabili locali qualificate `volatile` quando modificate tra `setjmp` e `longjmp`. Gestisci da `stdin` i comandi `EVAL <expr>` e `TRY <expr1> | <expr2>` (in `TRY`, un frame interno intercetta `ERR_DIV_ZERO` ed `ERR_OVERFLOW` di `<expr1>` ripiegando su `<expr2>`, mentre rilancia al frame esterno gli errori di sintassi, parentesi o profondità), stampando al termine il riepilogo `RIEPILOGO: ok=<ok> fallback=<fb> err=<err>` esattamente come nell'esempio.

**Concetti da tenere a mente**

- uso rigoroso di `setjmp` solo nei contesti consentiti dallo standard C23 (`if (setjmp(env) == 0)`)
- qualificazione `volatile` delle variabili automatiche locali modificate tra `setjmp` e `longjmp`
- pila di frame `jmp_buf` annidati per intercettare errori specifici e rilanciare gli altri al frame esterno
- tracciamento e rilascio delle risorse allocate sullo heap per evitare perdite di memoria dopo `longjmp`

**Domande guida**

1. Perché in C23 scrivere `int rc = setjmp(f.env);` è comportamento indefinito e come si aggira il limite salvando il codice d'errore dentro `frame_err_t`?
2. Quale rischio si corre se dentro la funzione che chiama `setjmp` modifichi una variabile locale non-`volatile` `fase` prima di un `longjmp` e poi la leggi nel ramo `else`?
3. Che cosa succederebbe alla memoria allocata con `malloc` per la copia di lavoro dell'espressione se `longjmp` saltasse fuori dalla ricorsione senza il registro risorse di `frame_err_t`?
4. Perché `err_pop` deve essere chiamato sia sul percorso normale sia prima di rilanciare un errore al frame esterno?

**Esempio di esecuzione**

```input
EVAL (2 + 3) * 4 - 6 / 2
EVAL 10 / (5 - 5)
EVAL 9223372036854775807 + 1
TRY 100 / 0 | 40 + 2
TRY (1 + 2 | 99
EVAL (((((((((1)))))))))
```

```output
EVAL -> OK 17
EVAL -> ERRORE DIV_ZERO pos=3
EVAL -> ERRORE OVERFLOW pos=20
TRY -> FALLBACK(DIV_ZERO) OK 42
TRY -> ERRORE PARENTESI pos=6
EVAL -> ERRORE PROFONDITA pos=8
RIEPILOGO: ok=1 fallback=1 err=4
```

## 24.4 Liste intrusive con `offsetof`

Nel capitolo 17 hai implementato liste concatenate in cui ogni elemento viene avvolto dentro un nodo ausiliario `struct nodo { void *dato; struct nodo *prev; struct nodo *next; }`. Questo schema funziona bene per contenitori generici, ma ha due costi strutturali: ogni inserimento richiede una `malloc` separata per il nodo wrapper (anche quando l'oggetto esiste già sullo stack o in un pool), e se vuoi rimuovere un oggetto che già possiedi in memoria devi prima cercarlo nella lista per trovarne il nodo wrapper.

Nei sistemi operativi, nei motori di simulazione e nei programmi a bassa latenza si usa invece la **lista intrusiva** (*intrusive list*): una lista concatenata i cui puntatori di collegamento sono incorporati direttamente dentro le strutture ospitanti e recuperati con `offsetof`.

```text
Lista non intrusiva (2 blocchi per elemento):
  [ nodo: prev | next | dato ] ---> [ oggetto: id | nome | ... ]

Lista intrusiva (1 solo blocco per elemento):
  [ oggetto: id | nome | nodo_intrusivo(prev | next) | ... ]
                          ^
                          |  indirizzo noto durante l'iterazione;
                          |  sottraendo offsetof(oggetto, link)
                          +-- si risale all'inizio dell'oggetto
```

### Lista circolare doppiamente concatenata con testa sentinella

Il tipo di collegamento è una piccola struct di due puntatori:

<!-- cod: id=24.4-b tipo=frammento -->
```c
typedef struct nodo_intrusivo {
    struct nodo_intrusivo *prev;
    struct nodo_intrusivo *next;
} nodo_intrusivo_t;
```

Una lista intrusiva circolare usa una **testa sentinella** dello stesso tipo `nodo_intrusivo_t` che non appartiene ad alcun oggetto reale. Quando la lista è vuota, la sentinella punta a sé stessa (`testa->prev = testa; testa->next = testa;`). Questo elimina tutti i casi speciali per lista vuota, inserimento in testa, inserimento in coda e rimozione dell'ultimo elemento:

- **Inserimento in testa** (`O(1)`): inserisce il nodo subito dopo `testa`.
- **Inserimento in coda** (`O(1)`): inserisce il nodo subito prima di `testa` (cioè dopo `testa->prev`).
- **Rimozione** (`O(1)`): scollega `n` collegando direttamente `n->prev->next = n->next` e `n->next->prev = n->prev`, senza nemmeno conoscere quale sia la testa della lista. Riportando infine `n->prev = n; n->next = n;`, il nodo torna nello stato isolato e un'eventuale seconda chiamata a `lista_rimuovi(n)` risulta innocua.

### Recuperare la struttura ospitante con `offsetof`

Quando scorri la lista, il puntatore `pos` di tipo `nodo_intrusivo_t *` punta al campo incorporato dentro la struct ospitante, non all'inizio della struct. Come risali all'oggetto intero? Con `offsetof(tipo, campo)` (da `<stddef.h>`, introdotto nel capitolo 13), che restituisce la distanza esatta in byte tra l'inizio di `tipo` e il campo `campo`. Convertendo `ptr` in `unsigned char *` e sottraendo questo scostamento in byte ottieni l'indirizzo esatto della struct ospitante:

<!-- cod: id=24.4-c tipo=frammento -->
```c
#define CONTENITORE_DI(ptr, tipo, campo) \
    ((tipo *)((unsigned char *)(ptr) - offsetof(tipo, campo)))

#define CONTENITORE_DI_CONST(ptr, tipo, campo) \
    ((const tipo *)((const unsigned char *)(ptr) - offsetof(tipo, campo)))
```

Rispetto allo standard C23, `offsetof` e l'aritmetica su `unsigned char *` (o `const unsigned char *`) all'interno dello stesso oggetto `struct` sono completamente definiti. Tuttavia, applicare `CONTENITORE_DI` a un puntatore che **non** punta realmente al campo `campo` di una vera istanza di `tipo` — per esempio applicarlo per errore alla testa sentinella `testa` oppure al campo di una struct diversa — provoca **comportamento indefinito**.

### Più liste simultanee e iterazione sicura

Uno dei vantaggi più potenti delle liste intrusive è che una stessa `struct` può incorporare due o più campi `nodo_intrusivo_t` distinti (ad esempio `link_tutti` e `link_pronti`) e appartenere contemporaneamente a più liste indipendenti con una sola allocazione e senza interferenze tra i puntatori.

Per attraversare la lista si usano in genere tre macro:

<!-- cod: id=24.4-d tipo=frammento -->
```c
#define LISTA_PER_OGNI(pos, testa) \
    for (nodo_intrusivo_t *(pos) = (testa)->next; (pos) != (testa); (pos) = (pos)->next)

#define LISTA_PER_OGNI_CONST(pos, testa) \
    for (const nodo_intrusivo_t *(pos) = (testa)->next; (pos) != (testa); (pos) = (pos)->next)

#define LISTA_PER_OGNI_SICURO(pos, tmp, testa)                      \
    for (nodo_intrusivo_t *(pos) = (testa)->next, *(tmp) = (pos)->next; \
         (pos) != (testa);                                          \
         (pos) = (tmp), (tmp) = (pos)->next)
```

Fai molta attenzione quando rimuovi o liberi nodi durante il ciclo: se usi `LISTA_PER_OGNI` e nel corpo del ciclo chiami `lista_rimuovi(pos)` (che reimposta `pos->next = pos`) oppure `free` sull'oggetto ospitante, il passo finale `(pos) = (pos)->next` entra in un ciclo infinito o esegue un uso dopo la liberazione (**comportamento indefinito**). In questi casi devi usare `LISTA_PER_OGNI_SICURO`, che salva in anticipo il nodo successivo nella variabile `tmp` prima che il corpo del ciclo modifichi o liberi `pos`.

> **Se vieni da Python** — In Python le liste sono collezioni di riferimenti gestite dal runtime; in C le liste intrusive con `offsetof` incorporano i collegamenti direttamente negli oggetti per evitare allocazioni extra e permettere l'appartenenza simultanea a più liste.

### Esempio guidato

Il programma seguente gestisce una lista intrusiva circolare di sensori allocati interamente sullo stack (zero chiamate a `malloc`). Dopo aver inserito tre sensori e averli stampati risalendo alla struct ospitante tramite `CONTENITORE_DI`, rimuove in `O(1)` i sensori inattivi durante l'attraversamento con `LISTA_PER_OGNI_SICURO` e stampa l'elenco residuo.

<!-- cod: id=24.4-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

typedef struct nodo_intrusivo {
    struct nodo_intrusivo *prev;
    struct nodo_intrusivo *next;
} nodo_intrusivo_t;

#define CONTENITORE_DI(ptr, tipo, campo) \
    ((tipo *)((unsigned char *)(ptr) - offsetof(tipo, campo)))

#define LISTA_PER_OGNI(pos, testa) \
    for (nodo_intrusivo_t *(pos) = (testa)->next; (pos) != (testa); (pos) = (pos)->next)

#define LISTA_PER_OGNI_SICURO(pos, tmp, testa)                          \
    for (nodo_intrusivo_t *(pos) = (testa)->next, *(tmp) = (pos)->next; \
         (pos) != (testa);                                              \
         (pos) = (tmp), (tmp) = (pos)->next)

static void lista_init(nodo_intrusivo_t *n) {
    n->prev = n;
    n->next = n;
}

static void lista_inserisci_coda(nodo_intrusivo_t *testa, nodo_intrusivo_t *n) {
    n->prev = testa->prev;
    n->next = testa;
    testa->prev->next = n;
    testa->prev = n;
}

static void lista_rimuovi(nodo_intrusivo_t *n) {
    n->prev->next = n->next;
    n->next->prev = n->prev;
    lista_init(n);
}

typedef struct sensore {
    int id;
    const char *nome;
    bool attivo;
    nodo_intrusivo_t link;
} sensore_t;

static void stampa_sensori(const char *titolo, nodo_intrusivo_t *testa) {
    printf("%s:", titolo);
    LISTA_PER_OGNI(pos, testa) {
        sensore_t *s = CONTENITORE_DI(pos, sensore_t, link);
        printf(" #%d:%s(%s)", s->id, s->nome, s->attivo ? "ON" : "OFF");
    }
    printf("\n");
}

int main(void) {
    nodo_intrusivo_t elenco;
    lista_init(&elenco);

    sensore_t s1 = {.id = 1, .nome = "Temp", .attivo = true};
    sensore_t s2 = {.id = 2, .nome = "Press", .attivo = false};
    sensore_t s3 = {.id = 3, .nome = "Umid", .attivo = true};
    lista_init(&s1.link);
    lista_init(&s2.link);
    lista_init(&s3.link);

    lista_inserisci_coda(&elenco, &s1.link);
    lista_inserisci_coda(&elenco, &s2.link);
    lista_inserisci_coda(&elenco, &s3.link);
    stampa_sensori("Tutti", &elenco);

    LISTA_PER_OGNI_SICURO(pos, tmp, &elenco) {
        sensore_t *s = CONTENITORE_DI(pos, sensore_t, link);
        if (!s->attivo) {
            lista_rimuovi(&s->link);
        }
    }
    stampa_sensori("Attivi", &elenco);
    return 0;
}
```

```output
Tutti: #1:Temp(ON) #2:Press(OFF) #3:Umid(ON)
Attivi: #1:Temp(ON) #3:Umid(ON)
```

Osserva i punti chiave:

- Nessuna chiamata a `malloc` o `free`: i tre oggetti `sensore_t` vivono sullo stack, ma partecipano a una lista dinamica completa grazie al campo `link` incorporato.
- In `sensore_t`, `link` è l'ultimo campo: `CONTENITORE_DI(pos, sensore_t, link)` sottrae `offsetof(sensore_t, link)` all'indirizzo di `link` e recupera esattamente l'inizio della struttura `sensore_t`.
- Nel ciclo di filtro, `LISTA_PER_OGNI_SICURO` permette di scollegare `s2.link` in `O(1)` senza perdere il puntatore a `s3.link`.

> **Approfondimento — Liste intrusive nei sistemi operativi e nei sistemi embedded**
> Il kernel Linux e numerosi sistemi embedded fondano le proprie code interne proprio sulle liste intrusive. Eliminare l'allocazione separata dei nodi riduce la frammentazione dello heap, evita di dover gestire fallimenti di `malloc` quando si sposta un oggetto da una coda a un'altra e permette di sfruttare meglio la cache del processore tenendo vicini i byte dell'oggetto (lo vedremo nel capitolo 25). Inoltre, un singolo descrittore di processo può appartenere nello stesso istante alla lista globale dei task e alla coda di attesa di un dispositivo senza alcuna duplicazione.

### Esercizio 24.4 — Schedulatore di lavori con doppia lista intrusiva circolare basata su `offsetof`

**Descrizione**

Realizza su tre file (`lista_intr.h`, `lista_intr.c`, `main.c`) una **lista intrusiva** circolare doppiamente concatenata e applicala a uno schedulatore in cui ogni lavoro appartiene contemporaneamente a due liste distinte senza allocare nodi wrapper separati. (1) In `lista_intr.h` (protetto da `LISTA_INTR_H`) definisci `typedef struct nodo_intrusivo { struct nodo_intrusivo *prev; struct nodo_intrusivo *next; } nodo_intrusivo_t;`, le macro `CONTENITORE_DI(ptr, tipo, campo)` e `CONTENITORE_DI_CONST(ptr, tipo, campo)` (tramite `offsetof` e `unsigned char *`/`const unsigned char *`), le macro di attraversamento `LISTA_PER_OGNI(pos, testa)`, `LISTA_PER_OGNI_CONST(pos, testa)` e `LISTA_PER_OGNI_SICURO(pos, tmp, testa)`, e dichiara `void lista_init(nodo_intrusivo_t *n);`, `bool lista_vuota(const nodo_intrusivo_t *testa);`, `bool lista_collegato(const nodo_intrusivo_t *n);`, `void lista_inserisci_testa(nodo_intrusivo_t *testa, nodo_intrusivo_t *n);`, `void lista_inserisci_coda(nodo_intrusivo_t *testa, nodo_intrusivo_t *n);`, `void lista_rimuovi(nodo_intrusivo_t *n);` e `size_t lista_conta(const nodo_intrusivo_t *testa);`. (2) In `lista_intr.c` implementa le operazioni in tempo `O(1)` (`lista_rimuovi` scollega il nodo e lo riporta allo stato isolato `prev = next = n`). (3) In `main.c` definisci `typedef struct lavoro { uint32_t id; char nome[16]; int prio; bool pronto; nodo_intrusivo_t link_tutti; nodo_intrusivo_t link_pronti; } lavoro_t;` e mantieni le due liste `lista_tutti` e `coda_pronti`. Gestisci da `stdin` i comandi `ADD <id> <nome> <prio>` (inserisce sempre in coda a `lista_tutti` e in `coda_pronti` in testa se `prio >= 10` o in coda altrimenti), `PAUSE <id>` (rimuove in `O(1)` da `coda_pronti`), `RESUME <id>` (reinserisce in `coda_pronti` con la stessa regola di priorità), `DEL <id>` (rimuove da entrambe le liste e libera), `PURGE_PAUSED` (rimuove e libera in un solo passaggio tutti i lavori in pausa usando `LISTA_PER_OGNI_SICURO`) e `SHOW`, liberando tutti i lavori residui prima di terminare.

**Concetti da tenere a mente**

- incorporamento di due campi `nodo_intrusivo_t` nella stessa struct `lavoro_t` per appartenere a due liste con una sola allocazione
- recupero del puntatore alla struct ospitante tramite `offsetof` in `CONTENITORE_DI` e `CONTENITORE_DI_CONST`
- rimozione `O(1)` con `lista_rimuovi` senza conoscere la testa della lista
- iterazione sicura con `LISTA_PER_OGNI_SICURO` quando il corpo del ciclo rimuove e libera nodi

**Domande guida**

1. Perché un oggetto `lavoro_t` può essere inserito contemporaneamente in `lista_tutti` e in `coda_pronti` senza interferenze tra i puntatori `prev` e `next`?
2. Come fa `CONTENITORE_DI(pos, lavoro_t, link_pronti)` a risalire all'inizio di `lavoro_t` anche se `link_pronti` non è il primo campo della struct?
3. Che cosa succederebbe in `PURGE_PAUSED` se usassi `LISTA_PER_OGNI` anziché `LISTA_PER_OGNI_SICURO` per scollegare e liberare con `free` i lavori in pausa?
4. Perché in una lista circolare con sentinella un nodo scollegato viene riportato a `n->prev = n; n->next = n;`?

**Esempio di esecuzione**

```input
ADD 1 Backup 5
ADD 2 Rete 12
ADD 3 Log 3
SHOW
PAUSE 2
SHOW
RESUME 2
PAUSE 3
PURGE_PAUSED
DEL 1
SHOW
```

```output
TUTTI(3): #1:Backup(P) #2:Rete(P) #3:Log(P)
PRONTI(3): #2:Rete #1:Backup #3:Log
TUTTI(3): #1:Backup(P) #2:Rete(S) #3:Log(P)
PRONTI(2): #1:Backup #3:Log
PURGE_PAUSED: rimossi=1
DEL #1: OK
TUTTI(1): #2:Rete(P)
PRONTI(1): #2:Rete
```

## 24.5 Macchine a stati con tabelle di puntatori a funzione

Protocolli di rete, parser lessicali, interfacce di controllo industriale e gestori di sessione condividono la stessa struttura logica: il comportamento del programma non dipende solo dall'evento appena arrivato, ma anche dalla fase in cui il sistema si trova in quel momento. Il modello formale che cattura questa logica è la **macchina a stati finiti** (*finite-state machine*): un modello di calcolo che si trova in uno stato alla volta e cambia stato in base agli eventi in ingresso.

Scrivere una macchina a stati con `switch` annidati (`switch (stato)` dentro cui si apre uno `switch (evento)`) funziona finché gli stati sono due o tre, ma diventa rapidamente difficile da leggere, facile da rompere quando si aggiunge un evento e impossibile da ispezionare a colpo d'occhio. Estendendo le tabelle di dispatch del capitolo 16, puoi rappresentare l'intera macchina come **tabella bidimensionale costante di puntatori a funzione**.

### Anatomia della tabella di transizione

Una macchina a stati finiti è descritta da cinque elementi: un insieme finito di **stati**, un insieme finito di **eventi**, le **transizioni** ammesse da `(stato, evento)` verso il nuovo stato, le eventuali **azioni** eseguite durante la transizione (eventualmente condizionate da una **guardia** sul contesto) e gli **hook di ingresso** (*on-enter*) eseguiti quando la macchina entra in un nuovo stato.

Ecco la mappa tabellare di un tornello automatico con 3 stati e 4 eventi:

```text
Stato \ Evento | MONETA         | PASSAGGIO      | ALLARME      | RIPARA
---------------+----------------+----------------+--------------+--------------
BLOCCATO       | -> SBLOCCATO   | (rifiutato)    | -> GUASTO    | (rifiutato)
SBLOCCATO      | (rifiutato)    | -> BLOCCATO    | -> GUASTO    | (rifiutato)
GUASTO         | (rifiutato)    | (rifiutato)    | (rifiutato)  | -> BLOCCATO
```

In C questa tabella si traduce direttamente in due enumerazioni chiuse da un valore sentinella di conteggio (`ST_CONTEGGIO`, `EV_CONTEGGIO`) e in una matrice costante `static const transizione_t TABELLA[ST_CONTEGGIO][EV_CONTEGGIO]` popolata con inizializzatori designati:

<!-- cod: id=24.5-b tipo=frammento -->
```c
typedef struct transizione {
    bool valida;
    stato_t prossimo;
    azione_fn azione;
} transizione_t;

static const transizione_t TABELLA[ST_CONTEGGIO][EV_CONTEGGIO] = {
    [ST_BLOCCATO]  = { [EV_MONETA]    = {true, ST_SBLOCCATO, az_incassa},
                       [EV_ALLARME]   = {true, ST_GUASTO, az_allarme} },
    [ST_SBLOCCATO] = { [EV_PASSAGGIO] = {true, ST_BLOCCATO, az_passaggio},
                       [EV_ALLARME]   = {true, ST_GUASTO, az_allarme} },
    [ST_GUASTO]    = { [EV_RIPARA]    = {true, ST_BLOCCATO, az_ripara} }
};
```

Tutte le celle non nominate nell'inizializzatore vengono azzerate automaticamente dal compilatore (`valida = false`, `azione = nullptr`), rendendo esplicito e sicuro il rifiuto di ogni coppia non ammessa. Ogni array parallelo indicizzato per stato (come `NOMI_STATO` o la tabella degli hook `ON_ENTER`) va sempre protetto con `static_assert` affinché aggiungere uno stato senza aggiornare le tabelle fallisca subito in compilazione.

### Motore di transizione e guardie dinamiche

Con la tabella 2D, il motore di transizione non contiene alcuno `switch` ed esegue sempre gli stessi passi in tempo `O(1)`:

1. Verifica che il contesto non sia `nullptr` e che `stato < ST_CONTEGGIO` ed `evento < EV_CONTEGGIO`.
2. Legge `const transizione_t *t = &TABELLA[stato][evento];` e, se `!t->valida`, rifiuta esplicitamente l'evento.
3. Se `t->azione != nullptr`, invoca la funzione di azione passando il contesto e lo stato di destinazione predefinito `t->prossimo`.
4. Aggiorna lo stato corrente e, se il nuovo stato differisce dal precedente e `ON_ENTER[nuovo]` non è `nullptr`, invoca l'hook di ingresso.

Perché far restituire alla funzione di azione lo stato effettivo di destinazione? Perché permette di gestire le **guardie dinamiche** in modo pulito: nella maggior parte dei casi l'azione restituisce lo stato predefinito `def_st`, ma se una condizione di contesto scatta (ad esempio, il terzo errore di autenticazione consecutivo) l'azione può deviare la transizione verso uno stato alternativo (come `ST_BLOCCATA`), oppure segnalare tramite un flag booleano `ok` che l'evento va rifiutato senza cambiare stato.

Rispetto allo standard C23, gli array bidimensionali costanti di struct con puntatori a funzione e gli inizializzatori designati sono completamente definiti; tuttavia, indicizzare `TABELLA` con uno stato o un evento fuori dai limiti oppure invocare un puntatore a funzione nullo provoca **comportamento indefinito**. I controlli di confine e i controlli `!= nullptr` nel motore sono quindi obbligatori.

### Esempio guidato

Il programma seguente implementa il tornello automatico a 3 stati (`ST_BLOCCATO`, `ST_SBLOCCATO`, `ST_GUASTO`) e 4 eventi (`EV_MONETA`, `EV_PASSAGGIO`, `EV_ALLARME`, `EV_RIPARA`) usando una tabella bidimensionale `TABELLA[ST_CONTEGGIO][EV_CONTEGGIO]`, controlli `static_assert` sulle tabelle ausiliarie e un motore di transizione privo di `switch`.

<!-- cod: id=24.5-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

typedef enum stato { ST_BLOCCATO = 0, ST_SBLOCCATO, ST_GUASTO, ST_CONTEGGIO } stato_t;
typedef enum evento { EV_MONETA = 0, EV_PASSAGGIO, EV_ALLARME, EV_RIPARA, EV_CONTEGGIO } evento_t;

typedef struct tornello {
    stato_t stato;
    int monete;
    int passaggi;
} tornello_t;

typedef stato_t (*azione_fn)(tornello_t *t, stato_t def_st);
typedef struct transizione {
    bool valida;
    stato_t prossimo;
    azione_fn azione;
} transizione_t;

static const char *const NOMI_STATO[] = {"BLOCCATO", "SBLOCCATO", "GUASTO"};
static const char *const NOMI_EVENTO[] = {"MONETA", "PASSAGGIO", "ALLARME", "RIPARA"};
static_assert(sizeof(NOMI_STATO) / sizeof(NOMI_STATO[0]) == ST_CONTEGGIO);
static_assert(sizeof(NOMI_EVENTO) / sizeof(NOMI_EVENTO[0]) == EV_CONTEGGIO);

static stato_t az_moneta(tornello_t *t, stato_t def_st) {
    ++t->monete;
    printf(" [incasso moneta #%d]", t->monete);
    return def_st;
}

static stato_t az_passaggio(tornello_t *t, stato_t def_st) {
    ++t->passaggi;
    printf(" [passaggio #%d]", t->passaggi);
    return def_st;
}

static stato_t az_allarme(tornello_t *t, stato_t def_st) {
    (void)t;
    printf(" [blocco di sicurezza]");
    return def_st;
}

static stato_t az_ripara(tornello_t *t, stato_t def_st) {
    (void)t;
    printf(" [ripristino]");
    return def_st;
}

static const transizione_t TABELLA[ST_CONTEGGIO][EV_CONTEGGIO] = {
    [ST_BLOCCATO]  = { [EV_MONETA]    = {true, ST_SBLOCCATO, az_moneta},
                       [EV_ALLARME]   = {true, ST_GUASTO, az_allarme} },
    [ST_SBLOCCATO] = { [EV_PASSAGGIO] = {true, ST_BLOCCATO, az_passaggio},
                       [EV_ALLARME]   = {true, ST_GUASTO, az_allarme} },
    [ST_GUASTO]    = { [EV_RIPARA]    = {true, ST_BLOCCATO, az_ripara} }
};

static bool elabora(tornello_t *t, evento_t ev) {
    if (t == nullptr || t->stato >= ST_CONTEGGIO || ev >= EV_CONTEGGIO) { return false; }
    const transizione_t *tr = &TABELLA[t->stato][ev];
    if (!tr->valida) {
        printf("%s + %s -> RIFIUTATO\n", NOMI_STATO[t->stato], NOMI_EVENTO[ev]);
        return false;
    }
    printf("%s + %s", NOMI_STATO[t->stato], NOMI_EVENTO[ev]);
    stato_t dopo = (tr->azione != nullptr) ? tr->azione(t, tr->prossimo) : tr->prossimo;
    t->stato = dopo;
    printf(" -> %s\n", NOMI_STATO[dopo]);
    return true;
}

int main(void) {
    tornello_t t = {.stato = ST_BLOCCATO, .monete = 0, .passaggi = 0};
    const evento_t sequenza[] = {
        EV_PASSAGGIO, EV_MONETA, EV_PASSAGGIO, EV_ALLARME, EV_MONETA, EV_RIPARA
    };
    for (size_t i = 0; i < sizeof(sequenza) / sizeof(sequenza[0]); ++i) {
        elabora(&t, sequenza[i]);
    }
    printf("Totale: monete=%d passaggi=%d\n", t.monete, t.passaggi);
    return 0;
}
```

```output
BLOCCATO + PASSAGGIO -> RIFIUTATO
BLOCCATO + MONETA [incasso moneta #1] -> SBLOCCATO
SBLOCCATO + PASSAGGIO [passaggio #1] -> BLOCCATO
BLOCCATO + ALLARME [blocco di sicurezza] -> GUASTO
GUASTO + MONETA -> RIFIUTATO
GUASTO + RIPARA [ripristino] -> BLOCCATO
Totale: monete=1 passaggi=1
```

Osserva quanto è compatto il motore `elabora`: controlla i limiti, consulta la cella `TABELLA[t->stato][ev]` in tempo costante, rifiuta gli eventi non validi e invoca il puntatore a funzione solo se diverso da `nullptr`. L'intera semantica del tornello è leggibile in cinque righe dentro `TABELLA`.

> **Approfondimento — Tabella 2D contro tabella di funzioni per stato**
> Una matrice `Stati x Eventi` rende immediatamente verificabile ogni coppia `(stato, evento)` quando il numero di stati ed eventi è contenuto (fino a una decina ciascuno). Se invece progetti una macchina con decine di eventi sparsi — dove quasi tutte le celle sarebbero vuote — una matrice 2D sprecherebbe memoria: in quel caso conviene usare un array monodimensionale di funzioni indicizzato per stato (ogni funzione gestisce solo gli eventi rilevanti per quello stato) oppure una lista di transizioni per stato.

### Esercizio 24.5 — Macchina a stati finiti opaca per sessioni di rete con tabella 2D di puntatori a funzione e guardie

**Descrizione**

Realizza su tre file (`fsm_sess.h`, `fsm_sess.c`, `main.c`) una **macchina a stati finiti** come **tipo opaco** `fsm_sess_t` che gestisce il ciclo di vita di una sessione autenticata mediante una tabella bidimensionale `static const transizione_t TABELLA[ST_CONTEGGIO][EV_CONTEGGIO]` priva di qualsiasi `switch` nel motore di transizione. (1) In `fsm_sess.h` (protetto da `FSM_SESS_H`) definisci `stato_sess_t` (`ST_CHIUSA`, `ST_HANDSHAKE`, `ST_AUTH`, `ST_ATTIVA`, `ST_BLOCCATA`, `ST_CONTEGGIO`), `evento_sess_t` (`EV_APRI`, `EV_ACK`, `EV_AUTH_OK`, `EV_AUTH_KO`, `EV_DATO`, `EV_CHIUDI`, `EV_RESET`, `EV_CONTEGGIO`) e `typedef struct fsm_sess fsm_sess_t;`, dichiarando `fsm_sess_t *fsm_crea(void);`, `void fsm_distruggi(fsm_sess_t *f);`, `bool fsm_invia(fsm_sess_t *f, evento_sess_t ev, int32_t payload);`, `stato_sess_t fsm_stato(const fsm_sess_t *f);`, `const char *fsm_nome_stato(stato_sess_t s);` e `void fsm_stampa_stats(const fsm_sess_t *f);`. (2) In `fsm_sess.c` verifica con `static_assert` le dimensioni delle tabelle `NOMI_STATO` e `ON_ENTER`. Le transizioni valide sono: `CHIUSA + APRI -> HANDSHAKE`; `HANDSHAKE + ACK -> AUTH` (azzera `err_auth`), `HANDSHAKE + CHIUDI -> CHIUSA`; `AUTH + AUTH_OK -> ATTIVA`, `AUTH + AUTH_KO -> AUTH` (con guardia nell'azione: al 3° errore consecutivo devia verso `ST_BLOCCATA`), `AUTH + CHIUDI -> CHIUSA`; `ATTIVA + DATO -> ATTIVA` (accetta `payload > 0` sommandolo a `byte_tx` e incrementando `pacchetti`; se `payload <= 0` rifiuta il pacchetto senza cambiare stato), `ATTIVA + CHIUDI -> CHIUSA`; `BLOCCATA + RESET -> CHIUSA` (azzera `err_auth`). Quando lo stato cambia invoca l'hook `ON_ENTER[nuovo_stato]` (`ATTIVA` incrementa `sessioni_ok`, `BLOCCATA` incrementa `blocchi`). (3) In `main.c` leggi da `stdin` i comandi `EV <nome> [payload]` (`payload` predefinito `0`), `STATO` e `STATS`, producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- tabella bidimensionale `static const transizione_t[ST_CONTEGGIO][EV_CONTEGGIO]` con inizializzatori designati
- motore di transizione privo di `switch` con validazione rigorosa degli indici di stato ed evento
- azioni di transizione capaci di deviare lo stato di destinazione tramite guardie sul contesto
- hook `ON_ENTER` invocati al cambio di stato e controlli a tempo di compilazione con `static_assert`

**Domande guida**

1. In che modo la tabella 2D `TABELLA[stato][evento]` gestisce le coppie `(stato, evento)` non ammesse senza causare comportamento indefinito?
2. Come riesce l'azione di `EV_AUTH_KO` nello stato `ST_AUTH` a mantenere la transizione dentro la tabella 2D pur portando la macchina in `ST_BLOCCATA` solo al terzo fallimento?
3. Perché l'hook `ON_ENTER[nuovo_stato]` va invocato solo quando `nuovo_stato != vecchio_stato`?
4. Che cosa garantiscono le `static_assert` sugli array `NOMI_STATO` e `ON_ENTER` se in futuro aggiungi un nuovo stato all'enum `stato_sess_t`?

**Esempio di esecuzione**

```input
STATO
EV DATO 50
EV APRI
EV ACK
EV AUTH_KO
EV AUTH_OK
EV DATO 120
EV DATO 0
EV DATO 80
EV CHIUDI
EV APRI
EV ACK
EV AUTH_KO
EV AUTH_KO
EV AUTH_KO
EV APRI
EV RESET
STATS
```

```output
STATO: CHIUSA
EV DATO: RIFIUTATO (stato=CHIUSA)
EV APRI: CHIUSA -> HANDSHAKE
EV ACK: HANDSHAKE -> AUTH
EV AUTH_KO: AUTH -> AUTH
EV AUTH_OK: AUTH -> ATTIVA
EV DATO: ATTIVA -> ATTIVA
EV DATO: RIFIUTATO (stato=ATTIVA)
EV DATO: ATTIVA -> ATTIVA
EV CHIUDI: ATTIVA -> CHIUSA
EV APRI: CHIUSA -> HANDSHAKE
EV ACK: HANDSHAKE -> AUTH
EV AUTH_KO: AUTH -> AUTH
EV AUTH_KO: AUTH -> AUTH
EV AUTH_KO: AUTH -> BLOCCATA
EV APRI: RIFIUTATO (stato=BLOCCATA)
EV RESET: BLOCCATA -> CHIUSA
STATS: stato=CHIUSA sess_ok=1 blocchi=1 pkt=2 byte=200 rifiutati=3
```

## 24.6 Formati binari compatti con campi di bit

Nel capitolo 13 hai incontrato i campi di bit, le unioni etichettate e l'ordine dei byte. Quando un programma deve mantenere in RAM milioni di record compatti — come nodi di un interprete, voci di una tabella di pagina o descrittori di pacchetti di telemetria — risparmiare anche pochi byte per oggetto riduce drasticamente il consumo di memoria. Al tempo stesso, molti di questi oggetti vanno poi salvati su file o trasmessi in rete secondo un formato binario preciso.

È qui che si commette uno degli errori più insidiosi del C: confondere la **rappresentazione in memoria** (ottimizzata per la macchina locale) con il **formato binario su cavo o file** (che deve essere identico su ogni architettura).

### Campi di bit avanzati e verifica con `static_assert`

Richiamando le regole sui campi di bit già introdotte nella sotto-sezione 13.4 — usare sempre tipi con segno esplicito (`unsigned int`, `signed int` o `bool`, mai `int` semplice) e ricorrere all'occorrenza a campi anonimi (`unsigned int : 3;`) o a separatori di unità (`unsigned int : 0;`) — in un formato compatto reale conviene affiancare una **verifica a tempo di compilazione** con `static_assert`, ad esempio `static_assert(sizeof(data_ora_bf_t) == sizeof(unsigned int));`, per accorgersi subito se un nuovo campo fa sforare la parola di 32 bit.

Abbinando un'intestazione a campi di bit con un'**unione etichettata** (il cui tag risiede proprio in uno dei campi di bit dell'intestazione), puoi rappresentare in pochissimi byte pacchetti binari con payload di tipo variabile: la `struct` occupa soltanto lo spazio dell'intestazione più il ramo più grande della `union`, invece della somma di tutti i possibili payload.

### Perché non si serializzano mai i byte grezzi di una struct a campi di bit

Una volta compattata un'intestazione in 32 bit con `sizeof(intestazione_bf_t) == 4`, la tentazione di copiarla direttamente in un buffer di rete con `memcpy` o di rileggerla come `uint32_t` tramite una `union` è fortissima:

<!-- cod: id=24.6-b tipo=frammento -->
```c
// ERRORE DI PORTABILITÀ: NON SCRIVERE COSÌ!
// L'ordine dei bit, il padding tra unità e l'ordine dei byte dipendono dall'implementazione.
uint8_t buffer[4];
memcpy(buffer, &hdr, sizeof(buffer)); // NON portabile su file o rete!
```

Questo codice non è portabile per i motivi già analizzati nel capitolo 13 (sotto-sezioni 13.4 e 13.5): ordine di impacchettamento dei bit, padding tra unità e ordine dei byte (*endianness*) sono **dipendenti dall'implementazione**; inoltre, tentare di rileggere i byte con un puntatore di tipo incompatibile viola le regole di *strict aliasing* (capitolo 22).

### Separare il modello in memoria dal codec portabile

La soluzione pulita separa nettamente due responsabilità:

- **Modello in memoria**: una `struct` a campi di bit (eventualmente affiancata da una `union` etichettata) per lavorare in modo espressivo e compatto dentro il programma (`hdr.versione`, `hdr.tipo`, `hdr.seq`).
- **Codec di serializzazione e deserializzazione**: due funzioni esplicite che convertono la `struct` verso e da un buffer `uint8_t[]` in un ordine dei byte fissato dal protocollo (tipicamente **big-endian**), usando esclusivamente spostamenti e maschere di bit su tipi senza segno (`uint32_t`, `uint16_t`, `uint8_t`).

Nei protocolli reali, al buffer serializzato si aggiunge un controllo di integrità come un **CRC-8** (un codice ridondante ciclico su 8 bit calcolato con spostamenti e XOR rispetto a un polinomio generatore fissato, ad esempio `0x07`), che in fase di decodifica va sempre verificato **prima** di interpretare i campi estratti.

Secondo lo standard C23, la semantica dei campi di bit senza segno, delle unioni etichettate e degli spostamenti su tipi senza segno è completamente definita; l'ordine di impacchettamento dei bit, il padding tra unità e il segno di `int` semplice nei campi di bit sono invece **dipendenti dall'implementazione**.

### Esempio guidato

Il programma seguente rappresenta una data e ora compatta in 32 bit (`data_ora_bf_t`: anno relativo al 2000 su 7 bit, mese su 4, giorno su 5, ora su 5, minuto su 6, doppio-secondo su 5, totale 32 bit), verifica con `static_assert` che la struct occupi una sola parola `unsigned int`, e implementa un codec portabile big-endian in un buffer `uint8_t[4]` verificando che codifica e decodifica restituiscano esattamente i campi originali.

<!-- cod: id=24.6-a tipo=programma -->
```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef struct data_ora_bf {
    unsigned int anno_off : 7;  // 0..127 -> 2000..2127
    unsigned int mese : 4;      // 1..12
    unsigned int giorno : 5;    // 1..31
    unsigned int ora : 5;       // 0..23
    unsigned int minuto : 6;    // 0..59
    unsigned int sec_div2 : 5;  // 0..29 -> secondi pari 0..58
} data_ora_bf_t;

static_assert(sizeof(data_ora_bf_t) == sizeof(unsigned int));

static void codifica_be(const data_ora_bf_t *d, uint8_t out[4]) {
    uint32_t parola = ((uint32_t)d->anno_off << 25) |
                      ((uint32_t)d->mese << 21) |
                      ((uint32_t)d->giorno << 16) |
                      ((uint32_t)d->ora << 11) |
                      ((uint32_t)d->minuto << 5) |
                      (uint32_t)d->sec_div2;
    out[0] = (uint8_t)(parola >> 24);
    out[1] = (uint8_t)(parola >> 16);
    out[2] = (uint8_t)(parola >> 8);
    out[3] = (uint8_t)parola;
}

static data_ora_bf_t decodifica_be(const uint8_t in[4]) {
    uint32_t parola = ((uint32_t)in[0] << 24) |
                      ((uint32_t)in[1] << 16) |
                      ((uint32_t)in[2] << 8) |
                      (uint32_t)in[3];
    data_ora_bf_t d = {
        .anno_off = (parola >> 25) & 0x7FU,
        .mese = (parola >> 21) & 0x0FU,
        .giorno = (parola >> 16) & 0x1FU,
        .ora = (parola >> 11) & 0x1FU,
        .minuto = (parola >> 5) & 0x3FU,
        .sec_div2 = parola & 0x1FU
    };
    return d;
}

int main(void) {
    data_ora_bf_t orig = {
        .anno_off = 26, .mese = 11, .giorno = 24,
        .ora = 17, .minuto = 35, .sec_div2 = 15
    };
    uint8_t filo[4] = {};
    codifica_be(&orig, filo);

    printf("Buffer big-endian: %02" PRIx8 " %02" PRIx8 " %02" PRIx8 " %02" PRIx8 "\n",
           filo[0], filo[1], filo[2], filo[3]);

    data_ora_bf_t dec = decodifica_be(filo);
    printf("Decodificato: %04u-%02u-%02u %02u:%02u:%02u\n",
           2000U + dec.anno_off, dec.mese, dec.giorno,
           dec.ora, dec.minuto, dec.sec_div2 * 2U);

    bool ok = (dec.anno_off == orig.anno_off) && (dec.mese == orig.mese) &&
              (dec.giorno == orig.giorno) && (dec.ora == orig.ora) &&
              (dec.minuto == orig.minuto) && (dec.sec_div2 == orig.sec_div2);
    printf("Consistenza round-trip: %s\n", ok ? "OK" : "ERRORE");
    return 0;
}
```

```output
Buffer big-endian: 35 78 8c 6f
Decodificato: 2026-11-24 17:35:30
Consistenza round-trip: OK
```

Osserva come `codifica_be` e `decodifica_be` non dipendono in alcun modo dal layout fisico dei campi di bit nella memoria della CPU: impacchettano e disimpacchettano esplicitamente la parola a 32 bit con spostamenti e maschere senza segno, producendo sempre gli stessi quattro byte `35 78 8c 6f` su qualsiasi architettura.

> **Approfondimento — Dove i campi di bit brillano davvero**
> I campi di bit danno il massimo nelle strutture puramente interne al processo: nodi di interpreti e compilatori, stati di simulatori, tabelle di pagina e cache dove milioni di oggetti piccoli convivono in RAM. Ogni volta che i dati devono uscire dalla memoria del processo (su disco o in rete), affiancare un codec esplicito a spostamenti e maschere ti permette di mantenere entrambi i vantaggi: compattezza in memoria e portabilità assoluta del formato binario.

### Esercizio 24.6 — Codec binario portabile per frame di telemetria con intestazione a campi di bit, unione etichettata e CRC-8

**Descrizione**

Realizza su tre file (`frame_bin.h`, `frame_bin.c`, `main.c`) un codec binario compatto che separa rigorosamente la rappresentazione in memoria (campi di bit + unione etichettata) dalla serializzazione portabile big-endian su buffer di byte con verifica CRC-8. (1) In `frame_bin.h` (protetto da `FRAME_BIN_H`) definisci `tipo_frame_t` (`FRM_PING = 0`, `FRM_SENSORE = 1`, `FRM_COMANDO = 2`, `FRM_ERRORE = 3`), `esito_frame_t` (`FRM_OK`, `FRM_ERR_LEN`, `FRM_ERR_CRC`, `FRM_ERR_VER`, `FRM_ERR_PAYLOAD`), la struct a campi di bit `intestazione_bf_t` con esattamente 32 bit (`unsigned int versione : 2; tipo : 2; priorita : 2; cifrato : 1; ack : 1; src : 6; dst : 6; len : 4; seq : 8;`, verificata con `static_assert(sizeof(intestazione_bf_t) == sizeof(unsigned int))`), l'unione `payload_frame_t` (`sensore { int16_t temp_d; uint16_t umid_d; }`, `comando { uint8_t op; uint8_t arg; }`, `errore { uint16_t cod; }`) e `frame_t { intestazione_bf_t hdr; payload_frame_t dati; }`. Dichiara `uint8_t frame_crc8(const uint8_t *buf, size_t n);` (polinomio `0x07`, stato iniziale `0x00`), `size_t frame_codifica(const frame_t *f, uint8_t *out, size_t cap);` e `esito_frame_t frame_decodifica(const uint8_t *buf, size_t n, frame_t *out);`. (2) In `frame_bin.c` serializza i 32 bit dell'intestazione in big-endian (`bit 31..30 = versione`, `29..28 = tipo`, `27..26 = priorita`, `25 = cifrato`, `24 = ack`, `23..18 = src`, `17..12 = dst`, `11..8 = len`, `7..0 = seq`), seguiti dal payload big-endian (`PING`: 0 byte, `SENSORE`: 4 byte, `COMANDO`: 2 byte, `ERRORE`: 2 byte) e dal byte finale `CRC-8` calcolato su tutti i byte precedenti. `frame_decodifica` rifiuta lunghezze `< 5` o `> 9` (`FRM_ERR_LEN`), CRC errato (`FRM_ERR_CRC`), `versione != 1` (`FRM_ERR_VER`), lunghezza dichiarata incoerente col tipo (`FRM_ERR_PAYLOAD`) o buffer di dimensione diversa da `5 + hdr.len` (`FRM_ERR_LEN`), ricostruendo `temp_d` in complemento a due senza UB. (3) In `main.c` gestisci da `stdin` i comandi `ENC_PING`, `ENC_SENS`, `ENC_CMD`, `ENC_ERR` (con `versione = 1`) e `DEC <n> <hex0> ... <hex{n-1}>`, riproducendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- rappresentazione in memoria compatta tramite campi di bit `unsigned int` e unione etichettata
- verifica a tempo di compilazione della compattezza della struct con `static_assert`
- serializzazione e deserializzazione big-endian portabile con spostamenti e maschere senza copiare byte grezzi della struct
- calcolo e verifica del codice di integrità CRC-8 e controllo di versione e lunghezza del payload

**Domande guida**

1. Perché non puoi serializzare `frame_t` con una semplice `memcpy(out, &f->hdr, 4)` anche se `sizeof(intestazione_bf_t)` vale 4 sulla tua macchina?
2. Come ricostruisci in modo portabile il valore con segno `int16_t temp_d` dai due byte big-endian del payload senza incorrere in comportamento indefinito?
3. Perché nella decodifica conviene verificare il byte CRC-8 prima di fidarsi dei campi `versione`, `tipo` e `len` estratti dall'intestazione?
4. Quale vantaggio offre combinare `intestazione_bf_t` con l'unione etichettata `payload_frame_t` rispetto a una struct che contenga separatamente tutti i possibili campi di tutti i tipi di frame?

**Esempio di esecuzione**

```input
ENC_PING 2 0 1 5 12 7
ENC_SENS 3 1 0 10 20 42 -125 645
ENC_CMD 1 0 1 1 2 9 16 250
DEC 5 49 14 c0 07 cc
DEC 9 5e 29 44 2a ff 83 02 85 39
DEC 5 49 14 c0 07 00
DEC 5 89 14 c0 07 66
```

```output
ENC(5): 49 14 c0 07 cc
ENC(9): 5e 29 44 2a ff 83 02 85 39
ENC(7): 65 04 22 09 10 fa 28
DEC OK: v=1 PING prio=2 cif=0 ack=1 5->12 seq=7
DEC OK: v=1 SENS prio=3 cif=1 ack=0 10->20 seq=42 temp=-125 umid=645
DEC ERR: CRC
DEC ERR: VER
```

## Riepilogo

- Le macro multi-istruzione vanno sempre racchiuse in `do { ... } while (0)` senza punto e virgola finale, così da comportarsi come una singola istruzione anche dentro `if (...) MACRO(); else ...`. Gli operatori `#` (stringificazione) e `##` (concatenazione di token) richiedono un doppio livello di espansione quando ricevono altre macro come argomenti; in C23 `__VA_OPT__(...)` rende portabili le macro variadiche con zero o più argomenti extra. Le **X-macro** definiscono una sola lista `LISTA(X)` espansa più volte per mantenere sincronizzati enumerazioni, tabelle e funzioni.
- Combinando `_Generic((x), T1: f1, T2: f2)(x, ...)` con funzioni `static inline` (o `inline` nell'header più `extern inline` in un solo file `.c`) si ottiene un sovraccarico statico sul tipo a costo zero, con valutazione unica degli argomenti e possibilità di preservare `const` distinguendo `T *` e `const T *`.
- Con `<setjmp.h>` (`jmp_buf`, `setjmp`, `[[noreturn]] longjmp`) si realizzano **salti non locali** attraverso più frame dello stack. `setjmp` va usata solo nei contesti sintattici consentiti (come `if (setjmp(env) == 0)`), ogni variabile automatica locale modificata tra `setjmp` e `longjmp` e riletta dopo il salto va qualificata `volatile`, e le risorse allocate sullo heap vanno tracciate esplicitamente perché `longjmp` non esegue codice di pulizia nei frame saltati.
- Una **lista intrusiva** circolare incorpora `nodo_intrusivo_t` (`prev`, `next`) direttamente nella struttura ospitante: elimina le allocazioni dei nodi wrapper, consente rimozioni in `O(1)` e permette l'appartenenza simultanea a più liste. Il puntatore alla struct ospitante si recupera con `CONTENITORE_DI` tramite `offsetof` e aritmetica su `unsigned char *`; la rimozione durante l'attraversamento richiede l'iterazione sicura (`LISTA_PER_OGNI_SICURO`).
- Una **macchina a stati finiti** si modella senza `switch` tramite una tabella bidimensionale costante `static const transizione_t TABELLA[ST_CONTEGGIO][EV_CONTEGGIO]` con inizializzatori designati, verifiche `static_assert` sulle dimensioni, controlli espliciti dei limiti, azioni con guardie dinamiche e hook di ingresso `ON_ENTER`.
- I campi di bit (`unsigned int`, `signed int`, `bool`, mai `int` semplice) e le unioni etichettate garantiscono rappresentazioni in memoria compatte verificabili con `static_assert`, ma l'ordine dei bit, il padding e l'ordine dei byte dipendono dall'implementazione: verso file o rete occorre sempre un codec esplicito con spostamenti, maschere di bit in ordine fissato e controllo di integrità (come CRC-8).

## Errori comuni

- **Racchiudere una macro multi-istruzione tra semplici graffe `{ ... }` invece di `do { ... } while (0)` (oppure mettere un `;` finale nella definizione)**: nel ramo `if` di un `if-else` il punto e virgola extra spezza il costrutto causando un errore di compilazione.
- **Scrivere `int rc = setjmp(env);` oppure dimenticare `volatile` sulle variabili locali modificate prima di un `longjmp`**: entrambi i casi violano i vincoli dello standard C23 e provocano comportamento indefinito.
- **Allocare memoria con `malloc` o aprire file in funzioni interne senza registrarli prima di un `longjmp`**: il salto non locale bypassa tutti i frame intermedi causando perdite di memoria silenziose.
- **Applicare `CONTENITORE_DI` alla testa sentinella della lista intrusiva, oppure rimuovere e liberare nodi con `LISTA_PER_OGNI` anziché `LISTA_PER_OGNI_SICURO`**: la sentinella non è contenuta in alcuna struct ospitante, e leggere `pos->next` dopo la rimozione o la liberazione provoca cicli infiniti o uso dopo la liberazione.
- **Indicizzare la tabella 2D di una macchina a stati senza verificare i limiti di stato ed evento o senza controllare `azione != nullptr`**: un indice fuori intervallo o la chiamata di un puntatore nullo causano comportamento indefinito.
- **Serializzare i byte grezzi di una struct a campi di bit con `memcpy` o `fwrite`**: ordine dei bit, padding ed endianness variano tra compilatori e architetture; usa sempre spostamenti e maschere esplicite.

## Prima di proseguire

- [ ] So scrivere macro multi-istruzione sicure con `do-while(0)`, macro variadiche C23 con `__VA_OPT__` e X-macro per sincronizzare enum, tabelle e funzioni.
- [ ] So progettare interfacce sovraccaricate con `_Generic` e funzioni `inline`/`extern inline` che valutano gli argomenti una sola volta e preservano `const`.
- [ ] So usare `setjmp` e `longjmp` rispettando i contesti sintattici ammessi, la qualificazione `volatile` e il rilascio deterministico delle risorse tracciate.
- [ ] So implementare una lista intrusiva circolare con `offsetof`, gestire l'appartenenza simultanea a più liste e rimuovere elementi in sicurezza durante l'iterazione.
- [ ] So costruire una macchina a stati finiti priva di `switch` basata su una tabella bidimensionale di puntatori a funzione con guardie e hook di ingresso.
- [ ] So combinare campi di bit e unioni etichettate per la compattezza in RAM separandoli da un codec big-endian portabile con verifica CRC-8.
