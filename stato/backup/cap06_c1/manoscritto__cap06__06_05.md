## 6.5 Cicli annidati e invarianti di ciclo

Finora ogni ciclo ha percorso una singola sequenza lineare di valori o di righe. Molti problemi reali, però, hanno due dimensioni: stampare una tabella di righe e colonne, esplorare una griglia, oppure confrontare tutte le coppie possibili di elementi. In questi casi si inserisce un ciclo *dentro* il corpo di un altro ciclo, ottenendo una coppia di **cicli annidati**.

### Come funzionano i cicli annidati

In una coppia di cicli annidati, per **ogni singola iterazione** del ciclo esterno, il ciclo interno viene eseguito completamente dall'inizio alla fine. Se il ciclo esterno compie `R` iterazioni e quello interno compie `C` iterazioni, il corpo del ciclo interno viene eseguito complessivamente `R * C` volte.

```text
Ciclo esterno (riga = 1..3)
  riga = 1  -->  colonna = 1, 2, 3, 4   (4 iterazioni interne)
  riga = 2  -->  colonna = 1, 2, 3, 4   (4 iterazioni interne)
  riga = 3  -->  colonna = 1, 2, 3, 4   (4 iterazioni interne)
                                         Totale: 3 * 4 = 12 passi
```

Due accortezze pratiche rendono i cicli annidati subito chiari e privi di errori:

1. **Scegli nomi distinti e significativi per i contatori**: usa `riga` e `colonna` (oppure `r` e `c`), evitando di riutilizzare lo stesso nome nel ciclo interno (che nasconderebbe la variabile del ciclo esterno creando grande confusione).
2. **Azzera i contatori locali al punto giusto**: se devi calcolare una statistica separata per ciascuna riga (per esempio la somma o il numero di elementi di quella riga), la variabile va inizializzata a `0` *dentro* il ciclo esterno, subito prima del ciclo interno, così da ripartire da zero a ogni nuova riga.

### Uscire in modo pulito da cicli annidati

Come hai visto nella sotto-sezione 6.4, `break` interrompe **soltanto il ciclo più interno** che la racchiude. Se stai cercando un elemento in una griglia e vuoi fermare *entrambi* i cicli appena lo trovi, un solo `break` non basta: il ciclo esterno proseguirebbe con la riga successiva.

Il modo più pulito e leggibile consiste nell'usare una variabile `bool` (per esempio `bool trovato = false;`) e controllarla nella condizione del ciclo esterno:

<!-- cod: id=6.5-b tipo=frammento -->
```c
bool trovato = false;
for (int riga = 1; riga <= n && !trovato; ++riga) {
    for (int col = 1; col <= n; ++col) {
        if (riga * col == obiettivo) {
            trovato = true;
            break;  // esce dal ciclo interno; !trovato ferma poi quello esterno
        }
    }
}
```

Appena il valore viene trovato, `trovato` diventa `true`, `break` chiude il ciclo interno e la condizione `riga <= n && !trovato` termina subito anche il ciclo esterno.

### Invarianti di ciclo: verificare correttezza e terminazione

Quando un ciclo diventa un po' più articolato, testarlo su uno o due esempi non basta a essere certi che sia corretto per *tutti* gli ingressi. Esiste uno strumento di ragionamento semplice e potentissimo: l'**invariante di ciclo** (*loop invariant*), cioè una proprietà logica che vale prima del ciclo e resta vera al termine di ogni iterazione.

Per usare un invariante di ciclo allo scopo di verificare la correttezza di un ciclo, controlli tre punti:

1. **Inizializzazione**: la proprietà è vera *prima* della prima iterazione (anche nel caso in cui il ciclo compia zero iterazioni).
2. **Mantenimento**: se la proprietà è vera all'inizio di un'iterazione ed esegui il corpo del ciclo, essa resta vera al termine dell'iterazione stessa.
3. **Conclusione**: quando la condizione di permanenza diventa falsa e il ciclo termina, combinare l'invariante con la negazione della condizione dimostra che il risultato finale è esattamente quello atteso.

Vediamo un esempio concreto. Supponi di sommare i numeri da `1` a `n` con:

<!-- cod: id=6.5-c tipo=frammento -->
```c
int somma = 0;
for (int i = 1; i <= n; ++i) {
    somma += i;
}
```

L'invariante prima di ogni controllo della condizione `i <= n` è: "`somma` contiene la somma degli interi da `1` a `i - 1`, e `1 <= i <= n + 1`".
- **Inizializzazione**: prima del ciclo `i = 1` e `somma = 0`, che è la somma dell'intervallo vuoto `1..0`. Vero.
- **Mantenimento**: se `somma` vale `1 + ... + (i - 1)` e nel corpo aggiungiamo `i` per poi incrementare `i` a `i + 1`, ora `somma` contiene esattamente la somma fino al nuovo `i - 1`. Vero.
- **Conclusione**: il ciclo si ferma quando `i <= n` è falsa, quindi `i == n + 1`. Sostituendo `i = n + 1` nell'invariante otteniamo che `somma` è la somma degli interi da `1` a `n`.

Oltre alla correttezza, occorre verificare la **terminazione**: basta individuare una quantità (per esempio `n + 1 - i`, oppure il numero di caratteri rimasti nello stream) che a ogni iterazione si avvicina strettamente al limite inferiore (o alla fine dello stream). Poiché un intero non può diminuire all'infinito restando maggiore o uguale a zero, il ciclo terminerà certamente in un numero finito di passi.

Secondo lo standard C23, la semantica esatta di tutti i cicli che terminano o che eseguono operazioni osservabili (come l'I/O su `stdin` e `stdout`) è pienamente definita; invece un ciclo infinito privo di qualsiasi effetto osservabile può avere conseguenze particolari durante le ottimizzazioni del compilatore, un motivo in più per garantire sempre la terminazione.

### Esempio guidato

Il programma seguente legge da `stdin` una dimensione `n` (tra `1` e `10`) e due interi positivi `x` e `y`, poi svolge due compiti:
1. stampa la tavola pitagorica `n x n` con due cicli `for` annidati, documentando l'invariante del ciclo esterno;
2. calcola il massimo comun divisore (MCD) di `x` e `y` tramite l'algoritmo di Euclide in un ciclo `while`, commentando invariante e terminazione.

<!-- cod: id=6.5-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char riga[128];
    int n = 0, x = 0, y = 0;
    char extra = '\0';

    if (fgets(riga, (int)sizeof(riga), stdin) == nullptr ||
        sscanf(riga, "%d %d %d %c", &n, &x, &y, &extra) != 3 ||
        n < 1 || n > 10 || x <= 0 || y <= 0) {
        fprintf(stderr, "Errore: inserisci n (1..10) e due interi positivi.\n");
        return EXIT_FAILURE;
    }

    printf("Tavola pitagorica %dx%d:\n", n, n);
    // Invariante: sono state stampate le righe 1..(r - 1) complete
    for (int r = 1; r <= n; ++r) {
        for (int c = 1; c <= n; ++c) {
            printf("%4d", r * c);
        }
        putchar('\n');
    }

    int a = x;
    int b = y;
    // Invariante: MCD(a, b) == MCD(x, y) e a > 0, b >= 0
    // Terminazione: b diminuisce strettamente (0 <= a % b < b) fino a 0
    while (b != 0) {
        int resto = a % b;
        a = b;
        b = resto;
    }
    printf("MCD(%d, %d) = %d\n", x, y, a);
    return EXIT_SUCCESS;
}
```

```input
4 84 36
```

```output
Tavola pitagorica 4x4:
   1   2   3   4
   2   4   6   8
   3   6   9  12
   4   8  12  16
