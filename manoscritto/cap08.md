# Capitolo 8 — Array

> **In questo capitolo imparerai a:**
> - Dichiarare, inizializzare e attraversare array mono e bidimensionali di dimensione costante
> - Riconoscere gli accessi fuori dai limiti come comportamento indefinito ed evitarli
> - Passare un array e la sua lunghezza a una funzione
> - Implementare algoritmi elementari di ricerca e ordinamento stimandone il costo

> **Ti servono:** i capitoli 2, 4, 6 e 7 (tipi fondamentali, `constexpr`, `sizeof` e `size_t`, condizioni e valutazione a corto circuito, cicli `for` e `while`, funzioni, prototipi e passaggio per valore).

Nel capitolo precedente hai imparato a scomporre un programma in funzioni piccole e ordinate, ciascuna dedicata a un compito preciso. Finora, però, ogni funzione lavorava su pochi valori isolati: una temperatura, un contatore, le coordinate di un punto. Che cosa succede quando il programma deve conservare tutte le temperature misurate durante un mese, i voti di un'intera classe o la griglia dei posti in una sala?

Dichiarare trenta o cento variabili distinte (`voto1`, `voto2`, `voto3`...) non è praticabile: non potresti scorrerle con un ciclo, né passarle insieme a una funzione, né cercarvi un valore in modo sistematico. Serve un costrutto che raccolga molti dati dello stesso tipo sotto un unico nome e permetta di individuare ciascun elemento attraverso la sua posizione numerica.

In C questo costrutto è l'**array**: una sequenza contigua di elementi in memoria. È il primo vero mattone con cui costruire collezioni di dati, tabelle bidimensionali e algoritmi di ricerca e ordinamento. Imparerai anche il suo aspetto più delicato: il C non controlla automaticamente che le posizioni richieste siano valide, quindi la disciplina sui limiti diventa una responsabilità diretta di chi scrive il codice.

## 8.1 Dichiarare, inizializzare e scorrere un array

Immagina di voler registrare il numero di libri venduti da una libreria in ciascuno dei sette giorni della settimana per calcolare il totale, la media giornaliera e i giorni con più vendite. Con sette variabili separate dovresti ripetere le stesse operazioni sette volte e non potresti automatizzare il calcolo con un ciclo `for`. Quando hai molti dati omogenei — cioè tutti dello stesso tipo — conviene conservarli insieme in un **array**: una sequenza contigua in memoria di un numero fissato di elementi tutti dello stesso tipo, accessibili tramite indice.

Ogni elemento di un array occupa la stessa quantità di memoria (per esempio `sizeof(int)` byte per un array di `int`) ed è collocato immediatamente accanto al successivo, senza spazi vuoti. Per identificare un singolo elemento si usa il suo **indice** (*index*): un valore intero non negativo che identifica la posizione di un elemento in un array a partire da `0`. Se un array ha `7` elementi, i suoi indici validi sono `0, 1, 2, 3, 4, 5, 6` — mai `7`.

```text
Indice:       0      1      2      3      4      5      6
           +------+------+------+------+------+------+------+
vendite:   |  12  |   9  |  15  |  11  |  18  |  24  |  20  |
           +------+------+------+------+------+------+------+
           ^                                                ^
       primo elemento                                 ultimo elemento
       vendite[0]                                     vendite[6]
```

Per dichiarare un array indichi il tipo degli elementi, il nome dell'array e, tra parentesi quadre, il numero di elementi `N`:

<!-- cod: id=8.1-b tipo=frammento -->
```c
constexpr size_t GIORNI = 7;
int vendite[GIORNI];
```

La dichiarazione `tipo nome[N];` riserva in memoria `N` elementi contigui tutti di tipo `tipo`, dove `N` è un'espressione costante intera positiva (come un letterale `7` oppure una costante `constexpr`). Lo standard C ammette anche array la cui dimensione viene determinata a tempo di esecuzione — chiamati *array a lunghezza variabile* (VLA, *Variable Length Array*) — ma in questo libro non li usiamo mai: un VLA può esaurire silenziosamente la memoria disponibile se la dimensione inserita dall'utente è grande e non offre alcun modo di gestire l'errore. Quando serviranno collezioni di dimensione nota solo durante l'esecuzione, useremo la memoria dinamica (lo vedremo nel capitolo 11).

> **C23** — L'uso di una costante `constexpr` come dimensione di un array a lunghezza fissa è una novità introdotta dal C23. Nei compilatori più vecchi (C17 e precedenti) una variabile dichiarata `const` non è un'espressione costante intera e trasformerebbe la dichiarazione in un VLA; in quel codice si usa invece un letterale intero oppure una macro `#define` (che vedremo nel capitolo 19).

Per accedere in lettura o in scrittura all'elemento in posizione `i` si usa l'operatore di indicizzazione `[]`, scrivendo `nome[i]`. L'espressione `vendite[0]` si comporta esattamente come una normale variabile di tipo `int`: puoi leggerla, assegnarle un valore (`vendite[0] = 14;`) o incrementarla (`++vendite[0];`).

Come le variabili scalari, anche un array locale dichiarato dentro una funzione senza inizializzatore contiene valori indeterminati: leggerli prima di averli scritti provoca **comportamento indefinito**. Conviene quindi inizializzare l'array già nella dichiarazione. Il C offre diverse forme di inizializzazione:

<!-- cod: id=8.1-c tipo=frammento -->
```c
int a[4] = {10, 20, 30, 40};          // lista completa
int b[] = {10, 20, 30, 40};           // lunghezza 4 dedotta dal compilatore
int zeri[10] = {0};                   // tutti i 10 elementi azzerati
int parziale[5] = {7, 3};             // 7, 3, 0, 0, 0
int sconti[7] = {[0] = 5, [5] = 15, [6] = 20}; // inizializzatore designato
```

Osserva le ultime tre righe:

- Se ometti la dimensione tra parentesi quadre (`int b[] = {10, 20, 30, 40};`), il compilatore deduce automaticamente la lunghezza contando gli elementi della lista.
- Se fornisci meno valori rispetto alla lunghezza dichiarata (`int parziale[5] = {7, 3};` oppure `int zeri[10] = {0};`), tutti gli elementi omessi vengono inizializzati a `0` (o `0.0` per `double`, `false` per `bool`, `'\0'` per `char`).
- Con un **inizializzatore designato** (`{[indice] = valore}`) puoi specificare solo gli elementi che ti interessano, in qualsiasi ordine; tutti gli altri elementi dell'array vengono azzerati automaticamente. È molto utile per tabelle sparse, come uno sconto applicato solo in alcuni giorni della settimana.

Secondo lo standard C23, la contiguità degli elementi in memoria, l'azzeramento degli elementi omessi in un inizializzatore e il funzionamento degli inizializzatori designati sono comportamento completamente **definito**. Al contrario, leggere un elemento di un array locale non inizializzato provoca **comportamento indefinito**.

Una volta dichiarato un array, come conosci il suo numero di elementi senza ripetere costanti numeriche sparse nel codice? Nella stessa visibilità in cui l'array è dichiarato, `sizeof(a)` restituisce la dimensione totale dell'array in byte e `sizeof(a[0])` la dimensione in byte di un singolo elemento. Il loro rapporto produce esattamente il numero di elementi, di tipo `size_t`:

<!-- cod: id=8.1-d tipo=frammento -->
```c
const size_t n = sizeof(vendite) / sizeof(vendite[0]);
for (size_t i = 0; i < n; ++i) {
    printf("Giorno %zu: %d\n", i + 1, vendite[i]);
}
```

Anche il calcolo di `sizeof(a) / sizeof(a[0])` nella stessa visibilità della dichiarazione è comportamento **definito** dallo standard C23. Usare `size_t` per la variabile di controllo `i` è coerente con il tipo restituito da `sizeof` e garantisce che l'indice non sia mai negativo. Fai attenzione però: vedrai nella sotto-sezione 8.3 che questa formula *non* funziona più quando l'array viene passato a una funzione.

Due operazioni che i principianti tentano spesso su un array non sono ammesse dal linguaggio C: **non puoi copiare né confrontare due array nel loro complesso con `=` o `==`**. Scrivere `a = b;` provoca un errore di compilazione, mentre scrivere `a == b` non confronta gli elementi (il motivo sarà chiaro nel capitolo 10, quando studierai i puntatori). Ogni copia e ogni confronto tra array si eseguono elemento per elemento con un ciclo `for`:

<!-- cod: id=8.1-e tipo=frammento -->
```c
for (size_t i = 0; i < n; ++i) {
    copia[i] = origine[i];
}
```

A questo punto si chiarisce anche un costrutto che usi già dal capitolo 5: quando dichiari `char riga[128];` per leggere una riga di testo con `fgets`, stai dichiarando un array di `128` elementi di tipo `char` contigui in memoria — cioè un buffer capace di contenere una sequenza di caratteri. Nel capitolo 9 vedrai nel dettaglio come il C rappresenta le stringhe dentro un array di `char`.

> **Se vieni da Python** — In Python le liste possono crescere o ridursi dinamicamente e contenere elementi di tipi diversi; in C un array ha lunghezza fissa stabilita alla dichiarazione e contiene solo elementi dello stesso tipo, disposti in modo contiguo in memoria.

### Esempio guidato

Il programma seguente analizza le vendite settimanali di una libreria usando un array `vendite` inizializzato per lista e un array costante `sconti` inizializzato con inizializzatori designati (sconto del 5% il primo giorno, 15% il sesto e 20% il settimo; 0% negli altri giorni). Calcola il numero di giorni con `sizeof`, stampa il riepilogo giornaliero e determina il totale e il giorno con il maggior numero di copie vendute.

<!-- cod: id=8.1-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

int main(void) {
    int vendite[7] = {12, 9, 15, 11, 18, 24, 20};
    const int sconti[7] = {[0] = 5, [5] = 15, [6] = 20};
    const size_t giorni = sizeof(vendite) / sizeof(vendite[0]);

    int totale = 0;
    size_t giorno_migliore = 0;

    for (size_t i = 0; i < giorni; ++i) {
        printf("Giorno %zu: %2d copie (sconto %2d%%)\n",
               i + 1, vendite[i], sconti[i]);
        totale += vendite[i];
        if (vendite[i] > vendite[giorno_migliore]) {
            giorno_migliore = i;
        }
    }

    printf("Totale settimanale: %d copie (media %.2f)\n",
           totale, (double)totale / (double)giorni);
    printf("Giorno migliore: giorno %zu con %d copie\n",
           giorno_migliore + 1, vendite[giorno_migliore]);
    return 0;
}
```

```output
Giorno 1: 12 copie (sconto  5%)
Giorno 2:  9 copie (sconto  0%)
Giorno 3: 15 copie (sconto  0%)
Giorno 4: 11 copie (sconto  0%)
Giorno 5: 18 copie (sconto  0%)
Giorno 6: 24 copie (sconto 15%)
Giorno 7: 20 copie (sconto 20%)
Totale settimanale: 109 copie (media 15.57)
Giorno migliore: giorno 6 con 24 copie
```

Analizziamo i punti chiave del programma:

- `int vendite[7] = {12, 9, 15, 11, 18, 24, 20};` dichiara un array di 7 interi e assegna esplicitamente ogni posizione da `0` a `6`.
- `const int sconti[7] = {[0] = 5, [5] = 15, [6] = 20};` usa gli inizializzatori designati e qualifica l'array come `const`, impedendo modifiche accidentali. Gli elementi con indici `1, 2, 3, 4` vengono automaticamente inizializzati a `0`, come conferma l'output.
- `sizeof(vendite) / sizeof(vendite[0])` calcola la lunghezza `7` in modo sicuro e indipendente dalla dimensione in byte di `int`.
- Nel ciclo `for`, l'indice `i` va da `0` a `giorni - 1` (quindi da `0` a `6`), mentre nella stampa aggiungiamo `1` (`i + 1`) per numerare i giorni da `1` a `7` in modo leggibile per l'utente.
- La variabile `giorno_migliore` conserva l'indice dell'elemento massimo anziché solo il suo valore: in questo modo, alla fine del ciclo, conosci sia quale giorno ha venduto di più sia quante copie ha venduto (`vendite[giorno_migliore]`).

> **Approfondimento — Perché un array senza inizializzatore non è azzerato**
> Quando dichiari un array locale come `int dati[1000];`, il C non azzera automaticamente i 1000 elementi: il compilatore si limita a riservare lo spazio in memoria, lasciandovi i bit rimasti da usi precedenti. Questa scelta segue un principio storico del linguaggio: non farti pagare il costo di operazioni che potresti non volere (per esempio se stai per riempire subito l'intero array leggendo da un file). Appena però scrivi un inizializzatore, anche con un solo valore come `{0}` oppure `{[3] = 42}`, lo standard impone che l'intero array sia inizializzato in modo completo e deterministico, azzerando tutti gli elementi non elencati.

### Esercizio 8.1 — Istogramma delle valutazioni con inizializzatore designato

**Descrizione**

Scrivi un programma C che legga da `stdin` una sequenza di lunghezza arbitraria di valutazioni intere comprese tra `1` e `5` inclusi (un `int` per riga, fino alla fine dell'input). Se una riga ha formato non valido (`"%d %c"` != `1`) o un valore fuori da `1..5`, stampa un messaggio su `stderr` e restituisci `EXIT_FAILURE`. Usa un array `int frequenze[6] = {0};` (gli indici `1..5` contano quante volte compare ciascun voto) e un array `const int punti[6]` inizializzato tramite inizializzatore designato (`{[1] = 0, [2] = 25, [3] = 50, [4] = 75, [5] = 100}`) per convertire ogni voto in punteggio di gradimento. Ricava la dimensione di `frequenze` tramite `sizeof(frequenze) / sizeof(frequenze[0])`. Se non è stata letta alcuna valutazione stampa `Nessuna valutazione inserita.` e restituisci `EXIT_SUCCESS`; altrimenti stampa per ciascun voto da `1` a `5` la riga `Voto V: K (` seguita da `K` asterischi scritti con `putchar('*')` e `)`, quindi il totale delle valutazioni, la media dei voti (`%.2f`), il gradimento medio (`%.2f / 100`) e il voto più frequente (in caso di parità il voto più piccolo), esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- dichiarazione e azzeramento di un array con `{0}`
- inizializzatore designato `{[i] = valore}`
- calcolo della lunghezza con `sizeof(a) / sizeof(a[0])`
- indicizzazione sicura con `size_t` e gestione dell'input vuoto

**Domande guida**

1. Perché dichiarare `frequenze` con 6 elementi (indici `0..5`) semplifica l'indicizzazione diretta usando il voto `1..5`?
2. Quale valore viene assegnato automaticamente all'elemento `punti[0]` quando usi un inizializzatore designato che specifica solo gli indici da `1` a `5`?
3. Come ti assicuri che, a parità di frequenza massima, venga conservato il voto numericamente più piccolo?
4. Perché conviene calcolare il limite del ciclo con `sizeof(frequenze) / sizeof(frequenze[0])` invece di ripetere il numero `6` in più punti?

**Esempio di esecuzione**

```input
5
4
5
2
4
5
```

```output
Voto 1: 0 ()
Voto 2: 1 (*)
Voto 3: 0 ()
Voto 4: 2 (**)
Voto 5: 3 (***)
Totale valutazioni: 6
Media voti: 4.17
Gradimento medio: 79.17 / 100
Voto piu frequente: 5 (3 voti)
```

## 8.2 Accessi fuori dai limiti e comportamento indefinito

Quando dichiari un array di lunghezza `N`, gli unici indici validi sono gli interi da `0` a `N - 1`. Che cosa succede se il programma tenta di leggere `a[N]` oppure di scrivere in `a[-1]`? In molti linguaggi di alto livello l'esecuzione si interrompe immediatamente con un messaggio d'errore preciso. In C no: il linguaggio non inserisce controlli automatici sugli indici a tempo di esecuzione per evitare il costo di una verifica a ogni singolo accesso in memoria.

Qualsiasi lettura o scrittura di un array con un indice negativo o maggiore o uguale alla sua lunghezza è un **accesso fuori dai limiti** (*out-of-bounds access*). Secondo lo standard C23, qualsiasi accesso in lettura o scrittura fuori dall'intervallo `[0, N - 1]` di un array provoca **comportamento indefinito**.

"Comportamento indefinito" significa che lo standard non impone alcun vincolo su ciò che accadrà:

- il programma potrebbe leggere dati privi di senso appartenenti ad altre variabili vicine;
- una scrittura fuori dai limiti potrebbe modificare silenziosamente il valore di un'altra variabile senza alcun segnale visibile;
- il sistema operativo potrebbe interrompere bruscamente il programma se l'accesso colpisce un'area di memoria protetta;
- il programma potrebbe persino sembrare funzionante durante le prove e fallire solo in seguito o su un altro computer.

Gli accessi fuori dai limiti nascono quasi sempre da errori di un'unità (*off-by-one*) nei cicli o nel calcolo degli indici. Ecco i tre casi più frequenti da riconoscere a colpo d'occhio:

1. **Condizione di ciclo `<=` invece di `<`**: scrivere `for (size_t i = 0; i <= n; ++i)` fa eseguire un'iterazione di troppo con `i == n`, accedendo ad `a[n]` che è già fuori dall'array.
2. **Accesso al vicino `a[i + 1]` all'ultima iterazione**: quando confronti elementi adiacenti (per esempio `a[i] < a[i + 1]`), il ciclo deve fermarsi a `i + 1 < n` (oppure partire da `i = 1` confrontando `a[i - 1]` e `a[i]`). Se lasci `i < n`, all'ultima iterazione `i` vale `n - 1` e `a[i + 1]` accede ad `a[n]`.
3. **Underflow su `size_t` con `i - 1`**: `size_t` è un tipo intero senza segno. Se `i` vale `0`, l'espressione `i - 1` non produce `-1`, bensì il valore massimo rappresentabile da `size_t` (un numero enorme, dell'ordine di $10^{19}$ sui sistemi a 64 bit), trasformando `a[i - 1]` in un accesso gravemente fuori dai limiti.

Guarda questo esempio di codice **errato** (non scriverlo mai nei tuoi programmi):

<!-- cod: id=8.2-b tipo=frammento -->
```c
// ERRORE: accesso fuori dai limiti — comportamento indefinito!
constexpr size_t CAPACITA = 8;
double letture[CAPACITA] = {0};
for (size_t i = 0; i <= CAPACITA; ++i) {  // SBAGLIATO: quando i == 8 scrive in letture[8]
    letture[i] = 1.0;
}
```

> **Attenzione — Codice vietato**
> Il frammento sopra contiene un errore grave: quando `i` raggiunge `CAPACITA` (`8`), `letture[8]` scrive oltre la fine dell'array provocando comportamento indefinito. Il ciclo corretto deve usare sempre `i < CAPACITA`.

Nei programmi reali raramente l'array è sempre pieno fino all'ultimo elemento: spesso dichiari un array di capacità massima fissa (per esempio `CAPACITA = 8` o `MAX_STAZIONI = 20`) e lo riempi solo in parte con i dati letti dall'input. In questi casi devi mantenere sempre **due grandezze distinte**:

- la **capacità fisica** dell'array (costante `constexpr`, fissata alla dichiarazione);
- la **lunghezza effettiva** `n` (variabile intera o `size_t`, sempre compresa tra `0` e la capacità fisica), che conta quanti elementi sono stati realmente caricati.

Prima di aggiungere un nuovo elemento controlla che `n < CAPACITA`; prima di leggere o modificare un elemento in posizione `idx`, controlla che `0 <= idx < n` — non `< CAPACITA`, perché le posizioni tra `n` e `CAPACITA - 1` non contengono dati validi.

Quando una condizione combina il controllo dell'indice con la lettura dell'elemento, sfrutta la **valutazione a corto circuito** di `&&` (capitolo 4): metti sempre il controllo dei limiti *a sinistra* dell'accesso all'array:

<!-- cod: id=8.2-c tipo=frammento -->
```c
if (idx >= 0 && idx < n && letture[idx] > 20.0) {
    printf("Valore sopra soglia: %.1f\n", letture[idx]);
}
```

Se `idx` è negativo oppure `idx >= n`, la valutazione si ferma subito e `letture[idx]` non viene mai valutato. Invertire l'ordine scrivendo `letture[idx] > 20.0 && idx >= 0 && idx < n` vanificherebbe la protezione, perché l'accesso fuori dai limiti avverrebbe prima del controllo. Durante i test esistono strumenti del compilatore chiamati sanitizer (lo vedremo nel capitolo 11) che individuano automaticamente molti accessi fuori dai limiti e fermano il programma segnalando la riga esatta dell'errore.

> **Se vieni da Python** — In Python un indice negativo come `a[-1]` accede all'ultimo elemento e un indice fuori intervallo solleva subito un'eccezione `IndexError`; in C non esistono indici negativi validi né controlli automatici, e qualsiasi accesso fuori dai limiti provoca comportamento indefinito.

### Esempio guidato

Il programma seguente gestisce un array di capacità fisica `CAPACITA = 8` destinato alle letture di un sensore di temperatura, ma contiene soltanto `5` campioni caricati (`usati = 5`). Una sequenza di interrogazioni chiede di consultare vari indici — alcuni validi, uno negativo, uno oltre `usati` ma entro `CAPACITA`, uno pari a `CAPACITA` — e il programma valida ogni richiesta prima di indicizzare `letture`.

<!-- cod: id=8.2-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

int main(void) {
    constexpr int CAPACITA = 8;
    double letture[CAPACITA] = {21.4, 21.8, 22.1, 21.9, 22.5};
    int usati = 5;

    const int richieste[] = {0, 4, -1, 5, 8};
    const size_t num_richieste = sizeof(richieste) / sizeof(richieste[0]);

    for (size_t k = 0; k < num_richieste; ++k) {
        int idx = richieste[k];
        if (idx >= 0 && idx < usati && letture[idx] >= 22.0) {
            printf("Indice %d: %.1f C (sopra soglia)\n", idx, letture[idx]);
        } else if (idx >= 0 && idx < usati) {
            printf("Indice %d: %.1f C (nella norma)\n", idx, letture[idx]);
        } else {
            printf("Indice %d: non valido (intervallo 0..%d)\n", idx, usati - 1);
        }
    }

    return 0;
}
```

