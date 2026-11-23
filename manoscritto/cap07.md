# Capitolo 7 — Funzioni

> **In questo capitolo imparerai a:**
> - Definire e dichiarare funzioni con prototipi coerenti e parametri passati per valore
> - Prevedere visibilità e durata di vita di variabili locali e variabili `static` locali
> - Scrivere funzioni ricorsive identificando caso base e passo ricorsivo
> - Scomporre un problema complesso in funzioni piccole e indipendenti

> **Ti servono:** variabili e tipi (capitolo 2), espressioni e conversioni (capitolo 3), decisioni (capitolo 4), lettura dell'input con `fgets` e `sscanf` (capitolo 5) e cicli (capitolo 6).

Finora hai scritto tutti i tuoi programmi interamente dentro `main`. Finché un esercizio conta trenta o cinquanta righe, tenere insieme lettura dell'input, controlli, calcoli e stampa in un unico blocco è ancora gestibile. Appena il programma cresce, però, un `main` lungo diventa difficile da leggere, da modificare e da verificare: la stessa formula compare ripetuta in più punti, una correzione va replicata a mano e il filo logico del problema si perde tra dettagli di basso livello.

In realtà hai già usato molte funzioni scritte da altri: `printf`, `fgets`, `sscanf`, `putchar`, `fabs` e `sqrt` svolgono ciascuna un compito preciso dietro un nome chiaro, senza costringerti a ricopiare ogni volta le istruzioni interne. In questo capitolo impari a scrivere le tue funzioni, a dichiararle con prototipi rigorosi e a governare con precisione come i dati entrano, vivono ed escono da ogni chiamata.

Vedrai come il C passa gli argomenti per valore, che cosa determina dove una variabile esiste e per quanto tempo conserva il proprio contenuto — scoprendo il ruolo di `static` locale — e come una funzione possa richiamare se stessa tramite la ricorsione. Infine imparerai a progettare programmi più articolati spezzandoli dall'alto verso il basso in funzioni brevi, coese e facili da controllare.

## 7.1 Definire e chiamare una funzione

Immagina di scrivere un programma che analizza decine di rilevazioni di velocità stradale. Ogni volta devi convertire una velocità da chilometri orari a metri al secondo, controllare se supera il limite e stampare una riga separatrice per rendere leggibile il prospetto. Se ricopi le stesse formule e gli stessi cicli in cinque punti diversi di `main`, il codice si allunga inutilmente e, se scopri un errore o decidi di cambiare lo stile del separatore, devi inseguire tutte le copie una per una.

La soluzione è raccogliere ciascun compito in un blocco autonomo dotato di un nome chiaro che ne descriva lo scopo. In C questo costrutto si chiama **funzione** (*function*): un blocco di codice dotato di nome, parametri e tipo di ritorno che svolge un compito definito e può essere richiamato ogni volta che serve. In realtà scrivi già una funzione dal primo capitolo: `main` è la funzione da cui il sistema operativo avvia il programma. Ora impari a crearne di nuove.

Una definizione di funzione ha sempre la stessa forma, composta da un'intestazione e da un corpo racchiuso tra parentesi graffe:

<!-- cod: id=7.1-b tipo=frammento -->
```c
double kmh_a_ms(double kmh) {
    return kmh / 3.6;
}
```

Osserva i quattro elementi che compongono questa definizione:

1. **Tipo di ritorno** (`double`): indica il tipo del valore che la funzione restituisce al punto in cui viene chiamata. Può essere qualunque tipo del linguaggio (`int`, `double`, `long`, `bool`, `char`, ecc.) oppure `void` quando la funzione esegue soltanto un'azione senza restituire alcun valore.
2. **Nome della funzione** (`kmh_a_ms`): segue le stesse regole degli identificatori delle variabili. In questo libro i nomi di funzione sono in `snake_case` italiano senza accenti e descrivono chiaramente che cosa fa la funzione.
3. **Lista dei parametri** (`(double kmh)`): racchiusa tra parentesi tonde, elenca i dati che la funzione si aspetta di ricevere, separati da virgole e preceduti ciascuno dal proprio tipo. Anche se due parametri hanno lo stesso tipo, il tipo va ripetuto per entrambi: si scrive `(double kmh, double limite)`, mai `(double kmh, limite)`. Se la funzione non accetta alcun parametro, tra le parentesi si scrive `void`, come in `int main(void)`.
4. **Corpo della funzione** (`{ ... }`): il blocco di istruzioni eseguito a ogni chiamata. A differenza di una dichiarazione, l'intestazione della definizione non termina mai con un punto e virgola: inserire `;` subito prima della graffa di apertura provoca un errore di compilazione.

Per parlare di funzioni con precisione occorre tenere ben distinti due termini che nel linguaggio comune vengono spesso confusi:

- Un **parametro** (*parameter*) è una variabile dichiarata nell'intestazione di una funzione che riceve il valore fornito alla chiamata. Nell'esempio precedente `kmh` è un parametro di `kmh_a_ms`.
- Un **argomento** (*argument*) è l'espressione passata tra parentesi nel punto in cui si chiama una funzione. Quando in `main` scrivi `double v = kmh_a_ms(54.0);` oppure `double v = kmh_a_ms(velocita + 2.0);`, le espressioni `54.0` e `velocita + 2.0` sono argomenti.

La distinzione è semplice da ricordare: i parametri vivono nella definizione della funzione, gli argomenti si passano alla chiamata.

Quando il programma incontra una chiamata di funzione, sospende temporaneamente la funzione chiamante, valuta gli argomenti, li copia nei rispettivi parametri ed esegue il corpo della funzione chiamata. L'istruzione `return` interrompe immediatamente l'esecuzione della funzione e restituisce il controllo al chiamante.

Se il tipo di ritorno è diverso da `void`, l'istruzione `return espressione;` calcola `espressione`, converte il risultato al tipo di ritorno dichiarato (se necessario) e lo consegna al chiamante, che può assegnarlo a una variabile, passarlo a `printf` o usarlo dentro un'altra espressione. Una funzione può contenere più istruzioni `return` per realizzare un'uscita anticipata quando una condizione è già sufficiente a determinare il risultato:

<!-- cod: id=7.1-c tipo=frammento -->
```c
bool supera_limite(double kmh, double limite) {
    if (kmh > limite) {
        return true;
    }
    return false;
}
```

Naturalmente questa funzione si può scrivere in modo ancora più conciso come `return kmh > limite;`, ma la versione con uscita anticipata mostra bene un principio utile nei casi più articolati: appena il risultato è noto, `return` conclude subito la funzione.

Se invece la funzione esegue solo un'azione — per esempio stampare un'intestazione o una riga di trattini — il suo tipo di ritorno è `void`. Una funzione `void` non restituisce alcun valore: non può essere usata dentro un'espressione (non puoi scrivere `int x = stampa_separatore(10);`) e termina quando raggiunge la graffa di chiusura oppure quando incontra `return;` senza alcuna espressione.

Riassumiamo la regola precisa stabilita dallo standard C23:

- Una definizione di funzione specifica tipo di ritorno, identificatore, lista dei parametri con i rispettivi tipi (oppure `void` se non accetta parametri) e corpo tra parentesi graffe.
- Una funzione con tipo di ritorno diverso da `void` deve restituire tramite `return` un valore convertibile al tipo dichiarato su ogni percorso di esecuzione possibile.
- Una funzione `void` non restituisce alcun valore e può terminare con `return;` oppure raggiungendo la graffa di chiusura.

> **C23** — Nello standard C23 una lista di parametri vuota `f()` ha lo stesso significato di `f(void)`: indica una funzione che non accetta argomenti. Negli standard precedenti (C17 e C11), invece, `f()` in una dichiarazione lasciava imprecisati numero e tipo dei parametri, disattivando il controllo del compilatore sulle chiamate. Per chiarezza e portabilità verso compilatori più vecchi, in questo libro scriviamo sempre esplicitamente `(void)` per le funzioni senza parametri.

