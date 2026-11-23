# Capitolo 10 — Puntatori

> **In questo capitolo imparerai a:**
> - Spiegare il rapporto tra oggetti in memoria, indirizzi, `&` e dereferenziazione con `*`
> - Gestire i puntatori nulli con `nullptr` e `NULL` prevenendo la dereferenziazione nulla
> - Prevedere il comportamento del decadimento degli array e dell'aritmetica dei puntatori
> - Scrivere funzioni che modificano variabili del chiamante tramite parametri puntatore
> - Applicare correttamente `const` ai puntatori e ai dati puntati

> **Ti servono:** variabili, tipi e `sizeof` (capitolo 2), comportamento indefinito (capitolo 3), valutazione a corto circuito (capitolo 4), `sscanf` e `nullptr` (capitolo 5), funzioni, passaggio per valore e durata di vita (capitolo 7), array (capitolo 8) e stringhe con `<string.h>` (capitolo 9).

Fin qui hai lavorato con variabili, array e stringhe riferendoti a ciascun oggetto tramite il suo nome. Questo approccio ti ha già portato lontano, ma lascia aperte almeno tre domande concrete che hai incontrato nei capitoli precedenti. Perché in `sscanf` devi anteporre `&` al nome di una variabile intera o in virgola mobile, mentre non lo fai per un array di `char`? Perché una funzione che riceve un `int` non può modificare la variabile del chiamante, mentre una funzione che riceve un array `int dati[]` modifica direttamente l'array originale e al suo interno `sizeof(dati)` non restituisce la dimensione dell'array? E ancora: che cosa restituiscono esattamente `fgets`, `strchr` e `strstr` quando ti dicono dove si trova un carattere dentro una stringa oppure `nullptr` se la ricerca fallisce?

La risposta a tutte queste domande ruota intorno a un unico concetto: il **puntatore**. Un puntatore è una variabile che non conserva un dato come un numero o un carattere, ma l'**indirizzo di memoria** in cui si trova un altro oggetto. Attraverso gli indirizzi puoi osservare e modificare un oggetto a distanza, far comunicare le funzioni con le variabili del chiamante per restituire più risultati, scorrere porzioni di array e stringhe senza copiare nulla e segnalare in modo pulito l'assenza di un risultato con il puntatore nullo.

I puntatori sono anche lo strumento che dà al C la sua reputazione di linguaggio esigente: se un indirizzo non è valido, è nullo o punta a una variabile che ha terminato la propria durata di vita, il linguaggio non interviene con una rete di sicurezza e il programma cade nel comportamento indefinito. In questo capitolo imparerai quindi non solo la sintassi di `&`, `*`, dell'aritmetica dei puntatori e di `const`, ma soprattutto la disciplina necessaria per usare i puntatori in modo chiaro, verificabile e sicuro.

## 10.1 Indirizzi di memoria, `&` e `*`

Quando dichiari una variabile come `int quota = 42;`, il programma riserva nella memoria centrale alcuni byte consecutivi (spesso quattro per un `int`) e vi registra il valore `42`. Finora hai lavorato solo con il nome `quota`, lasciando al compilatore il compito di ricordare dove quei byte si trovino. Per scrivere programmi più flessibili, però, spesso serve poter indicare *dove* si trova un oggetto in memoria, così da accedervi o modificarlo senza conoscerne il nome diretto.

Puoi immaginare la memoria di un programma come una lunga strada di case numerate in sequenza, dove ogni casa contiene un singolo byte e possiede un numero civico univoco. Un oggetto che occupa quattro byte, come un `int`, risiede in quattro byte contigui ed è identificato dal numero del suo primo byte. Questo numero è chiamato **indirizzo di memoria** (*memory address*): è la posizione numerica che identifica un byte o l'inizio di un oggetto nella memoria del programma. Una variabile costruita apposta per memorizzare questo tipo di informazione è un **puntatore** (*pointer*): una variabile che memorizza l'indirizzo di memoria di un oggetto o di una funzione, oppure il valore nullo.

```text
Indirizzo      Contenuto (4 byte)       Nome
-----------    ------------------       -----
0x1000         [     42     ]    <---+  quota (int)
...                                  |
0x1040         [   0x1000   ] -------+  p     (int *)
```

Nello schema gli indirizzi `0x1000` e `0x1040` sono puramente simbolici: in un programma reale il sistema operativo assegna gli indirizzi a ogni esecuzione. Osserva però il punto essenziale: `quota` contiene il numero `42`, mentre `p` è una variabile distinta, con un proprio indirizzo (`0x1040`), il cui contenuto è l'indirizzo di `quota` (`0x1000`).

Per ricavare l'indirizzo di un oggetto in memoria si usa l'**operatore indirizzo** `&` (*address-of operator*), posto davanti al nome dell'oggetto. Se `quota` ha tipo `int`, l'espressione `&quota` produce l'indirizzo di `quota`, che ha tipo `int *` (si legge "puntatore a `int`"). Questo spiega finalmente la sintassi che usi dal capitolo 5 nelle chiamate a `sscanf`: quando scrivi `sscanf(riga, "%d", &eta)`, passi a `sscanf` l'indirizzo di `eta` affinché la funzione sappia in quale posizione della memoria scrivere il numero convertito.

Per dichiarare un puntatore si indica il tipo dell'oggetto puntato seguito dal simbolo `*` e dal nome della variabile:

<!-- cod: id=10.1-b tipo=frammento -->
```c
int x = 10;
int y = 20;
int *p = &x;  // p memorizza l'indirizzo di x
p = &y;       // ora p memorizza l'indirizzo di y
```

Un puntatore è a tutti gli effetti una variabile: può essere inizializzato con `&x` e riassegnato in seguito a `&y`, purché `y` abbia lo stesso tipo puntato (`int`). Fai molta attenzione a una trappola sintattica del C quando dichiari più variabili sulla stessa riga: il simbolo `*` si lega al singolo identificatore, non al tipo base. Se scrivi `int* a, b;`, soltanto `a` ha tipo `int *`, mentre `b` è un normale `int`. Per evitare errori, scrivi sempre lo spazio prima dell'asterisco (`int *a;`) e dichiara un puntatore per riga.

Avere un indirizzo serve a poco se non puoi leggere o modificare l'oggetto che si trova a quell'indirizzo. L'operazione che segue il puntatore fino all'oggetto puntato si chiama **dereferenziazione** (*dereferencing*) e si esegue con l'**operatore di dereferenziazione** `*` applicato davanti al nome del puntatore:

<!-- cod: id=10.1-c tipo=frammento -->
```c
int x = 10;
int *p = &x;
int copia = *p;  // legge il valore di x (10)
*p = *p + 1;     // modifica x attraverso p: ora x vale 11
```

Non confondere i due significati del simbolo `*`: in una dichiarazione (`int *p`) fa parte del tipo e significa "`p` è un puntatore a `int`"; in un'espressione (`*p`) è l'operatore di dereferenziazione e significa "l'oggetto che si trova all'indirizzo contenuto in `p`".

Possiamo riassumere le regole fondamentali in questo modo:

- L'operatore indirizzo `&` applicato a un oggetto in memoria ne restituisce l'indirizzo di tipo `T *`.
- Un puntatore dichiarato come `T *p` memorizza l'indirizzo di un oggetto di tipo `T` (oppure il valore nullo, che vedrai nella prossima sotto-sezione).
- L'operatore di dereferenziazione `*` applicato a un puntatore valido accede in lettura o in scrittura all'oggetto puntato.
- Nelle dichiarazioni multiple il simbolo `*` si lega al singolo identificatore: in `int *a, b;` solo `a` è un puntatore.

Secondo lo standard C23, il comportamento di `&` e `*` applicati a oggetti e puntatori validi è completamente definito. Al contrario, dereferenziare un puntatore non inizializzato o che contiene un indirizzo non valido provoca **comportamento indefinito**: il puntatore conterrebbe bit casuali rimasti in memoria e leggere o scrivere a quell'indirizzo può far chiudere il programma o corrompere altri dati. Inizializza quindi sempre ogni puntatore nel momento in cui lo dichiari.

Quanta memoria occupa un puntatore? Puoi verificarlo con `sizeof(p)` o `sizeof(int *)`. La dimensione di un puntatore dipende dall'architettura (è un comportamento dipendente dall'implementazione: in genere 8 byte sui sistemi a 64 bit e 4 byte sui sistemi a 32 bit), ma sullo stesso sistema i puntatori ai vari tipi di oggetto hanno tipicamente la stessa dimensione: `sizeof(int *)` e `sizeof(double *)` coincidono, perché entrambi conservano un indirizzo di memoria, non l'oggetto intero.

Infine, per ispezionare un indirizzo durante il debug esiste lo specificatore `%p` di `printf`, ma gli indirizzi numerici cambiano a ogni esecuzione del programma per ragioni di sicurezza del sistema operativo. Nei programmi normali non si confrontano mai gli indirizzi stampandoli o convertendoli in numeri, bensì usando direttamente gli operatori `==` e `!=` (per esempio `p == &b` per verificare se `p` punta proprio a `b`).

