# Capitolo 16 — Puntatori a funzione

> **In questo capitolo imparerai a:**
> - Dichiarare, assegnare e invocare puntatori a funzione anche tramite `typedef` leggibili
> - Passare funzioni di richiamo (`callback`) per parametrizzare algoritmi generici
> - Ordinare e cercare array di qualsiasi tipo con `qsort` e `bsearch` scrivendo comparatori corretti
> - Organizzare scelte operative con tabelle di puntatori a funzione

> **Ti servono:** Capitoli 7 (funzioni e prototipi), 10 (puntatori e `nullptr`), 12 (`struct`, `enum` e `typedef`), 14 (puntatori avanzati) e 15 (`void *`, contenitori generici e `static_assert`).

Nel capitolo precedente hai visto come un puntatore generico `void *` permetta di scrivere contenitori e funzioni indipendenti dal tipo dei dati memorizzati. Un vettore dinamico generico, però, sa solo copiare e spostare sequenze grezze di byte: non sa come confrontare due elementi per ordinarli, né come decidere se un elemento soddisfa una condizione, né quale operazione eseguire durante una visita. Se vuoi rendere generico anche il *comportamento* di un algoritmo, oltre al tipo dei suoi dati, devi poter passare una funzione a un'altra funzione come se fosse un normale argomento.

In C questo meccanismo si realizza con i **puntatori a funzione**: variabili che memorizzano l'indirizzo di una funzione e permettono di invocarla indirettamente. Grazie ai puntatori a funzione puoi scrivere un algoritmo una sola volta e personalizzarne i passi decisivi tramite funzioni di richiamo (*callback*), esattamente come fanno le funzioni `qsort` e `bsearch` della libreria standard per ordinare e cercare array di qualunque tipo.

Lo stesso strumento ti permette di sostituire lunghe catene di `if-else` o `switch` con tabelle di puntatori a funzione, in cui un codice numerico o il nome di un comando seleziona direttamente l'operazione da eseguire. È un mattone fondamentale per il resto del libro: lo ritroverai nelle strutture dati dinamiche dei capitoli 17 e 18, nelle macchine a stati finiti del capitolo 24 e nella gestione dei comandi dell'interprete finale del capitolo 26.

## 16.1 Dichiarare e usare puntatori a funzione

Finora hai usato i puntatori per memorizzare l'indirizzo di oggetti in memoria: variabili intere, array, stringhe e strutture. Ma quando un programma C viene compilato e caricato in memoria, anche le istruzioni macchina che compongono ogni funzione risiedono in una zona precisa della memoria e hanno un proprio indirizzo di ingresso. Il linguaggio C ti permette di conservare quell'indirizzo in una variabile e di chiamare la funzione in un secondo momento senza conoscerne in anticipo il nome fisso nel punto della chiamata.

Una variabile di questo tipo è chiamata **puntatore a funzione** (*function pointer*): è un puntatore che contiene l'indirizzo di una funzione con una firma specifica e permette di chiamarla indirettamente. Proprio come un `int *` non memorizza soltanto un indirizzo generico ma porta con sé il tipo `int` dell'oggetto puntato, un puntatore a funzione porta sempre con sé il tipo di ritorno e i tipi dei parametri della funzione a cui può puntare. Questo consente al compilatore di verificare che ogni chiamata indiretta rispetti il numero e il tipo degli argomenti attesi.

### Sintassi della dichiarazione e ruolo delle parentesi

La sintassi di base per dichiarare un puntatore a funzione ricalca quella di un prototipo, ma il nome del puntatore è preceduto da `*` e racchiuso tra parentesi:

```text
tipo_ritorno (*nome)(tipi_parametri);
```

Per esempio, per dichiarare un puntatore `conv` capace di puntare a qualsiasi funzione che riceve un `double` e restituisce un `double`, scrivi:

<!-- cod: id=16.1-c tipo=frammento -->
```c
double (*conv)(double) = nullptr;
```

Le parentesi attorno a `(*conv)` sono **obbligatorie**. In C l'operatore di chiamata `()` ha precedenza più alta dell'asterisco `*`. Se dimentichi le parentesi e scrivi:

<!-- cod: id=16.1-d tipo=frammento -->
```c
double *conv(double);  // NON è un puntatore a funzione!
```

stai dichiarando il prototipo di una funzione chiamata `conv` che riceve un `double` e restituisce un `double *` (un puntatore a `double`), cioè qualcosa di completamente diverso. Le parentesi forzano `*` a legarsi prima a `conv`, indicando che `conv` è un puntatore e che ciò a cui punta è una funzione `(double) -> double`.

### Assegnazione, decadimento automatico e invocazione

Come avviene per il nome di un array nella maggior parte delle espressioni, anche il nome di una funzione subisce un decadimento automatico: quando compare senza parentesi di chiamata, si converte implicitamente nell'indirizzo della funzione stessa. Di conseguenza, se esiste una funzione `double celsius_a_fahrenheit(double c)`, le due assegnazioni seguenti sono del tutto equivalenti secondo lo standard C23:

<!-- cod: id=16.1-e tipo=frammento -->
```c
double (*conv)(double) = celsius_a_fahrenheit;  // decadimento automatico
conv = &celsius_a_fahrenheit;                   // operatore & esplicito: identico
```

Lo stesso vale per l'invocazione: puoi chiamare la funzione puntata usando direttamente il nome del puntatore seguito dagli argomenti tra parentesi, oppure dereferenziandolo esplicitamente prima di applicare `()`:

<!-- cod: id=16.1-f tipo=frammento -->
```c
double f1 = conv(25.0);     // forma compatta, più comune
double f2 = (*conv)(25.0);  // forma esplicita, equivalente
```

Le due forme producono esattamente lo stesso risultato. La forma compatta `conv(25.0)` è oggi la più diffusa, mentre `(*conv)(25.0)` ha il vantaggio di ricordare a colpo d'occhio a chi legge il codice che si tratta di una chiamata indiretta.

Prima di invocare qualunque puntatore a funzione devi sempre assicurarti che sia valido e diverso da `nullptr`. Un puntatore a funzione può essere inizializzato a `nullptr` per rappresentare l'assenza di una funzione associata (per esempio quando un codice di operazione non è riconosciuto), e confrontato con `== nullptr` o `!= nullptr`. Invocare un puntatore a funzione nullo o non inizializzato provoca **comportamento indefinito**: in pratica il processore tenta di saltare a un indirizzo inesistente o casuale e il programma si arresta in modo anomalo.

### Rendere leggibili i tipi con `typedef`

La sintassi grezza `tipo_ritorno (*nome)(tipi_parametri)` è ancora gestibile per una singola variabile, ma diventa rapidamente illeggibile quando un puntatore a funzione appare come parametro di un'altra funzione, come campo di una `struct`, in un array o, peggio ancora, come tipo restituito da una funzione. Osserva come appare la dichiarazione di una funzione `scegli_conversione` che riceve un `char` e restituisce un puntatore a una funzione `double (double)`:

<!-- cod: id=16.1-g tipo=frammento -->
```c
double (*scegli_conversione(char codice))(double);  // valido, ma faticoso da leggere
```

