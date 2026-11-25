## 15.5 `typeof`, `auto` e `static_assert`

Quando scrivi codice generico o strutture binarie con vincoli precisi di dimensione e allineamento, emergono due bisogni ricorrenti: dichiarare variabili temporanee che abbiano esattamente il tipo di un'altra espressione (senza ripeterlo a mano) e trasformare le assunzioni sul programma in controlli verificati dal compilatore prima ancora di produrre l'eseguibile. Lo standard C23 risponde a entrambi i bisogni con quattro strumenti nativi: `typeof`, `typeof_unqual`, `auto` e `static_assert`.

### Ricavare un tipo con `typeof` e `typeof_unqual`

L'operatore C23 **`typeof(expr)`** (applicabile sia a un'espressione sia a un nome di tipo) restituisce il tipo esatto di `expr` a tempo di compilazione, **senza valutare `expr`** a tempo di esecuzione. Puoi usarlo ovunque serva uno specificatore di tipo, per esempio per dichiarare una variabile di appoggio nello scambio di due elementi puntati da `a` e `b`:

<!-- cod: id=15.5-b tipo=frammento -->
```c
typeof(*a) tmp = *a;
*a = *b;
*b = tmp;
```

Se cambi il tipo di `a` e `b`, la dichiarazione di `tmp` si adatta automaticamente.

C'è però un caso in cui `typeof` conserva *troppo*: `typeof(expr)` mantiene tutti i qualificatori di primo livello dell'espressione, in particolare `const`. Se hai un parametro `const uint64_t limite` e scrivi `typeof(limite) copia = limite;`, anche `copia` risulta `const uint64_t` e il compilatore ti impedirà di modificarla (`++copia` genera un errore di compilazione).

Per risolvere questo problema, C23 affianca a `typeof` l'operatore **`typeof_unqual(expr)`**, che rimuove i qualificatori di primo livello (come `const`) e produce un tipo modificabile:

<!-- cod: id=15.5-c tipo=frammento -->
```c
const uint64_t limite = 100;
typeof_unqual(limite) copia = limite;  // tipo: uint64_t (modificabile)
++copia;                               // valido!
```