> **Se vieni da Python** — In Python i riferimenti agli oggetti sono gestiti implicitamente dall'interprete e non esistono indirizzi di memoria espliciti né operatori come `&` e `*`. In C i puntatori espongono direttamente gli indirizzi e ti danno controllo totale sulla memoria, ma richiedono disciplina rigorosa su inizializzazione e validità.

### Esempio guidato

Il programma seguente gestisce due contatori interi `a` e `b` attraverso un unico puntatore `p`. Prima legge e aggiorna `a` dereferenziando `p`, poi sposta `p` su `b` per aggiornarlo, verifica con `==` quale variabile sia puntata e infine mostra la dimensione in byte di `int *` e `double *`.

<!-- cod: id=10.1-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    int a = 10;
    int b = 25;
    int *p = &a;

    printf("Inizio: a=%d, b=%d, *p=%d\n", a, b, *p);

    *p += 5;
    printf("Dopo *p += 5: a=%d, b=%d\n", a, b);

    p = &b;
    *p -= 10;
    printf("Dopo p = &b e *p -= 10: a=%d, b=%d\n", a, b);

    if (p == &b) {
        printf("p punta a b (valore %d)\n", *p);
    }

    printf("sizeof(int *) = %zu, sizeof(double *) = %zu\n",
           sizeof(int *), sizeof(double *));
    return 0;
}
```

```output
Inizio: a=10, b=25, *p=10
Dopo *p += 5: a=15, b=25
Dopo p = &b e *p -= 10: a=15, b=15
p punta a b (valore 15)
sizeof(int *) = 8, sizeof(double *) = 8
```

Osserva passo dopo passo che cosa accade:

- Alla riga `int *p = &a;` il puntatore `p` riceve l'indirizzo di `a`. Leggere `*p` restituisce `10`, cioè il valore attuale di `a`.
- L'istruzione `*p += 5;` modifica l'oggetto puntato da `p`: il valore di `a` passa da `10` a `15`, mentre `b` resta intatto.
- Con `p = &b;` non modifichi `a` né `b`, ma cambi l'indirizzo memorizzato dentro `p`. La successiva operazione `*p -= 10;` agisce quindi su `b`, portandolo da `25` a `15`.
- Il controllo `if (p == &b)` confronta due indirizzi in modo portabile e deterministico, senza dipendere dal valore numerico assegnato dal sistema operativo.
- L'ultima `printf` stampa `8` su un sistema a 64 bit (potrebbe stampare `4` su un sistema a 32 bit), mostrando che un puntatore a `int` e un puntatore a `double` occupano la stessa quantità di memoria anche se `int` e `double` hanno dimensioni diverse.

> **Approfondimento — Perché un puntatore porta con sé il tipo puntato**
> Se un puntatore a `int` e un puntatore a `double` occupano lo stesso numero di byte, perché in C occorre distinguere `int *` da `double *`? Perché un indirizzo identifica solo il primo byte dell'oggetto: è il tipo del puntatore a dire al compilatore quanti byte leggere o scrivere durante `*p` e come interpretare i bit (come intero o come numero in virgola mobile). Inoltre il controllo dei tipi impedisce di assegnare per errore un `double *` a un `int *`, evitando corruzioni silenziose dei dati.

### Esercizio 10.1 — Controllo di due serbatoi tramite puntatore selettore

**Descrizione**

Scrivi un programma C che gestisca i livelli in litri di due serbatoi (`double serbatoio_a` e `double serbatoio_b`) usando un puntatore `double *attivo = &serbatoio_a;` che punta di volta in volta al serbatoio selezionato. Leggi dalla prima riga di `stdin` i due livelli iniziali (`double >= 0.0`, validati con `sscanf(riga, "%lf %lf %c", &serbatoio_a, &serbatoio_b, &extra) == 2`). Leggi poi fino alla fine dell'input una sequenza di comandi (uno per riga): `S A` sposta `attivo` su `&serbatoio_a`; `S B` sposta `attivo` su `&serbatoio_b`; `A <delta>` somma `delta` (`double`) al serbatoio puntato tramite `*attivo += delta;` (se `*attivo < 0.0`, azzera `*attivo = 0.0;`); `D` raddoppia il livello del serbatoio puntato tramite `*attivo *= 2.0;`. In caso di comando o formato non valido stampa un messaggio su `stderr` e restituisci `EXIT_FAILURE`. Al termine stampa quale serbatoio è attivo (usando il confronto di indirizzi `attivo == &serbatoio_a`), il valore letto attraverso `*attivo` e i livelli finali di entrambi i serbatoi con due cifre decimali, esattamente come nell'esempio di esecuzione (senza stampare indirizzi con `%p`).

**Concetti da tenere a mente**

- operatore indirizzo `&` per ottenere l'indirizzo di una variabile
- dichiarazione e riassegnazione di un puntatore `double *`
- dereferenziazione `*` per leggere e modificare la variabile puntata
- confronto tra puntatori con `==` senza dipendere dai valori numerici degli indirizzi

**Domande guida**

1. Quale operatore usi per fare in modo che il puntatore `attivo` memorizzi l'indirizzo di `serbatoio_a` o di `serbatoio_b`?
2. Che differenza c'è tra scrivere `attivo = &serbatoio_b` e scrivere `*attivo = serbatoio_b`?
3. Come puoi determinare alla fine quale serbatoio è selezionato usando solo il puntatore `attivo` e gli indirizzi dei due serbatoi?
4. Perché quando esegui `*attivo *= 2.0` viene aggiornato automaticamente il serbatoio corretto senza bisogno di un `if` su `A` o `B`?

**Esempio di esecuzione**

```input
10.0 25.0
A 5.5
S B
D
A -60.0
S A
D
```

```output
Serbatoio attivo: A
Livello attivo (*attivo): 31.00 L
Serbatoio A: 31.00 L
Serbatoio B: 0.00 L
```

## 10.2 Puntatori nulli: `nullptr` e `NULL`

Nella sotto-sezione precedente hai visto che un puntatore non inizializzato è pericoloso, perché contiene un indirizzo casuale. Spesso però, nel momento in cui dichiari un puntatore, non hai ancora un oggetto valido a cui farlo puntare: magari stai per cercarlo in un array, oppure l'oggetto esiste solo a determinate condizioni. Come puoi distinguere un puntatore che punta davvero a qualcosa da un puntatore che al momento non punta a nulla?

Il linguaggio C mette a disposizione un valore speciale riservato proprio a questo scopo. Un **puntatore nullo** (*null pointer*) è un puntatore con valore `nullptr` o `NULL` che indica esplicitamente di non puntare ad alcun oggetto valido. Lo standard garantisce che nessun oggetto e nessuna funzione validi abbiano mai un indirizzo uguale al puntatore nullo: questo lo rende un segnale inequivocabile di assenza di oggetto.

Ogni volta che dichiari un puntatore senza avere ancora un indirizzo da assegnargli, inizializzalo subito a `nullptr`:

<!-- cod: id=10.2-b tipo=frammento -->
```c
int *selezionato = nullptr;  // stato iniziale sicuro e verificabile
```

In C23 il puntatore nullo si scrive con la parola chiave `nullptr` (che hai già usato dal capitolo 5 con `fgets`). Nel codice C più vecchio e in moltissime librerie esistenti incontrerai invece la macro storica `NULL`, definita negli header `<stddef.h>`, `<stdio.h>`, `<stdlib.h>` e `<string.h>`. In C23 `nullptr` è preferita perché ha un tipo proprio non confondibile con l'intero `0`, ma entrambi rappresentano un puntatore nullo e risultano sempre uguali tra loro al confronto con `==`.

> **C23** — La parola chiave `nullptr` è stata introdotta in C23 e non richiede alcun `#include`. Se compili un programma con un compilatore configurato per C17 o C11, sostituisci `nullptr` con `NULL` includendo `<stddef.h>` (o `<stdio.h>`).

Un puntatore nullo è sicuro da memorizzare, copiare e confrontare con `==` o `!=`, ma **non può mai essere dereferenziato**. Dereferenziare `nullptr` o `NULL` provoca **comportamento indefinito**: nella pratica, sui sistemi operativi moderni causa quasi sempre la chiusura immediata del programma (*segmentation fault*), ma lo standard non garantisce neppure questo. Il frammento seguente mostra un errore grave da non scrivere mai:

<!-- cod: id=10.2-c tipo=frammento -->
```c
// ERRORE: comportamento indefinito, non scrivere mai così!
int *p = nullptr;
int valore = *p;  // dereferenziazione di un puntatore nullo
```

La regola operativa è semplice e non ammette eccezioni: prima di dereferenziare qualunque puntatore potenzialmente nullo, verifica sempre che sia diverso da `nullptr`. Qui torna utilissima la **valutazione a corto circuito** dell'operatore `&&` (capitolo 4):

<!-- cod: id=10.2-d tipo=frammento -->
```c
if (p != nullptr && *p > 0) {
    printf("Valore positivo: %d\n", *p);
}
```

Se `p` è uguale a `nullptr`, la condizione a sinistra di `&&` è `false` e il programma non valuta affatto `*p > 0`, evitando la dereferenziazione nulla. Se invertissi l'ordine scrivendo `*p > 0 && p != nullptr`, il controllo arriverebbe troppo tardi e il programma avrebbe comportamento indefinito.