```output
Indice 0: 21.4 C (nella norma)
Indice 4: 22.5 C (sopra soglia)
Indice -1: non valido (intervallo 0..4)
Indice 5: non valido (intervallo 0..4)
Indice 8: non valido (intervallo 0..4)
```

Osserva i dettagli essenziali:

- `letture` ha capacità fisica `8`, ma solo i primi `5` elementi (`0..4`) contengono dati reali; gli elementi `5..7` sono stati azzerati dall'inizializzazione parziale ma non rappresentano misure acquisite.
- L'interrogazione sull'indice `5` viene respinta anche se `5 < CAPACITA`: confrontare `idx < usati` invece di `idx < CAPACITA` evita di trattare uno `0.0` di riempimento come una misura reale.
- Nella prima condizione `if (idx >= 0 && idx < usati && letture[idx] >= 22.0)`, la valutazione a corto circuito garantisce che `letture[idx]` venga letto solo quando `idx` è compreso tra `0` e `usati - 1`.
- Gli indici `-1` e `8` sono respinti senza mai eseguire `letture[idx]`, evitando il comportamento indefinito.

> **Approfondimento — Perché un accesso fuori dai limiti può "sembrare" innocuo**
> Le variabili locali di una funzione vengono spesso collocate dal compilatore in zone adiacenti della memoria dedicata alle chiamate (lo stack, che studierai nel capitolo 11). Se un ciclo scrive per errore in `letture[8]` oltre la fine di `double letture[8]`, quei byte potrebbero appartenere alla variabile dichiarata subito accanto oppure a byte di riempimento inutilizzati. Nel secondo caso il programma può completare l'esecuzione senza errori visibili sul tuo computer; compilato con un altro livello di ottimizzazione o su un'altra architettura, lo stesso codice può invece sovrascrivere una variabile di controllo o provocare un arresto immediato. Per questo un accesso fuori dai limiti è sempre un difetto critico, anche quando una prova isolata produce l'output atteso.

### Esercizio 8.2 — Interrogazioni su sotto-intervalli con controlli sui limiti

**Descrizione**