> **Se vieni da Python** — In Python definisci una funzione con `def` senza indicare i tipi dei parametri né del valore restituito, e puoi restituire più valori insieme in una tupla con un solo `return`. In C ogni funzione dichiara esplicitamente il tipo di ritorno e il tipo di ciascun parametro, e restituisce al più un solo valore (nei capitoli 10 e 12 vedrai come gestire più risultati tramite puntatori o `struct`).

### Esempio guidato

Il programma seguente simula il controllo di due rilevazioni di velocità stradale. Definisce sopra `main` tre funzioni con tipi di ritorno diversi: `kmh_a_ms` (`double`), `supera_limite` (`bool`) e `stampa_separatore` (`void`). In `main` richiama le tre funzioni su due rilevazioni distinte.

<!-- cod: id=7.1-a tipo=programma -->
```c
#include <stdio.h>

double kmh_a_ms(double kmh) {
    return kmh / 3.6;
}

bool supera_limite(double kmh, double limite) {
    return kmh > limite;
}

void stampa_separatore(int lunghezza) {
    for (int i = 0; i < lunghezza; ++i) {
        putchar('-');
    }
    putchar('\n');
}

int main(void) {
    constexpr double LIMITE = 50.0;
    double rilevazione_1 = 48.6;
    double rilevazione_2 = 61.2;

    stampa_separatore(32);
    printf("Rilevazione 1: %.1f km/h (%.2f m/s) -> %s\n",
           rilevazione_1,
           kmh_a_ms(rilevazione_1),
           supera_limite(rilevazione_1, LIMITE) ? "INFRAZIONE" : "REGOLARE");
    printf("Rilevazione 2: %.1f km/h (%.2f m/s) -> %s\n",
           rilevazione_2,
           kmh_a_ms(rilevazione_2),
           supera_limite(rilevazione_2, LIMITE) ? "INFRAZIONE" : "REGOLARE");
    stampa_separatore(32);
    return 0;
}
```

```output
--------------------------------
Rilevazione 1: 48.6 km/h (13.50 m/s) -> REGOLARE
Rilevazione 2: 61.2 km/h (17.00 m/s) -> INFRAZIONE
--------------------------------
```

Analizziamo come collaborano le parti del programma:

- Le tre funzioni sono definite *prima* di `main`: quando il compilatore legge le chiamate dentro `main`, conosce già nome, tipo di ritorno e tipi dei parametri di ciascuna funzione.
- `kmh_a_ms` accetta un parametro `double kmh` e restituisce il valore convertito in metri al secondo. Nelle chiamate dentro `printf`, gli argomenti sono `rilevazione_1` e `rilevazione_2`; il valore restituito viene passato direttamente allo specificatore `%.2f`.
- `supera_limite` accetta due parametri `double` e restituisce un `bool` (`true` o `false`), che comanda l'operatore condizionale `?:` per scegliere la parola da stampare.
- `stampa_separatore` ha tipo di ritorno `void`: stampa una sequenza di trattini con `putchar` seguita da `'\n'` e termina raggiungendo la graffa di chiusura senza bisogno di `return`. Se volessi cambiare il separatore da 32 trattini a 40, ti basterebbe cambiare l'argomento alla chiamata; se volessi cambiare il carattere `'-'` con `'='`, modificheresti una sola riga dentro la funzione.

> **Approfondimento — Che cosa accade se dimentichi `return` in una funzione non `void`**
> Se una funzione dichiarata `int`, `double` o `bool` può raggiungere la graffa di chiusura senza eseguire `return` (per esempio perché un ramo `if` restituisce un valore ma manca il ramo `else`), lo standard C23 stabilisce che usare il valore restituito dal chiamante provoca **comportamento indefinito**. Fa eccezione solo `main`, per la quale lo standard prevede un `return 0;` implicito alla chiusura (anche se in questo libro lo scriviamo sempre in modo esplicito). Compilando con `-Wall -Wextra -Werror`, il compilatore rileva subito i percorsi privi di `return` e blocca la compilazione prima ancora di eseguire il programma.

### Esercizio 7.1 — Scheda di un lotto di terreno rettangolare

**Descrizione**

Scrivi un programma C che includa `<stdio.h>`, `<stdlib.h>` e `<math.h>` e definisca sopra `main` quattro funzioni:

- `void stampa_intestazione(void)`: stampa `=== SCHEDA LOTTO ===` seguito da ritorno a capo;
- `double calcola_area(double larghezza, double lunghezza)`: restituisce l'area del lotto;
- `double calcola_perimetro(double larghezza, double lunghezza)`: restituisce il perimetro del lotto;
- `bool e_quadrato(double larghezza, double lunghezza)`: restituisce `true` se `fabs(larghezza - lunghezza) <= 1e-9`, `false` altrimenti.

In `main` leggi da `stdin` una riga contenente `larghezza`, `lunghezza` e `prezzo_mq` (`double`) verificando la fine dell'input, il formato esatto (`"%lf %lf %lf %c"` == `3`) e i vincoli (`larghezza > 0.0`, `lunghezza > 0.0`, `prezzo_mq >= 0.0`). In caso di errore stampa un messaggio su `stderr` e restituisci `EXIT_FAILURE`. Altrimenti chiama le quattro funzioni, calcola il valore totale (`area * prezzo_mq`) e stampa il riepilogo con due cifre decimali esattamente come nell'esempio di esecuzione, restituendo `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- definizione e chiamata di funzioni con tipi di ritorno diversi (`void`, `double`, `bool`)
- differenza tra parametro e argomento
- istruzione `return`
- confronto in virgola mobile con `fabs` e tolleranza dentro un predicato `bool`

**Domande guida**

1. Quale tipo di ritorno devi usare per una funzione che si limita a stampare l'intestazione senza produrre un risultato numerico?
2. Quali parametri devono ricevere rispettivamente le funzioni per l'area, il perimetro e la verifica del quadrato?
3. Perché nella funzione che verifica se il lotto è quadrato conviene usare `fabs(larghezza - lunghezza) <= 1e-9` invece di `larghezza == lunghezza`?
4. In che modo il valore restituito da `calcola_area` può essere riutilizzato in `main` per ricavare il valore economico totale del lotto?

**Esempio di esecuzione**

```input
12.5 20.0 80.0
```

```output
=== SCHEDA LOTTO ===
Area: 250.00 mq
Perimetro: 65.00 m
Forma: Rettangolo
Valore stimato: 20000.00 euro
```

## 7.2 Prototipi e passaggio per valore

Nella sotto-sezione precedente hai collocato tutte le definizioni di funzione prima di `main`. Con tre brevi funzioni questa disposizione è comoda, ma in un programma più lungo costringe chi legge il file a scorrere decine o centinaia di righe di funzioni ausiliarie prima di arrivare a `main` e capire che cosa fa il programma nel complesso. Inoltre, se una funzione `a` deve chiamare una funzione `b` e `b` deve chiamare `a`, nessuna delle due definizioni può stare prima dell'altra.

Per risolvere entrambi i problemi, il C separa la *dichiarazione* di una funzione dalla sua *definizione*. La dichiarazione si chiama **prototipo** (*prototype*): una dichiarazione di funzione che ne specifica nome, tipo di ritorno e tipi dei parametri senza il corpo, chiusa da un punto e virgola:

<!-- cod: id=7.2-b tipo=frammento -->
```c
double kmh_a_ms(double kmh);
bool supera_limite(double kmh, double limite);
void stampa_separatore(int lunghezza);
```

Collocando i prototipi in cima al file sorgente, subito dopo gli `#include`, puoi scrivere `main` per primo e lasciare le definizioni complete più in basso. Il compilatore legge il file dall'alto verso il basso: quando incontra una chiamata dentro `main`, controlla nel prototipo che il numero degli argomenti sia corretto, che i loro tipi siano compatibili con quelli dei parametri e che il valore restituito venga usato in modo coerente. I nomi dei parametri nel prototipo sono facoltativi per il compilatore, ma scriverli sempre (uguali a quelli della definizione) funge da documentazione immediata per chi legge il file.

