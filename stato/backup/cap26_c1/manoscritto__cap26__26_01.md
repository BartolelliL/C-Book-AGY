## 26.1 Progettare il linguaggio e le strutture dati

Prima di scrivere una sola riga di codice di un interprete occorre decidere con precisione *che cosa* accetta il linguaggio e *come* il programma C rappresenta in memoria i dati e la struttura del codice letto. Progettare bene i tipi all'inizio evita di dover riscrivere mezzo programma quando aggiungerai il controllo di flusso e le funzioni.

Il linguaggio che costruiamo in questo capitolo si chiama **MiniL**, un piccolo linguaggio imperativo con sintassi ispirata al C. MiniL dispone di nove parole chiave (`var`, `if`, `else`, `while`, `fn`, `return`, `stampa`, `true`, `false`), commenti di riga introdotti da `//` fino al carattere di a capo, operatori aritmetici (`+`, `-`, `*`, `/`, `%`), relazionali (`==`, `!=`, `<`, `<=`, `>`, `>=`), logici (`&&`, `||`, `!`) e tre categorie di valori a tempo di esecuzione:

- interi con segno a 64 bit (`int64_t`);
- booleani (`bool`, rappresentati dai letterali `true` e `false`);
- un valore `nullo`, prodotto per esempio da una funzione che termina senza restituire un valore esplicito.

Un programma MiniL non viene eseguito direttamente sul testo grezzo: leggere e rileggere caratteri dentro un ciclo `while` sarebbe lento, fragile e difficile da estendere. L'architettura classica di un interprete suddivide il lavoro in tre stadi indipendenti, ciascuno con un ingresso e un'uscita ben definiti:

```text
  codice sorgente (char *)
            |
            v
  [ Analizzatore lessicale ]   --> sequenza di token (riga, colonna, tipo)
            |
            v
  [ Analizzatore sintattico ]  --> albero di sintassi astratta (nodi su arena)
            |
            v
  [ Valutatore ]               --> ambiente di esecuzione (tabelle hash) + output
```

Il punto di snodo tra analisi ed esecuzione è l'**albero di sintassi astratta** (*Abstract Syntax Tree*, AST): la rappresentazione ad albero della struttura grammaticale di un programma, costruita dall'analizzatore sintattico ed eseguita dal valutatore. Ogni nodo dell'albero rappresenta un costrutto preciso — un letterale intero, una somma binaria, una dichiarazione `var`, un ciclo `while`, una chiamata di funzione — liberato da dettagli puramente testuali come spazi, commenti o parentesi di raggruppamento.