La soluzione idiomatica in C è definire un alias con `typedef` (capitolo 12). Con un `typedef`, il nome al posto della variabile diventa il nome del nuovo tipo puntatore a funzione:

<!-- cod: id=16.1-h tipo=frammento -->
```c
typedef double (*conv_fn)(double);

conv_fn conv = celsius_a_fahrenheit;       // variabile
conv_fn scegli_conversione(char codice);   // funzione che restituisce un puntatore a funzione
```

Il guadagno in chiarezza è immediato: `conv_fn` si usa ovunque come un qualsiasi altro tipo, nei parametri delle funzioni, nei campi delle `struct` e negli array. Quando scrivi programmi reali, definisci quasi sempre un `typedef` con un suffisso esplicito come `_fn` per ogni firma di puntatore a funzione che riutilizzi più di una volta.

### Separazione rispetto a `void *` e incompatibilità di firma

Nel capitolo 15 hai visto che `void *` può contenere l'indirizzo di qualsiasi *oggetto* in memoria. È importante ricordare una regola fondamentale dello standard C23: **un puntatore a funzione non è convertibile in modo portabile a `void *`, né da `void *`**. In alcune architetture gli indirizzi del codice e gli indirizzi dei dati vivono in spazi di indirizzamento separati o hanno addirittura dimensioni in byte diverse. Pertanto il C standard non garantisce che `void *` possa rappresentare un puntatore a funzione, e con `-Wpedantic -Werror` il compilatore segnala la conversione come errore.

Lo standard C23 consente invece di convertire temporaneamente un puntatore a funzione in un altro tipo di puntatore a funzione (con un cast esplicito), **a patto di riconvertirlo esattamente al tipo originale prima di invocarlo**. Chiamare una funzione attraverso un puntatore a funzione di tipo incompatibile — per esempio con un numero diverso di parametri o tipi differenti — provoca **comportamento indefinito**, perché chiamante e chiamato si aspettano argomenti e valori di ritorno in registri o posizioni dello stack differenti.

Possiamo riassumere le regole essenziali di questa sotto-sezione:

- Un puntatore a funzione si dichiara come `tipo_ritorno (*nome)(tipi_parametri);`; le parentesi attorno a `(*nome)` sono obbligatorie.
- Un alias `typedef tipo_ritorno (*nome_fn)(tipi_parametri);` semplifica variabili, parametri, campi di `struct`, array e valori di ritorno.
- Il nome di una funzione decade automaticamente a puntatore a funzione (`p = f` equivale a `p = &f`) e l'invocazione `p(x)` equivale a `(*p)(x)`.
- Un puntatore a funzione non è convertibile in modo portabile a `void *` né da `void *`.
- Controlla sempre che il puntatore non sia `nullptr` prima di invocarlo; chiamare un puntatore nullo, non inizializzato o convertito a una firma incompatibile provoca **comportamento indefinito**.

### Esempio guidato

Il programma seguente realizza un piccolo convertitore di temperature tra Celsius, Fahrenheit e Kelvin. Nella prima parte usa la sintassi esplicita `double (*conv)(double)` per mostrare sia `conv = f` sia `conv = &f` e entrambe le forme di invocazione. Nella seconda parte introduce l'alias `typedef double (*conv_fn)(double);` e una funzione `scegli_conversione` che restituisce un `conv_fn` (oppure `nullptr` se il codice richiesto non esiste), applicandolo a una sequenza di test.

<!-- cod: id=16.1-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

typedef double (*conv_fn)(double);

double celsius_a_fahrenheit(double c) {
    return c * 9.0 / 5.0 + 32.0;
}

double fahrenheit_a_celsius(double f) {
    return (f - 32.0) * 5.0 / 9.0;
}

double celsius_a_kelvin(double c) {
    return c + 273.15;
}

conv_fn scegli_conversione(char codice) {
    if (codice == 'F') {
        return celsius_a_fahrenheit;
    }
    if (codice == 'C') {
        return fahrenheit_a_celsius;
    }
    if (codice == 'K') {
        return celsius_a_kelvin;
    }
    return nullptr;
}

int main(void) {
    // Sintassi estesa senza typedef
    double (*conv)(double) = celsius_a_fahrenheit;
    printf("20.0 C -> %.2f F (via conv)\n", conv(20.0));

    // Assegnazione esplicita con & e invocazione con (*conv)
    conv = &celsius_a_kelvin;
    printf("20.0 C -> %.2f K (via (*conv))\n", (*conv)(20.0));

    // Uso dell'alias typedef con selezione dinamica
    const char codici[] = {'F', 'C', 'K', 'X'};
    const double ingressi[] = {0.0, 212.0, 25.0, 10.0};
    constexpr size_t num_test = sizeof(codici) / sizeof(codici[0]);

    for (size_t i = 0; i < num_test; ++i) {
        conv_fn fn = scegli_conversione(codici[i]);
        if (fn == nullptr) {
            printf("Codice '%c': conversione sconosciuta\n", codici[i]);
        } else {
            printf("Codice '%c': %.2f -> %.2f\n", codici[i], ingressi[i], fn(ingressi[i]));
        }
    }

    return 0;
}
```

```output
20.0 C -> 68.00 F (via conv)
20.0 C -> 293.15 K (via (*conv))
Codice 'F': 0.00 -> 32.00
Codice 'C': 212.00 -> 100.00
Codice 'K': 25.00 -> 298.15
Codice 'X': conversione sconosciuta
```

Osserva i punti chiave del programma:

- `typedef double (*conv_fn)(double);` definisce l'alias di tipo in una sola riga, rendendo leggibile la firma `conv_fn scegli_conversione(char codice)` senza parentesi annidate.
- Le due righe `conv = celsius_a_fahrenheit;` e `conv = &celsius_a_kelvin;` dimostrano che `&` davanti al nome della funzione è facoltativo, così come `(*conv)(20.0)` equivale a `conv(20.0)`.
- Quando `codici[i]` vale `'X'`, `scegli_conversione` restituisce `nullptr`. Il controllo `if (fn == nullptr)` nel ciclo `for` impedisce di invocare un puntatore nullo e gestisce l'errore in modo pulito.

Che cosa succede invece se provi ad assegnare a un puntatore a funzione una funzione con firma incompatibile? Il blocco seguente non compila: il compilatore segnala un'incompatibilità tra i tipi di puntatore a funzione, perché `somma_interi` accetta due `int` e restituisce `int`, mentre `conv` richiede un `double` e restituisce `double`.

<!-- cod: id=16.1-b tipo=errore -->
```c
#include <stdio.h>

int somma_interi(int a, int b) {
    return a + b;
}

