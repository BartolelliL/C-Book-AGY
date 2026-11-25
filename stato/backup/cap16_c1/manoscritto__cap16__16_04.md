## 16.4 Tabelle di puntatori a funzione

Quando un programma deve rispondere a molti comandi diversi — per esempio le istruzioni di una calcolatrice, i comandi di un terminale interattivo o le azioni associate ai vari stati di un protocollo — il primo istinto è scrivere una lunga catena di `if-else if` su `strcmp` oppure un enorme costrutto `switch` con decine di `case`. Finché le scelte sono tre o quattro, uno `switch` funziona bene; ma quando le voci diventano dieci, venti o più, la funzione di smistamento diventa lunga, ripetitiva e difficile da estendere senza introdurre errori.

Con i puntatori a funzione puoi spostare la logica di scelta dal codice ai **dati**, costruendo una **tabella di puntatori a funzione** (*dispatch table*). Ne esistono due forme principali, entrambe molto diffuse nel C professionale:

1. **Tabella indicizzata da intero o `enum`**: un array di puntatori a funzione (`static const azione_fn AZIONI[] = { ... };`) in cui il codice numerico o il valore dell'`enum` seleziona direttamente la funzione in tempo costante con `AZIONI[codice](...)`.
2. **Tabella di `struct` chiave-funzione**: un array di strutture che associano una chiave simbolica (per esempio `const char *nome`) al corrispondente puntatore a funzione, interrogato con una scansione lineare o con `bsearch` se la tabella è ordinata per chiave.

### Progettare una firma uniforme

Il requisito indispensabile per inserire più funzioni nella stessa tabella è che **tutte abbiano esattamente la stessa firma**. Nella pratica, però, comandi diversi potrebbero aver bisogno di dati leggermente diversi (un comando `CLR` non prende argomenti, mentre `SET` ne prende due). Per conciliare questa diversità con una firma uniforme si adotta uno schema semplice e pulito: ogni funzione della tabella riceve un puntatore a una `struct` di stato condiviso (per esempio il contesto della calcolatrice o della macchina) e un parametro comune per gli argomenti (per esempio `const char *args` oppure due `double`), restituendo un `bool` o un codice di esito.

In questo modo lo smistatore non deve sapere che cosa fa ogni singolo comando: cerca la voce nella tabella, invoca il puntatore a funzione passando lo stato condiviso e gli argomenti, e controlla il valore restituito. Aggiungere un nuovo comando significa scrivere una nuova funzione con quella firma e inserire una riga nella tabella, senza toccare la logica di smistamento.

### Controlli essenziali di sicurezza e `static_assert`

Le tabelle di puntatori a funzione sono veloci e ordinate, ma richiedono due verifiche difensive imprescindibili prima di ogni chiamata indiretta:

1. **Controllo dei limiti dell'indice**: per una tabella indicizzata da intero o `enum`, verifica sempre che `idx < num_voci` (usando `size_t` oppure controllando anche `idx >= 0` se il valore arriva da input con segno). Accedere a `tabella[idx]` con un indice fuori dai limiti provoca **comportamento indefinito**.
2. **Controllo contro `nullptr`**: verifica sempre che `tabella[idx] != nullptr` (o `voce->esegui != nullptr`) prima di invocare la funzione, soprattutto se la tabella può avere voci non ancora implementate o disabilitate.

Per le tabelle indicizzate da un `enum`, esiste un errore di manutenzione tipico: qualcuno aggiunge un nuovo valore all'`enum` ma dimentica di aggiungere la funzione corrispondente nella tabella (o viceversa). Puoi prevenire completamente questo errore a tempo di compilazione combinando un valore sentinella nell'`enum` (come `FMT_CONTEGGIO`) con `static_assert` (capitolo 15):

