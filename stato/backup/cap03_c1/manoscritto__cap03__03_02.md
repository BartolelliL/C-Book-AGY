## 3.2 Assegnamenti composti, incremento e precedenza

Nei programmi reali capita di continuo di aggiornare una variabile a partire dal suo valore precedente: aggiungere punti a un punteggio, sottrarre un costo da un saldo, aumentare un contatore di una unità. Scrivere ogni volta `punteggio = punteggio + 10;` funziona, ma diventa ripetitivo e, con nomi di variabili lunghi, riduce la leggibilità.

### Assegnamenti composti

Il C mette a disposizione cinque **assegnamenti composti** aritmetici che combinano un'operazione e l'assegnamento in un solo operatore:

| Forma composta | Forma equivalente | Esempio (`x` iniziale = `10`) | Nuovo valore di `x` |
|---|---|---|---|
| `x += expr` | `x = x + (expr)` | `x += 5;` | `15` |
| `x -= expr` | `x = x - (expr)` | `x -= 3;` | `7` |
| `x *= expr` | `x = x * (expr)` | `x *= 2 + 1;` | `30` |
| `x /= expr` | `x = x / (expr)` | `x /= 4;` | `2` |
| `x %= expr` | `x = x % (expr)` | `x %= 3;` | `1` |

Fai attenzione alle parentesi implicite attorno a `expr`: `x *= 2 + 1;` significa `x = x * (2 + 1);`, non `x = x * 2 + 1;`. L'intera espressione a destra viene valutata prima di eseguire la moltiplicazione con `x`.

### Incremento (`++`) e decremento (`--`)

Aggiungere o sottrarre `1` a una variabile è così frequente che il C offre due operatori dedicati: `++` (incremento di `1`) e `--` (decremento di `1`). Entrambi esistono in due forme:

- **Forma prefissa** (`++x`, `--x`): prima aggiorna la variabile `x`, poi produce come risultato dell'espressione il **nuovo** valore.
- **Forma postfissa** (`x++`, `x--`): prima produce come risultato dell'espressione il valore **precedente** di `x`, poi aggiorna la variabile `x`.

Quando l'operatore compare in un'istruzione isolata — come `++contatore;` oppure `contatore++;` — l'effetto finale sulla variabile è identico, perché il valore dell'espressione non viene usato. La differenza emerge quando il risultato viene assegnato o passato altrove:

<!-- cod: id=3.2-b tipo=frammento -->
```c
int a = 5;
int b = 5;
int x = ++a;  // a diventa 6, poi x riceve 6
int y = b++;  // y riceve 5, poi b diventa 6
```

Per scrivere codice chiaro e privo di sorprese, usa `++` e `--` preferibilmente in istruzioni separate, evitando di mescolarli dentro espressioni complesse.

### Precedenza degli operatori e associatività

Come fa il compilatore a stabilire se `2 + 3 * 4` vale `14` oppure `20`? Applica la **precedenza degli operatori** (*operator precedence*): la regola che stabilisce in quale ordine gli operatori di un'espressione vengono raggruppati in assenza di parentesi. Quando due operatori hanno la stessa precedenza — come in `10 - 3 - 2` — interviene l'**associatività**, che stabilisce se raggruppare da sinistra a destra (`(10 - 3) - 2 == 5`) oppure da destra a sinistra.

Ecco la tabella sintetica per gli operatori incontrati finora, dal più alto al più basso:

| Livello | Operatori | Associatività |
|---|---|---|
| 1 (più alto) | `()` (parentesi), `x++`, `x--` (postfissi) | Da sinistra a destra |
| 2 | `+x`, `-x` (unari), `++x`, `--x` (prefissi), `sizeof` | Da destra a sinistra |
| 3 | `*`, `/`, `%` | Da sinistra a destra |
| 4 | `+`, `-` (binari) | Da sinistra a destra |
| 5 (più basso) | `=`, `+=`, `-=`, `*=`, `/=`, `%=` | Da destra a sinistra |

Nota l'associatività a destra degli assegnamenti: scrivere `a = b = 0;` significa `a = (b = 0);`, cioè prima si assegna `0` a `b` e il risultato (`0`) viene poi assegnato ad `a`. In ogni caso, le parentesi tonde `()` impongono sempre il raggruppamento che desideri: usarle quando un'espressione non è immediata da leggere è una buona abitudine che previene errori.

### Ordine di valutazione e modifiche non sequenziate

Una distinzione cruciale in C riguarda ciò che la precedenza *non* decide. La precedenza stabilisce come gli operatori si raggruppano, ma in molti casi **non** stabilisce in quale ordine vengono valutate le sotto-espressioni a tempo di esecuzione. Per esempio, nell'espressione `f1 + f2` o negli argomenti di una chiamata `printf("%d %d\n", expr1, expr2)`, il compilatore è libero di valutare prima il lato sinistro o prima il lato destro. Questo è il primo incontro con il **comportamento non specificato** (*unspecified behavior*): un comportamento per cui lo standard C ammette due o più possibilità senza obbligare il compilatore a documentare quale sceglie.

Finché le sotto-espressioni leggono variabili senza modificarle, l'ordine di valutazione è irrilevante. Se però una stessa variabile viene modificata più volte — oppure letta e modificata — dentro la stessa espressione senza un punto di ordinamento garantito, si entra nel **comportamento indefinito**:

> **Attenzione — Codice vietato (comportamento indefinito)**
> Non scrivere mai espressioni come quelle del frammento seguente: lo standard C23 le classifica come comportamento indefinito perché `i` viene modificata e letta (o modificata due volte) senza ordinamento nella stessa espressione.