Il prototipo e la definizione devono essere perfettamente coerenti tra loro: se il prototipo dichiara `int raddoppia(int x);` e la definizione scrive `double raddoppia(int x)`, il compilatore segnala un conflitto di tipi e rifiuta il programma. In C23 ogni funzione deve essere dichiarata prima della sua prima chiamata mediante un prototipo o una definizione completa; chiamare una funzione sconosciuta è un errore di compilazione.

Quando i tipi degli argomenti non coincidono esattamente con quelli dei parametri dichiarati nel prototipo, il C applica una **conversione implicita** esattamente come in un assegnamento. Se una funzione accetta un `double` e la chiami passando un `int` come `5`, il compilatore converte automaticamente `5` in `5.0`. Viceversa, passare un `double` come `3.9` a un parametro `int` tronca la parte frazionaria a `3`: il prototipo rende possibile questa conversione, ma resta tua responsabilità evitare troncamenti indesiderati.

Che cosa succede esattamente al valore di una variabile quando la passi come argomento a una funzione? In C vale una regola fondamentale, senza eccezioni: il **passaggio per valore** (*pass by value*). Questo meccanismo stabilisce che una funzione riceve una *copia* del valore di ciascun argomento. Ogni parametro è a tutti gli effetti una variabile locale della funzione, inizializzata con quella copia.

Di conseguenza, modificare un parametro dentro la funzione altera soltanto la copia locale e non modifica mai la variabile del chiamante. Ecco una rappresentazione schematica di ciò che avviene in memoria quando `main` ha una variabile `valore = 15` e chiama `tenta_raddoppio(valore)`:

```text
main:                    tenta_raddoppio:
+------------+           +------------+
| valore: 15 | --copia-> | x: 15      |
+------------+           +------------+
                             | x = x * 2;
                         +------------+
                         | x: 30      |  (valore in main resta 15)
                         +------------+
```

Alla fine di `tenta_raddoppio`, la copia `x` scompare e `valore` dentro `main` vale ancora `15`. Se vuoi aggiornare una variabile del chiamante usando una funzione, con gli strumenti che conosci finora la strada corretta è restituire il nuovo valore tramite `return` e riassegnarlo nel chiamante (`valore = raddoppia(valore);`). Quando invece servirà davvero modificare una o più variabili del chiamante direttamente dall'interno di una funzione, userai i puntatori (lo vedremo nel capitolo 10).

Un dettaglio sottile ma molto importante riguarda la valutazione degli argomenti quando una funzione ne riceve più d'uno. Lo standard C23 lascia l'ordine di valutazione degli argomenti come **comportamento non specificato**: in una chiamata come `f(g(), h())`, un compilatore può eseguire prima `g()` e poi `h()`, mentre un altro può fare il contrario, senza doverlo documentare. Finché gli argomenti non interferiscono tra loro, questo non crea alcun problema. Se però modifichi una variabile in un argomento e la leggi (o la modifichi di nuovo) in un altro argomento della stessa chiamata, entri nel **comportamento indefinito**:

<!-- cod: id=7.2-c tipo=frammento -->
```c
// ERRORE: comportamento indefinito! Non scrivere mai così.
int n = 5;
int risultato = somma(n, ++n);
```

Non è detto quale argomento venga valutato per primo, e il linguaggio non garantisce alcun risultato sensato. La regola pratica è semplice: esegui prima l'incremento in un'istruzione separata (`++n;`) e passa alla funzione argomenti privi di effetti collaterali incrociati.

Infine, in questo capitolo aggiungiamo alla tua cassetta degli attrezzi tre funzioni della libreria standard dichiarate in `<stdlib.h>` per calcolare il valore assoluto di numeri interi:

- `int abs(int j);` per gli interi di tipo `int`;
- `long int labs(long int j);` per gli interi di tipo `long`;
- `long long int llabs(long long int j);` per gli interi di tipo `long long`.

Ricorda di non confonderle con `fabs` di `<math.h>`, che lavora su `double`: passare un `double` a `abs` lo troncherebbe a `int` perdendo la parte decimale, mentre usare `abs` su un `long` o `long long` che supera `INT_MAX` provocherebbe un troncamento scorretto. Scegli sempre la variante corrispondente al tipo dell'argomento. Inoltre, come vedrai nell'approfondimento, chiamare `abs(INT_MIN)`, `labs(LONG_MIN)` o `llabs(LLONG_MIN)` provoca **comportamento indefinito** perché il valore assoluto del minimo intero con segno non è rappresentabile nel tipo di ritorno.

### Esempio guidato

Il programma seguente dichiara in cima i prototipi di due funzioni e ne scrive le definizioni dopo `main`. Confronta `tenta_raddoppio` (che modifica solo la propria copia locale del parametro) con `raddoppia` (che restituisce il nuovo valore), poi usa `abs` e `labs` per calcolare gli scarti di quota tra coppie di altitudini.

<!-- cod: id=7.2-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

void tenta_raddoppio(int x);
int raddoppia(int x);

int main(void) {
    int quota = 15;

    tenta_raddoppio(quota);
    printf("Dopo tenta_raddoppio: quota = %d\n", quota);

    quota = raddoppia(quota);
    printf("Dopo quota = raddoppia(quota): quota = %d\n", quota);

    int passo_a = 1200;
    int passo_b = 1850;
    int scarto_breve = abs(passo_a - passo_b);

    long vetta_a = -400L;
    long vetta_b = 2900L;
    long scarto_ampio = labs(vetta_a - vetta_b);

    printf("Scarto int: %d m\n", scarto_breve);
    printf("Scarto long: %ld m\n", scarto_ampio);
    return 0;
}

void tenta_raddoppio(int x) {
    x = x * 2;
    printf("Dentro tenta_raddoppio: x = %d\n", x);
}

int raddoppia(int x) {
    return x * 2;
}
```

```output
Dentro tenta_raddoppio: x = 30
Dopo tenta_raddoppio: quota = 15
Dopo quota = raddoppia(quota): quota = 30
Scarto int: 650 m
Scarto long: 3300 m
```

Osserva i punti chiave dell'esempio:

- I due prototipi prima di `main` informano il compilatore delle firme esatte delle funzioni, permettendo di collocare `main` in testa al file.
- Dentro `tenta_raddoppio`, `x` passa davvero da `15` a `30`, come dimostra la prima riga stampata. Tuttavia `x` è una copia: al rientro in `main`, `quota` vale ancora `15`.
- Con `quota = raddoppia(quota);` il valore calcolato dalla funzione torna al chiamante tramite `return` e aggiorna esplicitamente `quota` a `30`.
- Per `passo_a - passo_b` (`-650`, di tipo `int`) si usa `abs`, mentre per `vetta_a - vetta_b` (`-3300L`, di tipo `long`) si usa `labs`, evitando conversioni rischiose verso `int`.

> **Approfondimento — Perché `abs(INT_MIN)` è comportamento indefinito**
> In C23 gli interi con segno sono rappresentati in complemento a due (lo vedremo nel dettaglio nel capitolo 13). In questa rappresentazione l'intervallo è asimmetrico: per un `int` a 32 bit, `INT_MIN` vale `-2'147'483'648` mentre `INT_MAX` vale `2'147'483'647`. Il valore assoluto matematico di `INT_MIN` sarebbe `+2'147'483'648`, che supera `INT_MAX` di una unità e non entra in un `int`. Lo stesso vale per `labs(LONG_MIN)` e `llabs(LLONG_MIN)`. Poiché il risultato provoca overflow su un intero con segno, lo standard dichiara la chiamata **comportamento indefinito**. Prima di invocare `abs`, `labs` o `llabs` su dati esterni, verifica sempre che l'argomento rientri in un intervallo sicuro (oppure controlla esplicitamente `x != INT_MIN`).