int main(void) {
    double (*conv)(double) = somma_interi;  // errore: firma incompatibile
    printf("%f\n", conv(1.0));
    return 0;
}
```

> **Approfondimento — Decifrare le dichiarazioni con la regola a spirale**
> Quando incontri una dichiarazione C complessa senza `typedef`, puoi leggerla applicando la *regola a spirale* (o regola destra-sinistra): parti dal nome dell'identificatore, guarda prima a destra (parentesi `()` per le funzioni e quadre `[]` per gli array hanno precedenza più alta) e poi a sinistra (l'asterisco `*`), uscendo via via dalle parentesi che racchiudono il nome.
> Applichiamola a `double (*scegli(char codice))(double)`:
> 1. Parti da `scegli`: a destra c'è `(char codice)`, quindi `scegli` è una *funzione che accetta un `char`*.
> 2. A sinistra dentro le parentesi c'è `*`, quindi *restituisce un puntatore*.
> 3. Uscendo dalle parentesi, a destra c'è `(double)`, quindi punta a una *funzione che accetta un `double`*.
> 4. Infine a sinistra c'è `double`, quindi quella funzione *restituisce un `double`*.
> Conoscere questa regola serve a leggere codice scritto da altri o intestazioni di libreria, ma nel codice che scrivi tu usa sempre un `typedef` per spezzare le dichiarazioni complesse in passi chiari.

### Esercizio 16.1 — Pipeline configurabile di filtri numerici con puntatori a funzione

**Descrizione**

Scrivi un programma C che definisca `typedef double (*trasforma_fn)(double);` e `typedef struct stadio { char nome[24]; trasforma_fn fn; } stadio_t;`. Implementa quattro funzioni di trasformazione pura con firma `double f(double)`: `raddoppia` (`2.0 * x`), `dimezza` (`0.5 * x`), `opposto` (`(x == 0.0) ? 0.0 : -x` per evitare `-0.00`) e `satura` (limita `x` nell'intervallo `[-1.0, 1.0]`). Implementa inoltre: (1) `trasforma_fn risolvi_filtro(const char *nome)` che restituisce il puntatore alla funzione corrispondente ai nomi `"raddoppia"`, `"dimezza"`, `"opposto"`, `"satura"` oppure `nullptr` se il nome è sconosciuto; (2) `bool applica_pipeline(const stadio_t *stadi, size_t num_stadi, double *valori, size_t n)` che verifica la validità dei puntatori e che ogni `stadi[i].fn != nullptr` (restituendo `false` altrimenti) e applica in sequenza tutti gli stadi a ciascun elemento di `valori`. In `main` leggi dalla prima riga `k` (`0 <= k <= 16`) e dalle successive `k` righe i nomi dei filtri richiesti: per ogni nome chiama `risolvi_filtro`; se restituisce `nullptr` stampa `Filtro sconosciuto: <nome>` e non aggiungere lo stadio, altrimenti inseriscilo nell'array `stadi`. Leggi poi `n` (`0 <= n <= 32`) e, se `n > 0`, una riga contenente `n` numeri `double` separati da spazi. Salva i valori originali, chiama `applica_pipeline` sulla copia e stampa la composizione della pipeline (o `(vuota)` se ha `0` stadi) e le coppie `val[i]: <orig:.2f> -> <fin:.2f>` (o `Nessun dato.` se `n == 0`) esattamente come nell'esempio.

**Concetti da tenere a mente**

- alias `typedef` per un tipo puntatore a funzione (`trasforma_fn`)
- funzione che restituisce un puntatore a funzione o `nullptr` per input sconosciuti
- memorizzazione di puntatori a funzione nei campi di una `struct`
- controllo difensivo di ogni puntatore a funzione contro `nullptr` prima dell'invocazione

**Domande guida**

1. Perché nella dichiarazione `typedef double (*trasforma_fn)(double);` le parentesi attorno a `(*trasforma_fn)` sono indispensabili?
2. Come gestisci il caso in cui `risolvi_filtro` riceve un nome non riconosciuto senza interrompere l'intero programma né invocare un puntatore nullo?
3. Perché `applica_pipeline` controlla tutti i puntatori `stadi[i].fn` prima di iniziare a modificare l'array `valori`?
4. Perché nella funzione `opposto` conviene trattare esplicitamente `x == 0.0` restituendo `0.0` invece di `-x`?

**Esempio di esecuzione**

```input
4
raddoppia
ignoto
satura
opposto
3
0.25 1.5 -0.8
```

```output
Filtro sconosciuto: ignoto
Pipeline (3 stadi): raddoppia -> satura -> opposto
val[0]: 0.25 -> -0.50
val[1]: 1.50 -> -1.00
val[2]: -0.80 -> 1.00
```

## 16.2 Callback e algoritmi parametrizzati

Immagina di aver scritto un ciclo che scorre un array per contare quanti elementi superano una certa soglia. Il giorno dopo ti serve contare quanti elementi sono pari; il giorno seguente vuoi contare quanti prodotti in un catalogo hanno un prezzo inferiore a un budget dato. La struttura del ciclo di scansione è sempre la stessa: cambiano soltanto il tipo dell'elemento e la condizione di verifica. Duplicare lo stesso ciclo decine di volte rende il programma prolisso e moltiplica le occasioni di errore.

In C puoi separare la *struttura dell'algoritmo* (come attraversare i dati) dall'*operazione specifica* da eseguire su ciascun elemento passando quest'ultima come argomento. Una funzione passata in questo modo è detta **callback** (*callback*, funzione di richiamo): è una funzione passata come argomento tramite puntatore a funzione affinché un'altra funzione la invochi al momento opportuno.

### Schemi ricorrenti di funzioni parametrizzate

Combinando i puntatori a funzione con `void *` e `size_t dim_elem` (che hai studiato nel capitolo 15), puoi esprimere in C gli stessi schemi generali usati in molti linguaggi moderni per elaborare sequenze di dati:

- **Visita** (*for-each*): scorre tutti gli elementi e invoca una callback su ciascuno, per esempio per stamparlo o registrarne i dati.
- **Trasformazione sul posto**: scorre un array modificabile (`void *`) e invoca una callback che aggiorna ogni elemento direttamente in memoria.
- **Filtraggio tramite predicato**: invoca una callback booleana (`bool (*)(const void *, const void *)`) su ogni elemento e conserva o conta soltanto gli elementi per cui il predicato restituisce `true`.
- **Riduzione o aggregazione**: mantiene un accumulatore (una somma, un massimo, una struttura di statistiche) e invoca una callback che combina l'accumulatore con ciascun elemento della sequenza.

In tutti questi casi l'algoritmo generico non conosce il tipo concreto degli elementi: riceve un puntatore base (`const void *` per gli algoritmi in sola lettura, `void *` per quelli che modificano), il numero di elementi `n` e la dimensione in byte `dim_elem` di ciascun elemento. Per calcolare l'indirizzo dell'`i`-esimo elemento converte il puntatore base in `const unsigned char *` (oppure `unsigned char *`) e somma `i * dim_elem`, esattamente come nel vettore dinamico generico del capitolo 15.

### Il parametro di contesto `ctx`: compensare l'assenza di chiusure

Supponi di voler usare una funzione generica `conta_se` per contare quanti numeri di un array sono maggiori di una soglia `soglia` scelta a tempo di esecuzione. Se il predicato accettasse soltanto l'elemento:

<!-- cod: id=16.2-b tipo=frammento -->
```c
typedef bool (*predicato_semplice_fn)(const void *elem);  // limitato: dove metto la soglia?
```

non avresti alcun modo pulito per far arrivare il valore di `soglia` dentro il predicato! Qualcuno potrebbe essere tentato di mettere `soglia` in una variabile globale, ma le variabili globali creano dipendenze nascoste e si rompono appena due chiamate usano soglie diverse o si annidano tra loro.

Il motivo è strutturale: a differenza di altri linguaggi, il C non dispone di chiusure che catturino automaticamente le variabili locali dello spazio circostante. Un puntatore a funzione in C è solo l'indirizzo del codice della funzione, senza alcun dato associato.

La soluzione idiomatica e portabile del C è aggiungere alla firma della callback — e alla firma dell'algoritmo che la riceve — un **parametro di contesto** di tipo `const void *ctx` (o `void *ctx` quando la callback deve modificare lo stato contenuto nel contesto):

<!-- cod: id=16.2-c tipo=frammento -->
```c
typedef bool (*predicato_fn)(const void *elem, const void *ctx);