<!-- cod: id=16.4-b tipo=frammento -->
```c
typedef enum formato {
    FMT_BREVE = 0,
    FMT_ESTESO = 1,
    FMT_CONTEGGIO = 2
} formato_t;

typedef void (*stampa_fn)(double valore);

static const stampa_fn STAMPATORI[] = {stampa_breve, stampa_esteso};
static_assert(sizeof(STAMPATORI) / sizeof(STAMPATORI[0]) == FMT_CONTEGGIO,
              "STAMPATORI deve avere una voce per ogni formato_t");
```

Se in futuro aggiungi un terzo formato all'`enum` senza aggiornare `STAMPATORI`, la compilazione si ferma immediatamente con un messaggio chiaro, prima ancora di eseguire il programma.

### Smistamento di comandi testuali con `bsearch`

Quando i comandi sono identificati da nomi testuali (come `"add"`, `"sub"`, `"mul"`, `"div"`), puoi definire una `struct` di voce e dichiarare la tabella `static const` con le voci in ordine alfabetico crescente rispetto a `nome`:

```text
TABELLA_OP (ordinata per nome):
  [0] {"add", op_add}
  [1] {"div", op_div}
  [2] {"mul", op_mul}
  [3] {"sub", op_sub}
```

Per smistare un comando letto dall'input, costruisci una voce chiave con `.nome = nome_letto` e chiami `bsearch` (sotto-sezione 16.3) con un comparatore basato su `strcmp`. Se `bsearch` restituisce `nullptr` il comando è sconosciuto; altrimenti verifichi `voce->fn != nullptr` e lo invochi. Quando la tabella ha poche voci una scansione lineare è altrettanto semplice; quando le voci crescono, `bsearch` mantiene la ricerca rapida e il codice identico.

### Tabella di puntatori a funzione rispetto a `switch`

Una tabella di puntatori a funzione non rende obsoleto lo `switch`, ma lo affianca quando il problema diventa guidato dai dati. La stessa idea torna in due architetture centrali della seconda parte del libro: le **macchine a stati finiti** (lo vedremo nel capitolo 24), in cui ogni coppia `(stato, evento)` seleziona una funzione di transizione da una tabella, e la tabella dei comandi e degli operatori dell'**interprete finale** (lo vedremo nel capitolo 26).

> **Se vieni da Python** — In Python per scegliere un'operazione a partire dal suo nome si usa spesso un dizionario che mappa stringhe a funzioni (`{"add": op_add, ...}`); in C si costruisce una tabella statica di `struct` `{ nome, puntatore_a_funzione }` interrogata con scansione o `bsearch`, oppure un array di puntatori a funzione indicizzato direttamente da un `enum`.

### Esempio guidato

Il programma seguente realizza una piccola calcolatrice a quattro operazioni senza usare alcuno `switch` né alcuna catena di `if-else` sui nomi delle operazioni. Le operazioni sono raccolte in una tabella `static const` di strutture `{ nome, fn }` ordinata alfabeticamente e cercata con `bsearch`; lo stile di stampa del risultato è invece gestito da una tabella di puntatori a funzione indicizzata da `enum` e protetta da `static_assert`.

<!-- cod: id=16.4-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef bool (*op_fn)(double a, double b, double *ris);

typedef struct voce_op {
    const char *nome;
    op_fn fn;
} voce_op_t;

typedef enum stile_out {
    STILE_BREVE = 0,
    STILE_ESTESO = 1,
    STILE_CONTEGGIO = 2
} stile_out_t;

typedef void (*stampa_fn)(const char *op, double a, double b, double ris);

bool op_add(double a, double b, double *ris) { *ris = a + b; return true; }
bool op_sub(double a, double b, double *ris) { *ris = a - b; return true; }
bool op_mul(double a, double b, double *ris) { *ris = a * b; return true; }
bool op_div(double a, double b, double *ris) {
    if (b == 0.0) {
        return false;
    }
    *ris = a / b;
    return true;
}

static const voce_op_t TABELLA_OP[] = {
    {"add", op_add},
    {"div", op_div},
    {"mul", op_mul},
    {"sub", op_sub}
};