Un impiego fondamentale del puntatore nullo è come valore di ritorno delle funzioni di ricerca o di lettura quando l'operazione non trova ciò che cerca. Hai già visto questo schema nella libreria standard:

- `fgets` restituisce il puntatore al buffer se ha letto una riga, oppure un puntatore nullo in caso di fine dell'input o errore;
- `strchr`, `strrchr` e `strstr` (capitolo 9) cercano un carattere o una sottostringa e restituiscono il puntatore alla posizione trovata, oppure un puntatore nullo se l'elemento non compare.

Restituire `nullptr` risolve un problema che con un semplice `int` sarebbe scomodo: se una funzione cerca un intero dentro un array e restituisse `-1` in caso di assenza, non potresti distinguere il caso "non trovato" dal caso in cui l'array contiene proprio il numero `-1`. Restituendo un puntatore all'elemento trovato (o `nullptr` se assente), l'ambiguità scompare del tutto.

Ricapitolando le regole secondo lo standard C23: `nullptr`, `NULL` e l'uguaglianza tra tutti i puntatori nulli al confronto `==` hanno comportamento definito; dereferenziare un puntatore nullo provoca invece comportamento indefinito.

> **Se vieni da Python** — In Python il valore assente è `None` e provare a usarlo come un oggetto valido solleva un'eccezione controllata (`AttributeError` o `TypeError`). In C il puntatore nullo è `nullptr` (o `NULL`), ma il linguaggio non esegue controlli automatici prima della dereferenziazione: omettere `p != nullptr` porta direttamente al comportamento indefinito.

### Esempio guidato

Il programma seguente definisce una funzione `cerca_primo_negativo` che restituisce l'indirizzo del primo elemento negativo di un array oppure `nullptr` se tutti gli elementi sono non negativi. In `main` la funzione viene chiamata su due array diversi, ogni dereferenziazione è protetta da `if (p != nullptr)` e viene verificata l'uguaglianza tra `nullptr` e `NULL`.

<!-- cod: id=10.2-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

const int *cerca_primo_negativo(const int a[], size_t n);

int main(void) {
    const int serie_a[] = {12, 4, -7, 9, -2};
    const int serie_b[] = {3, 0, 15, 8};

    const int *p1 = cerca_primo_negativo(serie_a, 5);
    if (p1 != nullptr) {
        printf("Serie A: primo negativo = %d\n", *p1);
    } else {
        printf("Serie A: nessun negativo\n");
    }

    const int *p2 = cerca_primo_negativo(serie_b, 4);
    if (p2 != nullptr) {
        printf("Serie B: primo negativo = %d\n", *p2);
    } else {
        printf("Serie B: nessun negativo\n");
    }

    if (nullptr == NULL) {
        printf("Conferma: nullptr == NULL\n");
    }
    return 0;
}

const int *cerca_primo_negativo(const int a[], size_t n) {
    for (size_t i = 0; i < n; ++i) {
        if (a[i] < 0) {
            return &a[i];
        }
    }
    return nullptr;
}
```

```output
Serie A: primo negativo = -7
Serie B: nessun negativo
Conferma: nullptr == NULL
```

Analizziamo i dettagli principali:

- La funzione `cerca_primo_negativo` scorre gli elementi di `a` e, appena trova `a[i] < 0`, restituisce `&a[i]`, cioè l'indirizzo di quell'elemento dell'array del chiamante. Se il ciclo termina senza trovare negativi, restituisce `nullptr`.
- Il tipo di ritorno è `const int *` perché l'array di ingresso è `const int a[]`: vedrai tutti i dettagli di `const` con i puntatori nella sotto-sezione 10.6.
- Per `serie_a` il puntatore `p1` punta a `serie_a[2]`, quindi `p1 != nullptr` è vero e `*p1` vale `-7`.
- Per `serie_b` il puntatore `p2` vale `nullptr`; il ramo `else` evita la dereferenziazione e stampa il messaggio di assenza.
- Il confronto finale `nullptr == NULL` è sempre vero per definizione dello standard C23.

> **Approfondimento — Perché `nullptr` è più sicuro di `NULL`**
> Nello standard C la macro `NULL` può essere definita dall'implementazione come `((void *)0)` oppure come il semplice intero `0`. Nel secondo caso `NULL` è a tutti gli effetti un `int`, quindi espressioni errate come `int n = NULL;` possono compilare senza errori. In C23 `nullptr` ha invece un tipo dedicato (`nullptr_t`) che si converte a qualunque tipo puntatore e a `bool`, ma non si converte implicitamente a `int`: eventuali scambi tra un intero e un puntatore nullo vengono così intercettati subito dal compilatore.

### Esercizio 10.2 — Ricerca e correzione sicura con puntatori e `nullptr`

**Descrizione**

Scrivi un programma C che dichiari prima di `main` i prototipi di due funzioni che restituiscono un puntatore a un elemento di un array oppure `nullptr` se nessun elemento soddisfa il criterio: `int *trova_massimo(int dati[], size_t n)` (restituisce l'indirizzo del massimo, scegliendo il primo in caso di parità, oppure `nullptr` se `n == 0`) e `int *trova_primo_oltre_soglia(int dati[], size_t n, int soglia)` (restituisce l'indirizzo del primo elemento strettamente maggiore di `soglia`, oppure `nullptr` se assente). In `main` leggi dalla prima riga di `stdin` `n soglia` (`0 <= n <= 20`) e dalle successive `n` righe gli `n` interi dell'array `int misure[20] = {0};` (in caso di errore di input stampa su `stderr` e restituisci `EXIT_FAILURE`). Chiama `trova_massimo`: se restituisce `nullptr`, stampa `Massimo: nessuno (array vuoto)`; altrimenti stampa `Massimo: <val>` dereferenziando il puntatore. Chiama poi `trova_primo_oltre_soglia`: se restituisce `nullptr`, stampa `Oltre soglia: nessuno`; altrimenti stampa `Primo oltre soglia: <val>`, porta quell'elemento a `soglia` direttamente tramite `*p_oltre = soglia;` e stampa tutti gli elementi dell'array aggiornato su una riga (separati da spazio) esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- puntatore nullo con `nullptr` (C23)
- restituzione di un puntatore a un elemento di array oppure `nullptr`
- controllo obbligatorio `p != nullptr` prima della dereferenziazione
- modifica diretta di un elemento trovato tramite `*p = valore`

**Domande guida**

1. Perché le due funzioni restituiscono `nullptr` invece di un valore speciale come `-1` quando non trovano un elemento valido?
2. Che cosa succederebbe se dereferenziassi `p_max` nel caso limite `n == 0` senza aver controllato prima `p_max != nullptr`?
3. Come mai assegnare `*p_oltre = soglia` in `main` modifica proprio l'elemento corrispondente dentro l'array `misure`?
4. Perché è sicuro restituire `&dati[i]` da `trova_massimo` quando `dati` appartiene a `main`?

**Esempio di esecuzione**

```input
5 50
30
65
40
80
50
```

```output
Massimo: 80
Primo oltre soglia: 65
Dati aggiornati: 30 50 40 80 50
```

## 10.3 Il legame tra puntatori e array

Nel capitolo 8 hai osservato due fatti curiosi sugli array: quando passi un array a una funzione, la funzione può modificare direttamente gli elementi dell'array del chiamante; inoltre, dentro quella funzione, `sizeof(a)` non ti dice più quanti byte occupa l'intero array. Con i puntatori puoi finalmente capire il meccanismo esatto che governa gli array in C.

Un array e un puntatore **non sono la stessa cosa**: un array `int valori[5]` è un blocco contiguo di cinque oggetti `int` in memoria, mentre un puntatore `int *p` è una singola variabile che contiene un indirizzo. Tuttavia, il C collega strettamente i due concetti attraverso una regola di conversione chiamata **decadimento di array** (*array decay*): nella maggior parte delle espressioni, il nome di un array di tipo `T[N]` viene convertito automaticamente dal compilatore in un puntatore di tipo `T *` che punta al suo primo elemento, cioè `&a[0]`.

Per questo motivo puoi scrivere:

<!-- cod: id=10.3-b tipo=frammento -->
```c
int valori[5] = {10, 20, 30, 40, 50};
int *p = valori;  // equivalente a: int *p = &valori[0];
```

Il decadimento avviene quasi ovunque, ma esistono tre eccezioni importanti in cui l'array mantiene il proprio tipo `T[N]` senza diventare un puntatore:

1. Quando l'array è l'operando di `sizeof`: `sizeof(valori)` restituisce la dimensione dell'intero array in byte (`5 * sizeof(int)`), non la dimensione di un puntatore.
2. Quando l'array è l'operando di `&`: `&valori` produce l'indirizzo dell'intero array (un tipo puntatore ad array, diverso da `&valori[0]`).
3. Quando un letterale stringa viene usato per inizializzare un array di `char`, come in `char buf[] = "ciao";`: in quel caso i cinque byte `'c'`, `'i'`, `'a'`, `'o'`, `'\0'` vengono copiati dentro l'array `buf`.

Il legame tra array e puntatori è così stretto che nello standard C l'operatore di indicizzazione `[]` è definito proprio in termini di puntatori: per definizione, `a[i]` equivale esattamente a `*(a + i)` (la somma di un puntatore e di un intero sarà approfondita nella sotto-sezione 10.4). Da questa equivalenza discende una conseguenza pratica immediata: puoi applicare le parentesi quadre `p[i]` non solo al nome di un array, ma a **qualunque puntatore** che punti a un elemento di un array. Se `p = &valori[2]`, allora `p[0]` è `valori[2]`, `p[1]` è `valori[3]` e `p[2]` è `valori[4]`.

Questo chiarisce una volta per tutte il mistero del capitolo 8 sui parametri di funzione. In C gli array non vengono mai copiati per valore quando li passi a una funzione: un parametro dichiarato come `int a[]` (oppure `int a[10]`) viene adattato automaticamente dal compilatore a `int *a`. Ecco perché:

- passando `valori` alla funzione, l'array decade in `&valori[0]` e la funzione riceve l'indirizzo del primo elemento, potendo così leggere e modificare l'array del chiamante;
- dentro la funzione `a` è un vero puntatore `int *`, quindi `sizeof(a)` restituisce la dimensione di un puntatore, non quella dell'array originale (motivo per cui devi sempre passare la lunghezza `size_t n` come parametro separato).

Proprio per evitare illusioni sull'identità tra array e puntatori, tieni sempre presenti le loro differenze fondamentali:

- Un **array** occupa spazio per tutti i suoi `N` elementi e il suo nome **non è riassegnabile**: scrivere `valori = p;` è un errore di compilazione.
- Un **puntatore** occupa spazio per un solo indirizzo ed **è riassegnabile**: puoi spostarlo su un elemento intermedio (`p = &valori[2];`) oppure su un altro array dello stesso tipo.

La stessa distinzione vale per le stringhe. Osserva attentamente queste due righe:

<!-- cod: id=10.3-c tipo=frammento -->
```c
char buf[] = "ciao";        // array modificabile di 5 char ('c','i','a','o','\0')
const char *msg = "ciao";   // puntatore al primo carattere di un letterale stringa
```

Nel primo caso `buf` è un array locale che contiene una copia modificabile dei caratteri: puoi scrivere `buf[0] = 'C';`, ma non puoi riassegnare `buf` a un'altra stringa. Nel secondo caso `msg` è un puntatore che punta direttamente al letterale stringa: puoi riassegnare `msg = "arrivederci";`, ma non devi mai modificare i caratteri puntati. Secondo lo standard C23, il decadimento di array, le eccezioni di `sizeof` e `&`, l'equivalenza `a[i] == *(a + i)` e l'adattamento dei parametri array a puntatori hanno comportamento definito; tentare di modificare un letterale stringa tramite un puntatore provoca invece **comportamento indefinito**.

### Esempio guidato

Il programma seguente mette a confronto `sizeof(valori)` e `sizeof(p)`, verifica il decadimento `valori == &valori[0]`, mostra l'equivalenza tra `valori[i]`, `p[i]` e `*(p + i)`, sposta poi `p` sul terzo elemento per leggere una porzione dell'array e stampa un letterale stringa tramite `const char *`.

<!-- cod: id=10.3-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

int main(void) {
    int valori[5] = {10, 20, 30, 40, 50};
    int *p = valori;

    printf("sizeof(valori) = %zu, sizeof(p) = %zu\n",
           sizeof(valori), sizeof(p));

    if (valori == &valori[0] && p == &valori[0]) {
        printf("valori decade in &valori[0]\n");
    }

    for (size_t i = 0; i < 5; ++i) {
        printf("i=%zu: valori[i]=%d, p[i]=%d, *(p+i)=%d\n",
               i, valori[i], p[i], *(p + i));
    }

    p = &valori[2];
    printf("Sotto-sequenza da valori[2]: %d %d %d\n",
           p[0], p[1], p[2]);

    const char *messaggio = "Solo lettura";
    printf("Messaggio: %s\n", messaggio);
    return 0;
}
```