### Esercizio 7.2 — Percorso di un rover con prototipi, passaggio per valore e `abs`/`labs`/`llabs`

**Descrizione**

Scrivi un programma C che includa `<stdio.h>` e `<stdlib.h>`, dichiari prima di `main` i prototipi di quattro funzioni e ne collochi le definizioni dopo `main`:

- `long distanza_manhattan(long x1, long y1, long x2, long y2)`: restituisce `labs(x2 - x1) + labs(y2 - y1)`;
- `int sbilanciamento_assi(long x1, long y1, long x2, long y2)`: restituisce `abs((int)(labs(x2 - x1) - labs(y2 - y1)))`;
- `long long differenza_energia(long long e1, long long e2)`: restituisce `llabs(e1 - e2)`;
- `int applica_margine(int soglia)`: incrementa il proprio parametro di `10` e lo restituisce, mostrando che il passaggio per valore non modifica la variabile del chiamante.

In `main` leggi una riga da `stdin` con cinque interi `x1 y1 x2 y2 soglia` (i primi quattro `long` tra `-1'000'000` e `1'000'000`, `soglia` `int` tra `0` e `10'000'000`), validando il formato esatto (`"%ld %ld %ld %ld %d %c"` == `5`) e gli intervalli; in caso di errore stampa un messaggio su `stderr` e restituisci `EXIT_FAILURE`. Calcola `e1 = (long long)x1 * x1 + (long long)y1 * y1` ed `e2 = (long long)x2 * x2 + (long long)y2 * y2`, invoca le quattro funzioni e stampa distanza di Manhattan, sbilanciamento, differenza di energia, `soglia` originale in `main` (invariata), `soglia_estesa` restituita ed esito del percorso (`Entro soglia estesa` se `distanza <= soglia_estesa`, `Oltre soglia estesa` altrimenti), esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- prototipi dichiarati prima di `main` e definizioni dopo `main`
- passaggio per valore dei parametri
- funzioni `abs`, `labs` e `llabs` di `<stdlib.h>`
- scelta di tipi adeguati per prevenire l'overflow

**Domande guida**

1. Perché devi dichiarare i prototipi prima di `main` se scegli di scrivere le definizioni delle funzioni dopo `main`?
2. Dopo aver chiamato `applica_margine(soglia)`, perché la variabile `soglia` dentro `main` conserva ancora il suo valore originale?
3. Quale differenza esiste tra `abs`, `labs` e `llabs` e quale tipo di argomento accetta ciascuna?
4. Perché i limiti imposti sulle coordinate impediscono di incorrere nel comportamento indefinito di `abs(INT_MIN)`, `labs(LONG_MIN)` e `llabs(LLONG_MIN)`?

**Esempio di esecuzione**

```input
-3 4 5 -2 10
```

```output
Distanza Manhattan: 14
Sbilanciamento assi: 2
Differenza energia: 4
Soglia originale in main: 10
Soglia estesa restituita: 20
Esito: Entro soglia estesa
```

## 7.3 Visibilità, durata di vita e `static` locale

Quando un programma contiene più funzioni, ciascuna con i propri parametri e le proprie variabili, diventa essenziale sapere *dove* un nome può essere usato e *per quanto tempo* la memoria associata a una variabile resta valida. Nel capitolo 6 hai già incontrato un primo esempio di questo principio: una variabile dichiarata dentro un ciclo `for` o dentro il corpo di un `do-while` non può essere usata fuori dalle graffe. In questa sotto-sezione diamo a questi comportamenti regole precise.

Occorre distinguere due concetti diversi, che spesso si confondono ma governano aspetti separati del linguaggio:

- La **visibilità** (*scope*) è la regione del codice sorgente all'interno della quale un identificatore può essere utilizzato. È una proprietà del testo del programma, verificata dal compilatore.
- La **durata di vita** (*storage duration*) è l'intervallo di tempo durante l'esecuzione del programma in cui la memoria di un oggetto esiste ed è valida. È una proprietà dell'esecuzione.

In C, i parametri di una funzione e le variabili dichiarate all'interno di un blocco `{ ... }` (il corpo di una funzione, di un `if`, di un ciclo o di un semplice blocco annidato) hanno **visibilità di blocco**: esistono dal punto in cui sono dichiarati fino alla graffa di chiusura del blocco che li contiene. Anche il contatore dichiarato nell'intestazione di un ciclo `for (int i = 0; ...)` è visibile soltanto dentro quel ciclo. Due funzioni distinte possono quindi avere entrambe una variabile chiamata `totale` o un parametro chiamato `n` senza interferire in alcun modo tra loro.

I prototipi di funzione e le costanti `constexpr` dichiarate fuori da qualsiasi funzione hanno invece **visibilità di file**: sono visibili dal punto della dichiarazione fino alla fine del file sorgente. È tecnicamente possibile dichiarare fuori dalle funzioni anche variabili modificabili (dette *variabili globali mutabili*), ma nella buona programmazione C si evitano il più possibile: qualsiasi funzione potrebbe cambiarle in silenzio, rendendo difficile capire come evolve il programma. Le costanti `constexpr` a livello di file, invece, sono sicure perché non possono essere modificate.

Che cosa succede se dentro un blocco interno dichiari una variabile con lo stesso nome di una variabile del blocco esterno? In C è consentito, ma la dichiarazione interna **nasconde** quella esterna per tutta la durata del blocco interno: questo fenomeno si chiama *occultamento* (*shadowing*).

<!-- cod: id=7.3-b tipo=frammento -->
```c
int livello = 1;
{
    int livello = 99;  // nasconde la variabile esterna in questo blocco
    printf("%d\n", livello);  // stampa 99
}
printf("%d\n", livello);      // stampa 1: la variabile esterna è intatta
```

Anche se il linguaggio definisce con precisione questo comportamento, l'occultamento è una fonte frequente di errori di lettura: chi guarda il blocco interno può credere di stare modificando la variabile esterna. Scegli sempre nomi distinti per variabili in blocchi annidati.

Passiamo ora alla **durata di vita**. Per impostazione predefinita, i parametri e le variabili locali hanno **durata di vita automatica**: la loro memoria viene creata automaticamente a ogni ingresso nel blocco (o a ogni chiamata della funzione) e distrutta automaticamente all'uscita. Una variabile automatica *non viene azzerata implicitamente*: se la dichiari senza inizializzarla contiene bit indeterminati rimasti in memoria, e leggerne il valore provoca **comportamento indefinito**. Inoltre, quando la funzione viene chiamata una seconda volta, la variabile nasce da zero e non conserva nulla della chiamata precedente.

In certi casi, però, una funzione deve ricordare un'informazione tra una chiamata e la successiva — per esempio un numeratore progressivo per i biglietti di uno sportello — senza esporre quella variabile al resto del programma. Per ottenere questo comportamento si antepone la parola chiave `static` alla dichiarazione locale:

<!-- cod: id=7.3-c tipo=frammento -->
```c
int genera_ticket(void) {
    static int prossimo = 1;
    int attuale = prossimo;
    ++prossimo;
    return attuale;
}
```

La parola chiave `static` su una variabile locale lascia invariata la visibilità ma cambia completamente la durata di vita:

- La **visibilità** resta limitata al blocco della funzione: né `main` né altre funzioni possono leggere o modificare `prossimo`.
- La **durata di vita** diventa **statica**: l'oggetto esiste per l'intera esecuzione del programma, dall'avvio fino alla terminazione.
- L'inizializzazione avviene **una sola volta** prima dell'avvio del programma (non a ogni chiamata) e deve usare un'espressione costante (se l'inizializzatore viene omesso, lo standard C23 garantisce l'inizializzazione implicita a zero).
- Tra una chiamata e la successiva la variabile conserva il proprio valore.