void stampa_breve(const char *op, double a, double b, double ris) {
    (void)a;
    (void)b;
    printf("%s -> %.2f\n", op, ris);
}

void stampa_esteso(const char *op, double a, double b, double ris) {
    printf("%s(%.2f, %.2f) = %.2f\n", op, a, b, ris);
}

static const stampa_fn STAMPATORI[] = {stampa_breve, stampa_esteso};
static_assert(sizeof(STAMPATORI) / sizeof(STAMPATORI[0]) == STILE_CONTEGGIO,
              "STAMPATORI deve avere una voce per ogni stile_out_t");

int cmp_voce_op(const void *a, const void *b) {
    const voce_op_t *va = a;
    const voce_op_t *vb = b;
    return strcmp(va->nome, vb->nome);
}

int main(void) {
    constexpr size_t num_op = sizeof(TABELLA_OP) / sizeof(TABELLA_OP[0]);
    const char *nomi[] = {"add", "mul", "div", "div", "pow"};
    const double lhs[] = {12.0, 3.5, 10.0, 10.0, 2.0};
    const double rhs[] = {4.0, 2.0, 4.0, 0.0, 3.0};
    const size_t stile = STILE_ESTESO;

    for (size_t i = 0; i < sizeof(nomi) / sizeof(nomi[0]); ++i) {
        voce_op_t chiave = {.nome = nomi[i], .fn = nullptr};
        const voce_op_t *voce = bsearch(&chiave, TABELLA_OP, num_op,
                                        sizeof(TABELLA_OP[0]), cmp_voce_op);
        double ris = 0.0;
        if (voce == nullptr || voce->fn == nullptr) {
            printf("Operazione sconosciuta: %s\n", nomi[i]);
        } else if (!voce->fn(lhs[i], rhs[i], &ris)) {
            printf("Errore nell'operazione %s\n", nomi[i]);
        } else if (stile < STILE_CONTEGGIO && STAMPATORI[stile] != nullptr) {
            STAMPATORI[stile](nomi[i], lhs[i], rhs[i], ris);
        }
    }
    return 0;
}
```

```output
add(12.00, 4.00) = 16.00
mul(3.50, 2.00) = 7.00
div(10.00, 4.00) = 2.50
Errore nell'operazione div
Operazione sconosciuta: pow
```

Nota come la struttura del programma separa completamente i dati dal controllo:

- Tutte e quattro le operazioni condividono la firma uniforme `bool op_fn(double a, double b, double *ris)`: restituiscono `true` in caso di successo e `false` se l'operazione non è eseguibile (come la divisione per zero).
- `TABELLA_OP` è ordinata alfabeticamente (`"add"`, `"div"`, `"mul"`, `"sub"`), prerequisito indispensabile affinché `bsearch` funzioni correttamente.
- `STAMPATORI` è indicizzata da `stile_out_t` e la `static_assert` assicura che la tabella resti sempre allineata con l'`enum`. Prima di invocare `STAMPATORI[stile]`, il codice controlla sia `stile < STILE_CONTEGGIO` sia `STAMPATORI[stile] != nullptr`.

> **Approfondimento — Quando conviene una tabella di puntatori a funzione rispetto a uno `switch`**
> Una tabella di puntatori a funzione conviene quando le operazioni sono numerose, condividono tutte la stessa firma, devono essere selezionate a partire da un nome testuale o un codice denso, oppure quando il programma va esteso spesso aggiungendo nuove voci (basta aggiungere dati alla tabella). Al contrario, quando i casi sono solo tre o quattro, hanno argomenti eterogenei o richiedono poche righe inline senza bisogno di funzioni separate, un normale `switch` resta più semplice, più diretto e spesso anche più facile da ottimizzare per il compilatore.

### Esercizio 16.4 — Interprete di istruzioni su registri con tabella di comandi (`bsearch`) e tabella di stampa indicizzata da `enum`

**Descrizione**

Scrivi un programma C che simuli una piccola macchina a `4` registri a `64` bit (`typedef struct macchina { int64_t reg[4]; size_t ops_eseguite; } macchina_t;`) usando due tabelle di puntatori a funzione senza alcun costrutto `switch` sulle operazioni o sui formati di stampa. (1) Definisci `typedef bool (*comando_fn)(macchina_t *m, const char *args);` e `typedef struct voce_cmd { const char *nome; comando_fn esegui; } voce_cmd_t;`, poi costruisci una tabella `static const voce_cmd_t TABELLA_CMD[]` ordinata alfabeticamente per `nome` con `7` comandi: `ADD <dst> <src>` (`reg[dst] += reg[src]`), `CLR` (azzera tutti i registri con `memset`), `MOV <dst> <src>` (`reg[dst] = reg[src]`), `MUL <dst> <k>` (`reg[dst] *= k`), `SET <dst> <val>` (`reg[dst] = val`), `SUB <dst> <src>` (`reg[dst] -= reg[src]`) e `SWAP <a> <b>` (scambia `reg[a]` e `reg[b]`), controllando sempre che gli indici di registro siano in `0..3` e che non vi siano argomenti in eccesso. (2) Definisci `typedef enum formato_out { FMT_DEC = 0, FMT_HEX = 1, FMT_SOMMA = 2, FMT_CONTEGGIO = 3 } formato_out_t;` e `typedef void (*stampa_fn)(const macchina_t *m);` con una tabella `static const stampa_fn STAMPATORI[]` di `3` funzioni (`DEC` stampa i registri in decimale, `HEX` li stampa come `0x%016" PRIx64` castati a `uint64_t`, `SOMMA` stampa la somma dei `4` registri) e verifica a tempo di compilazione con `static_assert` che la lunghezza di `STAMPATORI` coincida con `FMT_CONTEGGIO`. In `main` leggi dalla prima riga il codice intero del formato (`0`, `1` o `2`; se invalido scrivi su `stderr` e restituisci `EXIT_FAILURE`), poi leggi comandi fino a fine input: cerca ciascun nome di comando in `TABELLA_CMD` tramite `bsearch`, stampa `Comando sconosciuto: <nome>` se assente, invoca `voce->esegui(&m, args)` verificando `!= nullptr`, incrementa `m.ops_eseguite` in caso di successo oppure stampa `Argomenti non validi per <nome>`. Al termine invoca `STAMPATORI[fmt](&m)` (dopo aver controllato l'indice e `!= nullptr`) e stampa `Operazioni eseguite: <ops>` esattamente come nell'esempio.