Per rappresentare in C oggetti che possono assumere forme diverse a seconda del caso (come un valore MiniL o un nodo dell'AST) lo strumento ideale è l'**unione etichettata** vista nel capitolo 13: una `struct` che affianca un campo `enum` (l'etichetta che indica la variante attiva) a una `union` che contiene i dati specifici di ciascuna variante. Per i valori a tempo di esecuzione otteniamo:

<!-- cod: id=26.1-b tipo=frammento -->
```c
typedef enum tipo_valore {
    VAL_NULLO,
    VAL_INT,
    VAL_BOOL
} tipo_valore_t;

typedef struct valore {
    tipo_valore_t tipo;
    union {
        int64_t intero;
        bool booleano;
    } dati;
} valore_t;
```

Lo stesso schema si applica ai nodi dell'albero di sintassi astratta (`nodo_t`): un `enum` elenca tutte le specie di nodi (`NODO_INT`, `NODO_BOOL`, `NODO_VAR`, `NODO_UNARIO`, `NODO_BINARIO`, `NODO_IF`, `NODO_WHILE`, `NODO_FN`, `NODO_CHIAMATA`, e così via), mentre la `union` raccoglie i campi pertinenti a ciascun nodo. Con un'`asserzione statica` (`static_assert`, capitolo 15) puoi verificare già in fase di compilazione che la dimensione di `valore_t` o di `nodo_t` resti compatta e non cresca per errore se aggiungi un campo troppo grande a una variante della `union`.

La regola fondamentale di sicurezza sulle unioni etichettate è tassativa: **prima di leggere un campo della `union` occorre sempre controllare l'etichetta `tipo` tramite `switch` o `if`**. Secondo lo standard C23, accedere a un campo di una `union` diverso dall'ultimo scritto (salvo casi particolari su prefissi comuni di `struct`) produce comportamento non specificato o indefinito.

Un'altra decisione architetturale cruciale riguarda il **possesso della memoria** dell'AST. Un programma MiniL di poche decine di righe genera facilmente centinaia di nodi `nodo_t` e di copie di identificatori. Allocare ogni singolo nodo con `malloc` comporta tre svantaggi concreti: frammenta lo heap con molte allocazioni minuscole, costringe a scrivere un distruttore ricorsivo che liberi correttamente ogni variante della `union`, e rende delicata la pulizia se l'analizzatore sintattico si arresta per un errore a metà della costruzione dell'albero.

Osserva però il ciclo di vita di tutti i nodi dell'AST: nascono durante l'analisi sintattica, restano immutabili durante la valutazione e cessano di servire tutti nello stesso istante, quando l'esecuzione termina. Questa è esattamente la situazione per cui nel capitolo 22 hai costruito l'**allocatore ad arena**. L'arena riserva un blocco contiguo di byte allineato ad `alignof(max_align_t)` e serve ogni richiesta `arena_alloca` in tempo `O(1)` semplicemente arrotondando l'indice `usati` al multiplo successivo di `alignof(max_align_t)` e avanzandolo della dimensione richiesta (verificando gli overflow di `size_t` con `ckd_add`). Quando l'interprete ha finito — sia dopo un'esecuzione riuscita sia dopo un errore sintattico — una singola chiamata `arena_distruggi` (o `arena_reset` per riutilizzare il buffer) libera l'intero albero in un colpo solo, senza distruttori ricorsivi e senza alcun rischio di perdita di memoria. Anche in questo caso lo standard C23 garantisce la validità dell'allocazione allineata su un buffer di `unsigned char`, mentre accedere a un nodo dopo la distruzione o il reset dell'arena provoca **comportamento indefinito** (uso dopo la liberazione).

> **C23** — In C23 `alignof`, `alignas`, `bool`, `true`, `false`, `nullptr` e `static_assert` sono parole chiave native del linguaggio: non servono header aggiuntivi come quelli usati in C11/C17, e `<stdckdint.h>` fornisce `ckd_add` per verificare gli overflow di aritmetica sugli indici dell'arena.

Infine, per mantenere il codice leggibile e compilabile separatamente (capitolo 19), l'interprete MiniL è suddiviso in moduli con dipendenze **acicliche** (ogni modulo dipende solo dai livelli inferiori, mai circolarmente):

```text
  arena.h/c          tabella_hash.h/c       test_fw.h
      \                     |                  |
       +----> valore.h/c    |                  |
                |           |                  |
                v           |                  |
            lexer.h/c       |                  |
                |           |                  |
                v           |                  |
            parser.h/c      |                  |
                \          /                   |
                 v        v                    |
                  eval.h/c                     |
                     \                        /
                      v                      v
                              main.c
```

Tutti gli errori — lessicali, sintattici o di esecuzione — condividono una sola struttura `errore_t` contenente `bool attivo`, `size_t riga`, `size_t col` e un buffer fisso `char msg[128]`. In questo modo qualunque stadio può segnalare un problema con coordinate precise senza dover allocare stringhe di errore sullo heap proprio nel momento in cui la memoria potrebbe scarseggiare.

> **Se vieni da Python** — In Python l'interprete è già integrato nel linguaggio (puoi persino ispezionare l'albero sintattico con il modulo `ast`) e un raccoglitore di memoria automatico gestisce tutti gli oggetti; in C costruisci esplicitamente ogni stadio e scegli la strategia di memoria più adatta a ciascuna struttura, come un'arena per l'AST e tabelle hash opache per gli ambienti.

### Esempio guidato

Questo esempio su tre file (`ast_demo.h`, `ast_demo.c`, `main.c`) costruisce il nucleo essenziale di un'arena su buffer statico allineato ad `alignof(max_align_t)` e definisce `valore_t` e un piccolo nodo AST `nodo_demo_t` con unione etichettata. Il programma assembla manualmente l'albero dell'espressione `-(3 + 4 * 2)`, lo stampa in notazione prefissa, verifica i byte occupati nell'arena e infine azzera l'arena con `arena_reset`.

<!-- cod: id=26.1-a tipo=programma gruppo=ast_demo file=ast_demo.h -->
```c
#ifndef AST_DEMO_H
#define AST_DEMO_H

#include <stddef.h>
#include <stdint.h>

typedef struct arena_demo {
    unsigned char *buf;
    size_t cap;
    size_t usati;
} arena_demo_t;

typedef enum tipo_nodo {
    ND_INT,
    ND_NEG,
    ND_BIN
} tipo_nodo_t;

typedef struct nodo_demo nodo_demo_t;

struct nodo_demo {
    tipo_nodo_t tipo;
    union {
        int64_t intero;
        const nodo_demo_t *figlio;
        struct {
            char op;
            const nodo_demo_t *sx;
            const nodo_demo_t *dx;
        } bin;
    } dati;
};

static_assert(sizeof(nodo_demo_t) <= 32, "nodo_demo_t troppo grande");

void *arena_alloca(arena_demo_t *a, size_t dim);
void arena_reset(arena_demo_t *a);
void stampa_prefissa(const nodo_demo_t *n);

#endif
```

<!-- cod: id=26.1-c tipo=programma gruppo=ast_demo file=ast_demo.c -->
```c
#include "ast_demo.h"
#include <inttypes.h>
#include <stdckdint.h>
#include <stdio.h>

void *arena_alloca(arena_demo_t *a, size_t dim) {
    if (a == nullptr || a->buf == nullptr || dim == 0) {
        return nullptr;
    }
    size_t allin = alignof(max_align_t);
    size_t somma = 0;
    size_t fine = 0;
    if (ckd_add(&somma, a->usati, allin - 1)) {
        return nullptr;
    }
    size_t inizio = somma & ~(allin - 1);
    if (ckd_add(&fine, inizio, dim) || fine > a->cap) {
        return nullptr;
    }
    a->usati = fine;
    return a->buf + inizio;
}

void arena_reset(arena_demo_t *a) {
    if (a != nullptr) {
        a->usati = 0;
    }
}

void stampa_prefissa(const nodo_demo_t *n) {
    if (n == nullptr) {
        return;
    }
    switch (n->tipo) {
        case ND_INT:
            printf("%" PRId64, n->dati.intero);
            break;
        case ND_NEG:
            printf("(- ");
            stampa_prefissa(n->dati.figlio);
            printf(")");
            break;
        case ND_BIN:
            printf("(%c ", n->dati.bin.op);
            stampa_prefissa(n->dati.bin.sx);
            printf(" ");
            stampa_prefissa(n->dati.bin.dx);
            printf(")");
            break;
    }
}
```

<!-- cod: id=26.1-d tipo=programma gruppo=ast_demo file=main.c -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include "ast_demo.h"

static alignas(max_align_t) unsigned char memoria[1024];

static nodo_demo_t *crea_int(arena_demo_t *a, int64_t v) {
    nodo_demo_t *n = arena_alloca(a, sizeof(*n));
    if (n != nullptr) {
        *n = (nodo_demo_t){.tipo = ND_INT, .dati.intero = v};
    }
    return n;
}

int main(void) {
    arena_demo_t arena = {.buf = memoria, .cap = sizeof(memoria), .usati = 0};
    nodo_demo_t *n3 = crea_int(&arena, 3);
    nodo_demo_t *n4 = crea_int(&arena, 4);
    nodo_demo_t *n2 = crea_int(&arena, 2);
    nodo_demo_t *mul = arena_alloca(&arena, sizeof(*mul));
    nodo_demo_t *somma = arena_alloca(&arena, sizeof(*somma));
    nodo_demo_t *radice = arena_alloca(&arena, sizeof(*radice));
    if (!n3 || !n4 || !n2 || !mul || !somma || !radice) {
        return EXIT_FAILURE;
    }
    *mul = (nodo_demo_t){.tipo = ND_BIN, .dati.bin = {'*', n4, n2}};
    *somma = (nodo_demo_t){.tipo = ND_BIN, .dati.bin = {'+', n3, mul}};
    *radice = (nodo_demo_t){.tipo = ND_NEG, .dati.figlio = somma};

    stampa_prefissa(radice);
    printf("\n");
    printf("Nodi allocati: 6, byte usati > 0: %s\n", arena.usati > 0 ? "si" : "no");
    arena_reset(&arena);
    printf("Dopo reset: usati=%zu\n", arena.usati);
    return 0;
}
```

```output
(- (+ 3 (* 4 2)))
Nodi allocati: 6, byte usati > 0: si
Dopo reset: usati=0
```

Osserva i punti chiave di questa struttura su tre file:

- `ast_demo.h` è protetto dalla protezione di inclusione `AST_DEMO_H` e contiene la `static_assert` sulla dimensione di `nodo_demo_t`, così da accorgersi subito se una nuova variante della `union` fa esplodere l'occupazione di ogni nodo.
- In `ast_demo.c`, `arena_alloca` allinea l'offset iniziale a `alignof(max_align_t)` usando `ckd_add` per escludere overflow aritmetici e restituisce `nullptr` se la capacità residua non basta.
- In `stampa_prefissa` il controllo `switch (n->tipo)` garantisce che venga letto sempre e solo il campo della `union` corrispondente all'etichetta attiva.
- In `main.c`, il buffer statico è dichiarato con `alignas(max_align_t)` così che l'indirizzo di base `memoria` sia allineato quanto il tipo più restrittivo della piattaforma. Dopo `arena_reset(&arena)` i sei nodi risultano rilasciati all'istante senza alcuna chiamata ricorsiva a `free`, e i vecchi puntatori (`radice`, `somma`, ecc.) non vanno più dereferenziati.

> **Approfondimento — Perché l'arena semplifica la gestione degli errori**
> In un analizzatore sintattico un errore di sintassi può comparire in qualsiasi momento, per esempio dopo aver già allocato trenta nodi per un'espressione complessa e una lista di argomenti. Con `malloc` individuali, ogni funzione del parser dovrebbe intercettare `nullptr`, liberare tutti i sottoalberi già creati e propagare il fallimento senza dimenticare un solo ramo. Con un allocatore ad arena, invece, in caso di errore il parser si limita a registrare il messaggio in `errore_t` e a restituire `nullptr`: la funzione chiamante libererà l'intera arena in un'unica istruzione.

### Esercizio 26.1 — Costruttore di AST tipizzato su arena con unioni etichettate e verifica dei tipi

**Descrizione**

Realizza su tre file (`arena_ast.h`, `arena_ast.c`, `main.c`) il nucleo di strutture dati per un **albero di sintassi astratta** di espressioni tipizzate allocato su un **allocatore ad arena**. (1) In `arena_ast.h` (protetto da `ARENA_AST_H`) definisci `arena_ast_t` (su buffer allocato una sola volta con `malloc`), `tipo_val_t` (`TV_INT`, `TV_BOOL`, `TV_ERR`), `tipo_nodo_t` (`N_INT`, `N_BOOL`, `N_ADD`, `N_MUL`, `N_EQ`, `N_NOT`, `N_TERN`) e la **unione etichettata** `nodo_expr_t` con i campi adatti a ciascuna variante (`int64_t val_int`, `bool val_bool`, coppia `sx`/`dx`, operando `unario`, terna `cond`/`ramo_v`/`ramo_f`). Dichiara `arena_ast_init`, `arena_ast_distruggi`, `arena_ast_alloca` (allineata ad `alignof(max_align_t)` con controllo di overflow tramite `ckd_add`), `arena_ast_reset`, `nodo_verifica_tipo`, `nodo_conta` e `nodo_profondita`. (2) In `arena_ast.c` implementa l'arena e le visite ricorsive sull'albero: `N_ADD` e `N_MUL` richiedono due operandi `TV_INT` e producono `TV_INT`; `N_EQ` richiede due operandi dello stesso tipo valido (`TV_INT` o `TV_BOOL`) e produce `TV_BOOL`; `N_NOT` richiede `TV_BOOL` e produce `TV_BOOL`; `N_TERN` richiede condizione `TV_BOOL` e due rami dello stesso tipo valido, restituendo quel tipo (in ogni altro caso restituisce `TV_ERR`). (3) In `main.c` inizializza un'arena da `4096` byte e una tabella di `32` slot `const nodo_expr_t *slot[32]` e leggi da `stdin` i comandi: `INT <id> <val>`, `BOOL <id> <0|1>`, `BIN <id> <ADD|MUL|EQ> <sx> <dx>`, `NOT <id> <figlio>`, `TERN <id> <c> <v> <f>`, `INFO <id>` (stampa numero di nodi, profondità e tipo inferito, oppure `VUOTO` se lo slot è nullo) e `RESET` (azzera arena e slot). Verifica l'allineamento di ogni nodo con `uintptr_t` e libera l'arena prima di uscire, producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- unione etichettata (`enum` + `union`) per rappresentare varianti diverse di nodi dell'albero di sintassi astratta
- allocatore ad arena con arrotondamento ad `alignof(max_align_t)` e controllo di overflow tramite `ckd_add`
- visita ricorsiva di un albero per calcolare numero di nodi, profondità e verifica dei tipi
- rilascio globale in `O(1)` con reset e distruzione unica dell'arena senza perdite di memoria

**Domande guida**

1. Perché conviene allocare tutti i nodi di tipo `nodo_expr_t` dentro un'arena anziché chiamare `malloc` per ogni singolo nodo?
2. Quale controllo devi fare prima di accedere a `n->dati.tern.cond` dentro `nodo_verifica_tipo`?
3. Come mai per il nodo `N_EQ` è necessario controllare `t_sx != TV_ERR` oltre a `t_sx == t_dx`?
4. Che cosa succede ai puntatori memorizzati nell'array `slot` dopo l'esecuzione del comando `RESET`?

**Esempio di esecuzione**

```input
INT 0 10
INT 1 5
BIN 2 ADD 0 1
BIN 3 EQ 2 0
NOT 4 3
TERN 5 4 2 1
INFO 5
BIN 6 ADD 0 4
INFO 6
RESET
INFO 5
```

```output
OK [0] INT
OK [1] INT
OK [2] ADD
OK [3] EQ
OK [4] NOT
OK [5] TERN
INFO[5]: nodi=11 prof=5 tipo=INT
OK [6] ADD
INFO[6]: nodi=8 prof=5 tipo=ERRORE
RESET: usati=0
INFO[5]: VUOTO
```
