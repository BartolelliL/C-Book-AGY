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