Scrivi un programma C che usi un array di capacità fissa `constexpr int MAX_STAZIONI = 20;` (`double misure[MAX_STAZIONI] = {0};`). Leggi dalla prima riga di `stdin` il numero effettivo di stazioni `n` (`int` compreso tra `1` e `MAX_STAZIONI` inclusi) e dalle successive `n` righe una misura `double` per ciascuna stazione `0..n-1` (controllando fine dell'input e formato esatto; in caso di errore stampa su `stderr` e restituisci `EXIT_FAILURE`). Leggi poi fino alla fine dell'input una sequenza di righe, ciascuna contenente una coppia di indici interi `inizio fine` (`"%d %d %c"` == `2`; se il formato è errato scrivi su `stderr` e restituisci `EXIT_FAILURE`). Prima di accedere all'array controlla sempre i limiti: se `inizio < 0 || fine < inizio || fine >= n`, non accedere a `misure`, incrementa `respinte` e stampa `Intervallo [inizio..fine]: fuori dai limiti (validi 0..n-1)`; altrimenti calcola minimo, massimo e media di `misure[inizio..fine]`, incrementa `valide` e stampa `Intervallo [inizio..fine]: min=..., max=..., media=...` con due cifre decimali. Al termine dello stream stampa `Interrogazioni valide: V, respinte: R` e restituisci `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- distinzione tra capacità fisica dell'array e lunghezza effettiva
- prevenzione degli accessi fuori dai limiti prima di indicizzare
- controllo di indici negativi, indici `>= n` e intervalli invertiti
- elaborazione sicura di sotto-intervalli di un array

**Domande guida**

1. Perché devi distinguere tra la capacità massima `MAX_STAZIONI` e il numero effettivo `n` di elementi caricati?
2. Quali tre condizioni di errore sugli indici devi verificare prima di accedere a `misure[inizio..fine]`?
3. Come inizializzi `min` e `max` per un sotto-intervallo `[inizio..fine]` già validato senza usare costanti arbitrarie?
4. Che cosa rischierebbe il programma se accedessi a `misure[fine]` quando `fine` è uguale a `n`?

**Esempio di esecuzione**

```input
4
10.0
14.5
12.0
16.5
1 3
-1 2
0 4
2 1
0 0
```

```output
Intervallo [1..3]: min=12.00, max=16.50, media=14.33
Intervallo [-1..2]: fuori dai limiti (validi 0..3)
Intervallo [0..4]: fuori dai limiti (validi 0..3)
Intervallo [2..1]: fuori dai limiti (validi 0..3)
Intervallo [0..0]: min=10.00, max=10.00, media=10.00
Interrogazioni valide: 2, respinte: 3
```

## 8.3 Array e funzioni

Nel capitolo 7 hai visto come dividere un programma in funzioni riutilizzabili. Appena inizi a lavorare con gli array, nasce subito la necessità di scrivere funzioni che calcolino la media di un array, ne trovino il massimo, lo stampino o ne aggiornino gli elementi.

Per ricevere un array come parametro, una funzione usa la sintassi `tipo a[]` (con parentesi quadre vuote) accompagnata **sempre** da un secondo parametro `size_t n` che indica quanti elementi contiene l'array:

<!-- cod: id=8.3-b tipo=frammento -->
```c
double calcola_media(const double a[], size_t n);
void scala_valori(double a[], size_t n, double fattore);
```

Quando chiami la funzione, passi semplicemente il nome dell'array (senza parentesi quadre) e la sua lunghezza:

<!-- cod: id=8.3-c tipo=frammento -->
```c
double m = calcola_media(prezzi, n);
scala_valori(prezzi, n, 1.10);
```

Qui incontri una differenza fondamentale rispetto alle variabili scalari viste nel capitolo 7. Quando passi un `int` o un `double` a una funzione, la funzione riceve una copia del valore e modificare il parametro non altera la variabile del chiamante. Quando invece passi un array con parametro `tipo a[]`, **la funzione non riceve una copia dell'intero array**: accede direttamente agli elementi dell'array del chiamante. Di conseguenza:

- se la funzione modifica `a[i]` al proprio interno, modifica direttamente l'elemento corrispondente nell'array del chiamante;
- la funzione può operare in modo efficiente anche su array grandi, perché evita di duplicare tutti gli elementi in memoria a ogni chiamata.

Questo non contraddice la regola del passaggio per valore del C: dietro le quinte, secondo lo standard C23, il compilatore adatta automaticamente un parametro dichiarato come `tipo a[]` a un puntatore al primo elemento dell'array, e passa quel puntatore per valore (il meccanismo completo dei puntatori verrà spiegato nel capitolo 10). È un comportamento completamente **definito** dallo standard.

Da questo adattamento discende una conseguenza pratica molto importante: **all'interno di una funzione, `sizeof(a)` non restituisce la dimensione in byte dell'array del chiamante**. Non puoi quindi usare `sizeof(a) / sizeof(a[0])` dentro una funzione per scoprire quanti elementi ha l'array ricevuto; otterresti un valore sbagliato (e il compilatore con `-Wall` emette un avviso per metterti in guardia). Ecco perché la lunghezza effettiva va **sempre** passata esplicitamente come parametro separato `size_t n`.

Proprio perché una funzione con parametro `double a[]` può modificare direttamente gli elementi del chiamante, devi distinguere con chiarezza le funzioni che *leggono soltanto* l'array da quelle che lo *modificano*:

- se la funzione deve solo consultare gli elementi (come `calcola_media`, `indice_massimo` o `stampa_array`), dichiara il parametro con il qualificatore `const`: `const double a[]`;
- se la funzione deve modificare gli elementi sul posto (come `scala_valori`), ometti `const`: `double a[]`.

Secondo lo standard C23, dichiarare `const tipo a[]` impedisce alla funzione di modificare gli elementi tramite quel parametro: qualsiasi tentativo di scrivere `a[i] = ...;` viene rifiutato dal compilatore con un errore di compilazione.

Separare i compiti in funzioni mirate rende i programmi su array molto più puliti. Nella pratica incontrerai spesso tre famiglie di operazioni modulari:

- **aggregazione** (`const tipo a[]`): scorre l'array senza alterarlo e restituisce una sintesi, come somma, media, minimo o indice del massimo;
- **modifica sul posto** (`tipo a[]`): trasforma ciascun elemento direttamente dentro l'array originale (per esempio applicando una scala o limitando i valori a un intervallo);
- **riorganizzazione sul posto** (`tipo a[]`): cambia la disposizione degli elementi senza usare un secondo array, per esempio invertendo l'ordine dell'array scambiando `a[0]` con `a[n - 1]`, `a[1]` con `a[n - 2]`, e così via fino a metà lunghezza (`i < n / 2`).

> **Se vieni da Python** — In Python `len(a)` restituisce la lunghezza di una lista anche all'interno di una funzione; in C una funzione che riceve un array non ne conosce la lunghezza e deve sempre riceverla come parametro separato `size_t n`.

### Esempio guidato

Il programma seguente dichiara i prototipi di quattro funzioni prima di `main`: tre funzioni di sola lettura (`calcola_media`, `indice_massimo`, `stampa_array`) con parametro `const double a[]`, e una funzione di modifica sul posto (`scala_valori`) con parametro `double a[]`. Dopo aver mostrato i prezzi iniziali, la media e l'indice del prezzo più alto, applica un aumento del 10% con `scala_valori` e ristampa `prezzi` per verificare che l'array di `main` è stato aggiornato direttamente.

<!-- cod: id=8.3-a tipo=programma -->
```c
#include <stdio.h>

double calcola_media(const double a[], size_t n);
size_t indice_massimo(const double a[], size_t n);
void scala_valori(double a[], size_t n, double fattore);
void stampa_array(const double a[], size_t n);

int main(void) {
    double prezzi[] = {12.0, 25.5, 18.0, 30.0};
    const size_t n = sizeof(prezzi) / sizeof(prezzi[0]);
    printf("Prima: ");
    stampa_array(prezzi, n);
    printf("Media: %.2f, massimo indice %zu\n", calcola_media(prezzi, n), indice_massimo(prezzi, n));
    scala_valori(prezzi, n, 1.10);
    printf("Dopo +10%%: ");
    stampa_array(prezzi, n);
    return 0;
}

double calcola_media(const double a[], size_t n) {
    double somma = 0.0;
    for (size_t i = 0; i < n; ++i) { somma += a[i]; }
    return (n > 0) ? somma / (double)n : 0.0;
}

size_t indice_massimo(const double a[], size_t n) {
    size_t idx = 0;
    for (size_t i = 1; i < n; ++i) {
        if (a[i] > a[idx]) { idx = i; }
    }
    return idx;
}

void scala_valori(double a[], size_t n, double fattore) {
    for (size_t i = 0; i < n; ++i) { a[i] *= fattore; }
}

void stampa_array(const double a[], size_t n) {
    for (size_t i = 0; i < n; ++i) { printf("%.2f%s", a[i], (i + 1 < n) ? " " : "\n"); }
}
```

```output
Prima: 12.00 25.50 18.00 30.00
Media: 21.38, massimo indice 3
Dopo +10%: 13.20 28.05 19.80 33.00
```

Esaminiamo come lavorano insieme `main` e le quattro funzioni:

- In `main`, `sizeof(prezzi) / sizeof(prezzi[0])` è valido perché `prezzi` è dichiarato proprio dentro `main`. Il risultato `n` (pari a `4`) viene poi passato come secondo argomento a tutte le funzioni.
- `calcola_media`, `indice_massimo` e `stampa_array` dichiarano `const double a[]`: non possono alterare `prezzi` e accettano sia array modificabili sia array `const`.
- `scala_valori` dichiara `double a[]` senza `const` perché moltiplica sul posto ciascun elemento per `fattore`. Non deve restituire nulla (`void`): quando il controllo torna a `main`, la seconda chiamata a `stampa_array(prezzi, n)` mostra i valori aggiornati.
- In `calcola_media`, il controllo `(n > 0)` evita una divisione per zero se la funzione venisse chiamata con `n == 0`.

> **Approfondimento — Perché usare sempre `const` sui parametri array di sola lettura**
> Aggiungere `const` davanti a `tipo a[]` ogni volta che una funzione non deve modificare l'array ha due vantaggi concreti. Il primo è documentare immediatamente il contratto della funzione: chi legge il prototipo `double calcola_media(const double a[], size_t n);` sa subito che i suoi dati non verranno toccati. Il secondo è la sicurezza verificata dal compilatore: se per distrazione scrivi un assegnamento su `a[i]` (per esempio `=` invece di `==` in una condizione), il compilatore rifiuta il codice invece di introdurre un difetto silenzioso. Inoltre, solo un parametro `const` può ricevere in argomento un array dichiarato `const` nel chiamante.

### Esercizio 8.3 — Saturazione e inversione di un segnale con funzioni su array

**Descrizione**

Scrivi un programma C che dichiari prima di `main` i prototipi di tre funzioni su array di `int` (`constexpr size_t MAX_CAMPIONI = 30;`) e ne collochi le definizioni dopo `main`: `size_t satura_array(int a[], size_t n, int minimo, int massimo)` (modifica l'array sul posto portando a `minimo` ogni elemento `< minimo` e a `massimo` ogni elemento `> massimo`, restituendo quanti elementi sono stati modificati), `void inverti_array(int a[], size_t n)` (inverte l'ordine degli elementi sul posto) e `void stampa_array(const int a[], size_t n)` (stampa gli elementi separati da un singolo spazio seguiti da ritorno a capo). In `main` leggi dalla prima riga `n minimo massimo` (`1 <= n <= 30`, `minimo <= massimo`, `-10'000 <= minimo`, `massimo <= 10'000`) e dalle successive `n` righe un campione intero ciascuna (`-10'000..10'000`); in caso di errore stampa su `stderr` e restituisci `EXIT_FAILURE`. Stampa l'array originale con `stampa_array`, applica `satura_array` e `inverti_array` sul posto e stampa l'array elaborato e il numero di elementi modificati dalla saturazione esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- passaggio di un array e della sua lunghezza `size_t` a una funzione
- qualificatore `const` per i parametri array di sola lettura
- modifica diretta degli elementi dell'array del chiamante sul posto
- scambio simmetrico di coppie per invertire un array senza array d'appoggio

**Domande guida**

1. Quale delle tre funzioni deve dichiarare il parametro array come `const int a[]` e quali invece come `int a[]`?
2. Perché tutte e tre le funzioni richiedono il parametro `size_t n` oltre all'array?
3. In `inverti_array`, fino a quale indice deve arrivare il ciclo di scambio affinché gli elementi non vengano scambiati due volte tornando all'ordine iniziale?
4. Perché `satura_array` modifica i valori dell'array `campioni` dentro `main` senza bisogno di restituire un nuovo array?

**Esempio di esecuzione**

```input
5 0 100
-15
40
120
75
100
```

```output
Originali: -15 40 120 75 100
Elementi modificati: 2
Elaborati: 100 75 100 40 0
```

## 8.4 Array bidimensionali

Molti dati reali non formano una singola sequenza lineare, ma una tabella con righe e colonne: le temperature rilevate da più stazioni in diverse fasce orarie, una scacchiera, una matrice matematica o i voti di una classe in più materie. In C puoi rappresentare queste strutture con un **array bidimensionale**, cioè un array i cui elementi sono a loro volta array.

Per dichiarare un array bidimensionale indichi il tipo degli elementi, il nome e le due dimensioni costanti tra parentesi quadre: prima il numero di righe, poi il numero di colonne. Per l'inizializzazione si usano liste tra graffe annidate, una per riga; come per gli array monodimensionali, gli elementi omessi vengono azzerati automaticamente e `{0}` azzera l'intera tabella:

<!-- cod: id=8.4-b tipo=frammento -->
```c
constexpr size_t RIGHE = 2;
constexpr size_t COLONNE = 3;
int tabella[RIGHE][COLONNE] = {
    {1, 2, 3},
    {4, 5, 6}
};
int vuota[RIGHE][COLONNE] = {0};  // tutti gli elementi valgono 0
```

Anche se pensiamo a `tabella` come a un rettangolo di righe e colonne, la memoria del computer è una sequenza lineare di byte. Lo standard C23 stabilisce come comportamento **definito** che un array `tipo m[RIGHE][COLONNE]` sia memorizzato in modo contiguo **per righe** (*row-major order*): prima tutti gli elementi della riga `0`, poi immediatamente accanto tutti gli elementi della riga `1`, e così via.

```text
Vista logica (2 x 3):          Disposizione contigua in memoria (per righe):

col:   0   1   2               indice:  [0][0] [0][1] [0][2] [1][0] [1][1] [1][2]
     +---+---+---+                     +------+------+------+------+------+------+
r=0  | 1 | 2 | 3 |             valore: |  1   |  2   |  3   |  4   |  5   |  6   |
     +---+---+---+                     +------+------+------+------+------+------+
r=1  | 4 | 5 | 6 |                     |<----- riga 0 ----->|<----- riga 1 ----->|
     +---+---+---+
```

Per leggere o modificare l'elemento alla riga `r` e colonna `c` scrivi `m[r][c]`, con `0 <= r < RIGHE` e `0 <= c < COLONNE`. Entrambi gli indici devono restare nei rispettivi limiti: un indice fuori intervallo provoca comportamento indefinito esattamente come negli array monodimensionali.

Lo schema naturale per attraversare un array bidimensionale usa due cicli `for` annidati (capitolo 6): il ciclo esterno scorre le righe `r`, il ciclo interno scorre le colonne `c`:

<!-- cod: id=8.4-c tipo=frammento -->
```c
for (size_t r = 0; r < RIGHE; ++r) {
    for (size_t c = 0; c < COLONNE; ++c) {
        printf("%4d", tabella[r][c]);
    }
    putchar('\n');
}
```

Quando passi un array bidimensionale a una funzione, vale una regola precisa e **definita** dallo standard C23: puoi omettere la prima dimensione, ma **devi sempre specificare la seconda dimensione costante** (`tipo m[][COLONNE]`, oppure `const tipo m[][COLONNE]` per sola lettura), passando il numero effettivo di righe come parametro separato `size_t righe`:

<!-- cod: id=8.4-d tipo=frammento -->
```c
void stampa_matrice(const int m[][COLONNE], size_t righe);
```

Perché la seconda dimensione è obbligatoria? Ripensa alla disposizione lineare in memoria: per raggiungere `m[r][c]`, il compilatore deve saltare `r` righe complete (ciascuna lunga `COLONNE` elementi) e poi avanzare di `c` posizioni, calcolando lo spiazzamento `r * COLONNE + c`. Senza conoscere `COLONNE` a tempo di compilazione, non saprebbe quanto è lunga una riga. Scrivere `const int m[][]` provoca quindi un errore di compilazione.

Con i cicli annidati e questa convenzione puoi realizzare tutte le operazioni fondamentali sulle matrici:

- **somma di una riga `r`**: fissi `r` e scorri `c` da `0` a `colonne - 1`;
- **somma di una colonna `c`**: fissi `c` e scorri `r` da `0` a `righe - 1`;
- **traccia della diagonale principale** (per una matrice quadrata `n x n`): un singolo ciclo `for (size_t i = 0; i < n; ++i)` somma gli elementi `m[i][i]`;
- **trasposizione**: copia ogni elemento `orig[r][c]` nella posizione `trasp[c][r]` di una seconda matrice, scambiando righe e colonne (una matrice `righe x colonne` diventa una matrice `colonne x righe`).

### Esempio guidato

Il programma seguente conserva in `const double temp[3][4]` le temperature registrate da 3 stazioni meteorologiche in 4 fasce orarie della giornata. Usa tre funzioni con parametro `const double m[][4]` per stampare la tabella, calcolare la media giornaliera di ogni stazione e individuare la fascia oraria mediamente più calda.

<!-- cod: id=8.4-a tipo=programma -->
```c
#include <stdio.h>

void stampa_tabella(const double m[][4], size_t righe);
double media_stazione(const double m[][4], size_t stazione);
size_t fascia_piu_calda(const double m[][4], size_t righe);

int main(void) {
    const double temp[3][4] = {
        {14.0, 21.6, 23.2, 17.2},
        {12.8, 19.6, 22.4, 16.0},
        {15.6, 22.0, 24.8, 18.0}
    };
    stampa_tabella(temp, 3);
    for (size_t s = 0; s < 3; ++s) {
        printf("Media stazione %zu: %.2f C\n", s + 1, media_stazione(temp, s));
    }
    printf("Fascia piu calda: %zu\n", fascia_piu_calda(temp, 3) + 1);
    return 0;
}
void stampa_tabella(const double m[][4], size_t righe) {
    for (size_t r = 0; r < righe; ++r) {
        printf("Stazione %zu:", r + 1);
        for (size_t c = 0; c < 4; ++c) { printf(" %5.1f", m[r][c]); }
        putchar('\n');
    }
}
double media_stazione(const double m[][4], size_t stazione) {
    double somma = 0.0;
    for (size_t c = 0; c < 4; ++c) { somma += m[stazione][c]; }
    return somma / 4.0;
}
size_t fascia_piu_calda(const double m[][4], size_t righe) {
    size_t migliore = 0;
    double somma_max = 0.0;
    for (size_t c = 0; c < 4; ++c) {
        double somma = 0.0;
        for (size_t r = 0; r < righe; ++r) { somma += m[r][c]; }
        if (c == 0 || somma > somma_max) { somma_max = somma; migliore = c; }
    }
    return migliore;
}
```

```output
Stazione 1:  14.0  21.6  23.2  17.2
Stazione 2:  12.8  19.6  22.4  16.0
Stazione 3:  15.6  22.0  24.8  18.0
Media stazione 1: 19.00 C
Media stazione 2: 17.70 C
Media stazione 3: 20.10 C
Fascia piu calda: 3
```

Osserva come funzionano i tre attraversamenti:

- Tutte e tre le funzioni dichiarano `const double m[][4]`: il qualificatore `const` protegge la matrice da modifiche accidentali e il `4` fisso permette al compilatore di calcolare l'offset di ogni elemento `m[r][c]`.
- `stampa_tabella` scorre per righe (ciclo esterno `r`) e per colonne (ciclo interno `c`), allineando i numeri con lo specificatore `%5.1f`.
- `media_stazione` fissa la riga `stazione` e somma le `4` fasce orarie con un solo ciclo su `c`.
- `fascia_piu_calda` esamina una colonna alla volta: somma le temperature delle `3` stazioni nella fascia `c` e aggiorna `migliore` quando trova una somma superiore (usando `c == 0` per inizializzare `somma_max` senza costanti arbitrarie).

> **Approfondimento — Scorrere per righe o per colonne**
> Poiché in C una matrice è memorizzata per righe, un ciclo che tiene `r` all'esterno e `c` all'interno visita byte consecutivi in memoria uno dopo l'altro. Un ciclo che invece varia `r` all'interno a parità di `c` salta ogni volta in avanti di un'intera riga. Su matrici piccole la differenza è invisibile, ma su matrici grandi scorrere in ordine contiguo sfrutta molto meglio la memoria veloce del processore (è la *località dei dati*, che approfondiremo nel capitolo 25). Quando l'algoritmo ti lascia libertà di scelta, preferisci sempre le righe nel ciclo esterno e le colonne nel ciclo interno.

### Esercizio 8.4 — Somme per righe, colonne e trasposta di una matrice

**Descrizione**

Scrivi un programma C che usi la costante a livello di file `constexpr size_t MAX_DIM = 6;` e dichiari prima di `main` i prototipi di tre funzioni su array bidimensionali con seconda dimensione costante `MAX_DIM`: `void stampa_matrice(const int m[][MAX_DIM], size_t righe, size_t colonne)` (stampa ogni elemento con `%4d` e un ritorno a capo al termine di ogni riga), `int somma_riga(const int m[][MAX_DIM], size_t riga, size_t colonne)` e `void trasponi(const int orig[][MAX_DIM], int trasp[][MAX_DIM], size_t righe, size_t colonne)` (scrive `orig[r][c]` in `trasp[c][r]`). In `main` leggi dalla prima riga di `stdin` `righe colonne` (due interi in `1..6`) e dalle successive `righe * colonne` righe un intero per riga in ordine per righe (`-1000..1000`); in caso di errore scrivi su `stderr` e restituisci `EXIT_FAILURE`. Calcola la trasposta `trasp` con `trasponi`, quindi stampa la matrice originale, le somme di tutte le righe tramite `somma_riga(mat, r, colonne)`, le somme di tutte le colonne riutilizzando `somma_riga(trasp, c, righe)` e infine la matrice trasposta (di dimensioni `colonne x righe`), esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- dichiarazione di array bidimensionali di dimensione massima costante
- disposizione per righe (*row-major order*) nella lettura e stampa
- seconda dimensione costante obbligatoria nei parametri di funzione (`m[][MAX_DIM]`)
- scambio degli indici `[r][c]` → `[c][r]` nella trasposizione e riuso di `somma_riga`

**Domande guida**

1. Perché nei parametri delle funzioni puoi omettere la prima dimensione della matrice ma sei obbligato a indicare la costante `MAX_DIM` come seconda dimensione?
2. Quali sono il numero di righe e il numero di colonne da passare a `stampa_matrice` quando visualizzi la trasposta di una matrice rettangolare `righe x colonne`?
3. Perché puoi ottenere la somma di ogni colonna della matrice originale applicando `somma_riga` alle righe della matrice trasposta?
4. In quale ordine conviene annidare i cicli su righe e colonne per seguire la disposizione contigua in memoria della matrice?

**Esempio di esecuzione**

```input
2 3
1
2
3
4
5
6
```

```output
Matrice originale:
   1   2   3
   4   5   6
Somma righe: 6 15
Somma colonne: 5 7 9
Matrice trasposta:
   1   4
   2   5
   3   6
```

## 8.5 Ricerca, ordinamento elementare e idea di costo

Una volta raccolti dei dati in un array, le due operazioni più frequenti sono **cercare** un elemento e **ordinare** gli elementi. Oltre a scrivere codice corretto, è importante iniziare a chiederti *quanto lavoro* svolge un algoritmo al crescere del numero di elementi $n$: due algoritmi che producono lo stesso risultato possono impiegare tempi completamente diversi su grandi quantità di dati.

### Ricerca lineare

La strategia più diretta per cercare un valore `chiave` in un array qualsiasi di lunghezza `n` è la **ricerca lineare**: scorri l'array da `0` a `n - 1` e ti fermi appena trovi `a[i] == chiave`. Se arrivi in fondo senza trovarlo, restituisci un valore che indica l'assenza (per esempio `-1`).

La ricerca lineare non richiede alcuna ipotesi sull'ordine degli elementi. Nel **caso migliore** (la chiave è in posizione `0`) esegue `1` solo confronto; nel **caso peggiore** (la chiave è all'ultima posizione oppure è assente) esegue `n` confronti. Il costo cresce quindi in modo proporzionale a `n`: raddoppiando la lunghezza dell'array, raddoppia nel caso peggiore il numero di confronti.

