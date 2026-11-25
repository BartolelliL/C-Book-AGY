# Capitolo 26 — Progetto finale: un interprete per un piccolo linguaggio

> **In questo capitolo imparerai a:**
> - Progettare la sintassi e le strutture dati di un piccolo linguaggio imperativo usando unioni etichettate ed enum
> - Implementare un analizzatore lessicale e un analizzatore sintattico a discesa ricorsiva con precedenza degli operatori
> - Gestire i nodi dell'albero di sintassi con un allocatore ad arena e gli ambienti di variabili e funzioni con la tabella hash generica opaca
> - Integrare controllo di flusso, funzioni definite dall'utente, funzioni predefinite e test automatici su più file senza perdite di memoria

> **Ti servono:** allocazione dinamica e sanitizer (capitolo 11), strutture ed enumerazioni (capitolo 12), unioni etichettate e allineamento (capitolo 13), programmazione generica con `void *` (capitolo 15), puntatori a funzione (capitolo 16), strutture dati dinamiche (capitolo 17), tabelle hash (capitolo 18), programmi su più file e tipi opachi (capitolo 19), `goto cleanup` e aritmetica controllata (capitolo 21), allocatore ad arena (capitolo 22) e test automatici (capitolo 25).

Nei venticinque capitoli precedenti hai costruito un intero repertorio di strumenti: dalla gestione rigorosa della memoria sullo heap fino agli allocatori ad arena, dai puntatori a funzione alle tabelle hash generiche come tipi opachi, dalla compilazione separata ai test automatici. Finora ciascuna tecnica ha risolto un problema ben delimitato; in questo capitolo conclusivo le riunisci tutte dentro un unico programma reale di alcune centinaia di righe: un interprete completo per un piccolo linguaggio imperativo chiamato **MiniL**.

Scrivere un interprete è uno dei modi più efficaci per consolidare la padronanza del C. Ogni fase del programma mette alla prova una competenza diversa: la scansione del testo esige cura su caratteri, indici e overflow; l'analisi grammaticale richiede ricorsione controllata e strutture ad albero; la gestione delle variabili trasforma la tabella hash opaca in un sistema di ambiti annidati; l'esecuzione del codice utente ti obbliga a difendere il programma ospite da divisioni per zero, overflow e cicli infiniti senza mai ricorrere a comportamento indefinito.

Il capitolo è organizzato come un cantiere in sei tappe progressive. Nelle prime cinque sotto-sezioni progetti e verifichi separatamente ogni componente dell'interprete — strutture dati e arena, analizzatore lessicale, analizzatore sintattico, valutatore con ambienti, controllo di flusso e funzioni — attraverso esempi mirati ed esercizi dedicati. Nella sesta sotto-sezione integri tutti i moduli in un progetto su più file corredato da una suite di test automatici e pronto per la verifica con i sanitizer.

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

Lo stesso schema si applica ai nodi dell'albero di sintassi astratta (`nodo_t`): un `enum` elenca tutte le specie di nodi (`NODO_INT`, `NODO_BOOL`, `NODO_VAR`, `NODO_UNARIO`, `NODO_BINARIO`, `NODO_IF`, `NODO_WHILE`, `NODO_FN`, `NODO_CHIAMATA`, e così via), mentre la `union` raccoglie i campi pertinenti a ciascun nodo. Con un'asserzione statica (`static_assert`, capitolo 15) puoi verificare già in fase di compilazione che la dimensione di `valore_t` o di `nodo_t` resti compatta e non cresca per errore se aggiungi un campo troppo grande a una variante della `union`.

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

Questo esempio su tre file (`ast_demo.h`, `ast_demo.c`, `main.c`) costruisce il nucleo essenziale di un'arena su buffer statico allineato ad `alignof(max_align_t)` e definisce un piccolo nodo AST `nodo_demo_t` con unione etichettata. Il programma assembla manualmente l'albero dell'espressione `-(3 + 4 * 2)`, lo stampa in notazione prefissa, verifica i byte occupati nell'arena e infine azzera l'arena con `arena_reset`.

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

## 26.2 L'analizzatore lessicale

Quando il programma riceve un testo MiniL come `var somma = 10 + 25;`, dal punto di vista del C si tratta di una semplice sequenza di `char` terminata da `'\0'`. Lavorare direttamente sui singoli caratteri dentro il parser renderebbe la grammatica illeggibile, perché ogni regola dovrebbe continuamente saltare spazi, ignorare commenti e distinguere `=` da `==`. Per separare la lettura dei caratteri dalla comprensione della grammatica si introduce il primo stadio dell'interprete: l'**analizzatore lessicale** (*lexer*), il componente iniziale di un interprete che trasforma il codice sorgente in una sequenza di token tipizzati dotati di posizione (riga e colonna).

Un **token** rappresenta la minima unità significativa del linguaggio: una parola chiave (`var`, `while`), un identificatore (`somma`), un letterale intero (`42`), un operatore (`>=`, `&&`) o un simbolo di punteggiatura (`(`, `;`). In C lo modelliamo con una `struct` leggera:

<!-- cod: id=26.2-b tipo=frammento -->
```c
typedef struct token {
    tok_tipo_t tipo;
    const char *inizio;
    size_t len;
    int64_t val_int;
    size_t riga;
    size_t col;
} token_t;
```

Il campo `tipo` appartiene a una enumerazione `tok_tipo_t` che comprende tutte le categorie del linguaggio, più due valori speciali: `TOK_EOF` (il **valore sentinella** che segnala la fine del sorgente) e `TOK_ERR` (un token diagnostico che trasporta il motivo dell'errore lessicale e le coordinate esatte). I campi `inizio` e `len` descrivono una vista (puntatore e lunghezza) direttamente dentro la stringa sorgente, senza creare copie sullo heap; `val_int` memorizza il valore già convertito per i letterali numerici; `riga` e `col` (a partire da `1`) registrano dove inizia il token nel sorgente.

Lo stato dell'analizzatore lessicale è altrettanto compatto: `const char *src` (il testo sorgente), `size_t pos` (l'indice del carattere corrente) e i contatori `riga` e `col`. Ogni volta che si consuma un carattere tramite una funzione interna `avanza`, se il carattere letto è `'\n'` si incrementa `riga` e si riporta `col` a `1`; altrimenti si incrementa `col`.

Prima di costruire il token successivo, il lexer salta tutti gli elementi privi di significato grammaticale:

1. **Spazi bianchi** (`' '`, `'\t'`, `'\r'`, `'\n'`), riconosciuti con `isspace` di `<ctype.h>`.
2. **Commenti di riga** introdotti da `//`: quando `src[pos] == '/'` e `src[pos + 1] == '/'`, il cursore avanza fino a incontrare `'\n'` oppure `'\0'`. Poiché lo spazio bianco successivo (lo stesso `'\n'`) verrà saltato dall'iterazione seguente del ciclo, anche la posizione di riga e colonna resta sempre coerente.

Fai molta attenzione a una regola fondamentale di `<ctype.h>` che hai incontrato nel capitolo 9: le funzioni `isspace`, `isalpha`, `isdigit` e `isalnum` accettano un `int` che **deve** essere rappresentabile come `unsigned char` oppure uguale a `EOF`. Su piattaforme dove `char` è con segno, passare direttamente un `char` negativo (per esempio un carattere accentato codificato in UTF-8) provoca **comportamento indefinito** secondo lo standard C23. Converti quindi **sempre** il carattere con `(unsigned char)c` prima di passarlo a qualunque funzione di `<ctype.h>`.

Saltati spazi e commenti, il lexer ispeziona il carattere corrente `c = src[pos]` e decide la categoria del token:

- **Fine del testo**: se `c == '\0'`, restituisce `TOK_EOF` con la riga e la colonna correnti, senza avanzare oltre il terminatore nullo.
- **Identificatori e parole chiave**: se `isalpha((unsigned char)c) || c == '_'`, consuma tutti i caratteri successivi che soddisfano `isalnum((unsigned char)src[pos]) || src[pos] == '_'`. Ottiene così la vista `(inizio, len)` e la confronta con una tabella `static const` di coppie `(parola_chiave, tok_tipo_t)` verificando sia `strlen(kw) == len` sia `strncmp(inizio, kw, len) == 0`. Controllare anche la lunghezza è indispensabile: senza di essa, un prefisso come `var` verrebbe confuso con `variabile`. Se la parola non è in tabella, il token è `TOK_IDENT`.
- **Letterali interi**: se `isdigit((unsigned char)c)`, accumula le cifre in un `int64_t val = 0`. In C23 l'overflow su un intero con segno con gli operatori `*` e `+` provoca **comportamento indefinito**: se l'utente scrive un numero di trenta cifre nel proprio sorgente MiniL, il tuo interprete non può permettersi di entrare in UB. Usa invece `ckd_mul(&val, val, 10)` e `ckd_add(&val, val, cifra)` di `<stdckdint.h>` (capitolo 21): entrambe sono completamente definite in C23 e restituiscono `true` se il risultato non entra in `int64_t`. In caso di overflow il lexer finisce di consumare le cifre contigue e restituisce `TOK_ERR` con il messaggio `"overflow intero"` e le coordinate di inizio del numero.
- **Operatori a uno o due caratteri e punteggiatura**: dopo aver consumato `c`, il lexer osserva il carattere successivo `p = src[pos]` (*lookahead* di un carattere) prima di decidere se avanzare di nuovo. Se `c == '='` e `p == '='`, consuma anche `p` e restituisce `TOK_EQ`; altrimenti lascia `p` intatto e restituisce `TOK_ASS`. Lo stesso vale per `!=`, `<=`, `>=`, `&&` e `||`. Nota un caso importante: `&` e `|` isolati non esistono in MiniL, quindi se dopo `&` non c'è un secondo `&` (o dopo `|` non c'è `|`), il lexer produce un token `TOK_ERR` con `"carattere non valido"` e le coordinate esatte del simbolo errato. Lo stesso accade per qualsiasi carattere non previsto dal linguaggio, come `@` o `$`.

> **C23** — Le macro `ckd_mul` e `ckd_add` di `<stdckdint.h>` sono una novità di C23; su compilatori più vecchi occorre verificare preventivamente il limite rispetto a `INT64_MAX / 10` e `INT64_MAX % 10` prima di moltiplicare o sommare.

### Esempio guidato

Questo breve lexer didattico analizza due brevi istruzioni contenenti una parola chiave, identificatori, interi e operatori `=`, `==`, `+` e `;`. Mostra il cursore con la colonna, il cast a `unsigned char`, la tabella statica delle parole chiave e il lookahead di un carattere per distinguere `=` da `==`.