MCD(84, 36) = 12
```

Osserva come funzionano gli invarianti nelle due parti:

- **Tavola pitagorica**: il ciclo esterno scorre le righe `r` da `1` a `n`; per ogni riga il ciclo interno scorre le colonne `c` da `1` a `n` stampando `r * c` su 4 caratteri (`%4d`), e subito dopo il ciclo interno `putchar('\n')` va a capo. Quando `r` raggiunge `n + 1`, l'invariante garantisce che sono state stampate tutte le righe da `1` a `n`.
- **Algoritmo di Euclide**: per una proprietà aritmetica fondamentale, `MCD(a, b)` è uguale a `MCD(b, a % b)`. Prima del ciclo `a = x` e `b = y`, quindi l'invariante `MCD(a, b) == MCD(x, y)` è vero. A ogni iterazione `a` e `b` vengono sostituiti con `b` e `a % b`, preservando l'invariante. Inoltre il resto `a % b` è sempre non negativo e strettamente minore di `b`: dunque `b` diminuisce strettamente a ogni passo e deve raggiungere `0`. All'uscita (`b == 0`), l'invariante afferma `MCD(a, 0) == MCD(x, y)`, e poiché `MCD(a, 0) = a`, la variabile `a` contiene certamente il massimo comun divisore cercato.

> **Approfondimento — Usare l'invariante prima di scrivere il codice**
> L'errore più comune nei cicli (sbagliare tra `<` e `<=`, inizializzare un contatore a `0` invece che a `1`, oppure dimenticare l'ultimo elemento) nasce quasi sempre dal fatto di scrivere prima il codice e solo dopo chiedersi che cosa rappresenti ciascuna variabile. Se invece scrivi in un commento di una riga l'invariante *prima* di scrivere il ciclo — per esempio "a questo punto `divisori` conta i divisori trovati nell'intervallo `1..(col - 1)`" — la scelta iniziale (`col = 1`, `divisori = 0`) e la condizione finale (`col <= n`) diventano obbligate e non lasciano spazio a dubbi off-by-one.

### Esercizio 6.5 — Tabella di divisibilità con cicli annidati e invarianti

**Descrizione**

Scrivi un programma C che legga da `stdin` un intero `n` compreso tra `2` e `12` inclusi (controllando fine dell'input, formato esatto con `"%d %c"` e intervallo; in caso di errore stampa su `stderr` e restituisci `EXIT_FAILURE`). Usando due cicli `for` annidati (`riga_val` da `1` a `n` e `col` da `1` a `n`), stampa una griglia `n x n` di divisibilità preceduta dall'intestazione `Tabella di divisibilita (1..n):`: ogni riga inizia con `%2d:` seguito, per ciascuna colonna `col`, da uno spazio e dal carattere `'X'` se `riga_val % col == 0` oppure `'.'` altrimenti (scritti con `putchar`). Durante il ciclo interno conta i divisori della riga; al termine del ciclo interno stampa ` | divisori: K` aggiungendo ` (primo)` se `K == 2` e aggiorna `conteggio_primi`, `max_divisori` e `miglior_numero` (in caso di parità sul numero massimo di divisori conserva il numero più piccolo). Documenta nei commenti l'invariante di ciclo sia del ciclo esterno sia del ciclo interno. Al termine stampa il conteggio dei numeri primi trovati e il numero con più divisori esattamente come nell'esempio di esecuzione, restituendo `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- cicli `for` annidati con variabili di controllo distinte
- invariante di ciclo esterno e interno
- ripristino del contatore locale a ogni iterazione del ciclo esterno
- gestione della parità nel calcolo del massimo (`>` contro `>=`)

**Domande guida**

1. Dove deve essere azzerata la variabile `divisori` affinché il conteggio di una riga non si sommi a quello delle righe precedenti?
2. Qual è l'invariante del ciclo interno al termine dell'iterazione `col`, e quale proprietà garantisce alla sua uscita quando `col` supera `n`?
3. Quale differenza produce scrivere `divisori > max_divisori` rispetto a `divisori >= max_divisori` quando due numeri hanno lo stesso numero massimo di divisori?
4. Quante volte in totale viene eseguito il corpo del ciclo interno in funzione di `n`?

**Esempio di esecuzione**

```input
6
```

```output
Tabella di divisibilita (1..6):
 1: X . . . . . | divisori: 1
 2: X X . . . . | divisori: 2 (primo)
 3: X . X . . . | divisori: 2 (primo)
 4: X X . X . . | divisori: 3
 5: X . . . X . | divisori: 2 (primo)
 6: X X X . . X | divisori: 4
Numeri primi trovati: 3
Numero con piu divisori: 6 (4 divisori)
```
