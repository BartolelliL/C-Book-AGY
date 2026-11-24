## 26.3 L'analizzatore sintattico

Una volta che l'analizzatore lessicale produce una sequenza pulita di token, il secondo stadio dell'interprete deve verificare che quei token rispettino la grammatica di MiniL e costruire l'albero di sintassi astratta. Questo compito spetta all'**analizzatore sintattico** (*parser*): il componente che verifica la grammatica della sequenza di token e costruisce l'albero di sintassi astratta rispettando precedenza e associatività.

La tecnica più chiara e diretta da scrivere a mano in C è la **discesa ricorsiva** (*recursive descent*). L'idea è immediata: a ogni regola grammaticale del linguaggio corrisponde una funzione C che consuma i token previsti da quella regola e restituisce un puntatore al sottoalbero `nodo_t *` appena allocato nell'arena (oppure `nullptr` in caso di errore).

Per coordinare il flusso dei token, il parser conserva in una `struct parser_t` un puntatore al lexer, il token corrente `cur` (sempre pronto per essere ispezionato), un puntatore all'arena dell'AST, un puntatore a `errore_t` e un contatore di profondità `prof`. Tre piccoli helper rendono ogni regola grammaticale leggibile quasi come una specifica formale:

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
