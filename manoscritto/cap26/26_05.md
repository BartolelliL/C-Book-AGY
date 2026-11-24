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

Infine, le **funzioni predefinite** (`abs`, `min`, `max`, `pot`) si integrano elegantemente grazie ai **puntatori a funzione** (capitolo 16). Definiamo una firma uniforme per tutte le funzioni predefinite e le registriamo in una tabella `static const` di coppie `(nome, arita, puntatore_a_funzione)`:

<!-- cod: id=26.5-b tipo=frammento -->
```c
typedef bool (*builtin_fn)(const valore_t *args, size_t n,
                           valore_t *out, errore_t *err);
```

Una sola funzione di dispatch cerca il nome in tabella, controlla che `n == arita` in un unico punto e invoca `voce.fn(args, n, out, err)`. Ogni funzione predefinita valida i tipi e i casi limite (come `abs(INT64_MIN)`, esponente negativo in `pot` e overflow via `ckd_mul`). Secondo lo standard C23, sia il bilanciamento esplicito tra creazione e distruzione degli ambienti sia l'invocazione indiretta tramite puntatori a funzione di tipo compatibile sono comportamenti completamente definiti.

> **Se vieni da Python** — In Python dizionari e funzioni di prima classe fanno parte del linguaggio base; in C gli ambienti di variabili e le funzioni predefinite si realizzano componendo la propria tabella hash generica opaca (`void *`) e i puntatori a funzione.

### Esempio guidato

Questo modulo dimostrativo registra due funzioni predefinite (`doppio` e `somma_sicura`) in una tabella di dispatch tramite puntatori a funzione e mostra come il flag `in_ritorno` interrompa un ciclo `while` annidato e restituisca il valore alla cornice della funzione chiamante senza perdere risorse.

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