size_t conta_se(const void *base, size_t n, size_t dim_elem,
                predicato_fn pred, const void *ctx);
```

Il meccanismo è lineare:

```text
chiamante ──(&soglia)──▶ conta_se(..., pred, ctx) ──(ctx invariato)──▶ pred(elem, ctx)
                                                                             │
                                                                             ▼
                                                              const int *s = ctx;
```

L'algoritmo generico `conta_se` non ispeziona mai `ctx`: si limita a inoltrarlo invariato a ogni invocazione di `pred(elem, ctx)`. La callback, che conosce il tipo effettivo tanto dell'elemento quanto del contesto, riconverte `elem` e `ctx` ai rispettivi tipi concreti (rispettando `const`). Se una particolare callback non ha bisogno di contesto, il chiamante passa semplicemente `nullptr` e la callback ignora il parametro con `(void)ctx;` per evitare avvisi del compilatore su parametri inutilizzati.

### Controlli di sicurezza e contratto sullo standard

Prima di invocare una callback dentro un algoritmo generico occorre rispettare alcune precauzioni rigorose:

1. **Verifica contro `nullptr`**: controlla sempre che il puntatore alla callback non sia `nullptr` (e che `dim_elem > 0` e, quando `n > 0`, `base != nullptr`). Invocare una callback nulla provoca **comportamento indefinito**.
2. **Coerenza dei tipi**: secondo lo standard C23, passare un oggetto tramite `void *` o `const void *` e riconvertirlo al tipo originale è perfettamente definito, mentre riconvertire `elem` o `ctx` a un tipo incompatibile con l'oggetto effettivamente passato provoca **comportamento indefinito**.
3. **Rispetto di `const`**: se l'algoritmo e la callback leggono soltanto i dati o il contesto, usa `const void *`. Questo permette al chiamante di passare anche array e configurazioni dichiarati `const` senza violare il sistema dei tipi.

> **Se vieni da Python** — In Python le funzioni sono oggetti di prima classe e le chiusure (*closure*) catturano automaticamente le variabili locali della funzione che le definisce; in C un puntatore a funzione memorizza solo l'indirizzo del codice e qualsiasi stato aggiuntivo (soglie, intervalli, accumulatori) va passato esplicitamente tramite un parametro `void *ctx` o `const void *ctx`.

### Esempio guidato

Il programma seguente definisce tre algoritmi generici riutilizzabili (`visita_generica`, `conta_se` e `trova_primo`) che operano su array `const void *` tramite callback e parametro `const void *ctx`, senza alcuna variabile globale. Gli stessi algoritmi vengono poi applicati a due tipi completamente diversi: un array di `int` (per stampare i valori e contare quelli sopra una soglia) e un array di `struct prodotto` (per trovare il primo prodotto il cui prezzo rientra in un budget).

<!-- cod: id=16.2-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

typedef void (*visita_fn)(const void *elem, const void *ctx);
typedef bool (*predicato_fn)(const void *elem, const void *ctx);
typedef struct prodotto { char nome[24]; double prezzo; } prodotto_t;

void visita_generica(const void *base, size_t n, size_t dim_elem,
                     visita_fn fn, const void *ctx) {
    if (fn == nullptr || dim_elem == 0 || (n > 0 && base == nullptr)) { return; }
    const unsigned char *p = base;
    for (size_t i = 0; i < n; ++i) {
        fn(p + i * dim_elem, ctx);
    }
}

size_t conta_se(const void *base, size_t n, size_t dim_elem,
                predicato_fn pred, const void *ctx) {
    if (pred == nullptr || dim_elem == 0 || (n > 0 && base == nullptr)) { return 0; }
    const unsigned char *p = base;
    size_t conteggio = 0;
    for (size_t i = 0; i < n; ++i) {
        if (pred(p + i * dim_elem, ctx)) { ++conteggio; }
    }
    return conteggio;
}

const void *trova_primo(const void *base, size_t n, size_t dim_elem,
                        predicato_fn pred, const void *ctx) {
    if (pred == nullptr || dim_elem == 0 || (n > 0 && base == nullptr)) { return nullptr; }
    const unsigned char *p = base;
    for (size_t i = 0; i < n; ++i) {
        const void *elem = p + i * dim_elem;
        if (pred(elem, ctx)) { return elem; }
    }
    return nullptr;
}

void stampa_int(const void *elem, const void *ctx) {
    const int *val = elem;
    const char *prefisso = ctx;
    printf("%s%d\n", (prefisso != nullptr) ? prefisso : "", *val);
}

bool maggiore_di(const void *elem, const void *ctx) {
    return *(const int *)elem > *(const int *)ctx;
}

bool entro_budget(const void *elem, const void *ctx) {
    const prodotto_t *prod = elem;
    return prod->prezzo <= *(const double *)ctx;
}

int main(void) {
    const int valori[] = {4, 15, 8, 23, 42};
    constexpr size_t n_val = sizeof(valori) / sizeof(valori[0]);
    visita_generica(valori, n_val, sizeof(valori[0]), stampa_int, "Valore: ");

    int soglia = 10;
    size_t sopra = conta_se(valori, n_val, sizeof(valori[0]), maggiore_di, &soglia);
    printf("Elementi > %d: %zu\n", soglia, sopra);

    const prodotto_t catalogo[] = {
        {"Monitor", 249.90}, {"Tastiera", 59.50}, {"Mouse", 29.90}
    };
    constexpr size_t n_cat = sizeof(catalogo) / sizeof(catalogo[0]);
    double budget = 60.0;
    const prodotto_t *trovato = trova_primo(catalogo, n_cat, sizeof(catalogo[0]),
                                            entro_budget, &budget);
    if (trovato != nullptr) {
        printf("Primo entro %.2f euro: %s (%.2f)\n", budget, trovato->nome, trovato->prezzo);
    }
    return 0;
}
```

```output
Valore: 4
Valore: 15
Valore: 8
Valore: 23
Valore: 42
Elementi > 10: 3
Primo entro 60.00 euro: Tastiera (59.50)
```

Esamina come lavorano insieme i vari pezzi:

- Tutte e tre le funzioni generiche (`visita_generica`, `conta_se`, `trova_primo`) controllano subito che il puntatore alla callback non sia `nullptr`, che `dim_elem` sia maggiore di `0` e che `base` non sia `nullptr` quando `n > 0`.
- L'accesso all'`i`-esimo elemento avviene convertendo `base` in `const unsigned char *p` e calcolando `p + i * dim_elem`, così l'algoritmo resta identico sia per `int` (tipicamente 4 byte) sia per `prodotto_t`.
- In `stampa_int`, il parametro `ctx` trasporta una stringa prefisso (`"Valore: "`); in `maggiore_di`, trasporta `&soglia` (`const int *`); in `entro_budget`, trasporta `&budget` (`const double *`). Nessuna variabile globale è necessaria.
- `trova_primo` restituisce `const void *`, che in C si converte implicitamente in `const prodotto_t *` nell'inizializzazione di `trovato`, preservando la protezione `const` sull'array `catalogo`.

> **Approfondimento — Perché `void *ctx` è superiore alle variabili globali `static`**
> Usare una variabile globale `static` per passare una soglia a una callback può sembrare più corto in un programmino di dieci righe, ma introduce tre problemi gravi nei programmi reali. Primo: rende la funzione non rientrante, cioè incapace di funzionare correttamente se una callback ne richiama a sua volta un'altra con una soglia diversa. Secondo: impedisce a più istanze dello stesso algoritmo di coesistere con configurazioni indipendenti. Terzo: nasconde le dipendenze della funzione, rendendo difficile capire leggendo il prototipo di quali dati ha bisogno. Il parametro `void *ctx` (o `const void *ctx`) risolve tutti e tre i problemi rendendo esplicito il flusso dei dati.

### Esercizio 16.2 — Motore generico di filtraggio e riduzione con callback e contesto `ctx`

**Descrizione**

Scrivi un programma C che definisca `typedef bool (*predicato_fn)(const void *elem, const void *ctx);` e `typedef void (*accumula_fn)(void *acc, const void *elem, const void *ctx);` e implementi due algoritmi generici indipendenti dal tipo, senza usare alcuna variabile globale: (1) `size_t filtra_generico(const void *src, size_t n, size_t dim_elem, void *dst, predicato_fn pred, const void *ctx)` che scorre gli `n` elementi di dimensione `dim_elem` in `src` (indirizzandoli tramite `const unsigned char *`), copia con `memcpy` in `dst` quelli per cui `pred(elem, ctx)` restituisce `true` e restituisce il numero di elementi copiati (`0` se i parametri sono invalidi o `n == 0`); (2) `bool riduci_generico(const void *src, size_t n, size_t dim_elem, void *acc, accumula_fn fn, const void *ctx)` che invoca `fn(acc, elem, ctx)` su ciascun elemento in ordine (restituendo `false` se `acc == nullptr`, `fn == nullptr`, `dim_elem == 0` o `n > 0 && src == nullptr`). Applica entrambi gli algoritmi a due tipi distinti: prima a `int32_t` filtrando i valori compresi nell'intervallo chiuso `[min_val, max_val]` (passato via `const void *ctx` con `typedef struct intervallo { int32_t min; int32_t max; } intervallo_t;`) e riducendo i valori filtrati in `typedef struct stat_int { int64_t somma; int32_t max; bool presente; } stat_int_t;`; poi a `typedef struct esame { char codice[16]; int voto; int crediti; } esame_t;` filtrando gli esami con `voto >= voto_min` (passato tramite `&voto_min` come `ctx`) e riducendoli in `typedef struct stat_esami { int64_t somma_pesata; int64_t tot_crediti; } stat_esami_t;` per calcolare la media ponderata (`0.00` se `tot_crediti == 0`). In `main` leggi dalla prima riga `n_int min_val max_val` (`0 <= n_int <= 32`, `min_val <= max_val`), dalla riga successiva (se `n_int > 0`) gli `n_int` interi separati da spazi, poi `n_es voto_min` (`0 <= n_es <= 32`) e le `n_es` righe `<codice> <voto> <crediti>` (`crediti >= 0`), e stampa esattamente il formato mostrato nell'esempio.

**Concetti da tenere a mente**

- callback generiche per predicato (`predicato_fn`) e riduzione (`accumula_fn`) su `void *` / `const void *`
- passaggio dello stato di configurazione tramite `const void *ctx` senza variabili globali
- calcolo degli spiazzamenti in byte con `unsigned char *` e copia degli elementi con `memcpy`
- riutilizzo dello stesso codice di filtraggio e riduzione su `int32_t` e su `esame_t`

**Domande guida**

1. Perché `filtra_generico` ha bisogno del parametro `const void *ctx` se vuoi filtrare sia per un intervallo `[min, max]` sia per una soglia `voto_min` senza variabili globali?
2. Come calcoli in `filtra_generico` l'indirizzo del `k`-esimo elemento sorgente e della posizione di scrittura in `dst`?
3. Perché in `stat_int_t` conviene avere un campo `bool presente` anziché inizializzare `max` a `0`?
4. Che cosa controlla `riduci_generico` quando `n == 0` rispetto a quando `n > 0`?

**Esempio di esecuzione**

```input
5 10 30
5 10 25 40 30
3 24
MAT1 28 9
FIS1 21 6
INF1 30 12
```

```output
Interi filtrati (3): 10 25 30
Stat interi: somma=65 max=30
Esami filtrati (2): MAT1(28) INF1(30)
Stat esami: crediti=21 media=29.14
```

## 16.3 Ordinare e cercare qualsiasi tipo con `qsort` e `bsearch`

Nel capitolo 8 hai implementato a mano un algoritmo di ordinamento elementare e una ricerca binaria su un array di interi. Quando però il programma cresce e devi ordinare strutture di clienti, elenchi di parole o array di misure in virgola mobile, riscrivere ogni volta l'ordinamento e la ricerca binaria sarebbe lento e rischioso. La libreria standard C mette a disposizione in `<stdlib.h>` due funzioni generiche basate esattamente sul modello appena visto (`void *`, dimensione dell'elemento e callback): `qsort` per ordinare sul posto e `bsearch` per eseguire la ricerca binaria.

### Ordinare sul posto con `qsort`

La firma di `qsort` in `<stdlib.h>` è:

<!-- cod: id=16.3-b tipo=frammento -->
```c
void qsort(void *base, size_t nmemb, size_t size,
           int (*compar)(const void *, const void *));
```

I quattro parametri hanno un significato diretto:

- `base`: puntatore al primo elemento dell'array da ordinare;
- `nmemb`: numero di elementi dell'array;
- `size`: dimensione in byte di un singolo elemento (tipicamente `sizeof(array[0])` o `sizeof(*base)`);
- `compar`: puntatore a funzione del **comparatore**, una callback che decide l'ordine tra due elementi.

`qsort` non conosce il tipo degli elementi: sposta blocchi di `size` byte direttamente dentro l'array `base` (ordinamento sul posto) e, ogni volta che ha bisogno di sapere se un elemento viene prima o dopo un altro, chiama `compar(a, b)` passando gli indirizzi dei due elementi come `const void *`.

