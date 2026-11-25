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