```output
sizeof(valori) = 20, sizeof(p) = 8
valori decade in &valori[0]
i=0: valori[i]=10, p[i]=10, *(p+i)=10
i=1: valori[i]=20, p[i]=20, *(p+i)=20
i=2: valori[i]=30, p[i]=30, *(p+i)=30
i=3: valori[i]=40, p[i]=40, *(p+i)=40
i=4: valori[i]=50, p[i]=50, *(p+i)=50
Sotto-sequenza da valori[2]: 30 40 50
Messaggio: Solo lettura
```

Osserva i punti chiave dell'esecuzione:

- `sizeof(valori)` vale `20` (5 elementi da 4 byte ciascuno) perché `sizeof` è un'eccezione al decadimento di array, mentre `sizeof(p)` vale `8` (la dimensione di un puntatore su un sistema a 64 bit).
- Il confronto `valori == &valori[0]` è vero perché nella valutazione di `==` il nome `valori` decade in `&valori[0]`.
- Nel ciclo `for`, le tre forme `valori[i]`, `p[i]` e `*(p + i)` accedono esattamente agli stessi elementi.
- Dopo `p = &valori[2];`, il puntatore punta al terzo elemento dell'array (`30`): da quel momento `p[0]`, `p[1]` e `p[2]` rappresentano la sotto-sequenza `30 40 50`, senza aver copiato alcun dato.
- Il puntatore `const char *messaggio` punta al primo carattere del letterale `"Solo lettura"`; il qualificatore `const` ti protegge da tentativi accidentali di modifica.

> **Approfondimento — Perché un letterale stringa va sempre associato a `const char *`**
> Per compatibilità storica con il C più antico, il tipo di un letterale stringa come `"ciao"` in C è `char[5]` (non `const char[5]`), quindi il compilatore potrebbe accettare `char *s = "ciao";`. Nonostante ciò, lo standard C consente al compilatore di collocare i letterali stringa in una zona di memoria di sola lettura o di condividere la stessa sequenza di byte tra più letterali identici nel programma: scrivere `s[0] = 'C';` provoca comportamento indefinito e di solito termina il programma con un errore di accesso alla memoria. Dichiarare sempre `const char *` trasforma qualunque tentativo di scrittura in un immediato errore di compilazione.

### Esercizio 10.3 — Finestre scorrevoli su array tramite decadimento e puntatori

**Descrizione**

Scrivi un programma C (`constexpr size_t MAX_DATI = 30;`) che dichiari prima di `main` i prototipi di due funzioni con parametro puntatore `const int *`: `int somma_finestra(const int *inizio, size_t k)` (somma i `k` elementi a partire da `inizio` usando `*(inizio + i)` oppure `inizio[i]`) e `void stampa_sequenza(const int *p, size_t n)` (stampa gli `n` elementi separati da un singolo spazio seguiti da ritorno a capo). In `main` leggi dalla prima riga di `stdin` `n k` (`1 <= k <= n <= 30`) e dalle successive `n` righe gli `n` valori interi dell'array `dati` (`-10'000..10'000`; in caso di errore stampa su `stderr` e restituisci `EXIT_FAILURE`). Stampa l'intera serie passando `dati` a `stampa_sequenza` (decadimento di array). Quindi esamina tutte le finestre contigue di lunghezza `k` (per `i` da `0` a `n - k` inclusi), passando `&dati[i]` a `somma_finestra`: stampa la somma di ciascuna finestra (`Finestra i: somma=...`) e conserva in un puntatore `const int *migliore` l'inizio della finestra di somma massima (in caso di parità mantieni la prima). Infine stampa la somma massima e gli elementi della finestra migliore chiamando `stampa_sequenza(migliore, k)`, esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- decadimento di array al primo elemento nel passaggio a funzione
- equivalenza tra parametri `const int a[]` e `const int *a`
- puntatore a un elemento intermedio (`&dati[i]`) come sotto-array
- equivalenza tra `p[i]` e `*(p + i)`

**Domande guida**

1. Perché puoi passare direttamente `dati` a `stampa_sequenza(const int *p, size_t n)` senza scrivere `&dati[0]`?
2. Come riesce `somma_finestra(const int *inizio, size_t k)` a lavorare su una qualsiasi porzione interna dell'array senza ricevere l'indice `i`?
3. Fino a quale valore può arrivare l'indice `i` di inizio finestra affinché `inizio[k - 1]` resti sempre dentro i limiti di `dati`?
4. Perché il puntatore `migliore` può essere passato direttamente a `stampa_sequenza(migliore, k)` al termine del ciclo?

**Esempio di esecuzione**

```input
6 3
4
-1
7
2
5
-3
```

```output
Serie: 4 -1 7 2 5 -3
Finestra 0: somma=10
Finestra 1: somma=8
Finestra 2: somma=14
Finestra 3: somma=4
Somma massima: 14
Finestra migliore: 7 2 5
```

## 10.4 Aritmetica dei puntatori e `ptrdiff_t`

Nella sotto-sezione precedente hai visto che `a[i]` equivale a `*(a + i)`. Che cosa significa esattamente sommare un intero `i` a un puntatore `a`? Se `a` punta a un `int` che occupa 4 byte, aggiungere `1` all'indirizzo grezzo ti porterebbe al secondo byte dello stesso `int`, non all'elemento successivo. Per rendere comoda e sicura la navigazione negli array, il C definisce una regola precisa.