### Ricerca binaria

Se invece l'array rispetta una precondizione precisa — **è già ordinato in senso crescente** — puoi fare molto meglio con la **ricerca binaria** (*binary search*). L'idea è la stessa con cui cerchi una parola in un dizionario cartaceo: controlli l'elemento centrale; se è minore della chiave, scarti tutta la metà sinistra; se è maggiore o uguale, scarti la metà destra.

Per scrivere la ricerca binaria in modo pulito e sicuro con indici `size_t`, conviene mantenere l'intervallo di ricerca come **intervallo semiaperto** `[sinistra, destra)` (estremo sinistro incluso, estremo destro escluso), inizializzato a `sinistra = 0` e `destra = n`. Finché `sinistra < destra`, l'intervallo contiene almeno un elemento e il suo punto centrale si calcola con:

```text
medio = sinistra + (destra - sinistra) / 2
```

Questa formula dà lo stesso risultato matematico di `(sinistra + destra) / 2`, ma evita l'overflow nella somma quando `sinistra` e `destra` sono grandi. Inoltre, restringendo l'intervallo con `sinistra = medio + 1` oppure `destra = medio`, non si esegue mai `medio - 1` e quindi non esiste alcun rischio di underflow su `size_t` nemmeno quando `medio` vale `0`. Secondo lo standard C23, l'uso dell'intervallo semiaperto `[sinistra, destra)` su `size_t` con `sinistra + (destra - sinistra) / 2` garantisce in modo **definito** l'assenza sia di overflow nella somma sia di underflow su indici senza segno.