Secondo lo standard C23, visibilità di blocco, occultamento di identificatori esterni, durata di vita automatica e durata di vita statica con inizializzazione costante unica sono tutti comportamenti completamente definiti; leggere una variabile automatica non inizializzata è invece comportamento indefinito.

Le variabili locali `static` sono utili per contatori progressivi o statistiche cumulative incapsulate in una singola funzione, ma vanno usate con giudizio perché introducono uno **stato interno nascosto**: la stessa chiamata `genera_ticket()` restituisce valori diversi a seconda di quante volte è stata invocata in precedenza, e non puoi azzerare o duplicare il contatore per due sportelli distinti senza aggiungere logica apposita (nei capitoli 10 e 12 vedrai come gestire più stati indipendenti in modo pulito con puntatori e `struct`).

> **Se vieni da Python** — In Python non esistono variabili locali `static` dentro una funzione: per conservare stato tra chiamate si usano chiusure, oggetti o variabili di modulo. In C una variabile locale `static` mantiene il proprio valore tra chiamate successive restando completamente invisibile al di fuori della funzione.

### Esempio guidato

Il programma seguente simula uno sportello che emette biglietti numerati. Confronta `genera_ticket`, che usa una variabile locale `static`, con `contatore_automatico`, che usa una normale variabile automatica; include inoltre un blocco annidato in `main` per mostrare la visibilità di blocco.

<!-- cod: id=7.3-a tipo=programma -->
```c
#include <stdio.h>

int genera_ticket(void);
int contatore_automatico(void);

int main(void) {
    for (int i = 1; i <= 3; ++i) {
        printf("Chiamata %d -> ticket static=%d, automatico=%d\n",
               i, genera_ticket(), contatore_automatico());
    }

    int sportello = 2;
    {
        int codice_turno = sportello * 100;
        printf("Dentro il blocco: sportello=%d, codice_turno=%d\n",
               sportello, codice_turno);
    }
    printf("Fuori dal blocco: sportello=%d\n", sportello);
    return 0;
}

int genera_ticket(void) {
    static int prossimo = 1;
    int attuale = prossimo;
    ++prossimo;
    return attuale;
}

int contatore_automatico(void) {
    int valore = 0;
    ++valore;
    return valore;
}
```

```output
Chiamata 1 -> ticket static=1, automatico=1
Chiamata 2 -> ticket static=2, automatico=1
Chiamata 3 -> ticket static=3, automatico=1
Dentro il blocco: sportello=2, codice_turno=200
Fuori dal blocco: sportello=2
```

Osserva che cosa mette in luce l'esecuzione:

- In `genera_ticket`, l'inizializzazione `static int prossimo = 1;` viene eseguita una sola volta. Alla prima chiamata la funzione restituisce `1` e porta `prossimo` a `2`; alla seconda restituisce `2` e lo porta a `3`; alla terza restituisce `3`.
- In `contatore_automatico`, la variabile `valore` ha durata di vita automatica: viene ricreata e re-inizializzata a `0` a ogni chiamata, quindi la funzione restituisce sempre `1`.
- Nel blocco annidato dentro `main`, `sportello` (dichiarata nel blocco esterno) è visibile e utilizzabile per calcolare `codice_turno`. Alla graffa di chiusura `codice_turno` cessa di esistere e non è più visibile: tentare di stamparla nella riga successiva produrrebbe un errore di compilazione.

> **Approfondimento — `static` locale contro variabili globali mutabili**
> Sia una variabile locale `static` sia una variabile globale mutabile (dichiarata fuori dalle funzioni) hanno durata di vita statica: entrambe vivono per tutta l'esecuzione del programma. La differenza decisiva è la **visibilità**: una variabile globale mutabile può essere modificata da qualunque funzione del file, creando dipendenze nascoste difficili da seguire; una variabile locale `static` è invece accessibile soltanto dentro la funzione che la dichiara, limitando i punti in cui lo stato può cambiare. Nel capitolo 19 vedrai un secondo uso della parola chiave `static` a livello di file, legato alla suddivisione di un programma in più file sorgenti.

### Esercizio 7.3 — Registratore di consumi elettrici con variabili `static` locali

**Descrizione**

Scrivi un programma C che legga da `stdin` una sequenza di lunghezza arbitraria di consumi elettrici in wattora (un `int` per riga compreso tra `0` e `100'000` inclusi) fino alla fine dell'input. Se una riga ha formato errato (`"%d %c"` != `1`) o un valore fuori intervallo, stampa un messaggio su `stderr` e restituisci `EXIT_FAILURE`. Gestisci lo stato cumulativo esclusivamente tramite variabili locali `static` all'interno di tre funzioni con prototipo prima di `main`:

- `long aggiorna_totale_wh(int consumo)`: mantiene il totale cumulato e lo restituisce;
- `int aggiorna_picco_wh(int consumo)`: mantiene il massimo finora osservato e lo restituisce;
- `int conta_oltre_soglia(int consumo, int soglia)`: incrementa il proprio contatore `static` ogni volta che `consumo > soglia` e restituisce il conteggio aggiornato.

In `main`, usa `constexpr int SOGLIA_WH = 500;` e per ogni ciclo stampa `Ciclo N: consumo=X Wh, cumulato=T Wh, picco=P Wh`. Al termine dello stream, se non è stato letto alcun ciclo stampa `Nessun ciclo registrato.`; altrimenti stampa cicli totali, consumo totale, picco massimo e cicli sopra `500` Wh esattamente come nell'esempio di esecuzione, restituendo `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- visibilità di blocco e durata di vita statica
- variabili locali `static` inizializzate una sola volta
- separazione dello stato interno tra funzioni distinte
- gestione del caso limite di input vuoto

**Domande guida**

1. Che cosa succederebbe al totale cumulato se la variabile dentro `aggiorna_totale_wh` non fosse dichiarata `static`?
2. Perché le variabili `static` dichiarate dentro le tre funzioni non possono essere lette o modificate direttamente da `main`?
3. Come puoi inizializzare la variabile `static` del picco affinché funzioni correttamente anche se tutti i consumi valessero `0`?
4. Perché in `main` conviene comunque salvare l'ultimo valore restituito da ciascuna funzione per poter stampare il riepilogo finale dopo la fine del ciclo?

**Esempio di esecuzione**

```input
320
640
480
510
```

```output
Ciclo 1: consumo=320 Wh, cumulato=320 Wh, picco=320 Wh
Ciclo 2: consumo=640 Wh, cumulato=960 Wh, picco=640 Wh
Ciclo 3: consumo=480 Wh, cumulato=1440 Wh, picco=640 Wh
Ciclo 4: consumo=510 Wh, cumulato=1950 Wh, picco=640 Wh
Cicli totali: 4
Consumo totale: 1950 Wh
Picco massimo: 640 Wh
Cicli sopra 500 Wh: 2
```

## 7.4 Funzioni ricorsive

Alcuni problemi hanno una forma naturale che si ripete su scala più piccola. Pensa al fattoriale di un numero intero non negativo $n$: per definizione $0! = 1$, mentre per ogni $n > 0$ vale $n! = n \cdot (n - 1)!$. Per calcolare $4!$ ti basta sapere quanto vale $3!$ e moltiplicarlo per $4$; per calcolare $3!$ ti basta $2!$, e così via fino a $0!$, che conosci direttamente.

In C una funzione può tradurre questa idea in modo diretto richiamando se stessa. Questa tecnica si chiama **ricorsione** (*recursion*): una tecnica in cui una funzione richiama se stessa su un sottoproblema più piccolo fino a raggiungere un caso base.

Affinché una funzione ricorsiva sia corretta e termini sempre, deve contenere due elementi indispensabili:

1. Almeno un **caso base** (*base case*): una condizione che termina la funzione ricorsiva restituendo un risultato immediato senza ulteriori chiamate ricorsive. Per il fattoriale il caso base è `n <= 1`, che restituisce `1`.
2. Un **passo ricorsivo** (*recursive step*): la chiamata della funzione su un argomento *strettamente più vicino* al caso base, combinando il risultato restituito per costruire la risposta del problema corrente. Per il fattoriale è `n * fattoriale(n - 1)`.