L'**aritmetica dei puntatori** (*pointer arithmetic*) consiste nella somma e nella sottrazione tra puntatori e interi (e nella sottrazione tra due puntatori allo stesso array), scalate automaticamente per la dimensione del tipo puntato. Se `p` ha tipo `T *`, allora `p + k` e `p - k` spostano l'indirizzo di `k * sizeof(*p)` byte: in altre parole, `p + 1` punta sempre al prossimo elemento di tipo `T`, qualunque sia la dimensione di `T`.

```text
Array di int (4 byte per elemento):
Indirizzo:   0x2000     0x2004     0x2008     0x200C
Elementi:   [  10  ]   [  20  ]   [  30  ]   [  40  ]
               ^          ^          ^
               p        p + 1      p + 2    (passo: +4 byte)

Array di char (1 byte per elemento):
Indirizzo:   0x3000  0x3001  0x3002  0x3003
Elementi:   [ 'a' ] [ 'b' ] [ 'c' ] [ '\0' ]
               ^       ^       ^
               q     q + 1   q + 2          (passo: +1 byte)
```

Grazie alla scalatura automatica puoi usare su un puntatore gli stessi operatori di spostamento a cui sei abituato con gli indici:

- `++p` sposta `p` all'elemento successivo (`p + 1`);
- `--p` sposta `p` all'elemento precedente (`p - 1`);
- `p + k` e `p - k` calcolano l'indirizzo spostato avanti o indietro di `k` elementi.

Un idioma molto diffuso in C per scorrere un array (o una sua porzione) usa una coppia di puntatori che delimitano un intervallo semiaperto `[inizio, fine)`, dove `inizio` punta al primo elemento da visitare e `fine` punta a una posizione **uno oltre l'ultimo elemento** (`fine = a + n`):

<!-- cod: id=10.4-b tipo=frammento -->
```c
for (const int *p = a; p < a + n; ++p) {
    // elabora *p
}
```

L'intervallo semiaperto `[inizio, fine)` ha due vantaggi immediati: il numero di elementi dell'intervallo è esattamente `fine - inizio`, e un intervallo vuoto si rappresenta in modo naturale con `inizio == fine`.

Quando sottrai due puntatori `q - p` che puntano a elementi dello stesso array (o a uno oltre la fine dello stesso array), il risultato non è in byte ma è il **numero di elementi di distanza** tra `q` e `p`. Il risultato di questa sottrazione ha tipo **`ptrdiff_t`**, un tipo intero con segno definito in `<stddef.h>` che si stampa con `printf` usando lo specificatore `%td`.

Le regole di validità stabilite dallo standard C23 per l'aritmetica dei puntatori sono molto rigorose:

- Dato un array `a` di `n` elementi, è lecito formare, confrontare e sottrarre qualunque puntatore nell'intervallo `[a, a + n]`, incluso il puntatore `a + n` (uno oltre la fine).
- **Non è mai lecito dereferenziare `a + n`**: non punta a nessun elemento dell'array e leggerlo o scriverlo provoca comportamento indefinito.
- **Non è mai lecito formare puntatori fuori da `[a, a + n]`**, neppure senza dereferenziarli: per esempio calcolare `a - 1` o `a + n + 1` provoca già comportamento indefinito.
- **Non è lecito sottrarre (`q - p`) né confrontare con `<`, `<=`, `>`, `>=` due puntatori che appartengono ad array distinti**: anche questa operazione provoca comportamento indefinito. (Il confronto di uguaglianza `==` e `!=` resta invece definito tra puntatori compatibili validi.)
- Non è possibile sommare due puntatori (`p + q` è un errore di compilazione), né moltiplicarli o dividerli.

Un'applicazione immediata della sottrazione di puntatori è il lavoro con le funzioni di ricerca di `<string.h>` che hai conosciuto nel capitolo 9: `strchr`, `strrchr` e `strstr` restituiscono un puntatore al carattere trovato all'interno della stringa passata (oppure un puntatore nullo). Per sapere a quale **indice** si trova l'occorrenza, non serve rifare un ciclo: basta verificare che il puntatore non sia `nullptr` e sottrarre il puntatore di inizio stringa (`pos - s`). Allo stesso modo, se hai trovato due posizioni `p1` e `p2` nella stessa stringa, `p2 - p1` ti dà subito la loro distanza in caratteri come `ptrdiff_t`.

### Esempio guidato

Il programma seguente scorre un array di `double` con una coppia di puntatori `[inizio, fine)` calcolando l'indice corrente tramite `p - inizio` (`ptrdiff_t` stampato con `%td`). Poi cerca `'C'` e `"moderno"` in una stringa con `strchr` e `strstr` e ricava indici e distanza per sottrazione di puntatori.

<!-- cod: id=10.4-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    const double misure[] = {18.5, 21.0, 19.5, 22.0};
    const size_t n = sizeof(misure) / sizeof(misure[0]);
    const double *inizio = misure;
    const double *fine = misure + n;

    double somma = 0.0;
    for (const double *p = inizio; p < fine; ++p) {
        ptrdiff_t indice = p - inizio;
        printf("misure[%td] = %.2f\n", indice, *p);
        somma += *p;
    }
    printf("Media = %.2f\n", somma / (double)n);

    const char *frase = "linguaggio C moderno";
    const char *pos_c = strchr(frase, 'C');
    const char *pos_mod = strstr(frase, "moderno");

    if (pos_c != nullptr && pos_mod != nullptr) {
        ptrdiff_t idx_c = pos_c - frase;
        ptrdiff_t idx_mod = pos_mod - frase;
        ptrdiff_t distanza = pos_mod - pos_c;
        printf("'C' a indice %td, \"moderno\" a indice %td\n",
               idx_c, idx_mod);
        printf("Distanza tra 'C' e \"moderno\": %td caratteri\n",
               distanza);
    }
    return 0;
}
```

```output
misure[0] = 18.50
misure[1] = 21.00
misure[2] = 19.50
misure[3] = 22.00
Media = 20.25
'C' a indice 11, "moderno" a indice 13
Distanza tra 'C' e "moderno": 2 caratteri
```

Osserva come lavorano i puntatori nell'esempio:

- `fine = misure + n` calcola il puntatore uno oltre la fine dell'array di 4 `double` (spostandosi di `4 * sizeof(double)` byte). Il ciclo termina quando `p == fine`, quindi `fine` viene usato solo nel confronto `p < fine` e non viene mai dereferenziato.
- A ogni iterazione `++p` avanza automaticamente di `sizeof(double)` byte; `p - inizio` divide implicitamente la distanza in byte per `sizeof(double)` e restituisce `0`, `1`, `2`, `3` con tipo `ptrdiff_t`.
- Nella seconda parte, `pos_c` e `pos_mod` puntano dentro la stessa stringa `frase`. Dopo aver verificato che entrambi siano diversi da `nullptr`, le sottrazioni `pos_c - frase`, `pos_mod - frase` e `pos_mod - pos_c` producono direttamente gli indici e la distanza in caratteri, stampati con `%td`.

> **Approfondimento — Perché `ptrdiff_t` è un tipo con segno (e non `size_t` o `int`)**
> La dimensione di un oggetto non può essere negativa, quindi `sizeof` restituisce il tipo senza segno `size_t`. La differenza tra due puntatori `p - q`, invece, è negativa ogniqualvolta `p` precede `q` nell'array: serve quindi un tipo con segno. Non si usa `int` perché sui sistemi a 64 bit un array può contenere più di `INT_MAX` elementi; `ptrdiff_t` ha invece la stessa ampiezza di `size_t` (tipicamente 64 bit con segno sui sistemi moderni), garantendo di poter rappresentare correttamente la distanza con segno tra elementi di grandi array.

### Esercizio 10.4 — Distanze tra delimitatori e inversione di intervalli con aritmetica dei puntatori

**Descrizione**

Scrivi un programma C che includa `<stddef.h>`, `<stdio.h>`, `<stdlib.h>` e `<string.h>` e dichiari prima di `main` i prototipi di due funzioni basate su aritmetica dei puntatori: `ptrdiff_t lunghezza_ptr(const char *s)` (avanza un puntatore `p` finché `*p != '\0'` e restituisce `p - s`) e `void inverti_intervallo(char *inizio, char *fine)` (inverte sul posto i caratteri nell'intervallo semiaperto `[inizio, fine)` senza dereferenziare mai `fine`). In `main` leggi due righe da `stdin`: la prima è una stringa `testo` (buffer `128` byte, rimuovendo `'\n'` con `strcspn`), la seconda contiene un solo carattere delimitatore `sep` validato con `sscanf(riga_s, " %c %c", &sep, &extra) == 1` (in caso di errore stampa su `stderr` e restituisci `EXIT_FAILURE`). Calcola `ptrdiff_t len = lunghezza_ptr(testo);` e cerca prima e ultima occorrenza di `sep` con `strchr` e `strrchr`. Se `sep` non compare, stampa `Lunghezza: <len>`, `Delimitatore '<sep>' assente.`, chiama `inverti_intervallo(testo, testo + len)` e stampa `Risultato: <testo>`. Se `sep` compare, conta tutte le occorrenze avanzando un puntatore `const char *cur = prima;` con `strchr` e `++cur`, calcola con `ptrdiff_t` gli indici della prima (`prima - testo`), dell'ultima (`ultima - testo`) e la distanza (`ultima - prima`), poi se `ultima > prima + 1` inverte solo i caratteri strettamente compresi tra la prima e l'ultima occorrenza chiamando `inverti_intervallo(prima + 1, ultima)`. Stampa tutti i valori con `%td` e il risultato finale esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- aritmetica dei puntatori (`++p`, `--p`, `p + k`, `q - p`)
- tipo `ptrdiff_t` (`<stddef.h>`) e specificatore `%td`
- intervallo semiaperto `[inizio, fine)` senza dereferenziare `fine`
- calcolo degli indici a partire dai puntatori restituiti da `strchr` e `strrchr`

**Domande guida**

1. Perché in `lunghezza_ptr` la sottrazione `p - s` restituisce un valore di tipo `ptrdiff_t` e quale specificatore di formato usi in `printf`?
2. In `inverti_intervallo(char *inizio, char *fine)`, perché il puntatore destro va decrementato prima di dereferenziarlo e perché il ciclo usa `sx < dx`?
3. Come fai a evitare di contare sempre la stessa occorrenza del delimitatore nel ciclo con `strchr(cur, sep)`?
4. Perché quando `prima` e `ultima` coincidono (una sola occorrenza) oppure sono adiacenti (`ultima == prima + 1`) l'intervallo `[prima + 1, ultima)` non contiene caratteri da invertire?

**Esempio di esecuzione**

```input
uno/due/tre/quattro
/
```

```output
Lunghezza: 19
Occorrenze di '/': 3
Prima: 3, ultima: 11, distanza: 8
Risultato: uno/ert/eud/quattro
```

## 10.5 Passaggio per puntatore

Nel capitolo 7 hai imparato che in C gli argomenti delle funzioni sono sempre trasferiti tramite **passaggio per valore**: la funzione riceve una copia dei valori passati dal chiamante, quindi qualunque modifica ai parametri resta confinata dentro la funzione. Se vuoi scrivere una funzione `scambia` che scambi i contenuti di due variabili `x` e `y` di `main`, oppure una funzione che calcoli contemporaneamente quoziente e resto di una divisione, il solo passaggio per valore di numeri non basta.

I puntatori risolvono questo limite in modo pulito: invece di passare il *valore* di `x` e `y`, passi i loro **indirizzi** (`&x` e `&y`) a parametri di tipo `int *`. La funzione riceve comunque una copia di quegli indirizzi, ma dereferenziandoli con `*a` e `*b` accede direttamente alle variabili originali del chiamante e può modificarle.

```text
In main:                          In scambia(int *a, int *b):
  x (0x1000): [ 17 ]  <----------- a: [ 0x1000 ]   (*a accede a x)
  y (0x1004): [  5 ]  <----------- b: [ 0x1004 ]   (*b accede a y)