<!-- cod: id=26.2-a tipo=programma -->
```c
#include <ctype.h>
#include <inttypes.h>
#include <stdckdint.h>
#include <stdio.h>
#include <string.h>

typedef enum tok_tipo {
    TK_EOF, TK_ERR, TK_VAR, TK_IDENT, TK_INT, TK_ASS, TK_EQ, TK_PIU, TK_PV
} tok_tipo_t;

typedef struct token {
    tok_tipo_t tipo;
    const char *inizio;
    size_t len, col;
    int64_t val;
} token_t;

typedef struct lexer {
    const char *src;
    size_t pos, col;
} lexer_t;

static char avanza(lexer_t *lx) { ++lx->col; return lx->src[lx->pos++]; }

static tok_tipo_t cerca_kw(const char *s, size_t n) {
    static const struct { const char *kw; tok_tipo_t t; } TAB[] = {{"var", TK_VAR}};
    for (size_t i = 0; i < sizeof(TAB) / sizeof(TAB[0]); ++i) {
        if (strlen(TAB[i].kw) == n && strncmp(s, TAB[i].kw, n) == 0) { return TAB[i].t; }
    }
    return TK_IDENT;
}

static token_t prossimo(lexer_t *lx) {
    while (lx->src[lx->pos] != '\0' && isspace((unsigned char)lx->src[lx->pos])) {
        avanza(lx);
    }
    size_t col = lx->col, start = lx->pos;
    char c = lx->src[lx->pos];
    if (c == '\0') { return (token_t){.tipo = TK_EOF, .col = col}; }
    if (isalpha((unsigned char)c) || c == '_') {
        while (isalnum((unsigned char)lx->src[lx->pos]) || lx->src[lx->pos] == '_') { avanza(lx); }
        size_t n = lx->pos - start;
        return (token_t){cerca_kw(lx->src + start, n), lx->src + start, n, col, 0};
    }
    if (isdigit((unsigned char)c)) {
        int64_t v = 0;
        while (isdigit((unsigned char)lx->src[lx->pos])) {
            int64_t d = (int64_t)(avanza(lx) - '0');
            if (ckd_mul(&v, v, 10) || ckd_add(&v, v, d)) { return (token_t){.tipo = TK_ERR, .col = col}; }
        }
        return (token_t){.tipo = TK_INT, .col = col, .val = v};
    }
    avanza(lx);
    if (c == '=' && lx->src[lx->pos] == '=') { avanza(lx); return (token_t){.tipo = TK_EQ, .col = col}; }
    if (c == '=') { return (token_t){.tipo = TK_ASS, .col = col}; }
    if (c == '+') { return (token_t){.tipo = TK_PIU, .col = col}; }
    if (c == ';') { return (token_t){.tipo = TK_PV, .col = col}; }
    return (token_t){.tipo = TK_ERR, .col = col};
}

int main(void) {
    static const char *NOMI[] = {"EOF", "ERR", "VAR", "IDENT", "INT", "ASS", "EQ", "PIU", "PV"};
    lexer_t lx = {.src = "var x = 12 + 34; x == 46;", .pos = 0, .col = 1};
    while (true) {
        token_t t = prossimo(&lx);
        if (t.tipo == TK_IDENT) {
            printf("col %2zu: IDENT(%.*s)\n", t.col, (int)t.len, t.inizio);
        } else if (t.tipo == TK_INT) {
            printf("col %2zu: INT(%" PRId64 ")\n", t.col, t.val);
        } else {
            printf("col %2zu: %s\n", t.col, NOMI[t.tipo]);
        }
        if (t.tipo == TK_EOF || t.tipo == TK_ERR) { break; }
    }
    return 0;
}
```

```output
col  1: VAR
col  5: IDENT(x)
col  7: ASS
col  9: INT(12)
col 12: PIU
col 14: INT(34)
col 16: PV
col 18: IDENT(x)
col 20: EQ
col 23: INT(46)
col 25: PV
col 26: EOF
```

Nota come lo specificatore `%.*s` di `printf` stampi esattamente `(int)t.len` caratteri a partire da `t.inizio`, senza che la sottostringa nel buffer sorgente debba terminare con `'\0'`. In `prossimo`, quando `c` è `'='`, il controllo `lx->src[lx->pos] == '='` è sempre sicuro perché, se `c` era l'ultimo carattere prima della fine, `lx->src[lx->pos]` è il terminatore `'\0'` (mai fuori dai limiti dell'array).

> **Approfondimento — Zero allocazioni nell'analizzatore lessicale**
> Perché `token_t` memorizza la coppia `(const char *inizio, size_t len)` che punta dentro il buffer sorgente invece di duplicare subito ogni identificatore con `strdup`? Perché la maggior parte dei token (parole chiave, numeri, operatori) non ha bisogno di alcuna copia in memoria, e anche per gli identificatori sarà eventualmente il parser a copiarli nell'arena dell'AST solo quando costruisce un nodo valido. In questo modo il lexer non esegue nessuna allocazione sullo heap, resta velocissimo e non può mai provocare perdite di memoria.

### Esercizio 26.2 — Analizzatore lessicale completo per MiniL con coordinate, commenti e controllo di overflow

**Descrizione**

Realizza su tre file (`lexer_minil.h`, `lexer_minil.c`, `main.c`) l'**analizzatore lessicale** completo del linguaggio MiniL. (1) In `lexer_minil.h` (protetto da `LEXER_MINIL_H`) definisci `tok_tipo_t` comprendente `TOK_EOF`, `TOK_ERR`, `TOK_INT`, `TOK_IDENT`, tutte le parole chiave (`var`, `if`, `else`, `while`, `fn`, `return`, `stampa`, `true`, `false`), gli operatori aritmetici/logici/relazionali (`+`, `-`, `*`, `/`, `%`, `!`, `=`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `&&`, `||`) e la punteggiatura (`(`, `)`, `{`, `}`, `,`, `;`), oltre a `token_t` (con `tipo`, `inizio`, `len`, `val_int`, `riga`, `col`) e `lexer_t`. Dichiara `lexer_init`, `lexer_prossimo` e `tok_nome`. (2) In `lexer_minil.c` salta spazi e commenti `//` aggiornando `riga` e `col`, converte ogni carattere a `unsigned char` prima di chiamare `<ctype.h>`, distingue identificatori e parole chiave, converte letterali interi in `int64_t` usando `ckd_mul` e `ckd_add` (restituendo `TOK_ERR` con messaggio `overflow intero` se supera `INT64_MAX`) e gestisce il lookahead per gli operatori doppi (`==`, `!=`, `<=`, `>=`, `&&`, `||`; un `&` o `|` singolo o un carattere ignoto produce `TOK_ERR` con `carattere non valido`). (3) In `main.c` leggi l'intero sorgente da `stdin` (fino a `4095` byte) e stampa un token per riga nel formato `<riga>:<col> <NOME>` (`INT=<val>` per i numeri, `IDENT=<testo>` per gli identificatori), arrestandosi con `ERRORE <riga>:<col>: <msg>` su `TOK_ERR` oppure terminando con `<riga>:<col> EOF`, esattamente come nell'esempio.

**Concetti da tenere a mente**

- conversione obbligatoria a `unsigned char` prima di invocare `isspace`, `isalpha`, `isdigit` e `isalnum`
- tracciamento esatto di riga e colonna attraverso spazi, ritorni a capo e commenti di riga `//`
- lookahead di un carattere per distinguere operatori a uno e due caratteri (`=` vs `==`, `&` isolato vs `&&`)
- parsing di interi `int64_t` con `ckd_mul` e `ckd_add` senza comportamento indefinito

**Domande guida**

1. Come fa il lexer a distinguere la parola chiave `var` da un identificatore come `variabile`?
2. Perché nella conversione di una sequenza di cifre in `int64_t` conviene usare `ckd_mul` e `ckd_add` invece di moltiplicare direttamente per `10`?
3. Che cosa succede alla riga e alla colonna quando il lexer incontra un commento `//` seguito da `'\n'`?
4. Perché un singolo carattere `'&'` non seguito da un altro `'&'` deve generare un token di errore invece di essere ignorato?

**Esempio di esecuzione**

```input
var x = 42; // init
if (x >= 10 && !false) {
    stampa x + 1;
}
```

```output
1:1 VAR
1:5 IDENT=x
1:7 ASS
1:9 INT=42
1:11 PV
2:1 IF
2:4 TONDA_A
2:5 IDENT=x
2:7 GE
2:10 INT=10
2:13 AND
2:16 BANG
2:17 FALSE
2:22 TONDA_C
2:24 GRAFFA_A
3:5 STAMPA
3:12 IDENT=x
3:14 PIU
3:16 INT=1
3:17 PV
4:1 GRAFFA_C
5:1 EOF
```

## 26.3 L'analizzatore sintattico

Una volta che l'analizzatore lessicale produce una sequenza pulita di token, il secondo stadio dell'interprete deve verificare che quei token rispettino la grammatica di MiniL e costruire l'albero di sintassi astratta. Questo compito spetta all'**analizzatore sintattico** (*parser*): il componente che verifica la grammatica della sequenza di token e costruisce l'albero di sintassi astratta rispettando precedenza e associatività.

La tecnica più chiara e diretta da scrivere a mano in C è la **discesa ricorsiva** (*recursive descent*). L'idea è immediata: a ogni regola grammaticale del linguaggio corrisponde una funzione C che consuma i token previsti da quella regola e restituisce un puntatore al sottoalbero `nodo_t *` appena allocato nell'arena (oppure `nullptr` in caso di errore).

Per coordinare il flusso dei token, il parser conserva in una struttura `parser_t` un puntatore al lexer, il token corrente `cur` (sempre pronto per essere ispezionato), un puntatore all'arena dell'AST, un puntatore a `errore_t` e un contatore di profondità `prof`. Tre piccoli helper rendono ogni regola grammaticale leggibile quasi come una specifica formale:

- `avanza(p)`: legge il token successivo dal lexer in `p->cur` (e se riceve `TOK_ERR`, registra subito l'errore lessicale).
- `corrisponde(p, tipo)`: se `p->cur.tipo == tipo`, chiama `avanza(p)` e restituisce `true`; altrimenti lascia `p->cur` intatto e restituisce `false`.
- `attendi(p, tipo, msg)`: richiede che il token corrente sia di tipo `tipo` (per esempio `)` o `;`); se lo è, avanza e restituisce `true`; altrimenti registra `msg` con la riga e la colonna di `p->cur` e restituisce `false`.

Il cuore della discesa ricorsiva per le espressioni consiste nel codificare la **precedenza degli operatori** attraverso una stratificazione di funzioni: ogni livello chiama il livello di precedenza immediatamente più alto. In MiniL la scala parte dal livello più basso (`||`) e scende fino agli operandi indivisibili (primari):

```text
  Livello (dal più basso al più alto)      Operatori / costrutti
  -----------------------------------      ------------------------------------------
  1. parse_or                              ||
  2. parse_and                             &&
  3. parse_uguaglianza                     ==, !=
  4. parse_confronto                       <, <=, >, >=
  5. parse_somma                           +, -
  6. parse_prodotto                        *, /, %
  7. parse_unario                          -, !   (associativi a destra: - -5, !!b)
  8. parse_primario                        interi, true, false, x, f(a, b), (expr)
```

Osserva che cosa accade quando `parse_somma` analizza `2 + 3 * 4`: per prima cosa chiama `parse_prodotto`, che legge `2`; vede il token `+`, lo consuma e richiama `parse_prodotto`, che legge l'intera moltiplicazione `3 * 4` come un unico sottoalbero `(* 3 4)`; infine costruisce il nodo `(+ 2 (* 3 4))`. La precedenza nasce automaticamente dall'ordine delle chiamate.

Per gli operatori binari associativi a sinistra (`+`, `-`, `*`, `/`, `%`, confronti, `&&`, `||`) vale una regola fondamentale: **devono essere analizzati con un ciclo `while`**, mai con ricorsione sinistra (che farebbe chiamare `parse_somma` da `parse_somma` senza consumare alcun token, provocando una ricorsione infinita) e mai con ricorsione destra (che raggrupperebbe `10 - 3 - 2` come `10 - (3 - 2)`). Il ciclo `while` mantiene il sottoalbero accumulato a sinistra in una variabile locale `sx` e a ogni operatore costruisce un nuovo nodo genitore con `sx` come figlio sinistro e il risultato della chiamata al livello superiore come figlio destro. Gli operatori unari `-` e `!`, invece, sono associativi a destra (`- -5` significa `-(-5)`), quindi `parse_unario` chiama ricorsivamente se stessa dopo aver consumato `-` o `!`.

In `parse_primario`, quando il parser incontra un identificatore `x`, guarda il token successivo: se è `(`, sta analizzando una chiamata di funzione `x(a1, a2, ...)` (anche con zero argomenti se trova subito `)`); altrimenti si tratta di una semplice lettura di variabile. Gli argomenti della chiamata sono collegati in una lista concatenata di nodi (o tramite un campo `prox`), tutti allocati nell'arena.

Lo stesso schema si estende alle istruzioni e alle dichiarazioni di MiniL:

- `var nome = expr;` verifica identificatore, `=`, espressione e `;`;
- un identificatore seguito da `=` è un assegnamento (`x = expr;`);
- `stampa expr;` legge un'espressione e il `;`;
- `if (cond) { ... } else { ... }` analizza la condizione tra parentesi, il blocco del ramo vero e, se `corrisponde(p, TOK_ELSE)`, un eventuale altro `if` (`else if`) oppure un blocco `{ ... }`;
- `while (cond) { ... }` analizza la condizione e il corpo;
- `fn nome(p1, p2) { ... }` legge il nome, la lista dei parametri separati da virgola e il corpo;
- `return;` oppure `return expr;` gestisce il ritorno con o senza valore;
- un blocco `{ ... }` accumula una sequenza di istruzioni collegandole con il puntatore `prox` (mantenendo `testa` e `**coda` per preservare l'ordine in `O(1)`).

Un analizzatore a discesa ricorsiva deve difendersi anche da input malevoli o malformati, come un file contenente diecimila parentesi aperte `((((...`. Secondo lo standard C23, la ricorsione controllata e la costruzione iterativa di alberi sono completamente definite, ma una ricorsione illimitata può esaurire lo stack di esecuzione (un evento non definito dallo standard che provoca la chiusura anomala del programma). Per questo motivo il parser incrementa `p->prof` ogni volta che entra in una parentesi, in un operatore unario o in un blocco annidato, lo decrementa all'uscita e rifiuta l'input appena supera un limite costante `MAX_PROF_PARSE` (per esempio `32`), segnalando il punto esatto con riga e colonna. Inoltre, al termine di un'espressione o di un programma, il parser controlla sempre che il token residuo sia `TOK_EOF` (o la fine riga prevista), in modo da non ignorare silenziosamente token spuri in coda.

### Esempio guidato

Questo mini parser a discesa ricorsiva analizza espressioni con `+`, `-`, `*` e parentesi, allocando i nodi in una piccola arena statica. Verifica che `10 - 3 - 2` produca l'albero associativo a sinistra `(- (- 10 3) 2)`, che `2 + 3 * 4` rispetti la precedenza di `*` su `+`, e che una parentesi chiusa mancante generi un errore sintattico chiaro.

<!-- cod: id=26.3-a tipo=programma -->
```c
#include <ctype.h>
#include <stdio.h>

typedef struct nodo nodo_t;
struct nodo { char op; int val; nodo_t *sx, *dx; };

typedef struct parser {
    const char *s;
    size_t pos, usati;
    nodo_t pool[64];
    bool err;
    const char *msg;
} parser_t;

static void salta(parser_t *p) {
    while (p->s[p->pos] != '\0' && isspace((unsigned char)p->s[p->pos])) { ++p->pos; }
}

static nodo_t *nuovo(parser_t *p, char op, int val, nodo_t *sx, nodo_t *dx) {
    if (p->usati >= 64) { p->err = true; p->msg = "arena piena"; return nullptr; }
    nodo_t *n = &p->pool[p->usati++];
    *n = (nodo_t){.op = op, .val = val, .sx = sx, .dx = dx};
    return n;
}

static nodo_t *parse_somma(parser_t *p);

static nodo_t *parse_primario(parser_t *p) {
    salta(p);
    if (p->s[p->pos] == '(') {
        ++p->pos;
        nodo_t *e = parse_somma(p);
        salta(p);
        if (!p->err && p->s[p->pos] != ')') {
            p->err = true; p->msg = "parentesi ')' mancante"; return nullptr;
        }
        if (!p->err) { ++p->pos; }
        return e;
    }
    if (isdigit((unsigned char)p->s[p->pos])) {
        int v = 0;
        while (isdigit((unsigned char)p->s[p->pos])) { v = v * 10 + (p->s[p->pos++] - '0'); }
        return nuovo(p, 'N', v, nullptr, nullptr);
    }
    p->err = true; p->msg = "atteso numero o '('"; return nullptr;
}

static nodo_t *parse_prodotto(parser_t *p) {
    nodo_t *sx = parse_primario(p);
    while (!p->err) {
        salta(p);
        if (p->s[p->pos] == '*') { ++p->pos; sx = nuovo(p, '*', 0, sx, parse_primario(p)); }
        else { break; }
    }
    return sx;
}

static nodo_t *parse_somma(parser_t *p) {
    nodo_t *sx = parse_prodotto(p);
    while (!p->err) {
        salta(p);
        char c = p->s[p->pos];
        if (c == '+' || c == '-') { ++p->pos; sx = nuovo(p, c, 0, sx, parse_prodotto(p)); }
        else { break; }
    }
    return sx;
}

static void stampa(const nodo_t *n) {
    if (n->op == 'N') { printf("%d", n->val); }
    else { printf("(%c ", n->op); stampa(n->sx); printf(" "); stampa(n->dx); printf(")"); }
}

int main(void) {
    const char *casi[] = {"10 - 3 - 2", "2 + 3 * 4", "(1 + 2"};
    for (size_t i = 0; i < 3; ++i) {
        parser_t p = {.s = casi[i]};
        nodo_t *rad = parse_somma(&p);
        if (!p.err) { stampa(rad); printf("\n"); }
        else { printf("ERRORE: %s\n", p.msg); }
    }
    return 0;
}
```

```output
(- (- 10 3) 2)
(+ 2 (* 3 4))
ERRORE: parentesi ')' mancante
```

Osserva come `parse_somma` tratti `10 - 3 - 2`: alla prima iterazione del ciclo `while` costruisce `(- 10 3)` e lo riassegna a `sx`; alla seconda iterazione legge `2` e costruisce `(- sx 2)`, cioè `(- (- 10 3) 2)`. Nell'esempio didattico la lettura dei numeri è semplificata per stare in poche righe; nel parser completo di MiniL l'analisi dei numeri con `<stdckdint.h>` resta affidata all'analizzatore lessicale.

> **Approfondimento — Associatività a sinistra contro ricorsione destra**
> Che cosa succederebbe se in `parse_somma`, dopo aver letto il segno `'-'`, chiamassi ricorsivamente `parse_somma(p)` anziché usare un ciclo `while` che chiama `parse_prodotto(p)`? Sull'espressione `10 - 3 - 2` la prima chiamata leggerebbe `10`, vedrebbe `'-'` e delegherebbe tutto il resto (`3 - 2`) alla chiamata ricorsiva: l'albero risultante sarebbe `(- 10 (- 3 2))`, che vale `9` anziché `5`. Il ciclo `while` elimina la ricorsione sinistra e raggruppa sempre gli operandi da sinistra verso destra.

### Esercizio 26.3 — Analizzatore sintattico a discesa ricorsiva per espressioni complete e chiamate su arena

**Descrizione**

Realizza su tre file (`expr_parser.h`, `expr_parser.c`, `main.c`) un **analizzatore sintattico** a discesa ricorsiva che trasforma espressioni MiniL in un **albero di sintassi astratta** allocato su un'**arena** su buffer statico `alignas(max_align_t)` e lo stampa in notazione prefissa completamente parentesizzata (S-espressione). (1) In `expr_parser.h` (protetto da `EXPR_PARSER_H`) definisci `expr_arena_t`, `enodo_tipo_t` (`EN_INT`, `EN_BOOL`, `EN_VAR`, `EN_UN`, `EN_BIN`, `EN_CALL`), `enodo_arg_t` (lista concatenata di argomenti allocata nell'arena) e `enodo_t`, e dichiara `parse_espressione_riga` e `stampa_sexpr`. (2) In `expr_parser.c` implementa la gerarchia completa di precedenza dal livello più basso al più alto: `||`, `&&`, `==`/`!=`, `<`/`<=`/`>`/`>=`, `+`/`-` (associativi a sinistra con `while`), `*`/`/`/`%` (associativi a sinistra con `while`), unari `-`/`!` (associativi a destra), e primari (interi `int64_t`, `true`, `false`, variabili, chiamate `nome(a1, a2, ...)` anche con 0 argomenti, parentesi `(expr)`). Imponi una profondità massima di annidamento di `16` (`ERRORE <col>: profondita eccessiva`), rifiuta parentesi non chiuse o token residui dopo l'espressione e controlla eventuali overflow numerici. (3) In `main.c` dichiara `static alignas(max_align_t) unsigned char mem[8192];`, leggi una espressione per riga non vuota da `stdin`, azzera l'arena a ogni riga, invoca il parser e stampa la S-espressione (`(<op> <sx> <dx>)`, `(<op> <x>)`, `(call <nome> <args...>)`) oppure `ERRORE <col>: <msg>`, riproducendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- gerarchia di funzioni a discesa ricorsiva per codificare sette livelli di precedenza degli operatori
- cicli `while` per garantire l'associatività a sinistra di `-` e `/` senza ricorsione sinistra
- parsing di liste di argomenti di chiamata `f(a, b, c)` allocate come lista nell'arena
- limite esplicito di profondità di ricorsione e controllo di fine espressione

**Domande guida**

1. In quale ordine di chiamata vanno collegate le funzioni di parsing affinché `a + b * c == d && !e` venga raggruppata correttamente?
2. Come distingue `parse_primario` un semplice identificatore `x` da una chiamata di funzione `x(1, 2)`?
3. Perché dopo aver chiamato il livello più esterno `parse_or` devi verificare che il token successivo sia la fine della riga?
4. In che modo il contatore di profondità impedisce uno stack overflow su input patologici come 20 parentesi aperte di fila?

**Esempio di esecuzione**

```input
10 - 3 - 2
2 + 3 * 4 == 14 && !false || x < 0
- -5 + f(1, g(), a + b)
(1 + 2
1 + * 2
```

```output
(- (- 10 3) 2)
(|| (&& (== (+ 2 (* 3 4)) 14) (! false)) (< x 0))
(+ (- (- 5)) (call f 1 (call g) (+ a b)))
ERRORE 7: attesa ')'
ERRORE 5: espressione inattesa
```

## 26.4 Valutazione delle espressioni e gestione delle variabili

Con l'albero di sintassi astratta pronto nell'arena, il terzo stadio dell'interprete — il **valutatore** — percorre i nodi per calcolare i risultati. Per le espressioni si tratta di una visita ricorsiva in post-ordine: per valutare un nodo binario come `(+ sx dx)`, si valuta prima il sottoalbero `sx`, poi (salvo corto circuito) il sottoalbero `dx`, si controllano i tipi delle due unioni etichettate `valore_t` e infine si applica l'operazione.

Qui entra in gioco una regola di sicurezza fondamentale per chi scrive un interprete in C: **il codice utente non deve mai poter provocare comportamento indefinito nel programma ospite C**. Se qualcuno scrive `stampa 10 / 0;` oppure `stampa 9223372036854775807 + 1;` in un sorgente MiniL, il tuo programma C non deve andare in crash né dipendere da comportamenti non definiti: deve intercettare la condizione prima di eseguire l'operazione C e produrre un errore di esecuzione deterministico in `errore_t`.

Per l'aritmetica su `int64_t` valgono quindi quattro controlli sistematici:

1. **Addizione, sottrazione e moltiplicazione**: usa sempre `ckd_add`, `ckd_sub` e `ckd_mul` di `<stdckdint.h>` (capitolo 21). Se restituiscono `true`, segnali `"overflow aritmetico"`.
2. **Negazione unaria `-x`**: in complemento a due `-INT64_MIN` non è rappresentabile in `int64_t` (overflow con segno, quindi UB). Verifica `x == INT64_MIN` oppure usa `ckd_sub(&ris, 0, x)`.
3. **Divisione `/` e modulo `%`**: secondo lo standard C23, sia la divisione o il modulo per `0` sia le coppie `INT64_MIN / -1` e `INT64_MIN % -1` (in complemento a due) provocano **comportamento indefinito**. Il valutatore controlla sempre `b == 0` (`"divisione per zero"`) e `a == INT64_MIN && b == -1` (`"overflow aritmetico"`) *prima* di applicare `/` o `%`.
4. **Controllo dei tipi**: gli operatori aritmetici e relazionali `<`, `<=`, `>`, `>=` richiedono entrambi gli operandi `VAL_INT`; `==` e `!=` richiedono due operandi dello stesso tipo valido (`VAL_INT` o `VAL_BOOL`); `!`, `&&` e `||` richiedono `VAL_BOOL`.

Gli operatori logici `&&` e `||` richiedono un'attenzione speciale: devono rispettare la **valutazione a corto circuito** (capitolo 4). In un'espressione come `x != 0 && 10 / x > 1`, se `x` vale `0` il lato sinistro è `false`, quindi il risultato dell'intera espressione è già `false` e il valutatore **non deve valutare** `10 / x > 1` (evitando così una divisione per zero). Analogamente, per `a || b`, se `a` valuta a `VAL_BOOL` con valore `true`, si restituisce subito `true` senza toccare `b`. Solo se il primo operando non decide il risultato si valuta il secondo e se ne verifica il tipo `VAL_BOOL`.

Per memorizzare le variabili del programma MiniL e gestirne la **visibilità** nei blocchi annidati introduciamo l'**ambiente di esecuzione** (*environment*): una catena di tabelle associative che mappa gli identificatori ai rispettivi valori a tempo di esecuzione gestendo ambiti annidati e oscuramento.

Qui entra finalmente in azione il traguardo centrale di questo libro: la **tabella hash generica come tipo opaco** costruita nei capitoli 18 e 19 (`tabella_hash.h`). Ogni nodo della catena è una piccola struttura `ambiente_t` che racchiude una `tabella_hash_t *tab` e un puntatore `struct ambiente *genitore`:

```text
  [ Ambiente blocco interno ]          [ Ambiente globale ]
   tab: { "x" -> 99 }                   tab: { "x" -> 10, "y" -> 1 }
   genitore  -------------------------> genitore: nullptr
```

Le tre operazioni sull'ambiente seguono regole limpide:

- **Dichiarazione (`var x = expr;`)**: cerca `"x"` *solo* nella tabella dell'ambito corrente. Se è già presente, segnala un errore di ridefinizione nello stesso ambito; altrimenti inserisce `"x"` nella tabella corrente. Se esiste già una `"x"` in un ambito genitore, la nuova dichiarazione locale la oscura temporaneamente (*shadowing*) senza modificarla: quando il blocco interno termina e il suo ambiente viene distrutto, la `"x"` esterna torna visibile con il proprio valore originario.
- **Lettura (`x`)**: cerca `"x"` nell'ambiente corrente; se non la trova, risale lungo `genitore` fino all'ambiente globale (`genitore == nullptr`). Se non esiste in alcun ambito, segnala `"variabile non dichiarata"`.
- **Assegnamento (`x = expr;`)**: risale la catena come la lettura per trovare il primo ambiente che contiene `"x"` e ne aggiorna il `valore_t` sul posto; se non la trova, segnala `"variabile non dichiarata"`.

Le regole di **possesso della memoria** dentro `tabella_hash_t` sono nette e prive di ambiguità: ogni chiave è una copia allocata con `strdup` (funzione standard C23 di `<string.h>`), ogni valore è un `valore_t *` allocato con `malloc`, ed entrambi sono posseduti dalla tabella hash, configurata con `d_chiave = free` e `d_valore = free`. Quando `env_distruggi` chiama `ht_distruggi(e->tab)` e `free(e)`, ogni singola stringa chiave e ogni `valore_t` di quell'ambito vengono liberati automaticamente.

> **C23** — `strdup` è parte della libreria standard `<string.h>` a partire da C23; su compilatori C11/C17 strettamente ISO occorre scrivere una piccola funzione di supporto basata su `strlen`, `malloc` e `memcpy`.

> **Se vieni da Python** — In Python gli interi hanno precisione arbitraria e non vanno mai in overflow, mentre un errore di esecuzione solleva un'eccezione catturabile con `try`/`except`; in C un interprete sicuro usa `int64_t` con `<stdckdint.h>` per rilevare gli overflow e propaga gli errori esplicitamente tramite `errore_t`.

### Esempio guidato

Questo programma su tre file (`tab_opaca.h`, `tab_opaca.c`, `main.c`) costruisce un ambiente globale e un ambiente figlio appoggiati a una tabella hash generica opaca (`void *`), dimostra la lettura risalendo dal figlio al genitore, l'oscuramento con una variabile locale `x`, l'aggiornamento della variabile globale `y` e la distruzione pulita di entrambi gli ambienti.

<!-- cod: id=26.4-a tipo=programma gruppo=env_demo file=tab_opaca.h -->
```c
#ifndef TAB_OPACA_H
#define TAB_OPACA_H

#include <stddef.h>
#include <stdint.h>

typedef struct tab_opaca tab_opaca_t;
typedef void (*distruggi_fn)(void *ptr);

tab_opaca_t *tab_crea(size_t cap, distruggi_fn d_chiave, distruggi_fn d_val);
void tab_distruggi(tab_opaca_t *t);
bool tab_inserisci(tab_opaca_t *t, char *chiave, void *val);
void *tab_cerca(const tab_opaca_t *t, const char *chiave);

#endif
```

<!-- cod: id=26.4-b tipo=programma gruppo=env_demo file=tab_opaca.c -->
```c
#include "tab_opaca.h"
#include <stdlib.h>
#include <string.h>

typedef struct nodo {
    char *chiave;
    void *val;
    struct nodo *prox;
} nodo_t;

struct tab_opaca {
    nodo_t **secchi;
    size_t cap;
    distruggi_fn dc;
    distruggi_fn dv;
};

static size_t indice_hash(const char *s, size_t cap) {
    uint64_t h = 14695981039346656037ULL;
    for (const unsigned char *p = (const unsigned char *)s; *p != '\0'; ++p) {
        h ^= (uint64_t)(*p);
        h *= 1099511628211ULL;
    }
    return (size_t)(h % cap);
}

tab_opaca_t *tab_crea(size_t cap, distruggi_fn d_chiave, distruggi_fn d_val) {
    tab_opaca_t *t = malloc(sizeof(*t));
    if (t == nullptr) {
        return nullptr;
    }
    t->secchi = calloc(cap, sizeof(*t->secchi));
    if (t->secchi == nullptr) {
        free(t);
        return nullptr;
    }
    t->cap = cap;
    t->dc = d_chiave;
    t->dv = d_val;
    return t;
}

void tab_distruggi(tab_opaca_t *t) {
    if (t == nullptr) {
        return;
    }
    for (size_t i = 0; i < t->cap; ++i) {
        for (nodo_t *c = t->secchi[i], *p = nullptr; c != nullptr; c = p) {
            p = c->prox;
            if (t->dc != nullptr) { t->dc(c->chiave); }
            if (t->dv != nullptr) { t->dv(c->val); }
            free(c);
        }
    }
    free(t->secchi);
    free(t);
}

bool tab_inserisci(tab_opaca_t *t, char *chiave, void *val) {
    size_t k = indice_hash(chiave, t->cap);
    nodo_t *n = malloc(sizeof(*n));
    if (n == nullptr) {
        return false;
    }
    *n = (nodo_t){.chiave = chiave, .val = val, .prox = t->secchi[k]};
    t->secchi[k] = n;
    return true;
}

void *tab_cerca(const tab_opaca_t *t, const char *chiave) {
    size_t k = indice_hash(chiave, t->cap);
    for (const nodo_t *c = t->secchi[k]; c != nullptr; c = c->prox) {
        if (strcmp(c->chiave, chiave) == 0) {
            return c->val;
        }
    }
    return nullptr;
}
```

<!-- cod: id=26.4-c tipo=programma gruppo=env_demo file=main.c -->
```c
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "tab_opaca.h"

typedef struct ambiente {
    tab_opaca_t *tab;
    struct ambiente *genitore;
} ambiente_t;

static int64_t *env_cerca(const ambiente_t *e, const char *nome) {
    for (; e != nullptr; e = e->genitore) {
        int64_t *v = tab_cerca(e->tab, nome);
        if (v != nullptr) {
            return v;
        }
    }
    return nullptr;
}

static bool env_def(ambiente_t *e, const char *nome, int64_t val) {
    char *k = strdup(nome);
    int64_t *vp = malloc(sizeof(*vp));
    if (k == nullptr || vp == nullptr) {
        free(k);
        free(vp);
        return false;
    }
    *vp = val;
    if (!tab_inserisci(e->tab, k, vp)) {
        free(k);
        free(vp);
        return false;
    }
    return true;
}

int main(void) {
    ambiente_t glob = {.tab = tab_crea(8, free, free), .genitore = nullptr};
    ambiente_t bloc = {.tab = tab_crea(8, free, free), .genitore = &glob};
    if (glob.tab == nullptr || bloc.tab == nullptr) {
        tab_distruggi(bloc.tab);
        tab_distruggi(glob.tab);
        return EXIT_FAILURE;
    }
    if (!env_def(&glob, "x", 10) || !env_def(&glob, "y", 1) || !env_def(&bloc, "x", 99)) {
        tab_distruggi(bloc.tab);
        tab_distruggi(glob.tab);
        return EXIT_FAILURE;
    }

    int64_t *py = env_cerca(&bloc, "y");
    if (py != nullptr) {
        *py = 2;
    }
    printf("Nel blocco: x=%" PRId64 ", y=%" PRId64 "\n",
           *env_cerca(&bloc, "x"), *env_cerca(&bloc, "y"));
    tab_distruggi(bloc.tab);
    printf("Nel globale: x=%" PRId64 ", y=%" PRId64 "\n",
           *env_cerca(&glob, "x"), *env_cerca(&glob, "y"));
    tab_distruggi(glob.tab);
    return 0;
}
```

```output
Nel blocco: x=99, y=2
Nel globale: x=10, y=2
```

Osserva il comportamento dello *shadowing*: nel blocco interno `env_cerca(&bloc, "x")` trova la `x` locale (`99`) prima di salire al genitore, mentre `env_cerca(&bloc, "y")` non trova `y` nel blocco, risale a `glob` e aggiorna la `y` globale a `2`. Quando `tab_distruggi(bloc.tab)` libera la tabella del blocco (incluse la copia `strdup("x")` e l'`int64_t` allocato con `malloc`), la `x` globale vale ancora `10`.

> **Approfondimento — Mai delegare ciecamente l'aritmetica utente al C**
> Perché l'interprete non deve mai calcolare direttamente `a + b` o `a / b` sui valori provenienti dal codice MiniL? Perché in C l'overflow su interi con segno e la divisione per zero sono comportamenti indefiniti: compilando con `-O2`, il compilatore è libero di assumere che non accadano mai e di generare istruzioni che terminano il processo con un segnale hardware (`SIGFPE`) o producono risultati assurdi. Intercettando `b == 0`, `INT64_MIN / -1` e usando `<stdckdint.h>`, il tuo interprete resta solido qualunque codice l'utente scriva.

### Esercizio 26.4 — Ambiente lessicale a catena su tabella hash opaca e valutatore sicuro con corto circuito

**Descrizione**

Realizza su tre file (`tabella_hash.h`, `tabella_hash.c`, `main.c`) il sottosistema di **ambiente di esecuzione** a catena basato sulla **tabella hash generica opaca** del capitolo 19 e usalo per gestire variabili tipizzate (`int64_t` e `bool`) con ambiti annidati, oscuramento (shadowing), aritmetica controllata (`ckd_add`, divisione sicura contro `0` e `INT64_MIN / -1`) e **valutazione a corto circuito**. (1) In `tabella_hash.h` e `tabella_hash.c` incapsula il **tipo opaco** `tabella_hash_t` con configurazione `ht_config_t`, ridimensionamento automatico al fattore di carico `0.75`, distruttori indipendenti per chiavi e valori e helper `ht_hash_stringa`/`ht_uguali_stringa`. (2) In `main.c` definisci `val_t` (`V_INT` o `V_BOOL`) e `env_t` (`tabella_hash_t *tab; struct env *genitore;`), configurando ciascuna tabella con chiavi `char *` possedute (`free`) e valori `val_t *` posseduti (`free`). Implementa `env_crea`, `env_distruggi`, `env_def` (inserisce solo nell'ambito corrente, rifiutando duplicati nello stesso ambito), `env_set` (aggiorna nel primo ambito della catena in cui il nome è definito) ed `env_get` (cerca risalendo la catena). (3) Leggi comandi da `stdin`: `ENTER` (apre un ambito figlio), `LEAVE` (chiude l'ambito corrente senza mai chiudere il globale), `DEF <nome> <int|true|false>`, `SET <nome> <int|true|false>`, `GET <nome>`, `ADD <a> <b>` (somma controllata con `ckd_add`), `DIV <a> <b>` (intercetta divisore `0` e `INT64_MIN / -1`) e `SHORT_AND <var_bool> <num> <den>` (valuta `var_bool && (num / den > 0)` applicando il corto circuito se `var_bool == false` senza eseguire la divisione). Distruggi tutti gli ambiti residui prima di uscire, producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- tabella hash generica come tipo opaco con possesso completo di chiavi `char *` e valori `valore_t *`
- catena di ambienti (`genitore`) per distinguere dichiarazione locale (`var`/`DEF`) da assegnamento (`SET`)
- controllo esplicito di overflow con `ckd_add` e dei casi proibiti `b == 0` e `INT64_MIN / -1`
- valutazione a corto circuito di `&&` per evitare di valutare un operando destro che genererebbe errore

**Domande guida**

1. Perché `DEF` verifica l'eventuale duplicato soltanto nella tabella dell'ambito corrente mentre `SET` risale la catena fino all'ambiente globale?
2. Che cosa succede alla variabile `x` dell'ambito globale quando un blocco interno esegue `DEF x 99` e poi viene chiuso con `LEAVE`?
3. Perché il comando `SHORT_AND` non produce `DIV_ZERO` quando la variabile booleana vale `false` e `den` vale `0`?
4. Come garantisce il programma che non resti memoria allocata sullo heap se l'input termina mentre ci sono ancora ambiti aperti con `ENTER`?

**Esempio di esecuzione**

```input
DEF x 10
DEF ok false
ENTER
DEF x 99
GET x
SET ok true
LEAVE
GET x
GET ok
ADD 9223372036854775807 1
DIV -9223372036854775808 -1
DEF flag false
SHORT_AND flag 10 0
SET flag true
SHORT_AND flag 10 0
SHORT_AND flag 10 3
```

```output
DEF x: OK
DEF ok: OK
ENTER prof=1
DEF x: OK
GET x: 99
SET ok: OK
LEAVE prof=0
GET x: 10
GET ok: true
ADD: OVERFLOW
DIV: OVERFLOW
DEF flag: OK
SHORT_AND: false (corto_circuito)
SET flag: OK
SHORT_AND: DIV_ZERO
SHORT_AND: true
```

## 26.5 Controllo di flusso e funzioni definite dall'utente

Un linguaggio che valuta soltanto espressioni è poco più di una calcolatrice. Per trasformare MiniL in un vero linguaggio imperativo occorre aggiungere il **flusso di controllo** (`if`/`else`, `while`), le funzioni definite dall'utente (`fn` e `return`, inclusa la ricorsione) e un insieme di funzioni predefinite (`abs`, `min`, `max`, `pot`).

L'esecuzione di `if`/`else` e `while` segue due regole rigide di robustezza:

1. **Condizione strettamente booleana**: in MiniL non esistono conversioni implicite da intero a booleano. Prima di decidere quale ramo eseguire, il valutatore calcola la condizione e controlla che il risultato abbia etichetta `VAL_BOOL`; se riceve `VAL_INT` o `VAL_NULLO`, registra un errore di tipo.
2. **Sotto-ambiente per i blocchi e guardia sui cicli**: ogni blocco `{ ... }` crea un proprio ambiente figlio con `genitore` uguale all'ambiente corrente e lo distrugge sempre all'uscita del blocco, anche se all'interno si è verificato un errore o un `return`. Nel ciclo `while`, inoltre, lo stato globale del valutatore incrementa un contatore di passi a ogni iterazione e interrompe l'esecuzione se supera `MAX_PASSI` (per esempio `10000`), impedendo che un ciclo infinito blocchi l'interprete o i test automatici.

Le funzioni definite dall'utente (`fn nome(p1, p2) { ... }`) sono registrate in una seconda `tabella_hash_t` (le cui chiavi sono i nomi delle funzioni e i cui valori sono puntatori `const nodo_t *` ai nodi `NODO_FN` nell'arena, quindi non posseduti dalla tabella perché l'arena stessa li rilascerà alla fine). Quando il valutatore incontra una chiamata `nome(a1, a2)`:

1. Valuta gli argomenti nell'ambiente del chiamante.
2. Controlla se `nome` è una funzione predefinita oppure una funzione definita dall'utente; in entrambi i casi verifica che il numero di argomenti coincida esattamente con l'**arità** attesa.
3. Incrementa il contatore `prof_chiamate` e lo confronta con `MAX_PROF_CHIAMATE` (per esempio `64`), fermando la ricorsione infinita molto prima che possa esaurire lo stack C.
4. Crea un nuovo ambiente di esecuzione `locale` con **`genitore = vm->globale`** (non l'ambiente del chiamante!) e inserisce in `locale` ciascun parametro legato al valore dell'argomento corrispondente.
5. Esegue il corpo della funzione dentro `locale`.
6. **Distrugge sempre `locale`** e decrementa `prof_chiamate` prima di restituire il risultato, sia su ritorno normale, sia su `return` anticipato, sia su errore.

Come si gestisce un'istruzione `return expr;` annidata dentro un `if`, dentro un `while`, dentro un altro blocco? Invece di ricorrere a salti non locali (`longjmp`), la soluzione più pulita e sicura per la memoria consiste nell'aggiungere due campi allo stato del valutatore: `bool in_ritorno` e `valore_t val_ritorno`. Quando viene eseguita `return expr;`, il valutatore calcola `expr`, salva il valore in `vm->val_ritorno` e imposta `vm->in_ritorno = true`. Ogni ciclo di esecuzione di blocco, `if` e `while` controlla `if (vm->in_ritorno || vm->err->attivo) { break; }`: in questo modo l'esecuzione risale ordinatamente tutte le funzioni C annidate, **distruggendo uno per uno ogni sotto-ambiente creato lungo la strada**, fino al confine della chiamata di funzione che azzera `vm->in_ritorno = false` e restituisce `vm->val_ritorno`.

Infine, le **funzioni predefinite** (`abs`, `min`, `max`, `pot`) si integrano elegantemente grazie ai **puntatori a funzione** (capitolo 16). Definiamo una firma uniforme per tutte le funzioni predefinite e le registriamo in una tabella `static const` di terne `(nome, arita, puntatore_a_funzione)`:

<!-- cod: id=26.5-b tipo=frammento -->
```c
typedef bool (*builtin_fn)(const valore_t *args, size_t n,
                           valore_t *out, errore_t *err);
```

Una sola funzione di dispatch cerca il nome in tabella, controlla che `n == arita` in un unico punto e invoca `voce.fn(args, n, out, err)`. Ogni funzione predefinita valida i tipi e i casi limite (come `abs(INT64_MIN)`, esponente negativo in `pot` e overflow via `ckd_mul`). Secondo lo standard C23, sia il bilanciamento esplicito tra creazione e distruzione degli ambienti sia l'invocazione indiretta tramite puntatori a funzione di tipo compatibile sono comportamenti completamente definiti.

> **Se vieni da Python** — In Python dizionari e funzioni di prima classe fanno parte del linguaggio base; in C gli ambienti di variabili e le funzioni predefinite si realizzano componendo la propria tabella hash generica opaca (`void *`) e i puntatori a funzione.

### Esempio guidato

Questo modulo dimostrativo registra due funzioni predefinite (`doppio` e `somma`) in una tabella di dispatch tramite puntatori a funzione e mostra come il flag `in_ritorno` interrompa un ciclo `while` annidato e restituisca il valore alla cornice della funzione chiamante senza perdere risorse.

<!-- cod: id=26.5-a tipo=programma -->
```c
#include <inttypes.h>
#include <stdckdint.h>
#include <stdio.h>
#include <string.h>

typedef bool (*builtin_fn)(const int64_t *args, size_t n, int64_t *out);

typedef struct voce_builtin {
    const char *nome;
    size_t arita;
    builtin_fn fn;
} voce_builtin_t;

static bool bi_doppio(const int64_t *args, size_t n, int64_t *out) {
    (void)n;
    return !ckd_mul(out, args[0], 2);
}

static bool bi_somma(const int64_t *args, size_t n, int64_t *out) {
    (void)n;
    return !ckd_add(out, args[0], args[1]);
}

static bool chiama_builtin(const char *nome, const int64_t *args, size_t n, int64_t *out) {
    static const voce_builtin_t TAB[] = {
        {"doppio", 1, bi_doppio},
        {"somma", 2, bi_somma}
    };
    for (size_t i = 0; i < sizeof(TAB) / sizeof(TAB[0]); ++i) {
        if (strcmp(TAB[i].nome, nome) == 0) {
            if (n != TAB[i].arita) {
                return false;
            }
            return TAB[i].fn(args, n, out);
        }
    }
    return false;
}

typedef struct stato_vm {
    bool in_ritorno;
    int64_t val_ritorno;
} stato_vm_t;

static void esegui_ciclo_con_return(stato_vm_t *vm, int64_t soglia) {
    int64_t somma = 0;
    int64_t k = 1;
    while (k <= 10 && !vm->in_ritorno) {
        somma += k;
        if (somma >= soglia) {
            vm->in_ritorno = true;
            vm->val_ritorno = k;
            break;
        }
        ++k;
    }
}

int main(void) {
    int64_t a1[] = {21};
    int64_t a2[] = {17, 25};
    int64_t ris = 0;
    if (chiama_builtin("doppio", a1, 1, &ris)) {
        printf("doppio(21) = %" PRId64 "\n", ris);
    }
    if (chiama_builtin("somma", a2, 2, &ris)) {
        printf("somma(17, 25) = %" PRId64 "\n", ris);
    }
    stato_vm_t vm = {};
    esegui_ciclo_con_return(&vm, 15);
    if (vm.in_ritorno) {
        printf("return anticipato al passo k = %" PRId64 "\n", vm.val_ritorno);
        vm.in_ritorno = false;
    }
    return 0;
}
```

```output
doppio(21) = 42
somma(17, 25) = 42
return anticipato al passo k = 5
```

Nota come `chiama_builtin` centralizzi la ricerca per nome e il controllo dell'arità: aggiungere una nuova funzione predefinita significa soltanto scrivere una piccola funzione `static bool` con la stessa firma e aggiungere una riga a `TAB`. Analogamente, `vm.in_ritorno` consente di uscire ordinatamente da cicli e blocchi annidati lasciando che ogni funzione esegua la propria pulizia finale.

> **Approfondimento — Ambito lessicale nelle chiamate di funzione**
> Perché il nuovo ambiente di una chiamata `fn` ha come `genitore` l'ambiente globale anziché quello del chiamante? Supponi che la funzione `f` usi una variabile `k` e chiami `g`, che a sua volta legge `k`. Se il genitore di `g` fosse l'ambiente di `f` (*ambito dinamico*), `g` vedrebbe per sbaglio le variabili locali di `f` e potrebbe persino sovrascriverle! Collegando ogni chiamata all'ambiente globale (*ambito lessicale* per funzioni di primo livello), ogni invocazione — anche ricorsiva — ha il proprio insieme isolato di parametri e variabili locali.

### Esercizio 26.5 — Tabella di funzioni predefinite tramite puntatori a funzione e gestione sicura di chiamate ricorsive e cicli

**Descrizione**

Realizza su tre file (`builtin.h`, `builtin.c`, `main.c`) il meccanismo di **funzioni predefinite** basato su **puntatori a funzione** e le guardie di esecuzione per ricorsione e cicli dell'interprete. (1) In `builtin.h` (protetto da `BUILTIN_H`) definisci `val_t` (`VT_INT`, `VT_BOOL`), il tipo puntatore a funzione `typedef bool (*builtin_fn)(const val_t *args, size_t n, val_t *out, char *err, size_t err_cap);` e `builtin_voce_t`, e dichiara `builtin_chiama`. (2) In `builtin.c` implementa cinque funzioni predefinite registrate in una tabella `static const builtin_voce_t`: `abs(x)` (rifiuta `INT64_MIN` con `overflow abs`), `min(a, b)`, `max(a, b)`, `pot(base, esp)` (rifiuta `esp < 0` con `esponente negativo` e controlla ogni prodotto con `ckd_mul` segnalando `overflow pot`) e `pari(x)` (restituisce `VT_BOOL`). In `builtin_chiama` verifica nome sconosciuto (`funzione sconosciuta`), arità errata (`arita errata`) e tipi degli argomenti (`tipo errato`). (3) In `main.c` leggi comandi da `stdin`: `CALL <nome> <n_args> [a0 ...]` (`0 <= n_args <= 4`, ogni argomento è `true`, `false` o `int64_t`), `FACT <n> <max_prof>` (calcola il fattoriale ricorsivo allocando e liberando una cornice dinamica `cornice_t` per ogni chiamata, rispettando il limite `max_prof`, intercettando `n < 0` e overflow con `ckd_mul`, e verificando che tutte le cornici create vengano liberate anche su errore) e `WHILE_SUM <n> <max_passi>` (somma `1..n` con un ciclo `while` protetto da contatore di passi `max_passi` e `ckd_add`), producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- tabella di dispatch `static const` con puntatori a funzione di firma uniforme per funzioni predefinite
- validazione sistematica di nome, arità, tipo degli argomenti e casi limite (`INT64_MIN`, esponente negativo, overflow)
- allocazione e rilascio garantito di ogni cornice di chiamata ricorsiva sia su ritorno sia su errore
- contatori di profondità massima e di passi massimi contro ricorsione e cicli infiniti

**Domande guida**

1. Perché conviene controllare l'arità in un unico punto dentro `builtin_chiama` invece di ripetere il controllo in ogni singola funzione predefinita?
2. Come mai `abs(INT64_MIN)` deve restituire un errore anziché calcolare `-x` in C?
3. In che modo il bilancio `cornici_create == cornici_liberate` dimostra l'assenza di perdite di memoria quando `FACT` si interrompe per profondità eccessiva?
4. Qual è la differenza tra il limite `max_prof` (per la ricorsione) e il limite `max_passi` (per i cicli `while`)?

**Esempio di esecuzione**

```input
CALL abs 1 -42
CALL abs 1 -9223372036854775808
CALL min 2 7 -3
CALL max 2 7 -3
CALL pot 2 2 10
CALL pot 2 2 -1
CALL pari 1 8
CALL abs 2 1 2
CALL ignota 0
FACT 6 10
FACT 6 3
WHILE_SUM 10 20
WHILE_SUM 10 5
```

```output
CALL abs: 42
CALL abs: ERRORE (overflow abs)
CALL min: -3
CALL max: 7
CALL pot: 1024
CALL pot: ERRORE (esponente negativo)
CALL pari: true
CALL abs: ERRORE (arita errata)
CALL ignota: ERRORE (funzione sconosciuta)
FACT(6): 720 (cornici=6/6)
FACT(6): ERR_PROFONDITA (cornici=4/4)
WHILE_SUM(10): 55 (passi=10)
WHILE_SUM(10): ERR_PASSI (passi=5)
```

## 26.6 L'interprete completo e la suite di test automatici

Hai ormai progettato e sperimentato ciascun ingranaggio di MiniL separatamente. L'ultima tappa consiste nel riunire gli otto moduli in un unico progetto C su più file:

- `arena.h` / `arena.c`: allocatore ad arena allineato ad `alignof(max_align_t)` per tutti i nodi dell'AST e le copie degli identificatori;
- `tabella_hash.h` / `tabella_hash.c`: tabella hash generica come tipo opaco (`void *`) con ridimensionamento automatico e distruttori personalizzati;
- `valore.h` / `valore.c`: unioni etichettate `valore_t` e `nodo_t`, struttura `errore_t` e buffer di output `out_buf_t`;
- `lexer.h` / `lexer.c`: analizzatore lessicale con coordinate, commenti `//` e parsing sicuro degli interi;
- `parser.h` / `parser.c`: analizzatore sintattico a discesa ricorsiva con sette livelli di precedenza e limite di profondità;
- `eval.h` / `eval.c`: valutatore con aritmetica controllata, corto circuito, ambienti lessicali a catena, `if`/`else`, `while`, funzioni `fn`, `return` e funzioni predefinite via puntatori a funzione;
- `test_fw.h`: mini framework di test automatici basato su macro `do { ... } while (0)` e puntatori a funzione (capitolo 25);
- `main.c`: suite di test integrata (`RUN_TESTS`) ed esecutore da `stdin` (`EXEC ... END`).

Ogni file di intestazione possiede una protezione di inclusione univoca (`ARENA_H`, `TABELLA_HASH_H`, `VALORE_H`, `LEXER_H`, `PARSER_H`, `EVAL_H`, `TEST_FW_H`) e dipendenze strettamente acicliche. Con la **compilazione separata** (capitolo 19), ogni file `.c` costituisce un'unità di traduzione autonoma, compilabile in un file oggetto `.o` e collegata nell'eseguibile finale con tutti gli avvisi attivi come errori: `-std=c23 -Wall -Wextra -Wpedantic -Werror`.

Il punto più delicato dell'integrazione è il coordinamento del ciclo di vita delle risorse dentro la funzione di ingresso `minil_esegui(const char *src, out_buf_t *out, errore_t *err)`. Una singola esecuzione di un programma MiniL acquisisce tre risorse distinte: l'**arena** che contiene l'AST, la **tabella hash delle funzioni** e l'**ambiente globale** delle variabili (oltre ai sotto-ambienti temporanei creati e distrutti durante l'esecuzione). Un errore può verificarsi in qualunque momento: durante l'inizializzazione dell'arena, durante il parsing di un'istruzione malformata, oppure a metà valutazione per una divisione per zero.

Per garantire zero perdite di memoria su ogni percorso di uscita — sia su successo sia su qualunque errore — si applica il modello **`goto cleanup`** del capitolo 21: tutte le risorse vengono inizializzate a `nullptr` (o stato vuoto) all'inizio della funzione; ogni fallimento imposta `errore_t` e salta a un'unica etichetta `cleanup:` in fondo alla funzione, che rilascia in ordine inverso l'ambiente globale, la tabella delle funzioni e l'arena. Poiché `ht_distruggi(nullptr)`, `env_distruggi(nullptr)` e `arena_distruggi` su un'arena vuota non eseguono alcuna azione, il blocco `cleanup:` è valido qualunque sia il punto in cui il salto è avvenuto. Secondo lo standard C23, la compilazione separata, le protezioni di inclusione, il salto `goto` verso un'etichetta nella stessa funzione e le macro `do { ... } while (0)` sono completamente definiti.

Per verificare la correttezza dell'intero interprete senza dover testare a mano decine di casi dopo ogni modifica, `main.c` integra una suite di **test automatici** deterministica costruita con `test_fw.h` (capitolo 25). Catturare l'output di `stampa` in un buffer `out_buf_t` anziché scrivere direttamente su `stdout` con `printf` rende ogni test automatico immediato: basta invocare `minil_esegui(sorgente, &out, &err)` e confrontare `out.dati` con la stringa attesa tramite `T_EQ_STR`. La suite copre sistematicamente otto categorie:

1. precedenza e associatività aritmetica (`10 - 3 - 2`, `2 + 3 * 4`, unari);
2. variabili, ambiti annidati e oscuramento (*shadowing*);
3. booleani e valutazione a corto circuito (`x != 0 && 10 / x > 1`);
4. controllo di flusso `if`/`else` e `while` (per esempio calcolo del MCD);
5. funzioni definite dall'utente e ricorsione (fattoriale, Fibonacci);
6. funzioni predefinite (`abs`, `min`, `max`, `pot`);
7. errori lessicali e sintattici (caratteri illegali, parentesi mancanti, overflow letterale);
8. errori di esecuzione (divisione per zero, overflow aritmetico, tipo errato nella condizione di `if`, variabile non dichiarata, arità errata, ciclo infinito).

L'ultima verifica prima di considerare pronto l'interprete è l'esecuzione dell'intera suite compilata con i **sanitizer** (capitolo 11): `-fsanitize=address,undefined` controlla a tempo di esecuzione che non esista neppure un accesso fuori dai limiti, un uso dopo la liberazione, un overflow con segno o una perdita di memoria in nessuno degli otto scenari.

### Esempio guidato

Quando tutti i file sorgenti dell'interprete MiniL sono pronti nella stessa cartella, puoi compilarli separatamente e collegarli con il comando seguente (aggiungendo `-fsanitize=address,undefined -g` durante i test di robustezza):

```text
cc -std=c23 -Wall -Wextra -Wpedantic -Werror -c arena.c tabella_hash.c valore.c lexer.c parser.c eval.c main.c
cc -std=c23 -Wall -Wextra -Wpedantic -Werror arena.o tabella_hash.o valore.o lexer.o parser.o eval.o main.o -o minil
```

Osserva passo passo che cosa accade dentro `minil` quando esegue un programma MiniL che stampa tutti i numeri primi fino a `20` usando una funzione `e_primo(n)`:

```text
  Sorgente MiniL:
    fn e_primo(n) {
        if (n < 2) { return false; }
        var d = 2;
        while (d * d <= n) {
            if (n % d == 0) { return false; }
            d = d + 1;
        }
        return true;
    }
    var k = 2;
    while (k <= 20) {
        if (e_primo(k)) { stampa k; }
        k = k + 1;
    }

  Traccia dell'esecuzione in minil_esegui:
  1. arena_crea(&arena, 65536) riserva il buffer unico dell'AST.
  2. lexer + parser producono nell'arena tre nodi di primo livello:
     NODO_FN("e_primo") -> NODO_VAR("k") -> NODO_WHILE(k <= 20).
  3. ht_crea crea la tabella delle funzioni e registra "e_primo" -> nodo AST.
  4. env_crea(nullptr) crea l'ambiente globale e inserisce "k" = 2.
  5. A ogni iterazione del while (k = 2..20):
     - chiama e_primo(k) creando un ambiente locale con genitore = globale;
     - inserisce il parametro "n" = k e la locale "d" = 2;
     - al primo divisore (o al termine del ciclo) imposta in_ritorno = true,
       distrugge l'ambiente locale di e_primo e restituisce VAL_BOOL;
     - se true, accoda k in out_buf_t ("2\n3\n5\n7\n11\n13\n17\n19\n").
  6. Etichetta cleanup: distrugge ambiente globale, tabella funzioni e arena AST.
```

Il breve programma C seguente dimostra in forma compatta l'accoppiamento tra il modello `goto cleanup` (che rilascia le risorse sia su successo sia su errore) e una macro di test `do { ... } while (0)` nello stile di `test_fw.h`, verificando il risultato atteso del filtro dei numeri primi fino a `20`.

<!-- cod: id=26.6-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define VERIFICA_STR(ctx, atteso, reale) do { \
    ++(ctx)->eseguiti; \
    if (strcmp((atteso), (reale)) == 0) { ++(ctx)->superati; } \
    else { ++(ctx)->falliti; } \
} while (0)

typedef struct test_ctx {
    size_t eseguiti;
    size_t superati;
    size_t falliti;
} test_ctx_t;

static bool esegui_pipeline(int limite, char *out, size_t cap) {
    bool ok = false;
    int *buf = malloc((size_t)(limite + 1) * sizeof(*buf));
    if (buf == nullptr) {
        goto cleanup;
    }
    size_t pos = 0;
    out[0] = '\0';
    for (int n = 2; n <= limite; ++n) {
        bool primo = true;
        for (int d = 2; d * d <= n; ++d) {
            if (n % d == 0) {
                primo = false;
                break;
            }
        }
        if (primo) {
            int scritti = snprintf(out + pos, cap - pos, "%s%d", pos > 0 ? " " : "", n);
            if (scritti < 0 || (size_t)scritti >= cap - pos) {
                goto cleanup;
            }
            pos += (size_t)scritti;
        }
    }
    ok = true;
cleanup:
    free(buf);
    return ok;
}

int main(void) {
    char out[64] = {};
    test_ctx_t ctx = {};
    if (esegui_pipeline(20, out, sizeof(out))) {
        printf("Primi <= 20: %s\n", out);
        VERIFICA_STR(&ctx, "2 3 5 7 11 13 17 19", out);
    }
    printf("Test: %zu/%zu falliti=%zu\n", ctx.superati, ctx.eseguiti, ctx.falliti);
    return ctx.falliti == 0 ? 0 : EXIT_FAILURE;
}
```

```output
Primi <= 20: 2 3 5 7 11 13 17 19
Test: 1/1 falliti=0
```

Osserva come in `esegui_pipeline` esista un solo punto di uscita `cleanup:` che libera `buf` sia in caso di successo (`ok = true`) sia in caso di buffer di output insufficiente (`goto cleanup`), e come la macro `VERIFICA_STR` incapsulata in `do { ... } while (0)` aggiorni il contesto di test in modo sicuro dentro qualunque costrutto `if`/`else`.

> **Approfondimento — Estensione facoltativa: un raccoglitore di memoria automatico per MiniL**
> Oggi MiniL gestisce solo valori scalari (`int64_t`, `bool`, `nullo`), facili da copiare per valore. Che cosa cambierebbe se volessi aggiungere al linguaggio stringhe e array dinamici creati a tempo di esecuzione? Poiché più variabili potrebbero riferirsi allo stesso array, liberarlo alla fine di un singolo blocco rischierebbe di lasciare puntatori pendenti in altri ambiti. La tecnica classica è un **raccoglitore di memoria automatico** (*garbage collector* a marcatura e scansione): si collegano tutti gli oggetti dinamici creati in una **lista intrusiva** (capitolo 24) con un flag `bool marcato`; quando la memoria allocata supera una soglia, la fase di **marcatura** parte dagli ambienti attivi nella pila delle chiamate e marca tutti gli oggetti raggiungibili; la fase di **scansione** percorre la lista intrusiva, libera con `free` gli oggetti rimasti non marcati e azzera il flag sui sopravvissuti.

### Progetto 26.6 — Interprete completo per il linguaggio MiniL su più file con suite di test automatici

**Descrizione**

Integra tutti i componenti progettati nel capitolo per realizzare l'interprete completo del linguaggio **MiniL** organizzato su più file (`arena.h`, `arena.c`, `tabella_hash.h`, `tabella_hash.c`, `valore.h`, `valore.c`, `lexer.h`, `lexer.c`, `parser.h`, `parser.c`, `eval.h`, `eval.c`, `test_fw.h`, `main.c`), privo di perdite di memoria e di comportamento indefinito. Il linguaggio supporta: valori `int64_t`, `bool` (`true`/`false`) e `nullo`; commenti `//`; operatori con precedenza (`||`, `&&` a corto circuito, `==`/`!=`, `<`/`<=`/`>`/`>=`, `+`/`-`, `*`/`/`/`%`, unari `-`/`!`); dichiarazione di variabili `var x = expr;`, assegnamento `x = expr;`, istruzione `stampa expr;`, `if (cond) { ... } else { ... }` (anche `else if`), `while (cond) { ... }`, dichiarazione e chiamata ricorsiva di funzioni `fn nome(p1, ...) { ... }` con `return [expr];`, e funzioni predefinite tramite puntatori a funzione (`abs`, `min`, `max`, `pot`). Tutti i nodi dell'**albero di sintassi astratta** vivono in un'**arena** (`arena.h/c`); gli ambienti delle variabili e la tabella delle funzioni usano la **tabella hash generica opaca** (`tabella_hash.h/c`). L'eseguibile accetta da `stdin` due comandi: `RUN_TESTS` (esegue la suite integrata di 8 **test automatici** con `test_fw.h` e stampa il riepilogo) ed `EXEC` seguito da righe di codice MiniL fino a una riga `END` (esegue il programma catturando l'output di `stampa` e stampa `--- OUTPUT ---` seguito dall'output e `--- OK ---`, oppure `--- ERRORE <riga>:<col>: <msg> ---`).

**Fasi**

1. Fase 1 — Strutture dati, valori e arena AST (`arena.h/c`, `valore.h/c`): implementa l'allocatore ad arena allineato ad `alignof(max_align_t)` e le unioni etichettate `valore_t` e `nodo_t` con `errore_t`. Criterio di verifica: allocazione di nodi AST e stringhe nell'arena con rilascio completo in `O(1)` e zero perdite con AddressSanitizer.
2. Fase 2 — Analizzatore lessicale (`lexer.h/c`): implementa la scansione di parole chiave, identificatori, letterali `int64_t` con `ckd_mul`/`ckd_add`, commenti `//` e operatori a 1 e 2 caratteri con riga e colonna. Criterio di verifica: riconoscimento esatto di tutti i token di MiniL e segnalazione puntuale di caratteri non validi e overflow.
3. Fase 3 — Analizzatore sintattico a discesa ricorsiva (`parser.h/c`): costruisci l'AST nell'arena per tutti i 7 livelli di precedenza e per tutte le istruzioni (`var`, assegnamento, `stampa`, `if`/`else`, `while`, `fn`, `return`) con limite di profondità 32. Criterio di verifica: `10 - 3 - 2` valuta `5`, `2 + 3 * 4` valuta `14` e parentesi o punti e virgola mancanti producono errori sintattici chiari.
4. Fase 4 — Valutatore di espressioni e ambienti su tabella hash opaca (`tabella_hash.h/c`, `eval.h/c`): collega `tabella_hash_t` agli ambienti a catena (con shadowing e lookup nel genitore), alla valutazione a corto circuito e all'aritmetica controllata con `<stdckdint.h>`. Criterio di verifica: `x != 0 && 10 / x > 1` non va in errore per `x = 0`, e divisione per zero o overflow producono errori puliti.
5. Fase 5 — Controllo di flusso, funzioni utente e funzioni predefinite (`eval.h/c`): implementa `if`/`else`, `while` con guardia a 10000 passi, funzioni ricorsive `fn` con `return` e guardia a 64 chiamate annidate, e funzioni predefinite `abs`, `min`, `max`, `pot` via puntatori a funzione. Criterio di verifica: fattoriale ricorsivo, Fibonacci, MCD con `while` e tutte le built-in producono i risultati attesi senza perdite di memoria.
6. Fase 6 — Integrazione su più file e suite di test automatici (`test_fw.h`, `main.c`): compila e collega l'intero interprete con `-std=c23 -Wall -Wextra -Wpedantic -Werror`, implementa la suite di 8 test automatici (`RUN_TESTS`) e l'esecutore da `stdin` (`EXEC ... END`). Criterio di verifica: 8/8 test superati, esecuzione deterministica di programmi validi ed errati da `stdin` e zero errori con AddressSanitizer e UndefinedBehaviorSanitizer.

**Concetti da tenere a mente**

- separazione modulare su più file con protezioni di inclusione e compilazione separata
- allocatore ad arena per l'intero ciclo di vita dell'albero di sintassi astratta
- tabella hash generica come tipo opaco per gli ambienti delle variabili e per la tabella delle funzioni
- puntatori a funzione per le funzioni predefinite e ricorsione con ambienti isolati per le funzioni utente
- modello `goto cleanup`, aritmetica controllata `<stdckdint.h>` e suite di test automatici con `test_fw.h`

**Domande guida**

1. In che modo il ciclo di vita dei nodi AST (gestiti dall'arena) differisce dal ciclo di vita degli ambienti delle chiamate di funzione (gestiti con `tabella_hash_t`)?
2. Come si propaga il valore di un'istruzione `return` annidata dentro un `while` e un `if` fino alla funzione chiamante senza perdere la memoria degli ambienti intermedi?
3. Perché conviene catturare l'output di `stampa` in un buffer `out_buf_t` anziché scrivere direttamente con `printf` dentro `eval.c`?
4. Quali controlli deve effettuare `eval.c` per impedire che un sorgente MiniL malformato provochi comportamento indefinito o esaurimento dello stack nell'interprete C?
5. Come permette il modello `goto cleanup` in `minil_esegui` di garantire l'assenza di perdite di memoria sia su errore lessicale/sintattico sia su errore di esecuzione?

**Esempio di esecuzione**

```input
RUN_TESTS
EXEC
fn fact(n) {
    if (n <= 1) {
        return 1;
    }
    return n * fact(n - 1);
}
var k = 1;
while (k <= 5) {
    stampa fact(k);
    k = k + 1;
}
END
```

```output
[PASS] aritmetica_precedenza
[PASS] variabili_ambiti
[PASS] booleani_corto_circuito
[PASS] if_else_while_mcd
[PASS] funzioni_ricorsive
[PASS] funzioni_predefinite
[PASS] errori_lessicali_sintattici
[PASS] errori_esecuzione
RIEPILOGO: test=8/8 falliti=0
--- OUTPUT ---
1
2
6
24
120
--- OK ---
```

## Riepilogo

- Un interprete completo separa la traduzione ed esecuzione in tre stadi distinti: l'**analizzatore lessicale** trasforma il codice sorgente in token tipizzati con coordinate `(riga, col)`; l'**analizzatore sintattico** a discesa ricorsiva costruisce l'**albero di sintassi astratta** rispettando precedenza e associatività; il **valutatore** esegue l'AST su una catena di **ambienti di esecuzione**.
- I valori a tempo di esecuzione (`valore_t`) e i nodi AST (`nodo_t`) sono modellati come **unioni etichettate** (`enum` + `union`), accedendo sempre a un campo solo dopo aver verificato l'etichetta. Tutti i nodi dell'AST e le copie degli identificatori vivono in un **allocatore ad arena** allineato ad `alignof(max_align_t)`, rilasciato in un colpo solo in `O(1)` anche quando il parser si arresta per un errore.
- Nell'analizzatore lessicale ogni carattere viene convertito a `unsigned char` prima di invocare `<ctype.h>`, i letterali interi usano `ckd_mul` e `ckd_add` contro gli overflow e gli operatori a due caratteri (`==`, `!=`, `<=`, `>=`, `&&`, `||`) vengono riconosciuti con uno sguardo in avanti di un carattere.
- Nell'analizzatore sintattico la stratificazione delle funzioni codifica i livelli di precedenza e i cicli `while` assicurano l'associatività a sinistra senza ricorsione sinistra; un contatore `MAX_PROF_PARSE` protegge lo stack da parentesi profondamente annidate.
- Il valutatore protegge il programma ospite C da qualsiasi comportamento indefinito usando `<stdckdint.h>`, intercettando `b == 0` e `INT64_MIN / -1` (e `% -1`), applicando il corto circuito su `&&`/`||` e imponendo guardie sui passi dei cicli (`MAX_PASSI`) e sulla profondità delle chiamate ricorsive (`MAX_PROF_CHIAMATE`).
- Gli ambienti delle variabili usano la **tabella hash generica come tipo opaco** (`void *`) con possesso completo di chiavi e valori; le funzioni predefinite sono registrate tramite **puntatori a funzione**; l'integrazione su più file coordina il rilascio deterministico con `goto cleanup` ed è verificata con test automatici e sanitizer.

## Errori comuni

- **Usare ricorsione sinistra o ricorsione destra nell'analizzatore sintattico**: chiamare subito `parse_somma` dentro `parse_somma` provoca ricorsione infinita e stack overflow; chiamare ricorsivamente `parse_somma` dopo `'-'` raggruppa `10 - 3 - 2` come `10 - (3 - 2) = 9` anziché `5`. Usa sempre un ciclo `while` per gli operatori binari associativi a sinistra.
- **Allocare i nodi dell'AST con `malloc` individuali senza un'arena**: quando il parser incontra un errore di sintassi a metà espressione è facilissimo dimenticare di liberare i sottoalberi parziali già costruiti. L'allocatore ad arena elimina il problema alla radice rilasciando tutto insieme.
- **Non proteggere l'interprete dai casi di comportamento indefinito provocati dal codice utente**: delegare direttamente `/`, `%`, `+` o `*` agli operatori C senza controllare divisore zero, `INT64_MIN / -1`, overflow con `<stdckdint.h>`, ricorsione infinita o cicli senza fine espone l'interprete a crash e risultati imprevedibili.
- **Dimenticare di distruggere l'ambiente locale di una chiamata di funzione su `return` anticipato o errore**: ogni chiamata `fn` alloca una nuova tabella hash; uscire prima della fine della funzione senza distruggerla genera perdite di memoria crescenti a ogni iterazione o chiamata ricorsiva.
- **Passare `char` con segno direttamente a `isspace`, `isalpha`, `isdigit` o `isalnum` nel lexer**: su sistemi in cui `char` è con segno, un byte con bit più significativo a `1` diventa un intero negativo diverso da `EOF` e provoca comportamento indefinito. Converti sempre a `(unsigned char)`.

## Prima di proseguire

- [ ] So progettare valori a tempo di esecuzione e nodi di un albero di sintassi astratta con unioni etichettate e gestirne la memoria con un allocatore ad arena.
- [ ] So scrivere un analizzatore lessicale senza allocazioni sullo heap con coordinate di riga/colonna, cast a `unsigned char` e parsing sicuro degli interi con `<stdckdint.h>`.
- [ ] So implementare un analizzatore sintattico a discesa ricorsiva che codifica precedenza e associatività a sinistra tramite cicli `while` e controlla la profondità massima di ricorsione.
- [ ] So costruire ambienti lessicali a catena sulla tabella hash generica opaca gestendo oscuramento, corto circuito e aritmetica priva di comportamento indefinito.
- [ ] So integrare controllo di flusso, funzioni ricorsive con `return`, funzioni predefinite via puntatori a funzione, `goto cleanup` e una suite di test automatici su più file verificata con AddressSanitizer e UndefinedBehaviorSanitizer.
