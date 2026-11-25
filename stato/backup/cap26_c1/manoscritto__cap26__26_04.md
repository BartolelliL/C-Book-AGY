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

Qui entra finalmente in azione il traguardo centrale di questo libro: la **tabella hash generica come tipo opaco** costruita nei capitoli 18 e 19 (`tabella_hash.h`). Ogni nodo della catena è una piccola `struct ambiente_t` che racchiude una `tabella_hash_t *tab` e un puntatore `struct ambiente *genitore`:

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
    env_def(&glob, "x", 10);
    env_def(&glob, "y", 1);
    env_def(&bloc, "x", 99);

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