```

In C questa tecnica si chiama **passaggio per puntatore**. È importante usare il termine esatto: a differenza di altri linguaggi, il C non ha un meccanismo di riferimento implicito o automatico. Anche quando usi i puntatori, il meccanismo del linguaggio resta sempre il passaggio per valore: ciò che viene copiato per valore dentro il parametro della funzione è l'indirizzo di memoria. Proprio perché il chiamante deve scrivere esplicitamente `&x`, leggendo una chiamata come `scambia(&x, &y)` si capisce subito quali variabili possono essere modificate.

Lo stesso schema permette di restituire **più risultati** da una sola funzione tramite i **parametri di uscita** (*output parameters*). In C è una convenzione molto diffusa combinare i parametri di uscita con un valore di ritorno `bool`: la funzione restituisce `true` se il calcolo è riuscito e scrive i risultati negli indirizzi forniti, oppure restituisce `false` in caso di errore (per esempio una divisione per zero o un array vuoto) senza alterare i dati del chiamante.

Prima di dereferenziare qualunque parametro puntatore di ingresso o di uscita, una funzione ben scritta controlla sempre che non sia `nullptr`. Questo controllo ti permette anche di progettare **parametri di uscita opzionali**: se il chiamante non è interessato a uno dei risultati (per esempio vuole solo massimo e media, ma non il minimo), può passare `nullptr` per quel parametro e la funzione scriverà il risultato solo se il puntatore corrispondente è diverso da `nullptr`:

<!-- cod: id=10.5-b tipo=frammento -->
```c
if (min_out != nullptr) {
    *min_out = mn;
}
```

Esiste un errore grave legato ai puntatori e alle funzioni che devi conoscere e prevenire fin da subito: **una funzione non deve mai restituire l'indirizzo di una propria variabile locale automatica**. Come hai visto nel capitolo 7, la durata di vita di una variabile locale automatica termina nel momento in cui la funzione finisce; l'indirizzo restituito punterebbe quindi a memoria non più valida. Usare quel puntatore nel chiamante provoca **comportamento indefinito** (approfondiremo questo problema e i modi corretti per evitarlo nel capitolo 14). Ecco un esempio di codice da non scrivere mai:

<!-- cod: id=10.5-c tipo=frammento -->
```c
// ERRORE: comportamento indefinito, non scrivere mai così!
int *sbagliata(void) {
    int locale = 42;
    return &locale;  // locale cessa di esistere all'uscita dalla funzione
}
```

Secondo lo standard C23, il passaggio per puntatore su oggetti ancora vivi è completamente definito; usare invece il puntatore a una variabile locale automatica dopo il termine della funzione provoca comportamento indefinito.

> **Se vieni da Python** — In Python una funzione può restituire più valori contemporaneamente impacchettandoli in una tupla (`return q, r`). In C una funzione restituisce un solo valore con `return`: per restituire più risultati o modificare variabili del chiamante si usa spesso il passaggio per puntatore con parametri di uscita.

### Esempio guidato

Il programma seguente mostra tre usi tipici del passaggio per puntatore: `scambia` modifica due variabili del chiamante, `dividi_sicuro` restituisce quoziente e resto tramite parametri di uscita segnalando con `bool` l'eventuale divisione per zero, e `statistiche` calcola minimo, massimo e media accettando `nullptr` per i risultati che il chiamante non desidera.

<!-- cod: id=10.5-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

void scambia(int *a, int *b) {
    if (a == nullptr || b == nullptr) { return; }
    int tmp = *a;
    *a = *b;
    *b = tmp;
}
bool dividi_sicuro(int num, int den, int *quoz, int *resto) {
    if (den == 0 || quoz == nullptr || resto == nullptr) { return false; }
    *quoz = num / den;
    *resto = num % den;
    return true;
}
bool statistiche(const int *a, size_t n, int *min_out, int *max_out, double *media_out) {
    if (a == nullptr || n == 0) { return false; }
    int mn = a[0], mx = a[0];
    double somma = 0.0;
    for (size_t i = 0; i < n; ++i) {
        if (a[i] < mn) { mn = a[i]; }
        if (a[i] > mx) { mx = a[i]; }
        somma += a[i];
    }
    if (min_out != nullptr) { *min_out = mn; }
    if (max_out != nullptr) { *max_out = mx; }
    if (media_out != nullptr) { *media_out = somma / (double)n; }
    return true;
}
int main(void) {
    int x = 17, y = 5, q = 0, r = 0, max_v = 0;
    scambia(&x, &y);
    printf("Dopo scambia: x=%d, y=%d\n", x, y);
    if (dividi_sicuro(y, x, &q, &r)) { printf("%d / %d = %d resto %d\n", y, x, q, r); }
    const int dati[] = {4, 12, 8, 16};
    double media = 0.0;
    if (statistiche(dati, 4, nullptr, &max_v, &media)) {
        printf("max=%d, media=%.2f\n", max_v, media);
    }
    return 0;
}
```

```output
Dopo scambia: x=5, y=17
17 / 5 = 3 resto 2
max=16, media=10.00
```

Esaminiamo il funzionamento delle tre funzioni:

- In `scambia(&x, &y)`, prima di dereferenziare `a` e `b`, la funzione controlla che nessuno dei due sia `nullptr`. Poi scambia i valori nelle celle di memoria di `x` e `y` usando `tmp`.
- In `dividi_sicuro`, i parametri `quoz` e `resto` sono obbligatori: se `den == 0` o uno dei puntatori è `nullptr`, la funzione restituisce `false` senza modificare nulla. Con `y = 17` e `x = 5`, scrive `3` in `q` e `2` in `r` e restituisce `true`.
- In `statistiche`, i tre parametri di uscita sono opzionali. In `main` passiamo `nullptr` per `min_out`, `&max_v` per `max_out` e `&media` per `media_out`: la funzione calcola comunque i valori in variabili locali e scrive solo nei puntatori non nulli.