A ogni iterazione la lunghezza dell'intervallo si dimezza. Su un array di `n` elementi bastano al più circa $\log_2(n)$ passi:

- per `n = 8`, al più `3–4` passi;
- per `n = 1'000`, al più `10` passi;
- per `n = 1'000'000`, al più `20` passi (contro `1'000'000` confronti della ricerca lineare).

Ricorda però la precondizione: se applichi la ricerca binaria a un array *non* ordinato, l'algoritmo scarta metà dell'array supponendo un ordine che non esiste e può dichiarare assente una chiave presente.

### Ordinamento per selezione e per inserzione

Come si ordina un array in ordine crescente? Vediamo due algoritmi elementari, entrambi basati sullo stesso **invariante di ciclo** (capitolo 6): all'inizio dell'iterazione `i`, il prefisso `a[0..i-1]` è già ordinato.

1. **Ordinamento per selezione** (*selection sort*): a ogni passo `i` (da `0` a `n - 2`) cerca l'indice `min_i` dell'elemento minimo nella parte ancora da ordinare `a[i..n-1]` e lo scambia con `a[i]`. Dopo lo scambio, `a[0..i]` contiene gli `i + 1` elementi più piccoli dell'intero array, già nella loro posizione definitiva.
   Il numero di confronti eseguiti è sempre lo stesso, indipendentemente dai dati iniziali:

   $$(n - 1) + (n - 2) + \dots + 1 = \frac{n \cdot (n - 1)}{2}$$

   cioè proporzionale a $n \cdot n$.