### Scrivere comparatori sicuri: il contratto e la trappola della sottrazione

Il comparatore deve rispettare un contratto preciso: restituire un `int` **minore di zero** se `*a` precede `*b`, **zero** se i due elementi sono equivalenti secondo il criterio scelto, oppure **maggiore di zero** se `*a` segue `*b`. Inoltre l'ordinamento definito dal comparatore deve essere coerente (un ordinamento stretto debole: se `a < b` allora `b > a`, e se `a < b` e `b < c` allora `a < c`). Un comparatore incoerente provoca **comportamento indefinito** in `qsort` e `bsearch`.

Molti esempi datati che circolano in rete scrivono il comparatore per due interi `int` usando una sottrazione:

<!-- cod: id=16.3-c tipo=frammento -->
```c
// ERRORE: MAI scrivere un comparatore così!
int cmp_int_sbagliato(const void *a, const void *b) {
    const int *pa = a;
    const int *pb = b;
    return *pa - *pb;  // overflow con segno -> comportamento indefinito!
}
```

> **Attenzione — Comportamento indefinito**: non usare MAI la sottrazione `*pa - *pb` dentro un comparatore. Il motivo vale per tre famiglie di tipi diverse:
> 1. **Interi con segno** (`int`, `int32_t`): se `*pa` vale `INT_MIN` (`-2147483648`) e `*pb` vale `1`, la sottrazione va in overflow con segno, che in C è **comportamento indefinito** (e in pratica ribalta il segno del risultato, rovinando l'ordinamento).
> 2. **Interi senza segno** (`unsigned int`, `size_t`): la sottrazione avvolge modulo $2^N$ e non può mai produrre un risultato negativo se non convertita con cura, causando wraparound errati.
> 3. **Virgola mobile** (`double`, `float`): `return (int)(*pa - *pb);` tronca differenze piccole come `0.3 - 0.1 = 0.2` a `0`, facendo credere a `qsort` che due numeri diversi siano uguali!

Il modo corretto, sicuro per qualsiasi tipo numerico (`int`, `int32_t`, `size_t`, `double`) e privo di overflow, consiste nel confrontare direttamente con `>` e `<`:

<!-- cod: id=16.3-d tipo=frammento -->
```c
int cmp_int_sicuro(const void *a, const void *b) {
    const int *pa = a;
    const int *pb = b;
    return (*pa > *pb) - (*pa < *pb);
}
```

Osserva l'espressione `(*pa > *pb) - (*pa < *pb)`: poiché i confronti relazionali in C valgono `1` oppure `0`, l'espressione restituisce sempre esattamente `1` se `*pa > *pb`, `-1` se `*pa < *pb` e `0` se `*pa == *pb`, senza alcun rischio di overflow né di troncamento. Per ordinare in senso decrescente basta invertire gli operandi: `(*pb > *pa) - (*pb < *pa)`.

### Criteri multipli e chiave secondaria di spareggio

Quando ordini un array di `struct` (per esempio record di studenti o articoli di un catalogo), capita spesso che due elementi abbiano lo stesso valore sul criterio principale (per esempio lo stesso anno o lo stesso punteggio). Lo standard C23 stabilisce che l'ordine relativo degli elementi equivalenti dopo `qsort` è **comportamento non specificato**: `qsort` non è garantito stabile. Per ottenere un ordine completamente deterministico su qualsiasi compilatore e sistema operativo, conviene strutturare il comparatore in cascata aggiungendo una chiave secondaria univoca di spareggio (*tie-breaker*): confronti prima il criterio principale; se il risultato è diverso da `0` lo restituisci subito, altrimenti passi al criterio successivo fino a una chiave univoca (come un codice identificativo).

### L'insidia degli array di stringhe (`const char *nomi[]`)

Una trappola molto frequente riguarda gli array di stringhe dichiarati come `const char *nomi[]`. Ogni elemento dell'array **non** è un `char`, bensì un puntatore `const char *` alla prima lettera della stringa. Poiché `qsort` passa al comparatore gli *indirizzi degli elementi dell'array*, i parametri `a` e `b` puntano a puntatori: il loro tipo reale è `const char *const *` (un puntatore a puntatore, capitolo 14), non `const char *`.

```text
nomi[0] (const char *) ──▶ "mela\0"
  ▲
  │
  a (const void * ──▶ const char *const *)
```

Se convertissi erroneamente `a` in `const char *` e lo passassi direttamente a `strcmp`, staresti confrontando i byte dell'indirizzo del puntatore invece dei caratteri della stringa (comportamento indefinito). Devi invece convertire a `const char *const *` e dereferenziare una volta:

<!-- cod: id=16.3-e tipo=frammento -->
```c
int cmp_stringhe(const void *a, const void *b) {
    const char *const *sa = a;
    const char *const *sb = b;
    return strcmp(*sa, *sb);
}
```

### Ricerca binaria generica con `bsearch`

Una volta ordinato l'array, puoi cercare un elemento in tempo logaritmico con `bsearch` (`<stdlib.h>`):

<!-- cod: id=16.3-f tipo=frammento -->
```c
void *bsearch(const void *key, const void *base, size_t nmemb, size_t size,
              int (*compar)(const void *, const void *));
```

`bsearch` riceve l'indirizzo della chiave cercata (`key`), l'array ordinato (`base`, `nmemb`, `size`) e il comparatore `compar`. Restituisce l'indirizzo dell'elemento trovato, oppure `nullptr` se la chiave non è presente.

Perché la chiamata sia corretta devi rispettare quattro regole:

1. **Precondizione di ordinamento**: l'array `base` deve essere già ordinato secondo lo **stesso** comparatore (o uno strettamente compatibile) passato a `bsearch`. Chiamare `bsearch` su un array non ordinato provoca **comportamento indefinito**.
2. **Chiave con il tipo dell'elemento**: `bsearch` passa `key` come primo argomento al comparatore; se cerchi una `struct` per codice, prepara una `struct` chiave con quel campo valorizzato; se cerchi in `const char *nomi[]`, passa l'indirizzo di una variabile `const char *chiave = "...";` (`&chiave`), così che il comparatore riceva `const char *const *`.
3. **Protezione del caso `nmemb == 0` e puntatore `base` nullo**: proprio come per le funzioni `mem*` del capitolo 15, evita di passare `nullptr` come `base` a `qsort` o `bsearch` anche quando `nmemb == 0` (può provocare comportamento indefinito). Proteggi sempre le chiamate con `if (nmemb > 0)` quando il puntatore dinamico potrebbe essere `nullptr`.
4. **Elementi equivalenti**: se nell'array compaiono più elementi equivalenti alla chiave, quale di essi restituisca `bsearch` è **comportamento non specificato**.

> **C23 — Preservazione di `const` in `bsearch`**
> Prima del C23, `bsearch` restituiva sempre un `void *` non qualificato anche quando `base` era `const void *`, costringendo a fare attenzione a non modificare per errore un array costante. In C23 `bsearch` è una funzione generica sul tipo (come `memchr` vista nel capitolo 15): se passi un puntatore a dati `const` (per esempio `const char *const *` o `const libro_t *`), il puntatore restituito preserva la qualificazione `const`, impedendo modifiche accidentali. Con compilatori C17 o precedenti, `bsearch` restituisce comunque `void *`, che si assegna senza problemi a un puntatore `const T *` (ma il compilatore non ti impedirebbe di assegnarlo a un `T *` non `const`).

> **Se vieni da Python** — In Python `list.sort(key=...)` è garantito stabile e accetta una funzione che estrae la chiave di confronto; in C `qsort` ordina sul posto usando un comparatore che confronta coppie di `const void *` e la stabilità non è garantita dallo standard, per cui conviene inserire uno spareggio univoco nel comparatore.

### Esempio guidato

Il programma seguente ordina con `qsort` prima un array di `int` che include gli estremi `INT_MIN` e `INT_MAX` (dove la sottrazione fallirebbe con overflow), poi un array di stringhe `const char *` mostrando il doppio livello di indirezione `const char *const *`. Infine cerca alcune parole nell'array ordinato con `bsearch`, assegnando il risultato a `const char *const *` per sfruttare la preservazione di `const` in C23.

<!-- cod: id=16.3-a tipo=programma -->
```c
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int cmp_int(const void *a, const void *b) {
    const int *pa = a;
    const int *pb = b;
    return (*pa > *pb) - (*pa < *pb);
}

int cmp_stringhe(const void *a, const void *b) {
    const char *const *sa = a;
    const char *const *sb = b;
    return strcmp(*sa, *sb);
}

int main(void) {
    int numeri[] = {42, INT_MAX, -7, INT_MIN, 0};
    constexpr size_t n_num = sizeof(numeri) / sizeof(numeri[0]);
    qsort(numeri, n_num, sizeof(numeri[0]), cmp_int);

    printf("Interi ordinati:");
    for (size_t i = 0; i < n_num; ++i) {
        printf(" %d", numeri[i]);
    }
    printf("\n");

    const char *parole[] = {"rete", "albero", "grafo", "codice", "pila"};
    constexpr size_t n_par = sizeof(parole) / sizeof(parole[0]);
    qsort(parole, n_par, sizeof(parole[0]), cmp_stringhe);

    printf("Parole ordinate:");
    for (size_t i = 0; i < n_par; ++i) {
        printf(" %s", parole[i]);
    }
    printf("\n");

    // Vista const: in C23 bsearch restituisce un puntatore const
    const char *const *vista = parole;
    const char *query[] = {"grafo", "coda", "albero"};
    constexpr size_t n_query = sizeof(query) / sizeof(query[0]);

    for (size_t i = 0; i < n_query; ++i) {
        const char *chiave = query[i];
        const char *const *trovato = bsearch(&chiave, vista, n_par,
                                             sizeof(vista[0]), cmp_stringhe);
        if (trovato != nullptr) {
            ptrdiff_t pos = trovato - vista;
            printf("Cerca '%s': trovato in posizione %td\n", chiave, pos);
        } else {
            printf("Cerca '%s': non trovato\n", chiave);
        }
    }

    return 0;
}
```

```output
Interi ordinati: -2147483648 -7 0 42 2147483647
Parole ordinate: albero codice grafo pila rete
Cerca 'grafo': trovato in posizione 2
Cerca 'coda': non trovato
Cerca 'albero': trovato in posizione 0
```

Osserva i dettagli più istruttivi dell'esempio:

- `cmp_int` usa `(*pa > *pb) - (*pa < *pb)`, gestendo senza alcun overflow il confronto tra `INT_MIN` e `INT_MAX`.
- In `cmp_stringhe`, i parametri `a` e `b` sono convertiti in `const char *const *` e dereferenziati come `*sa` e `*sb` prima di essere passati a `strcmp`.
- Nella chiamata a `bsearch`, passiamo `&chiave` (indirizzo di una variabile `const char *`), non `chiave` direttamente, in modo che il primo argomento ricevuto da `cmp_stringhe` abbia esattamente lo stesso livello di indirezione degli elementi di `vista`.
- Poiché `vista` ha tipo `const char *const *`, in C23 `bsearch` restituisce un puntatore qualificato `const`, e `trovato - vista` (aritmetica dei puntatori con `ptrdiff_t`, capitolo 10) fornisce l'indice esatto dell'elemento trovato.

> **Approfondimento — Stabilità di `qsort` e comportamento non specificato**
> Nonostante il nome richiami *quicksort*, lo standard C non impone quale algoritmo interno debba usare `qsort`: un'implementazione può usare quicksort, mergesort, introsort o un ibrido scelto in base alla dimensione dell'array. Poiché quicksort e introsort non sono algoritmi stabili, due elementi che il comparatore considera equivalenti (valore di ritorno `0`) possono scambiarsi di posto in modo diverso a seconda del sistema operativo o della versione della libreria standard. Quando desideri che l'ordine finale sia identico su tutte le piattaforme, aggiungi sempre nel comparatore un criterio di spareggio univoco.

### Esercizio 16.3 — Catalogo di libri con ordinamento multi-criterio (`qsort`) e ricerca binaria (`bsearch`)

**Descrizione**

Scrivi un programma C che definisca `typedef struct libro { int32_t codice; char titolo[32]; int32_t anno; int32_t pagine; } libro_t;` e implementi tre comparatori conformi a `qsort` e `bsearch` (`<stdlib.h>`), senza mai usare sottrazioni tra interi che possano causare overflow (usando sempre confronti sicuri come `(x > y) - (x < y)`): (1) `int cmp_per_anno_pagine(const void *a, const void *b)` che ordina per `anno` crescente, a parità per `pagine` decrescente e a parità per `codice` crescente; (2) `int cmp_per_titolo(const void *a, const void *b)` che ordina lessicograficamente per `titolo` (`strcmp`) e a parità per `codice` crescente; (3) `int cmp_per_codice(const void *a, const void *b)` che ordina per `codice` crescente. In `main` leggi dalla prima riga `n` (`0 <= n <= 64`) e dalle successive `n` righe `<codice> <titolo_senza_spazi> <anno> <pagine>` (con codici distinti che possono raggiungere anche `INT32_MIN` e `INT32_MAX`), allocando l'array con `calloc` quando `n > 0`. Leggi poi `q` (`0 <= q <= 16`) e `q` codici `int32_t` da cercare. Ordina l'array con `qsort` usando `cmp_per_anno_pagine` e stampalo; ordinalo poi con `cmp_per_titolo` e stampalo; infine ordinalo con `cmp_per_codice` e risolvi ogni query chiamando `bsearch` su un puntatore `const libro_t *vista = catalogo;` (sfruttando la preservazione di `const` in C23 per assegnare il risultato a `const libro_t *`, e proteggendo il caso `n == 0` senza chiamare `qsort` o `bsearch` su `nullptr`). Libera tutta la memoria allocata prima di uscire.

**Concetti da tenere a mente**

- comparatori sicuri per `qsort` e `bsearch` senza sottrazioni a rischio overflow
- ordinamento multi-criterio con chiave univoca di spareggio (*tie-breaker*)
- precondizione di ordinamento di `bsearch` coerente con lo stesso comparatore usato in `qsort`
- preservazione della qualificazione `const` nel valore restituito da `bsearch` in C23
- protezione del caso `n == 0` per non passare `nullptr` a `qsort` o `bsearch`

**Domande guida**

1. Perché scrivere `return la->codice - lb->codice;` in `cmp_per_codice` fallirebbe con comportamento indefinito quando un libro ha codice `INT32_MIN` e un altro `INT32_MAX`?
2. Perché è utile aggiungere il confronto sul campo univoco `codice` come ultimo spareggio in `cmp_per_anno_pagine` e `cmp_per_titolo`?
3. Che cosa succederebbe se chiamassi `bsearch` con `cmp_per_codice` subito dopo aver ordinato il catalogo con `cmp_per_titolo`?
4. In che modo il caso `n == 0` va gestito prima di invocare `qsort` e `bsearch`?

**Esempio di esecuzione**

```input
4
103 Algoritmi 2020 450
101 Reti 2018 320
104 Sistemi 2020 600
102 Compilatori 2020 450
3
104
999
101
```

```output
Ordinati per anno/pagine:
  [#101] Reti (2018, 320 pag)
  [#104] Sistemi (2020, 600 pag)
  [#102] Compilatori (2020, 450 pag)
  [#103] Algoritmi (2020, 450 pag)
Ordinati per titolo:
  [#103] Algoritmi (2020, 450 pag)
  [#102] Compilatori (2020, 450 pag)
  [#101] Reti (2018, 320 pag)
  [#104] Sistemi (2020, 600 pag)
Cerca 104: TROVATO Sistemi (2020, 600 pag)
Cerca 999: NON TROVATO
Cerca 101: TROVATO Reti (2018, 320 pag)
```

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

- Tutte e quattro le operazioni condividono la firma uniforme descritta da `op_fn` (`bool (double a, double b, double *ris)`): restituiscono `true` in caso di successo e `false` se l'operazione non è eseguibile (come la divisione per zero).
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

## Riepilogo

- Un **puntatore a funzione** memorizza l'indirizzo di una funzione con una firma specifica e si dichiara come `tipo_ritorno (*nome)(tipi_parametri);`, dove le parentesi attorno a `(*nome)` sono obbligatorie. Un alias `typedef tipo_ritorno (*nome_fn)(tipi_parametri);` rende leggibili variabili, parametri, campi di `struct`, array e funzioni che restituiscono puntatori a funzione. Il nome di una funzione decade automaticamente al suo indirizzo (`p = f` equivale a `p = &f`), l'invocazione `p(x)` equivale a `(*p)(x)` e un puntatore a funzione non è convertibile in modo portabile a `void *` né da `void *`.
- Una **callback** è una funzione passata come argomento tramite puntatore a funzione per parametrizzare algoritmi generici (visita, trasformazione, filtraggio, riduzione). Poiché il C non ha chiusure, lo stato aggiuntivo (soglie, intervalli, accumulatori) si passa esplicitamente tramite un parametro di contesto `void *ctx` o `const void *ctx` inoltrato invariato alla callback, evitando variabili globali.
- Le funzioni `qsort` e `bsearch` di `<stdlib.h>` ordinano sul posto e cercano in array di qualsiasi tipo usando un comparatore `int cmp(const void *a, const void *b)`. Il comparatore deve usare confronti espliciti come `(*pa > *pb) - (*pa < *pb)` (mai la sottrazione `*pa - *pb`), aggiungere uno spareggio univoco quando serve un risultato deterministico nonostante la stabilità di `qsort` sia comportamento non specificato, e per array di stringhe `const char *[]` convertire i parametri a `const char *const *` prima di dereferenziarli per `strcmp`. `bsearch` richiede che l'array sia già ordinato con lo stesso comparatore, preserva `const` in C23 ed evita chiamate su `base == nullptr` proteggendo `nmemb == 0`.
- Una **tabella di puntatori a funzione** (indicizzata da `enum` oppure come array ordinato di `struct` `{ nome, fn }` cercato con `bsearch`) sostituisce catene di `if-else` e `switch` ripetitivi con scelte guidate dai dati su funzioni di firma uniforme. Richiede sempre il controllo dei limiti dell'indice, la verifica `!= nullptr` prima dell'invocazione e, per tabelle indicizzate da `enum`, una `static_assert` sulla dimensione. Questi schemi torneranno nelle strutture dati dinamiche (lo vedremo nei capitoli 17 e 18), nelle macchine a stati finiti (lo vedremo nel capitolo 24) e nell'interprete finale (lo vedremo nel capitolo 26).

## Errori comuni

- **Dimenticare le parentesi nella dichiarazione di un puntatore a funzione**: scrivere `int *f(int)` invece di `int (*f)(int)` dichiara una funzione che restituisce `int *`, non un puntatore a funzione. Le parentesi attorno a `(*f)` sono obbligatorie, e definire un `typedef` elimina alla radice l'ambiguità.
- **Usare la sottrazione `return *pa - *pb;` nei comparatori di `qsort` e `bsearch`**: provoca comportamento indefinito per overflow con interi con segno (per esempio `INT_MIN - 1`), wraparound con interi senza segno e troncamento a zero con `double`. Usa sempre `(*pa > *pb) - (*pa < *pb)`.
- **Dimenticare un livello di indirezione nei comparatori per array di stringhe `const char *nomi[]`**: i parametri `a` e `b` puntano agli elementi dell'array, quindi hanno tipo `const char *const *` (non `const char *`) e vanno dereferenziati una volta (`*sa`, `*sb`) prima di passarli a `strcmp`.
- **Invocare un puntatore a funzione senza verificare `!= nullptr`, oppure chiamare `bsearch` su un array non ordinato (o ordinato con un comparatore diverso)**: entrambi gli errori causano comportamento indefinito. Controlla sempre l'indice e il puntatore prima della chiamata, e assicurati che `qsort` e `bsearch` usino lo stesso criterio d'ordine (proteggendo anche il caso `nmemb == 0`).
- **Tentare di convertire un puntatore a funzione in `void *` o viceversa**: in C standard `void *` è riservato ai puntatori a oggetto; convertire un puntatore a funzione in `void *` non è portabile e viene rifiutato con `-Wpedantic -Werror`.

## Prima di proseguire

- [ ] So dichiarare, assegnare e invocare un puntatore a funzione sia con la sintassi completa sia con `typedef`, spiegando il ruolo delle parentesi e perché `void *` non può contenere puntatori a funzione.
- [ ] So progettare algoritmi generici con `void *`, `dim_elem`, callback e parametro di contesto `void *ctx` / `const void *ctx` senza ricorrere a variabili globali.
- [ ] So scrivere comparatori sicuri per `qsort` e `bsearch` su numeri, `struct` (con criteri multipli e spareggio univoco) e array di stringhe `const char *[]`, gestendo `nmemb == 0` e la preservazione di `const` in C23.
- [ ] So costruire tabelle di puntatori a funzione indicizzate da `enum` (con `static_assert`) o cercate per nome con `bsearch`, verificando sempre i limiti dell'indice e `!= nullptr` prima della chiamata indiretta.