> **Approfondimento — Modificare `*p` contro modificare `p` dentro una funzione**
> Poiché in C il puntatore `p` viene copiato per valore quando chiami una funzione `void f(int *p)`, scrivere `*p = 10;` dentro `f` modifica l'oggetto puntato nel chiamante, ma scrivere `p = &altro;` modifica solo la copia locale del puntatore `p` e non ha alcun effetto sul puntatore del chiamante. Per fare in modo che una funzione possa riassegnare un puntatore appartenente al chiamante occorrono i puntatori a puntatori (`int **`) (lo vedremo nel capitolo 14).

### Esercizio 10.5 — Ordinamento e scomposizione di tempi di gara con passaggio per puntatore

**Descrizione**

Scrivi un programma C che dichiari prima di `main` i prototipi di tre funzioni basate sul passaggio per puntatore: `void scambia_int(int *a, int *b)` (se entrambi i puntatori sono diversi da `nullptr`, scambia `*a` e `*b`), `void ordina_tre(int *a, int *b, int *c)` (ordina in senso non decrescente `*a <= *b <= *c` richiamando `scambia_int`) e `bool scomponi_secondi(int secondi_totali, int *ore, int *minuti, int *secondi)` (se `secondi_totali < 0` restituisce `false` senza modificare alcun parametro di uscita; altrimenti scrive ore `tot / 3600`, minuti `(tot % 3600) / 60` e secondi `tot % 60` in ciascun puntatore di uscita diverso da `nullptr` — supportando parametri di uscita opzionali — e restituisce `true`). In `main` leggi da `stdin` una riga contenente tre tempi interi in secondi `t1 t2 t3` (ciascuno compreso tra `0` e `86'399` inclusi, validati con `"%d %d %d %c"` == `3`; in caso di errore stampa su `stderr` e restituisci `EXIT_FAILURE`). Ordina `t1`, `t2`, `t3` chiamando `ordina_tre(&t1, &t2, &t3)`. Stampa i tre tempi ordinati in formato `HH:MM:SS (T s)` usando `scomponi_secondi`, calcola e stampa il distacco `t3 - t1` con `scomponi_secondi`, e infine estrai solo i secondi residui del tempo mediano `t2` passando `nullptr` per ore e minuti (`scomponi_secondi(t2, nullptr, nullptr, &sec_med)`), producendo l'output esatto dell'esempio di esecuzione.

**Concetti da tenere a mente**

- passaggio per puntatore per modificare variabili del chiamante
- composizione di funzioni su puntatori (`ordina_tre` chiama `scambia_int`)
- parametri di uscita abbinati a un valore di ritorno `bool`
- supporto sicuro a parametri di uscita opzionali (`nullptr`)

**Domande guida**

1. Perché `ordina_tre` passa direttamente `a`, `b` e `c` a `scambia_int` invece di scrivere `&a`, `&b` e `&c`?
2. Quali tre confronti e scambi in sequenza garantiscono che tre variabili finiscano sempre nell'ordine `*a <= *b <= *c`?
3. Come evita `scomponi_secondi` la dereferenziazione nulla quando il chiamante passa `nullptr` per i campi `ore` e `minuti`?
4. Perché restituire `bool` da `scomponi_secondi` è più sicuro che assumere che `secondi_totali` sia sempre non negativo?

**Esempio di esecuzione**

```input
3725 125 3600
```

```output
1o tempo: 00:02:05 (125 s)
2o tempo: 01:00:00 (3600 s)
3o tempo: 01:02:05 (3725 s)
Distacco primo-ultimo: 01:00:00 (3600 s)
Secondi residui del mediano: 0
```

## 10.6 `const` e puntatori

Quando lavori con un puntatore `p` ci sono **due** cose distinte che potresti voler proteggere da modifiche accidentali: l'oggetto puntato (`*p`) e il puntatore stesso (`p`, cioè l'indirizzo che memorizza). Il qualificatore `const` ti permette di bloccare solo il primo, solo il secondo oppure entrambi, dando vita a quattro combinazioni possibili:

| Dichiarazione | `p` è modificabile? | `*p` è modificabile? | Significato |
|---|---|---|---|
| `T *p` | Sì | Sì | Puntatore modificabile a dato modificabile |
| `const T *p` | Sì | No | Puntatore modificabile a dato costante |
| `T *const p` | No | Sì | Puntatore costante a dato modificabile |
| `const T *const p` | No | No | Puntatore costante a dato costante |

Per non confondere mai le combinazioni, usa la **regola di lettura da destra verso sinistra** partendo dal nome della variabile:

- `const int *p` (che in C è equivalente a `int const *p`): "`p` è un puntatore (`*`) a un `int` costante (`const`)". Puoi spostare `p` su un altro `int`, ma non puoi modificare `*p` tramite `p`.
- `int *const p`: "`p` è un puntatore costante (`*const`) a un `int`". Puoi modificare `*p`, ma non puoi riassegnare `p` a un altro indirizzo (per questo deve essere inizializzato subito).
- `const int *const p`: "`p` è un puntatore costante (`*const`) a un `int` costante (`const`)". Né `p` né `*p` possono essere modificati.

Le regole di conversione tra puntatori qualificati e non qualificati sono pensate per proteggere i dati:

- La conversione implicita da `T *` a `const T *` è **sempre consentita**: promettere di non modificare un dato modificabile è sicuro. Quindi puoi passare un normale `int *` a una funzione che accetta `const int *`.
- La conversione inversa, da `const T *` a `T *`, **non è consentita senza un cast esplicito** e il compilatore la segnala come errore o avviso grave. Forzare il cast per scartare `const` e scrivere poi in un oggetto che era stato definito `const` provoca **comportamento indefinito**.

Nella pratica quotidiana, la combinazione più importante è `const T *` nelle firme delle funzioni. Una firma ben progettata comunica subito al lettore e al compilatore il contratto della funzione:

- usa `const T *` per tutti i parametri puntatore di **sola lettura** (come `const char *s` o `const int *dati`): garantisci al chiamante che i suoi dati non saranno toccati e consenti di passare sia oggetti mutabili sia oggetti `const`;
- usa `T *` (oppure `T *const` se vuoi impedire alla funzione stessa di riassegnare il parametro locale) per i parametri di **modifica o uscita**.

Su questo punto lo standard C23 ha risolto una storica imperfezione della libreria `<string.h>`. In C17 e nelle versioni precedenti, funzioni come `strchr`, `strrchr`, `strstr` e `strpbrk` ricevevano un `const char *` ma restituivano sempre `char *` (senza `const`), perdendo così la protezione di sola lettura sul puntatore restituito. In C23 queste funzioni **preservano `const`**: se passi un `const char *`, il valore restituito ha tipo `const char *`; se passi un `char *` modificabile, il valore restituito ha tipo `char *`.

> **C23** — La preservazione di `const` in `strchr`, `strrchr`, `strstr` e `strpbrk` è una novità di C23. Nei compilatori configurati per C17 o C11 queste funzioni restituiscono sempre `char *`: puoi comunque assegnare il risultato a `const char *` (la conversione da `char *` a `const char *` è sempre valida), ma il compilatore non ti avviserà se lo assegni per errore a un `char *` non costante partendo da una stringa `const`.

Secondo lo standard C23, tutte le regole di qualificazione `const` sui puntatori e la preservazione di `const` nelle funzioni di ricerca su stringhe hanno comportamento definito; tentare di modificare un oggetto definito `const` tramite un puntatore non `const` provoca invece comportamento indefinito.

### Esempio guidato

Il programma seguente mette a confronto `const int *p_dati`, `int *const p_fisso` e `const int *const p_bloccato`, poi usa `strrchr` su un `const char *` in C23 per isolare l'estensione di un percorso senza mai perdere la qualificazione `const`.

<!-- cod: id=10.6-a tipo=programma -->
```c
#include <stdio.h>
#include <string.h>

int main(void) {
    int a = 10;
    int b = 20;

    const int *p_dati = &a;
    printf("p_dati -> %d\n", *p_dati);
    p_dati = &b;
    printf("p_dati spostato -> %d\n", *p_dati);

    int *const p_fisso = &a;
    *p_fisso = 15;
    printf("Dopo *p_fisso = 15: a = %d\n", a);

    const int *const p_bloccato = &b;
    printf("p_bloccato -> %d\n", *p_bloccato);

    const char *percorso = "/archivio/relazione.finale.txt";
    const char *punto = strrchr(percorso, '.');
    if (punto != nullptr) {
        printf("Estensione trovata: %s\n", punto);
    }
    return 0;
}
```

```output
p_dati -> 10
p_dati spostato -> 20
Dopo *p_fisso = 15: a = 15
p_bloccato -> 20
Estensione trovata: .txt
```

Osserva come il compilatore fa rispettare i vincoli:

- `p_dati` può cambiare bersaglio (`p_dati = &b;`), ma non può scrivere in `*p_dati`.
- `p_fisso` può modificare il bersaglio (`*p_fisso = 15;`, cambiando `a`), ma resta legato per sempre all'indirizzo di `a`.
- `p_bloccato` consente solo la lettura di `*p_bloccato`.
- Poiché `percorso` ha tipo `const char *`, in C23 `strrchr(percorso, '.')` restituisce un `const char *` che punta all'ultimo punto della stringa (`".txt"`).