2. **Ordinamento per inserzione** (*insertion sort*): a ogni passo `i` (da `1` a `n - 1`) prende l'elemento `chiave = a[i]` e lo inserisce nella posizione corretta dentro il prefisso già ordinato `a[0..i-1]`, spostando a destra (`a[j] = a[j - 1]`) gli elementi maggiori di `chiave`.
   Nel **caso peggiore** (array ordinato al contrario), ogni elemento attraversa tutto il prefisso: gli spostamenti sono $\frac{n \cdot (n - 1)}{2}$, ancora proporzionali a $n \cdot n$. Nel **caso migliore** (array già ordinato), il ciclo interno non sposta nulla: esegue `0` spostamenti e solo `n - 1` confronti, con costo lineare in `n`. Per questo l'ordinamento per inserzione è molto rapido su array piccoli o quasi ordinati.

### Idea di costo e scelta dell'algoritmo

Confrontando questi algoritmi vedi emergere tre ritmi di crescita diversi al crescere di `n` (che formalizzeremo con la notazione O nel capitolo 23):

- **logaritmico** ($\log_2 n$): ricerca binaria su array ordinato;
- **lineare** ($n$): ricerca lineare, oppure ordinamento per inserzione su array già ordinato;
- **quadratico** ($n \cdot n$): ordinamento per selezione sempre, e ordinamento per inserzione nel caso peggiore.

Ne nasce un compromesso pratico molto comune: se devi fare una sola ricerca su un array non ordinato, conviene la ricerca lineare (`n` confronti), perché ordinare prima costerebbe circa $n \cdot n$ operazioni. Se invece devi eseguire *molte* ricerche sullo stesso insieme di dati, conviene ordinare l'array una sola volta e poi usare sempre la ricerca binaria (e nel capitolo 16 vedrai come ordinare ancora più velocemente con `qsort`).

### Esempio guidato

Il programma seguente cerca la chiave `53` in un array non ordinato di 8 codici con la ricerca lineare (contando i confronti), ordina l'array con l'ordinamento per selezione (contando i confronti) e ripete la ricerca con la ricerca binaria (contando i passi), mostrando il confronto tra i numeri ottenuti.

<!-- cod: id=8.5-a tipo=programma -->
```c
#include <stdio.h>

void cerca_lineare(const int a[], size_t n, int chiave) {
    for (size_t i = 0; i < n; ++i) {
        if (a[i] == chiave) { printf("Lineare: indice %zu (%zu confronti)\n", i, i + 1); return; }
    }
    printf("Lineare: assente (%zu confronti)\n", n);
}

size_t ordina_selezione(int a[], size_t n) {
    size_t confronti = 0;
    for (size_t i = 0; i + 1 < n; ++i) {
        size_t min_i = i;
        for (size_t j = i + 1; j < n; ++j) {
            ++confronti;
            if (a[j] < a[min_i]) { min_i = j; }
        }
        int tmp = a[i]; a[i] = a[min_i]; a[min_i] = tmp;
    }
    return confronti;
}

void cerca_binaria(const int a[], size_t n, int chiave) {
    size_t sinistra = 0, destra = n, passi = 0;
    while (sinistra < destra) {
        ++passi;
        size_t medio = sinistra + (destra - sinistra) / 2;
        if (a[medio] == chiave) { printf("Binaria: indice %zu (%zu passi)\n", medio, passi); return; }
        if (a[medio] < chiave) { sinistra = medio + 1; } else { destra = medio; }
    }
    printf("Binaria: assente (%zu passi)\n", passi);
}

int main(void) {
    int codici[] = {42, 15, 88, 7, 31, 64, 19, 53};
    const size_t n = sizeof(codici) / sizeof(codici[0]);
    cerca_lineare(codici, n, 53);
    printf("Selezione: %zu confronti\n", ordina_selezione(codici, n));
    cerca_binaria(codici, n, 53);
    return 0;
}
```

```output
Lineare: indice 7 (8 confronti)
Selezione: 28 confronti
Binaria: indice 5 (3 passi)
```

Analizziamo i numeri prodotti:

- Nell'array iniziale `{42, 15, 88, 7, 31, 64, 19, 53}`, la chiave `53` si trova all'ultima posizione (`indice 7`): la ricerca lineare ispeziona tutti gli `8` elementi.
- `ordina_selezione` trasforma l'array sul posto in `{7, 15, 19, 31, 42, 53, 64, 88}` eseguendo esattamente $\frac{8 \cdot 7}{2} = 28$ confronti. Nota la condizione del ciclo esterno `i + 1 < n`: evita underflow anche se `n` fosse `0`.
- Sull'array ordinato, `53` si trova all'indice `5` e `cerca_binaria` lo individua in soli `3` passi: prima controlla `medio = 4` (`42 < 53`), poi `medio = 6` (`64 > 53`), infine `medio = 5` (`53 == 53`).

> **Approfondimento — Due errori classici nella ricerca binaria**
> Anche programmatori esperti commettono spesso due errori nella ricerca binaria. Il primo è calcolare il punto medio come `(sinistra + destra) / 2`: se `sinistra` e `destra` superano la metà del valore massimo del loro tipo, la somma va in overflow; scrivere `sinistra + (destra - sinistra) / 2` elimina il problema alla radice. Il secondo errore riguarda la variante con intervallo chiuso `[sinistra, destra]` usando `size_t`: se la chiave è minore di `a[0]`, l'algoritmo arriva a `medio == 0` e poi esegue `destra = medio - 1`, provocando un underflow di `size_t` (che diventa un numero enorme) e un ciclo infinito o un accesso fuori dai limiti. L'intervallo semiaperto `[sinistra, destra)` con `destra = medio` elimina completamente anche questo secondo errore.

