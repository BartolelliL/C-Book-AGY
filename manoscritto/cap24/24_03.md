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

1. **Contesti sintattici ammessi per `setjmp`**: `setjmp` può comparire **soltanto** come intera espressione di controllo di `if`, `switch`, `while`, `do-while` o `for`, oppure confrontata con una costante intera tramite un operatore relazionale o di uguaglianza (es. `if (setjmp(env) == 0)`), oppure come operando di `!`, oppure come istruzione il cui valore viene scartato. Scrivere `int rc = setjmp(env);` è vietato dallo standard e provoca comportamento indefinito. Se vuoi sapere quale errore si è verificato, memorizza il codice e la posizione in una `struct` di contesto prima di chiamare `longjmp(env, 1)`.
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

Il programma seguente simula un parser di configurazione su tre livelli di chiamata (`analizza_config` → `analizza_sezione` → `analizza_coppia`). Un contesto `ctx_parser_t` contiene `jmp_buf`, codice d'errore, riga incriminata e il puntatore a un buffer dinamico allocato durante il parsing. Quando il livello più profondo incontra un valore negativo o una riga malformata, invoca `segnala_errore` (`longjmp`), risalendo direttamente al chiamante `esegui_parse`, dove la variabile `volatile int fase` mantiene il proprio valore aggiornato e il buffer tracciato viene sempre liberato.

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

static void esegui_parse(const char *nome, const char *const *righe, size_t n) {
    ctx_parser_t ctx = {.messaggio = nullptr, .riga = 0, .buf_lavoro = nullptr};
    volatile int fase = 0;

    printf("Analisi %s:\n", nome);
    if (setjmp(ctx.env) == 0) {
        fase = 1;
        analizza_sezione(&ctx, righe, n);
        fase = 2;
        free(ctx.buf_lavoro);
        printf("Esito %s: COMPLETATO (fase=%d)\n", nome, fase);
    } else {
        free(ctx.buf_lavoro);
        printf("Esito %s: ERRORE alla riga %d (fase=%d): %s\n",
               nome, ctx.riga, fase, ctx.messaggio);
    }
}

int main(void) {
    const char *ok_cfg[] = {"porta=8080", "timeout=30"};
    const char *ko_cfg[] = {"porta=8080", "timeout=-5", "retry=3"};

    esegui_parse("cfg_valida", ok_cfg, 2);
    esegui_parse("cfg_errata", ko_cfg, 3);
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

- `setjmp(ctx.env)` appare nella forma ammessa `if (setjmp(ctx.env) == 0)`.
- `fase` è qualificata `volatile int` perché viene modificata (`fase = 1;`) dopo `setjmp` e riletta nel ramo `else` dopo `longjmp`.
- `ctx.buf_lavoro` è salvato nella struttura `ctx` prima di poter scatenare qualsiasi errore, quindi `free(ctx.buf_lavoro)` nel ramo `else` rilascia il blocco allocato dentro `analizza_sezione` senza alcuna perdita di memoria.
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
3. Che cosa succederebbe alla memoria allocata con `malloc` dentro `valuta_stringa` se `longjmp` saltasse fuori dalla ricorsione senza il registro risorse di `frame_err_t`?
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