**Concetti da tenere a mente**

- tabella di puntatori a funzione associati per nome e cercati con ricerca binaria tramite `bsearch`
- firma uniforme per tutti i gestori di comando (`macchina_t *m, const char *args`)
- tabella di puntatori a funzione indicizzata da `enum` con verifica `static_assert` sulla dimensione
- validazione rigorosa degli indici e controllo contro `nullptr` prima di ogni chiamata indiretta

**Domande guida**

1. Perché le voci di `TABELLA_CMD` devono essere disposte in ordine alfabetico crescente rispetto al campo `nome`?
2. Quale errore di manutenzione previene la `static_assert` che confronta `sizeof(STAMPATORI) / sizeof(STAMPATORI[0])` con `FMT_CONTEGGIO`?
3. Perché ogni gestore di comando accetta `const char *args` invece di un numero fisso di parametri interi?
4. Quali controlli servono prima di eseguire `STAMPATORI[fmt](&m)` per garantire assenza di comportamento indefinito?

**Esempio di esecuzione**

```input
0
SET 0 10
SET 1 25
ADD 0 1
MUL 0 2
SWAP 0 3
SUB 3 1
MOV 2 3
FOO 1 2
SET 9 100
```

```output
Comando sconosciuto: FOO
Argomenti non validi per SET
Registri (DEC): R0=0 R1=25 R2=45 R3=45
Operazioni eseguite: 7
```