<!-- cod: id=3.2-c tipo=frammento -->
```c
int i = 1;
i = i++ + 1;              // VIETATO: comportamento indefinito!
printf("%d %d\n", i, i++); // VIETATO: comportamento indefinito!
```

La regola pratica è lineare e infallibile: **in una singola espressione, modifica una variabile al massimo una volta, e se la modifichi non leggerla altrove nella stessa espressione**. Spezzare l'operazione in due istruzioni separate rende il programma portabile, leggibile e completamente definito.

### Esempio guidato

Il programma seguente gestisce il saldo di un salvadanaio usando gli assegnamenti composti `+=`, `-=`, `*=` e `%=`, mostra con due variabili distinte la differenza tra `++a` e `b++`, e confronta `2 + 3 * 4` con `(2 + 3) * 4`.

<!-- cod: id=3.2-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    int saldo = 100;
    printf("Saldo iniziale: %d\n", saldo);

    saldo += 45;
    saldo -= 20;
    saldo *= 2;
    printf("Saldo dopo depositi, prelievo e raddoppio: %d\n", saldo);

    saldo %= 60;
    printf("Resto dopo pacchetti da 60: %d\n", saldo);

    int a = 5;
    int b = 5;
    int val_pre = ++a;
    int val_post = b++;
    printf("Pre-incremento (++a): valore=%d, a=%d\n", val_pre, a);
    printf("Post-incremento (b++): valore=%d, b=%d\n", val_post, b);

    int senza_parentesi = 2 + 3 * 4;
    int con_parentesi = (2 + 3) * 4;
    printf("2 + 3 * 4 = %d\n", senza_parentesi);
    printf("(2 + 3) * 4 = %d\n", con_parentesi);
    return 0;
}
```

```output
Saldo iniziale: 100
Saldo dopo depositi, prelievo e raddoppio: 250
Resto dopo pacchetti da 60: 10
Pre-incremento (++a): valore=6, a=6
Post-incremento (b++): valore=5, b=6
2 + 3 * 4 = 14
(2 + 3) * 4 = 20
```

Osserva come si comporta ciascun blocco:

- Partendo da `100`, `saldo += 45` lo porta a `145`, `saldo -= 20` a `125` e `saldo *= 2` a `250`. Infine `saldo %= 60` calcola il resto di `250 / 60`, cioè `10`.
- Per confrontare pre-incremento e post-incremento usiamo due variabili separate (`a` e `b`) e due istruzioni distinte: in questo modo non c'è alcun comportamento indefinito. Al termine sia `a` sia `b` valgono `6`, ma `val_pre` ha ricevuto `6` mentre `val_post` ha ricevuto `5`.
- Nell'ultimo blocco, senza parentesi `*` ha precedenza su `+`, quindi `2 + (3 * 4)` vale `14`; le parentesi forzano invece `(2 + 3) * 4`, che vale `20`.

> **Approfondimento — Precedenza e ordine di valutazione non sono la stessa cosa**
> Molti confondono la precedenza con l'ordine temporale di esecuzione. Nell'espressione `(a + b) + (c * d)`, la precedenza e le parentesi garantiscono che `c` sia moltiplicato per `d` e `a` sia sommato a `b` prima dell'addizione centrale. Tuttavia, lo standard C23 *non* impone se il programma debba calcolare prima `(a + b)` oppure prima `(c * d)`: quell'ordine è un comportamento non specificato. Il compilatore può scegliere l'ordine che ritiene più efficiente per il processore, ed è proprio per questo che non bisogna mai far dipendere una sotto-espressione dagli effetti collaterali di un'altra nella stessa istruzione.

### Esercizio 3.2 — Punteggio di una gara ciclistica a tappe

**Descrizione**

Un ciclista inizia una gara con `punti = 50` e `tappe = 0`. Scrivi un programma C che aggiorni `punti` e `tappe` in sequenza usando assegnamenti composti e l'operatore di incremento: nella prima tappa incrementa `tappe` e aggiungi `30` punti; nella seconda tappa raddoppia `punti` e incrementa `tappe`; nella terza tappa sottrai `15` punti, dividi `punti` per `3` con divisione intera e incrementa `tappe`. Successivamente, partendo da `bonus_pre = 10` e `bonus_post = 10`, calcola `val_pre = ++bonus_pre` e `val_post = bonus_post++` in istruzioni separate. Infine calcola `senza_parentesi = 10 + 4 * 3 - 6 / 2` e `con_parentesi = (10 + 4) * 3 - 6 / 2`. Stampa il riepilogo esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- assegnamento composto (`+=`, `-=`, `*=`, `/=`)
- differenza tra pre-incremento (`++x`) e post-incremento (`x++`)
- precedenza degli operatori
- uso delle parentesi tonde

**Domande guida**

1. Quale vantaggio offrono gli assegnamenti composti rispetto a riscrivere il nome della variabile su entrambi i lati di `=`?
2. In quale caso `++bonus_pre` e `bonus_post++` assegnano valori diversi alla variabile di destinazione, pur portando entrambi il contatore a `11`?
3. Quali operatori vengono raggruppati per primi nell'espressione `10 + 4 * 3 - 6 / 2` senza parentesi?
4. Perché conviene sempre scrivere l'incremento in un'istruzione separata quando non serve usarne il risultato in un'espressione più complessa?

**Esempio di esecuzione**

```output
Tappe completate: 3
Punteggio finale: 48
Pre-incremento: valore=11, variabile=11
Post-incremento: valore=10, variabile=11
Senza parentesi: 19
Con parentesi: 39
```