Come fa il programma a non confondere il valore di `n` delle diverse chiamate attive nello stesso momento? Ogni volta che una funzione viene chiamata — anche ricorsivamente — il programma crea un nuovo spazio riservato in cima alla **pila delle chiamate** (lo vedremo nel dettaglio nel capitolo 11), con copie completamente indipendenti dei parametri e delle variabili locali automatiche. Le chiamate scendono una sopra l'altra fino al caso base, poi risalgono una alla volta restituendo i risultati:

```text
Discesa delle chiamate:                Risalita dei risultati:
fattoriale(4)                          4 * 6 = 24  (torna a main)
  -> 4 * fattoriale(3)                 ^
       -> 3 * fattoriale(2)            3 * 2 = 6
            -> 2 * fattoriale(1)       ^
                 -> caso base: 1  ---> 2 * 1 = 2
```

Osserva lo schema: mentre `fattoriale(1)` sta eseguendo, le chiamate `fattoriale(2)`, `fattoriale(3)` e `fattoriale(4)` sono ancora in attesa sulla pila delle chiamate, ciascuna con la propria copia separata di `n`. Solo quando `fattoriale(1)` restituisce `1`, la chiamata `fattoriale(2)` può completare `2 * 1`, liberare il proprio spazio e consegnare `2` a `fattoriale(3)`, e così via fino a `main`.

Lo standard C23 definisce con precisione la ricorsione e garantisce l'indipendenza delle variabili automatiche di ciascuna invocazione. Esistono però due errori critici da conoscere bene:

- **Caso base assente o mai raggiunto (ricorsione infinita)**: se dimentichi il caso base, oppure se il passo ricorsivo non riduce strettamente il problema verso il caso base (per esempio chiamando `fattoriale(n)` invece di `fattoriale(n - 1)`, o passando un numero negativo a una funzione che controlla solo `n == 0`), le chiamate continuano ad accumularsi fino a esaurire la memoria disponibile per la pila delle chiamate. In C questo esaurimento provoca **comportamento indefinito** (in genere il programma si arresta bruscamente).
- **Ricorsione esponenziale ingenua**: anche con un caso base corretto, se ogni chiamata genera due o più chiamate ricorsive che ricalcolano più volte gli stessi sottoproblemi, il numero di chiamate esplode esponenzialmente, come vedrai nell'approfondimento su Fibonacci.

Quando conviene allora usare la ricorsione rispetto a un ciclo iterativo del capitolo 6? Un ciclo occupa memoria costante e non ha il costo delle chiamate di funzione ripetute: per compiti lineari come il fattoriale o il massimo comune divisore l'iterazione è spesso altrettanto semplice e più leggera in memoria. La ricorsione diventa invece uno strumento prezioso quando il problema stesso ha una forma ramificata o gerarchica (come alberi, espressioni matematiche o scomposizioni *divide et impera*, che incontrerai dal capitolo 17 in poi) oppure quando la risalita della pila delle chiamate permette di produrre risultati in ordine inverso senza memoria aggiuntiva esplicita.

> **Se vieni da Python** — In Python una ricorsione troppo profonda viene intercettata dall'interprete e solleva un'eccezione `RecursionError` controllata. In C non esiste alcun limite gestito dal linguaggio: superare lo spazio della pila delle chiamate provoca comportamento indefinito e l'arresto immediato del programma.

### Esempio guidato

Il programma seguente mostra due funzioni ricorsive: `fattoriale`, che calcola $n!$ in un `long long` (esatto fino a $n = 20$), e `mcd_ricorsivo`, che applica l'algoritmo di Euclide sfruttando il fatto che $\text{MCD}(a, 0) = a$ (caso base) e $\text{MCD}(a, b) = \text{MCD}(b, a \bmod b)$ (passo ricorsivo).

<!-- cod: id=7.4-a tipo=programma -->
```c
#include <stdio.h>

long long fattoriale(int n);
int mcd_ricorsivo(int a, int b);

int main(void) {
    printf("4! = %lld\n", fattoriale(4));
    printf("10! = %lld\n", fattoriale(10));
    printf("MCD(48, 18) = %d\n", mcd_ricorsivo(48, 18));
    printf("MCD(105, 42) = %d\n", mcd_ricorsivo(105, 42));
    return 0;
}

long long fattoriale(int n) {
    if (n <= 1) {
        return 1;
    }
    return (long long)n * fattoriale(n - 1);
}

int mcd_ricorsivo(int a, int b) {
    if (b == 0) {
        return a;
    }
    return mcd_ricorsivo(b, a % b);
}
```

```output
4! = 24
10! = 3628800
MCD(48, 18) = 6
MCD(105, 42) = 21
```

Analizziamo come funzionano le due funzioni:

- In `fattoriale`, il caso base `if (n <= 1) { return 1; }` gestisce sia `0!` sia `1!` senza ulteriori chiamate. Nel passo ricorsivo il cast `(long long)n` garantisce che la moltiplicazione avvenga in `long long`, evitando overflow su `int` già per valori piccoli come $13!$.
- In `mcd_ricorsivo`, a ogni chiamata `a % b` è strettamente minore di `b` (per `a >= 0` e `b > 0`), quindi il secondo argomento diminuisce a ogni passo finché raggiunge il caso base `b == 0`. Per `mcd_ricorsivo(48, 18)` la sequenza delle chiamate è `(48, 18) -> (18, 12) -> (12, 6) -> (6, 0) -> 6`.
- Confronta `mcd_ricorsivo` con un ciclo `while (b != 0)` come quelli del capitolo 6: entrambe le versioni eseguono esattamente gli stessi resti, ma la versione iterativa usa memoria costante mentre quella ricorsiva apre un livello sulla pila delle chiamate per ogni resto (comunque pochissimi passi, perché il resto cala molto rapidamente).

> **Approfondimento — Perché Fibonacci ricorsivo ingenuo è lentissimo**
> La successione di Fibonacci è definita da $F(0) = 0$, $F(1) = 1$ e $F(n) = F(n - 1) + F(n - 2)$. Tradurla direttamente in una funzione ricorsiva sembra naturale, ma è un pessimo affare: per calcolare $F(5)$ la funzione chiama $F(4)$ e $F(3)$, e dentro $F(4)$ ricalcola di nuovo $F(3)$ e $F(2)$, ripetendo gli stessi sottoproblemi un numero enorme di volte. Per $n = 40$ supera già i 300 milioni di chiamate, mentre un ciclo iterativo del capitolo 6 con due variabili di stato calcola $F(40)$ in appena 40 iterazioni. Prima di scegliere la ricorsione, controlla sempre se le chiamate si sovrappongono ripetendo lo stesso lavoro.

### Esercizio 7.4 — Potenza veloce, somma delle cifre e stampa binaria con ricorsione

**Descrizione**

Scrivi un programma C che legga da `stdin` una sola riga contenente tre valori: `base` (`int` tra `-10` e `10` inclusi), `esponente` (`int` tra `0` e `15` inclusi) e `numero` (`long long` tra `0` e `1'000'000'000` inclusi). Verifica la fine dell'input, il formato esatto (`"%d %d %lld %c"` == `3`) e gli intervalli; in caso di errore stampa un messaggio su `stderr` e restituisci `EXIT_FAILURE`. Implementa tre funzioni ricorsive (senza usare cicli al loro interno) con prototipi prima di `main`:

- `long long potenza_veloce(int base, int esponente)`: con caso base `esponente == 0` che restituisce `1` (anche per `base == 0`), e passo ricorsivo che calcola una sola volta `meta = potenza_veloce(base, esponente / 2)` restituendo `meta * meta` se `esponente` è pari e `meta * meta * base` se è dispari;
- `int somma_cifre_ric(long long n)`: somma ricorsiva delle cifre decimali di `n`;
- `void stampa_binario_ric(long long n)`: stampa la rappresentazione binaria di `n >= 0` usando `putchar` durante la risalita della ricorsione, stampando `0` per `n == 0`.