I due brevi programmi seguenti mostrano invece due violazioni dirette dei vincoli di `const` che il compilatore rifiuta con un errore di compilazione: il primo tenta di scrivere tramite un `const int *`, il secondo tenta di riassegnare un `int *const`.

<!-- cod: id=10.6-b tipo=errore -->
```c
int main(void) {
    int a = 10;
    const int *p_dati = &a;
    *p_dati = 99;
    return 0;
}
```

<!-- cod: id=10.6-c tipo=errore -->
```c
int main(void) {
    int a = 10;
    int b = 20;
    int *const p_fisso = &a;
    p_fisso = &b;
    return 0;
}
```

Nel primo caso il compilatore segnala che stai tentando di assegnare un valore a una posizione di sola lettura; nel secondo segnala che stai tentando di riassegnare una variabile qualificata `const`.

> **Approfondimento — La regola mnemonica per `const`**
> Quando incontri `const` in una dichiarazione complessa, ricorda una sola regola: `const` qualifica sempre ciò che si trova **immediatamente alla sua sinistra**; solo se `const` è la prima parola della dichiarazione (cioè non ha nulla a sinistra) qualifica ciò che si trova alla sua destra. Per questo `int const *p` e `const int *p` significano la stessa cosa (in entrambi i casi è `int` a essere costante), mentre in `int *const p` alla sinistra di `const` c'è `*`, quindi è il puntatore a essere costante.

### Esercizio 10.6 — Estrattore di coppie `chiave=valore` con `const`, puntatori e C23

**Descrizione**

Scrivi un programma C che includa `<ctype.h>`, `<stddef.h>`, `<stdio.h>`, `<stdlib.h>` e `<string.h>` per cercare ed estrarre i valori associati a una chiave da righe nel formato `chiave=valore`. Dichiara prima di `main` i prototipi di due funzioni con uso rigoroso di `const` sui puntatori: `const char *trova_valore(const char *riga, const char *chiave_attesa)` (cerca `'='` in `riga` tramite `const char *eq = strchr(riga, '=');` sfruttando la preservazione di `const` in C23; se `'='` è presente e la parte a sinistra coincide esattamente con `chiave_attesa`, restituisce `eq + 1`, altrimenti `nullptr`) e `bool copia_trim(const char *inizio, char *const dest, size_t cap, ptrdiff_t *lunghezza_out)` (salta gli spazi bianchi iniziali e finali tramite `isspace((unsigned char)...)` e aritmetica dei puntatori; se `inizio == nullptr || dest == nullptr || cap == 0` oppure la lunghezza ripulita `>= cap`, restituisce `false`; altrimenti copia i caratteri ripuliti in `dest` chiudendo con `'\0'`, scrive la lunghezza in `*lunghezza_out` se non nullo e restituisce `true`). In `main` leggi dalla prima riga di `stdin` la chiave cercata (buffer `32` byte, non vuota dopo rimozione di `'\n'`; se mancante o vuota stampa su `stderr` e restituisci `EXIT_FAILURE`). Leggi poi le righe di configurazione fino a fine input (`char riga[128]`), numerandole da `1`: per ogni riga in cui `trova_valore` restituisce un puntatore non nullo, chiama `copia_trim` in `char valore[32]`: se riesce incrementa `trovate` e stampa `Riga N: [<valore>] (len=<L>)`, altrimenti stampa `Riga N: valore troppo lungo`. Al termine stampa `Corrispondenze trovate: <trovate>`.

**Concetti da tenere a mente**

- puntatore a dato costante (`const char *`) e puntatore costante a dato mutabile (`char *const`)
- preservazione di `const` in `strchr` secondo lo standard C23
- aritmetica dei puntatori e `ptrdiff_t` per isolare sottostringhe senza copiarle prima del controllo
- cast a `(unsigned char)` in `isspace` e prevenzione del buffer overflow

**Domande guida**

1. Quale vincolo esprime la firma `const char *trova_valore(const char *riga, const char *chiave_attesa)` nei confronti della stringa passata dal chiamante?
2. Che differenza c'è tra il parametro `const char *inizio` e il parametro `char *const dest` nella funzione `copia_trim`?
3. Perché in `copia_trim` devi usare una variabile puntatore locale `char *d = dest` per scorrere la destinazione invece di scrivere `++dest`?
4. Come evita `trova_valore` di confondere una chiave come `"porta"` con `"portata"` quando usa `strncmp`?

**Esempio di esecuzione**

```input
host
# commento
host=  localhost  
port=8080
hostname=server1
host=	127.0.0.1
```

```output
Riga 2: [localhost] (len=9)
Riga 5: [127.0.0.1] (len=9)
Corrispondenze trovate: 2
```

## Riepilogo

- Un **puntatore** (`T *p`) è una variabile che memorizza l'**indirizzo di memoria** di un oggetto di tipo `T` (oppure il valore nullo). L'operatore `&` ricava l'indirizzo di un oggetto; l'operatore di **dereferenziazione** `*` accede in lettura o scrittura all'oggetto puntato.
- Un **puntatore nullo** si scrive in C23 con `nullptr` (preferito perché tipizzato) oppure con la macro storica `NULL`. Tutti i puntatori nulli sono uguali tra loro al confronto `==`; prima di dereferenziare qualunque puntatore potenzialmente nullo occorre controllarlo (`p != nullptr`).
- Per **decadimento di array**, il nome di un array `T[N]` diventa automaticamente `&a[0]` (`T *`) nella maggior parte delle espressioni, tranne in `sizeof(a)`, `&a` e nell'inizializzazione di un array di `char` da letterale stringa. Per definizione `a[i]` equivale a `*(a + i)` e un parametro di funzione `T a[]` viene adattato a `T *a`.
- Nell'**aritmetica dei puntatori**, `p + k` e `p - k` si spostano di `k * sizeof(*p)` byte e la differenza `q - p` tra due puntatori allo stesso array ha tipo con segno `ptrdiff_t` (`<stddef.h>`, stampato con `%td`). È lecito formare e confrontare il puntatore `a + n`, ma mai dereferenziarlo.
- Il **passaggio per puntatore** permette a una funzione di modificare variabili del chiamante e di restituire più risultati tramite parametri di uscita (anche opzionali con `nullptr`), abbinati a un valore di ritorno `bool`.
- Il qualificatore `const` distingue tra dato costante (`const T *p`), puntatore costante (`T *const p`) ed entrambi costanti (`const T *const p`). In C23 `strchr`, `strrchr`, `strstr` e `strpbrk` preservano `const` sul puntatore restituito.

## Errori comuni

- **Dereferenziare un puntatore non inizializzato o nullo (`nullptr`/`NULL`)**: provoca comportamento indefinito. Inizializza sempre ogni puntatore al momento della dichiarazione e proteggi la dereferenziazione con `p != nullptr` (sfruttando il corto circuito di `&&` quando serve).
- **Scrivere `int* a, b;` pensando che entrambi siano puntatori**: in C l'asterisco si lega al singolo identificatore, quindi solo `a` ha tipo `int *` mentre `b` è un `int`. Scrivi `int *a;` e dichiara un puntatore per riga.
- **Confondere il puntatore (`p`) con il dato puntato (`*p`)**: assegnare un intero a `p` o controllare `*p == nullptr` invece di `p == nullptr` mescola indirizzi e valori. Verifica sempre se vuoi agire sull'indirizzo (`p`) o sull'oggetto puntato (`*p`).
- **Restituire da una funzione l'indirizzo di una variabile locale automatica**: la variabile cessa di esistere quando la funzione termina, rendendo l'indirizzo non valido e il suo uso comportamento indefinito (lo vedremo nel capitolo 14).
- **Uscire dai limiti dell'aritmetica dei puntatori**: dereferenziare `a + n`, formare `a - 1` oppure sottrarre o confrontare con `<`, `<=`, `>`, `>=` puntatori appartenenti ad array diversi provoca comportamento indefinito.
- **Confondere `const int *p` con `int *const p` o modificare un letterale stringa**: ricorda di leggere da destra verso sinistra (`const int *p` blocca il dato, `int *const p` blocca il puntatore) e usa sempre `const char *` per i letterali stringa.

## Prima di proseguire

- [ ] So spiegare che cosa rappresentano `&x`, `int *p` e `*p`, e perché `int *a, b;` dichiara un solo puntatore.
- [ ] So inizializzare un puntatore a `nullptr`, controllarlo con `p != nullptr` prima della dereferenziazione e spiegare la differenza tra `nullptr` (C23) e `NULL`.
- [ ] So prevedere quando un array subisce il decadimento di array, quali sono le eccezioni (`sizeof`, `&`, inizializzazione da letterale stringa) e perché `a[i]` equivale a `*(a + i)`.
- [ ] So usare l'aritmetica dei puntatori su un intervallo `[inizio, fine)` e calcolare indici e distanze con `ptrdiff_t` (`%td`) senza uscire dai limiti leciti.
- [ ] So scrivere funzioni con passaggio per puntatore e parametri di uscita (anche opzionali) evitando di restituire indirizzi di variabili locali automatiche.
- [ ] So distinguere `const T *p`, `T *const p` e `const T *const p` e applicare correttamente `const` nelle firme delle funzioni e con `strchr`/`strrchr`/`strstr` in C23.