> **C23** — Gli operatori `typeof` e `typeof_unqual` sono stati standardizzati in C23. Nei compilatori più vecchi (C11/C17) non fanno parte dello standard (esisteva solo l'estensione non portabile `__typeof__` di GCC/Clang, priva di `typeof_unqual`): con compilatori anteriori a C23 occorre scrivere esplicitamente il nome del tipo desiderato.

### Inferenza statica del tipo con `auto`

In C23 la parola chiave **`auto`** permette al compilatore di dedurre automaticamente il tipo di una singola variabile dal suo inizializzatore, interamente a tempo di compilazione:

<!-- cod: id=15.5-d tipo=frammento -->
```c
auto somma = (uint64_t)0;       // tipo dedotto: uint64_t
auto media = somma / 4.0;       // tipo dedotto: double
```

Le regole di `auto` in C23 sono rigorose:
- ogni dichiarazione con `auto` deve avere un **inizializzatore** (scrivere `auto x;` senza valore iniziale è un errore di compilazione);
- in C23 `auto` dichiara una **singola variabile** (non elenchi di più variabili con tipi misti);
- il tipo dedotto viene fissato definitivamente a tempo di compilazione (rimuovendo i qualificatori di primo livello dell'inizializzatore e applicando il decadimento degli array).

Usa `auto` con giudizio: è utile quando il tipo è già evidente dall'inizializzatore (per esempio `auto somma = (uint64_t)0;` o il valore di ritorno di una funzione dal nome chiaro) o per evitare di ripetere tipi lunghi. Quando invece l'inizializzatore è un letterale semplice come `0` (che ha tipo `int`, non `size_t` né `uint64_t`), scrivere il tipo esplicito o un cast chiaro evita sorprese silenziose sui tipi interi.

> **C23** — Prima del C23, `auto` era una vecchia parola chiave ereditata dalle origini del C che indicava la durata di vita automatica delle variabili locali (già predefinita e quasi mai scritta). C23 ha ridefinito `auto` come deduzione di tipo: su compilatori C11/C17 questa sintassi non è supportata e devi sempre scrivere il tipo esplicito.

> **Se vieni da Python** — In Python una variabile non ha tipo fisso e può cambiare tipo a ogni assegnamento; in C23 la parola chiave `auto` deduce un tipo statico definitivo dall'inizializzatore al momento della compilazione.

### Verifiche a tempo di compilazione: `static_assert`

Quando progetti strutture binarie o tabelle indicizzate da un `enum`, molte ipotesi devono essere vere *prima* ancora di eseguire il programma: per esempio che un byte sia di 8 bit (`CHAR_BIT == 8`), che una `struct` non abbia padding imprevisto (`sizeof(record_t) == 16`), che l'offset di un campo sia quello atteso (`offsetof(...)`), oppure che un array di etichette contenga esattamente tante voci quanti sono i valori dell'`enum`.

Per trasformare queste ipotesi in controlli automatici esiste l'**asserzione statica** (*static assertion*): un controllo verificato dal compilatore con `static_assert` che interrompe la compilazione se una condizione costante è falsa.

In C23 `static_assert` è una parola chiave nativa (non richiede di includere alcun header) e accetta due forme:
- **due argomenti**: `static_assert(condizione, "messaggio");`
- **un solo argomento** (novità C23): `static_assert(condizione);`

La condizione deve essere un'**espressione costante intera** valutabile a tempo di compilazione (non una variabile ordinaria letta da input). Se la condizione è vera, `static_assert` non produce alcun codice macchina e ha costo zero a tempo di esecuzione; se è falsa, la compilazione si arresta subito con un errore di compilazione.

> **C23** — In C11 e C17 la parola chiave nativa era `_Static_assert` e richiedeva obbligatoriamente due argomenti (condizione e messaggio); per scrivere `static_assert` occorreva includere l'header delle asserzioni. In C23 `static_assert` è diventata una parola chiave nativa del linguaggio e il messaggio diagnostico è diventato opzionale.

### Asserzione statica contro controlli a tempo di esecuzione

Distingui bene i due livelli di verifica:
- **`static_assert`** controlla proprietà note **a tempo di compilazione** (dimensioni `sizeof`, allineamenti `alignof`, spiazzamenti `offsetof`, limiti come `CHAR_BIT`, coerenza tra `enum` e array statici). Se fallisce, l'eseguibile non viene nemmeno creato.
- I **controlli a tempo di esecuzione** (`if`, validazione dell'input, controllo di `nullptr`) verificano valori che dipendono dai dati forniti mentre il programma gira (nel capitolo 21 introdurremo anche le asserzioni a tempo di esecuzione con `assert`).

### Esempio guidato

Il programma C23 seguente definisce un'enumerazione di stati, un array parallelo di nomi e una struttura compatta `voce_log_t`. Verifica il layout e la sincronizzazione con `static_assert` (sia a due argomenti sia a un argomento), usa `typeof` per scambiare due strutture, `typeof_unqual` per creare una copia modificabile di un parametro `const` e `auto` per le variabili locali verificandone il tipo dedotto con `_Generic`.

<!-- cod: id=15.5-a tipo=programma -->
```c
#include <inttypes.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef enum livello : uint8_t {
    LIV_INFO = 0,
    LIV_AVVISO = 1,
    LIV_ERRORE = 2,
    LIV_CONTEGGIO = 3
} livello_t;

static const char *const NOMI_LIVELLO[] = {"INFO", "AVVISO", "ERRORE"};

typedef struct voce_log {
    uint64_t istante;
    uint32_t codice;
    uint16_t durata_ms;
    uint8_t livello;
    uint8_t priorita;
} voce_log_t;

static_assert(CHAR_BIT == 8, "Sono richiesti byte da 8 bit");
static_assert(sizeof(voce_log_t) == 16, "voce_log_t deve occupare 16 byte");
static_assert(alignof(voce_log_t) >= alignof(uint64_t));
static_assert(offsetof(voce_log_t, codice) == 8 && offsetof(voce_log_t, priorita) == 15);
static_assert(sizeof(NOMI_LIVELLO) / sizeof(NOMI_LIVELLO[0]) == LIV_CONTEGGIO,
              "NOMI_LIVELLO non sincronizzato con livello_t");

void scambia_voci(voce_log_t *a, voce_log_t *b) {
    typeof(*a) tmp = *a;
    *a = *b;
    *b = tmp;
}

uint32_t calcola_punteggio(const voce_log_t *v, const uint32_t base) {
    typeof_unqual(base) fattore = base;
    if (v->priorita > 0U) {
        ++fattore;
    }
    auto risultato = (uint32_t)v->durata_ms * fattore;
    return risultato;
}

int main(void) {
    voce_log_t a = {.istante = 200, .codice = 12, .durata_ms = 30,
                    .livello = LIV_AVVISO, .priorita = 1};
    voce_log_t b = {.istante = 100, .codice = 5, .durata_ms = 20,
                    .livello = LIV_INFO, .priorita = 0};

    if (b.istante < a.istante) {
        scambia_voci(&a, &b);
    }

    auto punti_a = calcola_punteggio(&a, 2U);
    auto punti_b = calcola_punteggio(&b, 2U);
    const char *tipo_punti = _Generic(punti_a, uint32_t: "uint32_t", default: "altro");

    printf("Layout verificato: sizeof(voce_log_t)=%zu, tipo punti=%s\n",
           sizeof(voce_log_t), tipo_punti);
    printf("Prima voce: ts=%" PRIu64 " #%u [%s] punti=%" PRIu32 "\n",
           a.istante, a.codice, NOMI_LIVELLO[a.livello], punti_a);
    printf("Seconda voce: ts=%" PRIu64 " #%u [%s] punti=%" PRIu32 "\n",
           b.istante, b.codice, NOMI_LIVELLO[b.livello], punti_b);
    return 0;
}
```

```output
Layout verificato: sizeof(voce_log_t)=16, tipo punti=uint32_t
Prima voce: ts=100 #5 [INFO] punti=40
Seconda voce: ts=200 #12 [AVVISO] punti=90
```

Esaminiamo come lavorano insieme i quattro strumenti C23:
- Le cinque `static_assert` controllano ipotesi critiche sul programma già in fase di compilazione: se in futuro aggiungessi un quarto valore a `livello_t` dimenticando di aggiornare `NOMI_LIVELLO`, il compilatore ti avviserebbe immediatamente bloccando la compilazione.
- In `scambia_voci`, `typeof(*a) tmp = *a;` dichiara `tmp` con il tipo esatto di `*a` (`voce_log_t`).
- In `calcola_punteggio`, il parametro `base` è `const uint32_t`: usando `typeof_unqual(base) fattore = base;`, otteniamo una copia locale di tipo `uint32_t` priva del qualificatore `const`, così `++fattore;` compila senza errori.
- Le variabili `risultato`, `punti_a` e `punti_b` usano `auto`: il compilatore deduce `uint32_t` come confermato dall'espressione `_Generic` stampata in uscita.

> **Approfondimento — `auto` in C23 non introduce tipizzazione dinamica**
> Chi proviene da linguaggi come Python o JavaScript talvolta interpreta `auto` come una variabile capace di contenere valori di qualsiasi tipo. In C23 non è affatto così: `auto` è soltanto un'abbreviazione sintattica risolta interamente dal compilatore. Una volta dedotto `uint32_t` per `punti_a`, quella variabile resta `uint32_t` per tutta la sua durata di vita e il codice macchina generato è identico a quello prodotto scrivendo `uint32_t punti_a = ...;`.

### Esercizio 15.5 — Verificatore di pacchetti C23 con `static_assert`, `typeof`, `typeof_unqual` e `auto`

**Descrizione**

Scrivi un programma C23 che definisca `typedef enum stato_pkt : uint8_t { PKT_OK = 0, PKT_ATTESA = 1, PKT_ERRORE = 2, PKT_CONTEGGIO = 3 } stato_pkt_t;`, l'array costante `static const char *const NOMI_STATO[] = {"OK", "ATTESA", "ERRORE"};` e la struttura compatta `typedef struct pacchetto { uint64_t timestamp; uint32_t id; uint16_t lunghezza; uint8_t stato; uint8_t flag; } pacchetto_t;`. Inserisci cinque `static_assert` (usando sia la forma a due argomenti sia la forma C23 a un solo argomento) per verificare a tempo di compilazione: `CHAR_BIT == 8`, `sizeof(pacchetto_t) == 16`, `alignof(pacchetto_t) >= alignof(uint64_t)`, `offsetof(pacchetto_t, id) == 8 && offsetof(pacchetto_t, flag) == 15` e `sizeof(NOMI_STATO) / sizeof(NOMI_STATO[0]) == PKT_CONTEGGIO`. Implementa:

1. `void scambia_pacchetti(pacchetto_t *a, pacchetto_t *b)` usando `typeof(*a) tmp = *a;`;
2. `uint64_t peso_pacchetto(const pacchetto_t *p, const uint64_t fattore)` che usa `typeof_unqual(fattore) molt = fattore;` (rimuovendo `const` per poter incrementare `molt` di `1` quando `p->flag != 0`) e `auto ris = (uint64_t)p->lunghezza * molt;`.

In `main` leggi dalla prima riga `n` (`1 <= n <= 32`) e dalle successive `n` righe `timestamp id lunghezza stato flag` (`stato` in `0..2`, `lunghezza <= UINT16_MAX`, `flag <= UINT8_MAX`). Alloca `pacchetto_t *elenco` con `calloc`, ordina i pacchetti in ordine crescente di `timestamp` (e a parità per `id` crescente) tramite `scambia_pacchetti`, accumula `auto somma_len = (uint64_t)0;` e `auto somma_pond = (uint64_t)0;` (con `fattore = 2`) verificando il tipo dedotto da `auto` con `_Generic(somma_len, uint64_t: "uint64_t", default: "altro")`, stampa l'esito delle verifiche, i pacchetti ordinati e i totali esattamente come nell'esempio e libera la memoria.

**Concetti da tenere a mente**

- asserzione statica con `static_assert` (a uno e a due argomenti in C23) su `sizeof`, `alignof`, `offsetof` e `CHAR_BIT`
- `typeof(*a)` per dichiarare variabili temporanee coerenti con il tipo puntato
- `typeof_unqual(fattore)` per rimuovere `const` di primo livello e creare una copia modificabile
- inferenza statica del tipo con `auto` in C23 verificata a tempo di compilazione con `_Generic`

**Domande guida**

1. Che cosa succederebbe in `peso_pacchetto` se scrivessi `typeof(fattore) molt = fattore;` invece di `typeof_unqual(fattore) molt = fattore;` e poi tentassi `++molt`?
2. Quale errore protegge in modo automatico la `static_assert` su `sizeof(NOMI_STATO) / sizeof(NOMI_STATO[0]) == PKT_CONTEGGIO`?
3. Perché le cinque `static_assert` non aggiungono alcun costo di esecuzione al programma compilato?
4. Come mai in `auto somma_len = (uint64_t)0;` serve il cast esplicito `(uint64_t)0` se vuoi garantire che il tipo inferito sia `uint64_t`?

**Esempio di esecuzione**

```input
3
200 102 50 1 0
100 105 80 0 3
100 101 20 2 1
```

```output
Verifiche static_assert: superate (sizeof=16)
Tipo somma_len (auto): uint64_t
#101 ts=100 len=20 stato=ERRORE flag=1 pond=60
#105 ts=100 len=80 stato=OK flag=3 pond=240
#102 ts=200 len=50 stato=ATTESA flag=0 pond=100
Totale lunghezza: 150, totale ponderato: 400
```