Stampa i risultati esattamente come nell'esempio di esecuzione e restituisci `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- ricorsione con caso base e passo ricorsivo convergente
- dimezzamento dell'esponente nella potenza veloce
- ordine di stampa nella risalita della pila delle chiamate
- prevenzione dell'overflow tramite vincoli di ingresso e `long long`

**Domande guida**

1. Qual è il caso base di `potenza_veloce` e perché calcolare `meta` una sola volta invece di chiamare `potenza_veloce` due volte riduce drasticamente il numero di chiamate?
2. Qual è il caso base di `somma_cifre_ric` e come garantisci che `n` diminuisca strettamente a ogni chiamata?
3. Perché in `stampa_binario_ric` devi chiamare ricorsivamente la funzione su `n / 2` prima di chiamare `putchar` per il resto `n % 2`?
4. Che cosa stampa `stampa_binario_ric` quando riceve il caso limite `n = 0`?

**Esempio di esecuzione**

```input
3 5 42
```

```output
Potenza 3^5: 243
Somma cifre di 42: 6
Binario di 42: 101010
```

## 7.5 Scomporre un problema in funzioni

Conoscere la sintassi di funzioni, prototipi, passaggio per valore e ricorsione è solo metà del lavoro. L'altra metà, quella che fa davvero la differenza quando i programmi superano il centinaio di righe, è saper decidere *quali* funzioni scrivere e *come* suddividere tra loro le responsabilità.

La strategia più efficace per affrontare un problema articolato è la **progettazione dall'alto verso il basso** (*top-down*). Invece di partire subito a scrivere cicli e formule dentro `main`, inizi descrivendo i passi principali del problema come chiamate a funzioni dal nome chiaro: per esempio leggere e validare i dati, calcolare il subtotale, applicare lo sconto, calcolare l'IVA e stampare il riepilogo. Poi realizzi ciascuna funzione come un piccolo problema indipendente, dotato di una sola responsabilità precisa.

Per progettare bene ogni funzione conviene definirne prima il **contratto**, rispondendo a tre domande essenziali:

1. **Che cosa fa esattamente?** Il nome della funzione deve dirlo subito: `calcola_sconto`, `e_bisestile`, `giorni_del_mese` sono nomi autoesplicativi; nomi vaghi come `elabora` o `fai_tutto` nascondono invece lo scopo del codice.
2. **Che cosa richiede in ingresso (precondizioni)?** Quali tipi accetta e quali vincoli devono rispettare gli argomenti (per esempio `quantita >= 0` oppure `mese` compreso tra `1` e `12`)? Stabilire chiaramente chi controlla la validità evita controlli duplicati o mancanti.
3. **Che cosa garantisce in uscita?** Quale valore restituisce nei casi normali e, se previsto, nei casi limite (per esempio `0` o `false` per un ingresso fuori dominio)?

Un principio di progettazione particolarmente utile è **separare tre ruoli distinti**:

- **Validazione dell'input**: leggere da `stdin`, verificare fine dell'input, formato e intervalli, e segnalare errori su `stderr`. In programmi di media grandezza questo lavoro sta in `main` o in funzioni dedicate alla lettura.
- **Funzioni di calcolo pure**: ricevono dati già validati come parametri e restituiscono un risultato calcolato, *senza* leggere da `stdin`, *senza* stampare su `stdout` e *senza* dipendere da stato esterno nascosto. A parità di argomenti producono sempre lo stesso risultato.
- **Presentazione dell'output**: funzioni `void` che ricevono i risultati già calcolati e li formattano con `printf`.

Quando le funzioni di base sono piccole e pure, diventa immediato costruire funzioni di livello superiore per **composizione**: una funzione più complessa richiama funzioni elementari già scritte e verificate. Pensa a un calendario: una volta verificata `e_bisestile(anno)`, puoi usarla dentro `giorni_del_mese(mese, anno)`, che a sua volta semplifica `data_valida(g, m, a)` e `giorno_dell_anno(g, m, a)`. Ogni livello aggiunge un solo concetto nuovo, senza mai ripetere la logica dei livelli sottostanti.

Come capisci, mentre scrivi o rileggi un programma, che una funzione andrebbe spezzata in due o più funzioni più piccole? Osserva questi tre segnali pratici:

- **Lunghezza e annidamento eccessivi**: se una funzione non entra in una schermata o accumula molti livelli di `if` e cicli annidati, probabilmente sta facendo più cose insieme.
- **Compiti mescolati**: se una funzione che dovrebbe calcolare un importo contiene anche `fgets` o `printf`, sta mescolando calcolo e I/O e non potrà essere riutilizzata altrove.
- **Logica ripetuta**: se ti accorgi di aver copiato lo stesso blocco di cinque o dieci righe cambiando solo un paio di variabili, quel blocco merita di diventare una funzione con parametri.

### Esempio guidato

Il programma seguente calcola il conto di un ordine di cancelleria scomponendo il lavoro in quattro funzioni brevi e coordinate da `main`: `calcola_subtotale`, `calcola_sconto` (10% di sconto da 50 euro in su), `calcola_iva` (aliquota del 22%) e `stampa_riepilogo`, con tutti i prototipi raccolti in testa al file.

<!-- cod: id=7.5-a tipo=programma -->
```c
#include <stdio.h>

double calcola_subtotale(int quantita, double prezzo_unitario);
double calcola_sconto(double subtotale);
double calcola_iva(double imponibile);
void stampa_riepilogo(double subtotale, double sconto, double iva, double totale);

int main(void) {
    int quaderni = 25;
    double prezzo_unitario = 2.40;

    double subtotale = calcola_subtotale(quaderni, prezzo_unitario);
    double sconto = calcola_sconto(subtotale);
    double imponibile = subtotale - sconto;
    double iva = calcola_iva(imponibile);
    double totale = imponibile + iva;

    stampa_riepilogo(subtotale, sconto, iva, totale);
    return 0;
}

double calcola_subtotale(int quantita, double prezzo_unitario) {
    return quantita * prezzo_unitario;
}

double calcola_sconto(double subtotale) {
    constexpr double SOGLIA_SCONTO = 50.0;
    constexpr double ALIQUOTA_SCONTO = 0.10;
    if (subtotale >= SOGLIA_SCONTO) {
        return subtotale * ALIQUOTA_SCONTO;
    }
    return 0.0;
}

double calcola_iva(double imponibile) {
    constexpr double ALIQUOTA_IVA = 0.22;
    return imponibile * ALIQUOTA_IVA;
}

void stampa_riepilogo(double subtotale, double sconto, double iva, double totale) {
    printf("Subtotale: %6.2f euro\n", subtotale);
    printf("Sconto:    %6.2f euro\n", sconto);
    printf("IVA (22%%): %6.2f euro\n", iva);
    printf("Totale:    %6.2f euro\n", totale);
}
```

```output
Subtotale:  60.00 euro
Sconto:      6.00 euro
IVA (22%):  11.88 euro
Totale:     65.88 euro
```

Osserva come appare `main`: si legge quasi come una frase in italiano. In sei righe vedi l'intero flusso del calcolo senza alcun dettaglio sulle aliquote, sulle soglie di sconto o sui formati di `printf`. Le tre funzioni di calcolo sono completamente pure (nessun `printf`, nessuna lettura da tastiera), mentre `stampa_riepilogo` si occupa soltanto della presentazione. Se domani cambiasse l'aliquota IVA o la soglia di sconto, sapresti immediatamente in quale funzione intervenire senza toccare il resto del programma.