### Esercizio 8.5 — Ordinamento per inserzione e confronto tra ricerca lineare e binaria

**Descrizione**

Scrivi un programma C (`constexpr size_t MAX_ELEM = 50;`) che dichiari prima di `main` i prototipi di tre funzioni: `size_t ordina_inserzione(int a[], size_t n)` (ordina `a[0..n-1]` in ordine crescente con l'algoritmo di ordinamento per inserzione e restituisce il numero totale di spostamenti `a[j] = a[j - 1]` effettuati), `int ricerca_lineare(const int a[], size_t n, int chiave)` (restituisce il primo indice `0..n-1` in cui compare `chiave`, oppure `-1` se assente) e `int ricerca_binaria(const int a[], size_t n, int chiave)` (usa l'intervallo semiaperto `[sinistra, destra)` su `size_t` con `medio = sinistra + (destra - sinistra) / 2` per restituire il primo indice in cui compare `chiave` nell'array ordinato, oppure `-1` se assente). In `main` leggi dalla prima riga `n` (`1 <= n <= 50`), dalle successive `n` righe gli `n` interi dell'array e dalle eventuali righe restanti fino alla fine dell'input le chiavi intere da cercare (se una riga non è un intero valido stampa su `stderr` e restituisci `EXIT_FAILURE`). Ordina l'array con `ordina_inserzione`, stampa l'array ordinato su una riga (elementi separati da uno spazio) e il numero di spostamenti eseguiti; per ogni chiave letta esegui sia `ricerca_lineare` sia `ricerca_binaria` sull'array ordinato e stampa `Chiave K: lineare=L, binaria=B` (dove `-1` indica chiave assente) esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- ordinamento per inserzione e invariante del prefisso ordinato
- conteggio degli spostamenti per osservare il costo (`0` nel caso migliore, `n * (n - 1) / 2` nel caso peggiore)
- ricerca lineare e ricerca binaria con intervallo semiaperto `[sinistra, destra)`
- calcolo sicuro del punto medio `sinistra + (destra - sinistra) / 2`

**Domande guida**

1. Qual è l'invariante del ciclo esterno dell'ordinamento per inserzione all'inizio dell'iterazione `i`?
2. Quanti spostamenti esegue l'ordinamento per inserzione su un array già ordinato rispetto a uno ordinato al contrario?
3. Perché l'intervallo semiaperto `[sinistra, destra)` su `size_t` nella ricerca binaria evita l'underflow quando la chiave cercata è minore del primo elemento?
4. Come riesce la variante con `destra = medio` quando `a[medio] >= chiave` a trovare sempre la prima occorrenza della chiave anche in presenza di duplicati?

**Esempio di esecuzione**

```input
6
40
10
30
20
30
5
30
15
5
```

```output
Array ordinato: 5 10 20 30 30 40
Spostamenti inserzione: 10
Chiave 30: lineare=3, binaria=3
Chiave 15: lineare=-1, binaria=-1
Chiave 5: lineare=0, binaria=0
```

## Riepilogo

- Un **array** è una sequenza contigua in memoria di un numero fissato di elementi tutti dello stesso tipo, accessibili tramite un **indice** intero a partire da `0` (indici validi `0..N-1`). In questo libro la dimensione `N` è sempre una costante positiva (`constexpr` o letterale) ed evitiamo gli array a lunghezza variabile (VLA).
- In un inizializzatore (`{v0, v1, ...}`, `{0}` oppure con inizializzatori designati `{[i] = v}`), tutti gli elementi omessi sono azzerati automaticamente; al contrario, un array locale senza inizializzatore contiene valori indeterminati e leggerli provoca comportamento indefinito. Nella stessa visibilità della dichiarazione, la lunghezza si ricava con `sizeof(a) / sizeof(a[0])`.
- Non è possibile copiare o confrontare array con `=` o `==`: occorre un ciclo elemento per elemento. Il C non effettua controlli automatici sugli indici: qualsiasi **accesso fuori dai limiti** (`i < 0` oppure `i >= N`) provoca comportamento indefinito.
- Negli array a capacità fissa parzialmente riempiti vanno tenuti distinti la capacità fisica e il numero effettivo di elementi usati `n`, validando ogni indice (anche tramite valutazione a corto circuito) prima di indicizzare.
- Quando passi un array a una funzione (`tipo a[]` o `const tipo a[]` per sola lettura), la funzione accede direttamente agli elementi del chiamante senza copiarli (il meccanismo basato sui puntatori verrà spiegato nel capitolo 10) e `sizeof(a)` dentro la funzione non restituisce la dimensione dell'array: la lunghezza `size_t n` va sempre passata come parametro separato.
- Un array bidimensionale `tipo m[RIGHE][COLONNE]` è memorizzato in modo contiguo per righe (*row-major order*); nei parametri di funzione va sempre indicata la seconda dimensione costante (`tipo m[][COLONNE]`).
- La ricerca lineare richiede al più `n` confronti su qualsiasi array; la ricerca binaria richiede un array ordinato e impiega al più circa $\log_2(n)$ passi, usando l'intervallo semiaperto `[sinistra, destra)` su `size_t` e `medio = sinistra + (destra - sinistra) / 2`. L'ordinamento per selezione e quello per inserzione hanno costo proporzionale a $n \cdot n$ nel caso peggiore, ma l'inserzione è lineare su array già ordinati.

## Errori comuni

- **Accedere all'elemento `a[n]` di un array di lunghezza `n` (errore *off-by-one*)**: scrivere `for (size_t i = 0; i <= n; ++i)` invece di `i < n`, oppure accedere ad `a[i + 1]` all'ultima iterazione, provoca un accesso fuori dai limiti e comportamento indefinito; verifica sempre che gli indici restino in `0..n-1`.
- **Provare a copiare o confrontare due array con `a = b` oppure `a == b`**: il compilatore rifiuta `a = b`, mentre `a == b` non confronta gli elementi; esegui sempre copia e confronto elemento per elemento con un ciclo `for`.
- **Usare `sizeof(a) / sizeof(a[0])` dentro una funzione su un parametro `int a[]`**: il parametro array viene adattato dal compilatore e `sizeof(a)` non restituisce la dimensione dell'array del chiamante; passa sempre la lunghezza come parametro `size_t n`.
- **Dimenticare la seconda dimensione costante nella firma di una funzione su array bidimensionali**: scrivere `int m[][]` invece di `int m[][COLONNE]` provoca un errore di compilazione perché il compilatore non può calcolare lo spiazzamento delle righe.
- **Applicare la ricerca binaria a un array non ordinato, oppure calcolare il punto medio in modo insicuro**: senza ordinamento il risultato è errato; inoltre `(sinistra + destra) / 2` rischia l'overflow e `destra = medio - 1` su `size_t` rischia l'underflow quando `medio == 0`. Usa sempre `[sinistra, destra)` e `sinistra + (destra - sinistra) / 2`.
- **Dimenticare di inizializzare un array locale e supporre che valga zero**: senza inizializzatore gli elementi locali contengono valori indeterminati; scrivi almeno `{0}` quando desideri azzerarli tutti.

## Prima di proseguire

- [ ] So dichiarare e inizializzare un array monodimensionale con lista completa, `{0}` e inizializzatori designati, ricavandone la lunghezza con `sizeof(a) / sizeof(a[0])` nella stessa visibilità.
- [ ] So spiegare perché un accesso fuori dai limiti provoca comportamento indefinito e so evitarlo distinguendo capacità fisica e lunghezza effettiva e validando gli indici prima di indicizzare.
- [ ] So scrivere funzioni che ricevono array (`tipo a[]` e `const tipo a[]`) insieme alla lunghezza `size_t n`, scegliendo correttamente `const` per le funzioni di sola lettura.
- [ ] So dichiarare, inizializzare, attraversare e passare a funzioni array bidimensionali (`tipo m[][COLONNE]`), spiegando la disposizione per righe in memoria.
- [ ] So implementare ricerca lineare, ricerca binaria con intervallo semiaperto `[sinistra, destra)`, ordinamento per selezione e ordinamento per inserzione, confrontandone il costo al crescere di `n`.