> **Approfondimento — Perché separare calcolo e input/output paga nel tempo**
> Tenere le funzioni di calcolo prive di `fgets` e `printf` offre due vantaggi concreti. Il primo è la **riutilizzabilità**: la stessa funzione `calcola_iva` funziona identica sia che i dati arrivino da tastiera, sia che in futuro arrivino da un file o da un'altra funzione. Il secondo è la **verificabilità**: una funzione pura può essere messa alla prova su decine di casi limite (come `0.0`, `49.99` e `50.0` per lo sconto) confrontando semplicemente il valore restituito con quello atteso, senza dover simulare input da tastiera né analizzare testo stampato.

### Esercizio 7.5 — Validatore di calendario e distanza tra due date

**Descrizione**

Scrivi un programma C che legga da `stdin` due righe, ciascuna contenente una data nel formato `giorno mese anno` (tre `int` separati da spazi, con `anno` compreso tra `1900` e `2100` inclusi). Scomponi il programma in cinque funzioni pure e coese con prototipi prima di `main`:

- `bool e_bisestile(int anno)`: un anno è bisestile se è divisibile per `400`, oppure se è divisibile per `4` e non per `100`;
- `int giorni_del_mese(int mese, int anno)`: usa `switch` ed `e_bisestile` per febbraio; restituisce `0` se il mese non è in `1..12`;
- `bool data_valida(int g, int m, int a)`: controlla `anno` in `1900..2100`, `mese` in `1..12` e `giorno` in `1..giorni_del_mese(m, a)`;
- `int giorno_dell_anno(int g, int m, int a)`: restituisce il numero d'ordine del giorno dall'inizio dell'anno, da `1` a `365` (o `366` negli anni bisestili);
- `long giorni_dal_1900(int g, int m, int a)`: somma i giorni degli anni interi `1900..a-1` più `giorno_dell_anno`.

In `main` verifica fine dell'input, formato esatto (`"%d %d %d %c"` == `3`) e validità di ciascuna data tramite `data_valida` (in caso di errore scrivi su `stderr` e restituisci `EXIT_FAILURE`). Altrimenti stampa per entrambe le date la data, il giorno dell'anno e l'indicazione di anno bisestile (`1` o `0`), seguiti dalla distanza assoluta in giorni calcolata con `labs`, esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- scomposizione top-down in funzioni piccole con una sola responsabilità
- composizione di funzioni (`giorni_dal_1900` richiama `giorno_dell_anno` ed `e_bisestile`)
- separazione tra validazione/calcolo puro e I/O in `main`
- regola completa degli anni bisestili (multipli di 4, 100 e 400)

**Domande guida**

1. In quale ordine di dipendenza si richiamano le cinque funzioni del calendario, dalla più elementare alla più composta?
2. Perché conviene mantenere `data_valida` e `giorni_del_mese` completamente prive di chiamate a `fgets` o `printf`?
3. Come si comporta la regola degli anni bisestili sui casi secolari come `1900` e `2000`?
4. In che modo convertire ogni data nel numero di giorni trascorsi dal 1900 semplifica il calcolo della distanza rispetto a confrontare direttamente giorni, mesi e anni?

**Esempio di esecuzione**

```input
28 2 2024
1 3 2024
```

```output
Data 1: 28/2/2024 (giorno 59, bisestile=1)
Data 2: 1/3/2024 (giorno 61, bisestile=1)
Distanza: 2 giorni
```

## Riepilogo

- Una **funzione** racchiude un compito ben definito dietro un nome, una lista di **parametri** con i rispettivi tipi (oppure `void` se non accetta parametri) e un tipo di ritorno (oppure `void` se non restituisce valori). Gli **argomenti** sono le espressioni passate alla chiamata.
- Ogni funzione va dichiarata prima della sua prima chiamata tramite definizione completa o **prototipo**, con firma perfettamente coerente con la definizione. Alla chiamata gli argomenti subiscono conversione implicita verso i tipi dei parametri.
- Il C usa sempre il **passaggio per valore**: la funzione riceve una copia di ciascun argomento e modificare un parametro non altera mai la variabile del chiamante (per modificare variabili del chiamante useremo i puntatori nel capitolo 10). L'ordine di valutazione degli argomenti è comportamento non specificato.
- Le funzioni `abs`, `labs` e `llabs` di `<stdlib.h>` calcolano il valore assoluto di `int`, `long` e `long long`, ma chiamarle su `INT_MIN`, `LONG_MIN` o `LLONG_MIN` provoca comportamento indefinito.
- La **visibilità** stabilisce dove un nome può essere usato (visibilità di blocco per variabili locali e parametri, visibilità di file per prototipi e costanti `constexpr`); la **durata di vita** stabilisce per quanto tempo esiste la memoria dell'oggetto (automatica per le variabili locali normali, statica per l'intera esecuzione nel caso di `static` locale).
- Una funzione che usa la **ricorsione** richiama se stessa su un sottoproblema più piccolo: richiede sempre almeno un **caso base** e un passo ricorsivo strettamente convergente; ogni invocazione attiva dispone di copie indipendenti dei propri parametri e delle variabili automatiche.
- Scomporre un problema dall'alto verso il basso in funzioni brevi, pure e con una sola responsabilità, separando calcolo, validazione e I/O, rende i programmi più leggibili, riutilizzabili e facili da verificare.

## Errori comuni

- **Aspettarsi che modificare un parametro dentro una funzione aggiorni la variabile del chiamante**: in C il passaggio è sempre per valore; per aggiornare una variabile del chiamante restituisci il nuovo valore con `return` e riassegnalo nel chiamante (oppure usa i puntatori, lo vedremo nel capitolo 10).
- **Chiamare una funzione prima di averla definita o averne dichiarato il prototipo, oppure scrivere un prototipo con tipi diversi dalla definizione**: il compilatore segnala un identificatore non dichiarato o un conflitto di tipi; tieni tutti i prototipi allineati alle definizioni in cima al file.
- **Dimenticare un'istruzione `return` in uno dei rami di una funzione non `void`, oppure scrivere un punto e virgola indesiderato nell'intestazione della definizione**: nel primo caso usare il valore restituito provoca comportamento indefinito (e `-Wall -Werror` lo segnala); nel secondo il compilatore rifiuta la definizione per errore di sintassi.
- **Dichiarare una variabile locale senza `static` quando serve conservarne il valore tra chiamate successive, oppure inizializzare una variabile `static` con un'espressione non costante**: una variabile automatica si azzera o si ricrea a ogni chiamata, mentre una `static` accetta solo inizializzatori costanti noti a tempo di compilazione.
- **Scrivere una funzione ricorsiva senza caso base o con un passo ricorsivo che non si avvicina al caso base**: la ricorsione prosegue all'infinito fino a esaurire la memoria della pila delle chiamate, provocando comportamento indefinito.
- **Chiamare `abs`, `labs` o `llabs` rispettivamente su `INT_MIN`, `LONG_MIN` o `LLONG_MIN` senza controllo preventivo**: nella rappresentazione in complemento a due (lo vedremo nel capitolo 13) il valore assoluto del minimo intero con segno non è rappresentabile nel tipo di ritorno e la chiamata provoca comportamento indefinito.

## Prima di proseguire

- [ ] So scrivere definizioni e prototipi coerenti di funzioni con tipi di ritorno numerici, `bool` e `void`, distinguendo con precisione tra parametri e argomenti.
- [ ] So prevedere gli effetti del passaggio per valore, evitare effetti collaterali incrociati tra argomenti di una stessa chiamata e usare in sicurezza `abs`, `labs` e `llabs`.
- [ ] So distinguere visibilità di blocco e durata di vita automatica o statica, spiegando come e quando usare una variabile locale `static`.
- [ ] So scrivere una funzione ricorsiva identificando caso base e passo ricorsivo convergente, e so tracciarne discesa e risalita sulla pila delle chiamate.
- [ ] So scomporre un problema articolato in funzioni piccole, pure e componibili, separando la logica di calcolo dalla lettura dell'input e dalla stampa dell'output.
