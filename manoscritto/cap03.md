# Capitolo 3 — Operatori ed espressioni

> **In questo capitolo imparerai a:**
> - Prevedere il risultato di espressioni aritmetiche, relazionali e logiche applicando precedenza e associatività
> - Distinguere la divisione intera dalla divisione in virgola mobile e usare l'operatore modulo
> - Controllare le conversioni di tipo implicite ed esplicite senza perdere informazioni
> - Usare le funzioni matematiche di `<math.h>` collegando correttamente la libreria matematica (`-lm`)
> - Riconoscere e prevenire l'overflow degli interi con segno e gli errori di arrotondamento in virgola mobile

> **Ti servono:** i capitoli 1 e 2 (struttura di un programma C, compilazione con avvisi attivi, `printf` con gli specificatori di formato, variabili, tipi fondamentali, costanti `const` e `constexpr`, `sizeof` e `<limits.h>`).

Nel capitolo 2 hai imparato a dichiarare variabili, scegliere il tipo di dato adatto e stampare i valori con `printf`. Dichiarare dati, però, è soltanto il punto di partenza: un programma diventa utile quando trasforma quei dati, calcola nuove grandezze e verifica condizioni. Che tu debba convertire una durata in ore e minuti, calcolare una media o stabilire se un sensore segnala un'anomalia, il lavoro avviene attraverso operatori combinati in espressioni.

In C le espressioni sembrano a prima vista simili a quelle della matematica scolastica, ma nascondono regole precise che è fondamentale padroneggiare fin dall'inizio. Dividere due interi non produce mai un risultato decimale; mescolare tipi diversi fa scattare conversioni automatiche; superare il limite massimo di un intero con segno non dà un avviso a schermo, ma apre la porta a errori silenziosi e difficili da individuare.

In questo capitolo costruirai la padronanza completa del calcolo in C23: dagli operatori aritmetici, relazionali e logici fino alle conversioni di tipo, alle funzioni matematiche di `<math.h>` e ai limiti reali dell'aritmetica del calcolatore. Queste competenze ti serviranno immediatamente nel capitolo 4 per scrivere programmi capaci di prendere decisioni.

## 3.1 Operatori aritmetici, divisione intera e resto

Ogni volta che un programma esegue un calcolo — sommare due prezzi, convertire chilometri in metri, verificare se un numero è pari — sta valutando un'**espressione** (*expression*): una combinazione di operandi (costanti o variabili) e operatori che il programma valuta per produrre un valore o un effetto collaterale. Anche un singolo letterale come `42` o il nome di una variabile come `totale` è già un'espressione, ma la vera forza nasce combinando più operandi tramite operatori.

Gli operatori aritmetici binari del C sono cinque:

| Operatore | Significato | Esempio | Risultato |
|---|---|---|---|
| `+` | addizione | `8 + 3` | `11` |
| `-` | sottrazione | `8 - 3` | `5` |
| `*` | moltiplicazione | `8 * 3` | `24` |
| `/` | divisione | `8 / 3` | `2` |
| `%` | modulo (resto intero) | `8 % 3` | `2` |

Accanto a questi cinque operatori binari (che agiscono su due operandi), esistono anche gli operatori unari `+` e `-`, che agiscono su un singolo operando: `-x` inverte il segno di `x`, mentre `+x` ne mantiene il valore inalterato.

### Divisione intera contro divisione in virgola mobile

Osserva la riga della divisione nella tabella precedente: in C `8 / 3` vale `2`, non `2.666...`. Questo è uno dei punti più importanti del linguaggio: il comportamento dell'operatore `/` dipende dal tipo di dato degli operandi.

- Se **entrambi** gli operandi sono interi (come `7` e `2`, oppure due variabili `int`), `/` esegue la **divisione intera**: calcola il quoziente e **tronca** la parte frazionaria verso lo zero. Quindi `7 / 2` vale `3`, e `-7 / 2` vale `-3` (non `-4`).
- Se **almeno uno** degli operandi è in **virgola mobile** (*floating point*, cioè `float` o `double`, la rappresentazione binaria approssimata dei numeri reali tramite mantissa ed esponente), `/` esegue la **divisione in virgola mobile**: `7.0 / 2.0` vale `3.5`, e anche `7.0 / 2` o `7 / 2.0` valgono `3.5`.

La scelta del tipo di divisione avviene prima che il risultato venga eventualmente assegnato a una variabile. Se scrivi:

<!-- cod: id=3.1-b tipo=frammento -->
```c
double meta = 7 / 2;  // attenzione: 7 / 2 vale 3, poi viene convertito in 3.0!
```

la variabile `meta` riceve `3.0` e non `3.5`, perché `7` e `2` sono entrambi `int`: la divisione intera tronca subito a `3`, e solo dopo il valore `3` diventa `3.0` per entrare nel `double`. Per ottenere `3.5` occorre che almeno uno dei due operandi sia già in virgola mobile (`7.0 / 2.0`), oppure usare una conversione esplicita come vedrai nella sotto-sezione 3.4.

### L'operatore modulo (`%`)

Quando esegui una divisione intera, la parte scartata non va perduta se usi l'operatore **modulo** `%`, che restituisce il resto della divisione intera. A differenza di `/`, l'operatore `%` accetta **solo operandi interi**: applicarlo a un `double` o a un `float` provoca un errore di compilazione (per il resto in virgola mobile esiste la funzione `fmod`, che vedrai nella sotto-sezione 3.5).

L'operatore `%` è uno strumento utilissimo in molte situazioni concrete:

- **Scomporre quantità**: trasformare un numero totale di secondi in ore, minuti e secondi, oppure suddividere oggetti in confezioni intere contando quelli rimasti sfusi.
- **Verificare la divisibilità**: un intero `n` è multiplo di `k` (con `k != 0`) se e solo se `n % k` vale `0`; in particolare un numero è pari quando `n % 2` vale `0`.
- **Cicli periodici**: mantenere un contatore dentro un intervallo fisso da `0` a `N - 1`.

Quando compaiono numeri negativi, lo standard C23 definisce una regola precisa e priva di ambiguità: per ogni coppia di interi `a` e `b` (con `b != 0` e con quoziente rappresentabile), vale sempre l'identità:

```text
(a / b) * b + (a % b) == a
```

Poiché `a / b` tronca verso lo zero, ne segue che `a % b` ha sempre lo **stesso segno del dividendo `a`** (se il resto è diverso da zero). Per esempio, `-7 / 2` vale `-3` e `-7 % 2` vale `-1`, infatti `(-3) * 2 + (-1) == -7`. Allo stesso modo, `7 / -2` vale `-3` e `7 % -2` vale `1`, perché `(-3) * (-2) + 1 == 7`.

### Divisione per zero e comportamento indefinito

Che cosa accade se provi a dividere un intero per zero (`a / 0` oppure `a % 0`)? Nello standard C23 la divisione e il modulo per zero su interi provocano **comportamento indefinito** (*undefined behavior*): una situazione per cui lo standard C non pone alcun vincolo, e il programma può produrre qualunque risultato, bloccarsi o interrompersi in modo anomalo. Lo stesso accade nel caso limite `INT_MIN / -1` (e `INT_MIN % -1`), perché il risultato matematico `-INT_MIN` supera `INT_MAX` e non è rappresentabile in `int`.

Non scrivere mai divisioni o moduli in cui il divisore possa valere zero: dal capitolo 4 imparerai a proteggere queste operazioni con controlli condizionali prima di eseguirle.

> **Se vieni da Python** — In Python l'operatore `/` esegue sempre la divisione in virgola mobile (quindi `7 / 2` vale `3.5`) e `//` esegue la divisione intera arrotondando verso meno infinito (`-7 // 2` vale `-4` e `-7 % 2` vale `1`). In C non esiste `//` (che introduce un commento): `/` cambia comportamento in base al tipo degli operandi, tronca verso lo zero sui negativi (`-7 / 2` vale `-3`) e `%` mantiene il segno del dividendo (`-7 % 2` vale `-1`).

### Esempio guidato

Il programma seguente converte una durata di `3725` secondi in ore, minuti e secondi usando `/` e `%`, mette a confronto la divisione intera `7 / 2` con la divisione in virgola mobile `7.0 / 2.0` e verifica la regola del segno su `-7 / 2` e `-7 % 2`.

<!-- cod: id=3.1-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    constexpr int SECONDI_TOTALI = 3725;
    constexpr int SECONDI_IN_ORA = 3600;
    constexpr int SECONDI_IN_MINUTO = 60;

    int ore = SECONDI_TOTALI / SECONDI_IN_ORA;
    int secondi_residui = SECONDI_TOTALI % SECONDI_IN_ORA;
    int minuti = secondi_residui / SECONDI_IN_MINUTO;
    int secondi = secondi_residui % SECONDI_IN_MINUTO;

    int div_intera = 7 / 2;
    double div_reale = 7.0 / 2.0;

    int quoziente_neg = -7 / 2;
    int resto_neg = -7 % 2;
    int verifica = quoziente_neg * 2 + resto_neg;

    printf("%d secondi = %d h, %d min, %d s\n",
           SECONDI_TOTALI, ore, minuti, secondi);
    printf("Divisione intera 7 / 2 = %d\n", div_intera);
    printf("Divisione reale 7.0 / 2.0 = %.1f\n", div_reale);
    printf("Negativi: -7 / 2 = %d, -7 %% 2 = %d (verifica: %d)\n",
           quoziente_neg, resto_neg, verifica);
    return 0;
}
```

```output
3725 secondi = 1 h, 2 min, 5 s
Divisione intera 7 / 2 = 3
Divisione reale 7.0 / 2.0 = 3.5
Negativi: -7 / 2 = -3, -7 % 2 = -1 (verifica: -7)
```

Analizziamo i passaggi chiave:

- `SECONDI_TOTALI / SECONDI_IN_ORA` calcola quante ore intere stanno in `3725` secondi (`1`), mentre `SECONDI_TOTALI % SECONDI_IN_ORA` estrae i secondi avanzati (`125`).
- Su questi `125` secondi residui si ripete lo stesso schema con `60`: `125 / 60` produce `2` minuti e `125 % 60` produce i `5` secondi finali.
- Il confronto tra `7 / 2` (`3`) e `7.0 / 2.0` (`3.5`) evidenzia subito l'effetto del tipo degli operandi sullo stesso simbolo `/`.
- Nell'ultima `printf`, per stampare il carattere letterale `%` si scrive `%%`, come hai visto nel capitolo 2. Il controllo `quoziente_neg * 2 + resto_neg` restituisce esattamente `-7`, confermando l'identità dello standard C23.

> **Approfondimento — Perché la divisione tra interi tronca verso lo zero**
> In informatica esistono almeno due modi convenzionali di definire la divisione intera con resto sui numeri negativi: troncare verso lo zero (come fa il C dal C99 in poi, e quindi anche il C23) oppure arrotondare verso meno infinito (come fa Python con `//`). Il C ha scelto il troncamento verso lo zero perché coincide direttamente con l'istruzione di divisione intera della stragrande maggioranza dei processori moderni, garantendo prestazioni ottimali senza istruzioni correttive. L'identità `(a / b) * b + a % b == a` rimane così valida in modo uniforme per tutti i segni di `a` e `b`, con l'unica accortezza che `a % b` può essere negativo quando lo è `a`.

### Esercizio 3.1 — Confezionamento di libri in scatole e bancali

**Descrizione**

Un magazzino deve spedire `535` libri. Ogni scatola contiene esattamente `12` libri e ogni bancale completo ospita `8` scatole. Inoltre, un campione di `8` libri pesa complessivamente `3.0` kg. Scrivi un programma C che usi costanti e gli operatori aritmetici `/`, `%` e `*` per calcolare e stampare: il numero di scatole complete e i libri rimasti sfusi; il numero di bancali completi e le scatole rimaste fuori dai bancali; il totale dei libri caricati sui bancali completi; il peso medio in chilogrammi di un singolo libro calcolato con divisione in virgola mobile (stampato con tre cifre decimali). Stampa l'output esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- espressione
- divisione intera
- operatore modulo `%`
- differenza tra divisione intera e divisione in virgola mobile

**Domande guida**

1. Quali due operatori ti permettono di ricavare sia il numero di scatole complete sia i libri rimanenti da un totale intero?
2. Come usi il numero di scatole complete appena ottenuto per ricavare bancali completi e scatole avanzate?
3. Cosa otterresti se calcolassi il peso medio dividendo due interi invece di due valori `double`?
4. Quale specificatore di formato mostra il peso medio con esattamente tre cifre dopo la virgola?

**Esempio di esecuzione**

```output
Libri totali: 535
Scatole complete: 44 (libri sfusi: 7)
Bancali completi: 5 (scatole avanzate: 4)
Libri su bancali completi: 480
Peso medio di un libro: 0.375 kg
```

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

La regola pratica è lineare e infallibile: **in una singola espressione, modifica una variabile al massimo una volta e, se la modifichi con `++`, `--` o un assegnamento, non leggerla in un'altra parte dell'espressione (al di fuori del normale calcolo del nuovo valore a destra di `=`)**. Spezzare l'operazione in due istruzioni separate rende il programma portabile, leggibile e completamente definito.

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

Un ciclista inizia una gara con `punti = 50` e `tappe = 0`. Scrivi un programma C che aggiorni `punti` e `tappe` in sequenza usando assegnamenti composti e l'operatore di incremento: nella prima tappa incrementa `tappe` e aggiungi `30` punti; nella seconda tappa raddoppia `punti` e incrementa `tappe`; nella terza tappa sottrai `15` punti, dividi `punti` per `3` con divisione intera e incrementa `tappe`. Successivamente, partendo da `bonus_pre = 10` e `bonus_post = 10`, salva in due nuove variabili rispettivamente il risultato del pre-incremento di `bonus_pre` e del post-incremento di `bonus_post`, in istruzioni separate. Infine calcola `senza_parentesi = 10 + 4 * 3 - 6 / 2` e `con_parentesi = (10 + 4) * 3 - 6 / 2`. Stampa il riepilogo esattamente come nell'esempio di esecuzione.

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

## 3.3 Operatori relazionali e logici

Finora hai calcolato numeri. Per controllare se una temperatura è entro i limiti di sicurezza, se un utente ha l'età richiesta o se due valori coincidono, servono espressioni capaci di rispondere "vero" o "falso". In C queste verifiche si scrivono con gli **operatori relazionali**, di **uguaglianza** e **logici**.

### Operatori relazionali e di uguaglianza

Il C dispone di quattro operatori relazionali e due operatori di uguaglianza:

| Operatore | Significato | Esempio | Risultato |
|---|---|---|---|
| `<` | minore di | `4 < 7` | `1` (vero) |
| `<=` | minore o uguale a | `7 <= 7` | `1` (vero) |
| `>` | maggiore di | `4 > 7` | `0` (falso) |
| `>=` | maggiore o uguale a | `9 >= 5` | `1` (vero) |
| `==` | uguale a | `5 == 5` | `1` (vero) |
| `!=` | diverso da | `5 != 5` | `0` (falso) |

Secondo lo standard C23, il risultato di qualunque confronto relazionale o di uguaglianza è sempre un valore di tipo `int` pari a `1` se la relazione è vera, oppure `0` se è falsa. Puoi salvare direttamente questo risultato in una variabile `bool` (dove `1` corrisponde a `true` e `0` a `false`) e stamparlo con `%d`.

Presta la massima attenzione alla differenza tra `=` e `==`:

- `=` è l'**assegnamento**: copia il valore di destra nella variabile a sinistra (`x = 5`).
- `==` è il **confronto di uguaglianza**: controlla se i due operandi hanno lo stesso valore (`x == 5`) senza modificare nulla.

Scrivere `=` al posto di `==` è uno degli errori più frequenti in C. Compilare sempre con `-Wall -Wextra -Wpedantic -Werror` aiuta a intercettare molti di questi scambi accidentali.

### Operatori logici: `&&`, `||`, `!`

Spesso una condizione singola non basta: occorre combinare più verifiche ("l'altezza è sufficiente **e** l'età è valida") oppure negarne una ("**non** sta piovendo"). A questo servono i tre operatori logici del C:

- `&&` (**AND logico**): vero (`1`) solo se **entrambi** gli operandi sono veri.
- `||` (**OR logico**): vero (`1`) se **almeno uno** degli operandi è vero.
- `!` (**NOT logico**, unario): inverte il valore logico dell'operando (vero diventa `0`, falso diventa `1`).

Ecco le tabelle di verità complete:

| `a` | `b` | `a && b` | `a \|\| b` | `!a` |
|---|---|---|---|---|
| `0` (falso) | `0` (falso) | `0` | `0` | `1` |
| `0` (falso) | `1` (vero) | `0` | `1` | `1` |
| `1` (vero) | `0` (falso) | `0` | `1` | `0` |
| `1` (vero) | `1` (vero) | `1` | `1` | `0` |

In C vige una regola fondamentale sui valori di verità: **`0` significa falso, e qualunque valore diverso da `0` (anche `-3` o `42`) è interpretato come vero** dagli operatori logici. Il risultato restituito da `&&`, `||` e `!` è però sempre normalizzato a un `int` che vale `1` o `0`. Salvare le condizioni intermedie in variabili `bool` con nomi chiari — come `altezza_ok` o `accesso_consentito` — rende il codice molto più leggibile rispetto a lunghe catene di confronti inline.

### Attenzione agli intervalli: mai concatenare confronti

In matematica scrivi spesso `10 <= x <= 20` per verificare che `x` sia compreso tra `10` e `20`. In C questa espressione compila, ma **non fa quello che pensi**! Poiché `<=` associa da sinistra a destra, il compilatore la raggruppa come `(10 <= x) <= 20`:

1. Prima valuta `10 <= x`, che produce `0` (falso) oppure `1` (vero).
2. Poi confronta quel `0` o `1` con `20`. Siccome sia `0` sia `1` sono sempre minori o uguali a `20`, l'intera espressione vale **sempre `1`**, anche quando `x` vale `5` o `100`!

Un intervallo va quindi sempre spezzato esplicitamente con `&&`:

<!-- cod: id=3.3-b tipo=frammento -->
```c
bool in_intervallo = (x >= 10 && x <= 20);  // corretto
```

### Precedenza relativa tra gli operatori

Estendendo la tabella della sotto-sezione 3.2, la precedenza definita dallo standard C23 procede dall'alto verso il basso:

1. `!` (NOT logico, stessa precedenza degli altri operatori unari `+x`, `-x`, `++x`, `--x`)
2. `*`, `/`, `%`
3. `+`, `-`
4. Relazionali: `<`, `<=`, `>`, `>=`
5. Uguaglianza: `==`, `!=`
6. AND logico: `&&`
7. OR logico: `||`
8. Assegnamenti: `=`, `+=`, `-=`, `*=`, `/=`, `%=`

Grazie a questa gerarchia, `a + 1 < b && c != 0` viene raggruppato esattamente come `((a + 1) < b) && (c != 0)`. Quando mescoli `&&` e `||` nella stessa espressione, aggiungi comunque sempre le parentesi tonde per rendere evidente l'intenzione a chi legge: `a || (b && c)` è molto più chiaro di `a || b && c`.

Infine, a differenza degli operatori aritmetici, gli operatori `&&` e `||` valutano sempre i propri operandi **da sinistra a destra** e applicano la cosiddetta valutazione a corto circuito: se il lato sinistro decide già l'esito, il lato destro non viene nemmeno valutato (lo vedremo nel capitolo 4).

> **Se vieni da Python** — In Python gli operatori logici sono parole (`and`, `or`, `not`) e i confronti concatenati come `10 <= x <= 20` sono validi. In C gli operatori logici sono simboli (`&&`, `||`, `!`) e ogni intervallo va scritto esplicitamente come `10 <= x && x <= 20`.

### Esempio guidato

Il programma seguente verifica i requisiti di accesso a una giostra in base all'età, all'altezza in centimetri e alla presenza di un accompagnatore. Ogni verifica viene salvata in una variabile `bool` e stampata come `1` (vero) o `0` (falso).

<!-- cod: id=3.3-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    int eta = 11;
    int altezza_cm = 138;
    bool con_accompagnatore = true;

    bool altezza_ok = (altezza_cm >= 120 && altezza_cm <= 195);
    bool eta_autonoma = (eta >= 14);
    bool accesso_consentito = (altezza_ok && (eta_autonoma || con_accompagnatore));
    bool accesso_negato = !accesso_consentito;

    printf("Altezza valida (120-195 cm) : %d\n", altezza_ok);
    printf("Eta per accesso autonomo    : %d\n", eta_autonoma);
    printf("Accesso consentito          : %d\n", accesso_consentito);
    printf("Accesso negato              : %d\n", accesso_negato);
    return 0;
}
```

```output
Altezza valida (120-195 cm) : 1
Eta per accesso autonomo    : 0
Accesso consentito          : 1
Accesso negato              : 0
```

Osserva come le condizioni si compongono in modo leggibile:

- `altezza_ok` verifica l'intervallo corretto usando `&&`: poiché `138` è maggiore o uguale a `120` e minore o uguale a `195`, vale `true` (`1`).
- `eta_autonoma` vale `false` (`0`) perché `11 >= 14` è falso.
- `accesso_consentito` combina le condizioni con `&&` e `||`: le parentesi intorno a `(eta_autonoma || con_accompagnatore)` assicurano che l'altezza sia sempre obbligatoria, mentre la presenza di un accompagnatore può compensare l'età inferiore a `14` anni.
- `accesso_negato` applica `!` a `accesso_consentito`, invertendo `1` in `0`.

> **Approfondimento — Le leggi di De Morgan**
> Quando devi negare una condizione composta, è facile commettere errori di logica. Le due **leggi di De Morgan** forniscono la regola esatta:
> - `!(a && b)` equivale a `!a || !b` (non è vero che valgono entrambe = almeno una è falsa);
> - `!(a || b)` equivale a `!a && !b` (non è vero che ne vale almeno una = sono entrambe false).
>
> Per esempio, l'opposto di `altezza_cm >= 120 && altezza_cm <= 195` non è `altezza_cm < 120 && altezza_cm > 195` (impossibile!), ma `altezza_cm < 120 || altezza_cm > 195`.

### Esercizio 3.3 — Verifica di sicurezza prima del volo di un drone

**Descrizione**

Un drone di monitoraggio ambientale dispone dei seguenti dati dei sensori: `batteria = 68` (percentuale), `vento_kmh = 22`, `temperatura_c = 14`, `modalita_volo = 2` (dove `0` indica sistema bloccato), `gps_attivo = true` e `pioggia = false`. Scrivi un programma C che valuti e memorizzi in variabili `bool` le seguenti verifiche usando solo operatori relazionali e logici (senza alcun costrutto condizionale): `batteria_ok` (batteria almeno `30`), `vento_ok` (vento strettamente minore di `35`), `temperatura_ok` (temperatura compresa tra `0` e `40` inclusi), `modalita_ok` (`modalita_volo` diversa da `0`), `meteo_ok` (vento ok, temperatura ok e assenza di pioggia), `pronto_al_volo` (batteria ok, meteo ok, modalità ok e GPS attivo) e `allerta` (batteria minore di `20` oppure GPS non attivo). Stampa tutti i risultati (`1` = vero, `0` = falso) esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- operatori relazionali (`<`, `<=`, `>=`, `!=`)
- operatori logici (`&&`, `||`, `!`)
- scrittura corretta degli intervalli con `&&`
- tipo `bool` e stampa di `0` o `1` con `%d`

**Domande guida**

1. Perché non puoi scrivere `0 <= temperatura_c <= 40` per controllare che la temperatura sia nell'intervallo da `0` a `40`?
2. Quale operatore logico ti permette di esprimere l'assenza di pioggia a partire dalla variabile `bool` `pioggia`?
3. Che differenza c'è tra l'operatore `=` e l'operatore `==`, e quale operatore verifica invece la disuguaglianza?
4. Come cambia il risultato di `allerta` quando almeno una delle due condizioni collegate da `||` diventa vera?

**Esempio di esecuzione**

```output
=== CONTROLLO PRE-VOLO DRONE ===
Batteria sufficiente : 1
Vento sicuro         : 1
Temperatura valida   : 1
Modalita attiva      : 1
Meteo favorevole     : 1
Pronto al volo       : 1
Allerta attiva       : 0
```

## 3.4 Conversioni di tipo implicite ed esplicite

Nel codice reale gli operandi di un'espressione non hanno sempre lo stesso tipo: potresti sommare un `int` a un `double`, combinare due variabili `short`, oppure dover dividere due contatori interi ottenendo una media con la virgola. Per gestire queste situazioni il C applica regole precise di conversione, che possono avvenire in modo automatico oppure su tua richiesta esplicita.

### Conversione implicita: promozioni intere e conversioni aritmetiche usuali

Quando un'espressione combina valori di tipi diversi, il compilatore esegue una **conversione implicita** (*implicit conversion*): una trasformazione automatica di un valore da un tipo a un altro applicata secondo le regole dello standard C23. Il meccanismo procede in due fasi:

1. **Promozioni intere**: prima di eseguire qualunque operazione aritmetica, i tipi interi più stretti di `int` — cioè `char`, `short` e `bool` — vengono promossi automaticamente a `int` (se `int` può rappresentarne tutti i valori). Quindi, se `a` e `b` sono due variabili `short`, l'espressione `a + b` viene calcolata in `int` e ha tipo `int`, come puoi verificare con `sizeof(a + b)`.
2. **Conversioni aritmetiche usuali**: se dopo le promozioni i due operandi hanno ancora tipi diversi, il C li porta a un tipo comune scegliendo quello più ampio o più espressivo:
   - se uno degli operandi è `double`, l'altro viene convertito a `double` (per esempio `3 + 2.5` diventa `3.0 + 2.5` e produce `5.5`);
   - analogamente, `float` prevale sui tipi interi;
   - tra interi con segno diversi, il tipo più stretto viene promosso al più ampio (`int` verso `long`, `long` verso `long long`).

### Conversioni negli assegnamenti e perdita di informazioni

Una conversione implicita avviene anche quando assegni un'espressione a una variabile di tipo diverso: il valore a destra viene convertito nel tipo della variabile a sinistra.

- Da `int` a `double` (per esempio `double x = 5;`): il valore `5` diventa `5.0` senza perdita di precisione per gli interi ordinari.
- Da `double` a `int` (per esempio `int n = 3.9;`): la parte frazionaria viene **troncata verso lo zero** (non arrotondata!), quindi `3.9` diventa `3` e `-3.9` diventa `-3`.
- Da un tipo intero più ampio a uno più stretto (per esempio da `long long` a `short`): se il valore non entra nel tipo di destinazione, perdi informazioni (per gli interi con segno il risultato dipende dall'implementazione o può generare risultati inattesi).

Ancora più grave è il caso in cui converti un `double` o un `float` verso un tipo intero quando la sua parte intera è **fuori dall'intervallo rappresentabile** dal tipo di destinazione (per esempio convertire `1e20` in `int`): secondo lo standard C23 questa operazione provoca **comportamento indefinito**. Prima di convertire un numero in virgola mobile a intero, assicurati sempre che rientri nei limiti del tipo scelto.

### Cast esplicito

A volte la conversione automatica non basta. Supponi di avere due variabili intere `somma = 23` e `conteggio = 3` e di volerne calcolare la media esatta. Scrivere `double media = somma / conteggio;` produce `7.0`, perché la divisione tra due `int` è intera e tronca a `7` prima ancora dell'assegnamento.

Per forzare una conversione nel punto esatto che desideri, usa il **cast esplicito** (*explicit cast*): l'operatore `(tipo)` posto davanti a un'espressione con cui richiedi esplicitamente la conversione verso un tipo specifico.

<!-- cod: id=3.4-b tipo=frammento -->
```c
int somma = 23;
int conteggio = 3;
double media = (double)somma / conteggio;  // corretto: 23.0 / 3 -> 7.666667
```

Fai molta attenzione alla **precedenza** del cast esplicito: `(tipo)` è un operatore unario e ha precedenza **superiore** a `*`, `/` e `%`. Per questo motivo:

- `(double)somma / conteggio` converte prima `somma` in `double` (`23.0`), poi la conversione aritmetica usuale promuove anche `conteggio` a `double` (`3.0`), eseguendo la divisione in virgola mobile (`7.666667`).
- `(double)(somma / conteggio)` è invece un **cast tardivo** (un errore classico): le parentesi forzano prima la divisione intera `23 / 3` (`7`), e il cast trasforma solo il risultato già troncato in `7.0`!

Il cast esplicito serve anche a documentare intenzioni deliberate, come `(int)prezzo` quando vuoi esplicitamente scartare i centesimi, così che chi legge il codice capisca che il troncamento è voluto e non accidentale.

### Il pericolo delle espressioni miste tra `signed` e `unsigned`

Un'insidia tipica delle conversioni implicite riguarda la combinazione di interi con segno (`signed`, come `int`) e senza segno (`unsigned`, come `unsigned int` o `size_t`). Se confronti o sommi un `int` negativo come `-1` con un `unsigned int` come `1U`, il C converte `-1` a `unsigned int`: invece di rimanere negativo, `-1` si trasforma in `UINT_MAX` (un numero enorme, oltre quattro miliardi su sistemi con `int` a 32 bit)! Di conseguenza, l'espressione `-1 < 1U` risulta **falsa (`0`)**.

Compilare con `-Wextra` (come facciamo sempre) attiva un avviso del compilatore sui confronti tra `signed` e `unsigned`, aiutandoti a individuare subito queste trappole. La regola migliore è non mescolare tipi con segno e senza segno nella stessa espressione.

### Esempio guidato

Il programma seguente calcola la media di tre voti interi (`7`, `8` e `8`), mette a confronto `somma / 3`, il cast tardivo `(double)(somma / 3)` e il cast corretto `(double)somma / 3`, mostra il troncamento esplicito da `double` a `int` e verifica con `sizeof` la promozione intera di due variabili `short`.

<!-- cod: id=3.4-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

int main(void) {
    int voto_1 = 7;
    int voto_2 = 8;
    int voto_3 = 8;
    int somma = voto_1 + voto_2 + voto_3;

    int media_intera = somma / 3;
    double media_tardiva = (double)(somma / 3);
    double media_reale = (double)somma / 3;

    double prezzo = 19.85;
    int euro_interi = (int)prezzo;

    short a = 300;
    short b = 450;
    int somma_short = a + b;
    size_t dim_short = sizeof(a);
    size_t dim_espressione = sizeof(a + b);

    printf("Somma voti: %d\n", somma);
    printf("Media intera (somma / 3): %d\n", media_intera);
    printf("Cast tardivo ((double)(somma / 3)): %.2f\n", media_tardiva);
    printf("Cast corretto ((double)somma / 3): %.2f\n", media_reale);
    printf("Troncamento di %.2f a int: %d\n", prezzo, euro_interi);
    printf("Somma short: %d (sizeof(short)=%zu, sizeof(a+b)=%zu)\n",
           somma_short, dim_short, dim_espressione);
    return 0;
}
```

```output
Somma voti: 23
Media intera (somma / 3): 7
Cast tardivo ((double)(somma / 3)): 7.00
Cast corretto ((double)somma / 3): 7.67
Troncamento di 19.85 a int: 19
Somma short: 750 (sizeof(short)=2, sizeof(a+b)=4)
```

Osserva i risultati:

- `somma / 3` produce `7` e `(double)(somma / 3)` produce `7.00`, perdendo per sempre la parte decimale. Solo `(double)somma / 3` porta `somma` a `23.0` prima della divisione e ottiene `7.67` (arrotondato a due cifre da `%.2f`).
- `(int)prezzo` tronca `19.85` a `19`, senza arrotondare a `20`.
- `sizeof(a)` vale `2` (su piattaforme desktop comuni con `short` a 2 byte), ma `sizeof(a + b)` vale `4` (`sizeof(int)`): è la prova concreta che la promozione intera trasforma `a` e `b` in `int` prima di sommarli.

> **Approfondimento — Conversioni tra `signed` e `unsigned` di pari ampiezza**
> Nelle conversioni aritmetiche usuali, quando un operando `signed` e uno `unsigned` hanno lo stesso rango (per esempio `int` e `unsigned int`), il tipo `signed` viene convertito al corrispondente tipo `unsigned`. Il valore negativo viene ridotto modulo $2^N$ (dove $N$ è il numero di bit del tipo), diventando un intero positivo enorme. Se invece il tipo `signed` è strettamente più ampio e può contenere tutti i valori del tipo `unsigned` (per esempio `long long` e `unsigned int` su sistemi a 64 bit), è il tipo `unsigned` a essere promosso al tipo `signed`. Proprio perché il risultato dipende anche dalle dimensioni dei tipi sulla piattaforma, la scelta più sicura è mantenere coerente il segno degli operandi.

### Esercizio 3.4 — Percentuali e seggi di un sondaggio scolastico

**Descrizione**

In un sondaggio scolastico hanno risposto `favorevoli = 118`, `contrari = 39` e `astenuti = 18` studenti (tutti `int`). Inoltre due classi contribuiscono a una raccolta fondi con due variabili `short`: `quota_a = 1200` e `quota_b = 350`. Scrivi un programma C che calcoli: il totale delle risposte; la percentuale intera dei favorevoli ottenuta moltiplicando per `100` e dividendo per il totale con divisione intera; il risultato errato del cast tardivo applicando il cast a `double` solo dopo la divisione intera tra favorevoli e totale e moltiplicando poi per `100.0`; le percentuali corrette in `double` di favorevoli, contrari e astenuti usando un cast esplicito prima della divisione (stampate con due cifre decimali); la quota teorica di seggi dei favorevoli su un comitato di `15` membri in `double` (con due cifre decimali) e i seggi interi ottenuti troncando con `(int)`; la somma di `quota_a` e `quota_b` in `int` e la dimensione in byte dell'espressione di somma tramite `sizeof` per osservare la promozione intera. Stampa l'output esattamente come nell'esempio di esecuzione (riferito alle piattaforme desktop comuni con `int` a 4 byte).

**Concetti da tenere a mente**

- conversione implicita e promozioni intere
- cast esplicito `(double)` e `(int)`
- precedenza del cast rispetto alla divisione
- troncamento verso lo zero da `double` a `int`

**Domande guida**

1. Perché applicare il cast a `double` solo dopo la divisione intera tra `favorevoli` e `totale` produce `0.00` anche moltiplicando poi per `100.0`?
2. In che modo posizionare il cast a `double` prima della divisione cambia il tipo dell'operazione eseguita dal compilatore?
3. Che cosa succede alla parte decimale della quota teorica di seggi quando applichi un cast esplicito a `int`?
4. Perché `sizeof(quota_a + quota_b)` è uguale a `sizeof(int)` anche se entrambi gli operandi sono `short`?

**Esempio di esecuzione**

```output
Totale risposte: 175
Percentuale intera favorevoli: 67%
Cast tardivo (errato): 0.00%
Favorevoli: 67.43%
Contrari: 22.29%
Astenuti: 10.29%
Quota comitato (15 seggi): 10.11 -> seggi assegnati: 10
Somma quote short: 1550 (dimensione espressione: 4 byte)
```

## 3.5 Funzioni matematiche con `<math.h>`

Gli operatori aritmetici `+`, `-`, `*`, `/` e `%` coprono le operazioni di base, ma non bastano appena devi calcolare una radice quadrata, un elevamento a potenza, un valore assoluto o un arrotondamento controllato. In C non esiste un operatore per la potenza né per la radice quadrata: tutte queste operazioni sono fornite dalla libreria standard matematica, dichiarata nell'header `<math.h>`.

### Includere `<math.h>` e collegare con `-lm`

Per usare le funzioni matematiche servono due passaggi:

1. Aggiungere `#include <math.h>` all'inizio del file sorgente.
2. Aggiungere il flag **`-lm`** al **termine** del comando di compilazione:

```text
cc -std=c23 -Wall -Wextra -Wpedantic -Werror programma.c -o programma -lm
```

Su alcuni sistemi (come macOS) la libreria matematica è già integrata nella libreria C principale, mentre su molti sistemi Linux è distribuita in un file separato (`libm`). Aggiungere sempre `-lm` alla fine della riga di compilazione rende il comando portabile ovunque. La necessità o meno di `-lm` è un esempio di **comportamento dipendente dall'implementazione** (*implementation-defined behavior*): un comportamento che può variare tra compilatori o piattaforme, ma che ciascuna implementazione documenta.

### Le funzioni fondamentali di `<math.h>`

Tutte le funzioni di base presentate in questo capitolo accettano argomenti `double` e restituiscono un `double`:

| Funzione | Firma | Significato | Esempio |
|---|---|---|---|
| `fabs` | `double fabs(double x);` | valore assoluto in virgola mobile | `fabs(-4.5)` → `4.5` |
| `sqrt` | `double sqrt(double x);` | radice quadrata non negativa (`x >= 0`) | `sqrt(25.0)` → `5.0` |
| `pow` | `double pow(double x, double y);` | potenza $x^y$ | `pow(2.0, 3.0)` → `8.0` |
| `floor` | `double floor(double x);` | intero più grande $\le x$ (verso $-\infty$) | `floor(3.6)` → `3.0` |
| `ceil` | `double ceil(double x);` | intero più piccolo $\ge x$ (verso $+\infty$) | `ceil(3.2)` → `4.0` |
| `round` | `double round(double x);` | intero più vicino (metà via dallo zero) | `round(3.5)` → `4.0` |
| `fmod` | `double fmod(double x, double y);` | resto in virgola mobile di `x / y` (segno di `x`) | `fmod(7.5, 2.0)` → `1.5` |

Nota che `floor`, `ceil` e `round` restituiscono comunque un `double` (per esempio `4.0`, non un `int`): puoi stamparlo senza cifre decimali con `%.0f`, oppure convertirlo a intero con un cast esplicito solo se sei certo che il valore rientri nell'intervallo del tipo intero.

### Confronto tra `floor`, `ceil`, `round` e il cast `(int)`

Sui numeri positivi `floor(x)` e `(int)x` danno lo stesso valore intero (`3.0` e `3` per `3.6`), ma sui numeri **negativi** la differenza è sostanziale:

| Valore `x` | `(int)x` (verso `0`) | `floor(x)` (verso $-\infty$) | `ceil(x)` (verso $+\infty$) | `round(x)` (più vicino) |
|---|---|---|---|---|
| `3.6` | `3` | `3.0` | `4.0` | `4.0` |
| `3.5` | `3` | `3.0` | `4.0` | `4.0` |
| `-3.5` | `-3` | `-4.0` | `-3.0` | `-4.0` |
| `-3.6` | `-3` | `-4.0` | `-3.0` | `-4.0` |

Osserva `-3.6`: il cast `(int)` tronca verso lo zero e produce `-3`; `floor(-3.6)` scende all'intero inferiore, cioè `-4.0`; `ceil(-3.6)` sale all'intero superiore, cioè `-3.0`; `round(-3.6)` sceglie l'intero più vicino (`-4.0`), e nei casi esattamente a metà (come `3.5` e `-3.5`) allontana dallo zero (`4.0` e `-4.0`). Scegli sempre la funzione che corrisponde al significato del problema: per esempio `ceil` quando devi comprare un numero intero di confezioni sufficiente a coprire una superficie, `floor` quando conti quanti pezzi completi stanno in una lunghezza.

### Quando evitare `pow` ed errori di dominio

Per calcolare il quadrato di un numero (`x * x`) o il cubo (`x * x * x`), preferisci sempre la moltiplicazione diretta invece di `pow(x, 2.0)`: è più chiara, più veloce e spesso più precisa, perché `pow` è una funzione generale progettata per esponenti reali arbitrari.

Fai infine attenzione agli **errori di dominio**, cioè agli argomenti per cui la funzione matematica non è definita nei numeri reali: per esempio `sqrt(-4.0)` oppure `fmod(5.0, 0.0)`. Il modo esatto in cui vengono segnalati questi errori di dominio (valori speciali come `NaN` o codici di errore) dipende dall'implementazione; la buona pratica è verificare sempre che gli argomenti siano validi prima di chiamare la funzione.

> **Se vieni da Python** — In Python puoi scrivere `2 ** 10` con l'operatore di potenza `**`. In C non esiste un operatore di potenza (il simbolo `^` ha un significato completamente diverso, legato ai bit, che vedrai nel capitolo 13): per elevare a potenza si usa `pow(base, esponente)` di `<math.h>`, oppure `x * x` per un semplice quadrato.

### Esempio guidato

Il programma seguente calcola la distanza tra due punti nel piano cartesiano con `sqrt`, lo scostamento orizzontale con `fabs`, una potenza con `pow`, normalizza un angolo oltre `360` gradi con `fmod` e confronta `floor`, `ceil` e `round` su `3.6` e `-3.6`.

<!-- cod: id=3.5-a tipo=programma -->
```c
#include <math.h>
#include <stdio.h>

int main(void) {
    double x1 = 1.5;
    double y1 = 2.0;
    double x2 = 4.5;
    double y2 = 6.0;

    double dx = x2 - x1;
    double dy = y2 - y1;
    double distanza = sqrt(dx * dx + dy * dy);
    double scostamento_x = fabs(x1 - x2);
    double potenza = pow(2.0, 10.0);

    double angolo_grezzo = 765.5;
    double angolo_norm = fmod(angolo_grezzo, 360.0);

    double pos = 3.6;
    double neg = -3.6;

    printf("Distanza tra i due punti: %.2f\n", distanza);
    printf("Scostamento assoluto su x: %.2f\n", scostamento_x);
    printf("2^10 con pow: %.0f\n", potenza);
    printf("Angolo %.1f normalizzato (0-360): %.1f\n", angolo_grezzo, angolo_norm);
    printf("Su  3.6 -> floor=%.1f, ceil=%.1f, round=%.1f\n",
           floor(pos), ceil(pos), round(pos));
    printf("Su -3.6 -> floor=%.1f, ceil=%.1f, round=%.1f\n",
           floor(neg), ceil(neg), round(neg));
    return 0;
}
```

```output
Distanza tra i due punti: 5.00
Scostamento assoluto su x: 3.00
2^10 con pow: 1024
Angolo 765.5 normalizzato (0-360): 45.5
Su  3.6 -> floor=3.0, ceil=4.0, round=4.0
Su -3.6 -> floor=-4.0, ceil=-3.0, round=-4.0
```

Osserva i dettagli del programma:

- Per calcolare la distanza con il teorema di Pitagora scriviamo `dx * dx + dy * dy` invece di `pow(dx, 2.0) + pow(dy, 2.0)`, applicando la regola appena vista.
- `fabs(x1 - x2)` restituisce `3.00` anche se `x1 - x2` vale `-3.0`.
- `fmod(765.5, 360.0)` rimuove i due giri completi (`720.0`) e restituisce il resto `45.5` in virgola mobile, operazione impossibile con `%`.
- Le ultime due righe confermano il diverso comportamento di `floor`, `ceil` e `round` quando si passa da `3.6` a `-3.6`.

> **Approfondimento — Perché `-lm` va messo alla fine del comando**
> Quando il compilatore termina la traduzione del sorgente, entra in azione il **collegatore**, che unisce il tuo file oggetto alle librerie necessarie. Molti collegatori esaminano i file passati sulla riga di comando **da sinistra a destra**: tengono traccia dei simboli ancora irrisolti (come `sqrt` o `fmod`) e cercano ciascuna libreria solo per i simboli richiesti dai file incontrati *prima* di essa. Se metti `-lm` prima del file `.c`, al momento in cui il collegatore legge `-lm` non sa ancora che il tuo programma ha bisogno di `sqrt`, quindi la ignora e segnala un errore di simbolo non definito. Mettere `-lm` alla fine garantisce che funzioni sempre.

### Esercizio 3.5 — Preventivo per la pavimentazione di una terrazza

**Descrizione**

Devi preparare un preventivo per una terrazza rettangolare lunga `7.4` m e larga `4.8` m. Ogni scatola di piastrelle copre `1.44` m² e costa `48.75` euro; il budget iniziale è di `1200.0` euro. Il bordo decorativo del perimetro si vende in rotoli da `3.5` m. Infine, un fondo di `1000.0` euro viene accantonato per `3` anni al tasso composto annuo del `4%` (`1.04`). Scrivi un programma C che includa `<math.h>` (compilato con `-lm`) e calcoli: area e perimetro; diagonale della terrazza con `sqrt`; numero minimo di scatole intere necessarie con `ceil`; numero di rotoli completi contenuti nel perimetro con `floor` e metri rimanenti del perimetro con `fmod`; costo totale delle scatole, costo arrotondato all'euro più vicino con `round` e scostamento assoluto rispetto al budget con `fabs`; montante del fondo dopo `3` anni con `pow`. Stampa i risultati con due cifre decimali (e `%.0f` per scatole, rotoli e costo arrotondato) esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- inclusione di `<math.h>` e collegamento con `-lm`
- funzioni `sqrt`, `pow` e `fabs`
- funzioni di arrotondamento `floor`, `ceil` e `round`
- resto in virgola mobile con `fmod`

**Domande guida**

1. Quale funzione tra `floor`, `ceil` e `round` assicura di acquistare abbastanza scatole per coprire l'intera superficie senza restare scoperti?
2. Perché per calcolare i metri rimanenti del perimetro dopo i rotoli completi devi usare `fmod` invece dell'operatore `%`?
3. In che modo `fabs` ti garantisce di ottenere uno scostamento non negativo dal budget indipendentemente dal fatto che il costo sia maggiore o minore?
4. Perché conviene aggiungere sempre l'opzione `-lm` alla fine del comando di compilazione quando includi `<math.h>`?

**Esempio di esecuzione**

```output
Area terrazza: 35.52 mq
Diagonale: 8.82 m
Scatole necessarie: 25
Perimetro: 24.40 m (rotoli completi: 6, resto: 3.40 m)
Costo piastrelle: 1218.75 euro (arrotondato: 1219 euro)
Scostamento dal budget: 18.75 euro
Fondo dopo 3 anni: 1124.86 euro
```

## 3.6 Overflow degli interi e imprecisione della virgola mobile

In matematica i numeri interi sono infiniti e i numeri reali hanno precisione illimitata. In un calcolatore, invece, ogni variabile occupa un numero finito di byte. Questa limitazione fisica ha due conseguenze fondamentali che ogni programmatore C deve conoscere bene: l'**overflow** sugli interi e l'imprecisione dei calcoli in **virgola mobile**.

### Le tre categorie di comportamento nello standard C23

Nel corso di questo capitolo hai già incontrato tre espressioni tecniche molto precise. Prima di esaminare l'overflow, fissiamole in modo netto:

- **Comportamento indefinito** (*undefined behavior*): lo standard C23 non pone alcun vincolo su ciò che accade. Il programma può restituire un risultato assurdo, interrompersi, oppure sembrare funzionante oggi e fallire domani cambiando compilatore o livello di ottimizzazione. Va **sempre** evitato (esempi: divisione intera per zero, `i = i++ + 1`, overflow di un intero con segno).
- **Comportamento dipendente dall'implementazione** (*implementation-defined behavior*): può variare tra piattaforme o compilatori, ma ciascuna implementazione deve scegliere una regola fissa e documentarla (esempi: quanti byte occupa `int`, il valore di `DBL_DIG`, se occorre `-lm`).
- **Comportamento non specificato** (*unspecified behavior*): lo standard ammette due o più possibilità senza obbligare il compilatore a documentare quale sceglie, e la scelta può cambiare anche tra due punti diversi dello stesso programma (esempio: l'ordine di valutazione degli argomenti di una funzione).

### Overflow degli interi con segno

Si verifica un **overflow** quando il risultato di un'operazione supera l'intervallo rappresentabile dal tipo di destinazione (per un `int`, l'intervallo `INT_MIN..INT_MAX` definito in `<limits.h>`).

In C23 l'overflow di un'operazione aritmetica su **interi con segno** (`signed`, come `int`, `long`, `long long`) provoca **comportamento indefinito**:

> **Attenzione — Codice vietato (comportamento indefinito)**
> Non scrivere mai un'operazione che supera `INT_MAX` (o scende sotto `INT_MIN`) su un tipo con segno:

<!-- cod: id=3.6-b tipo=frammento -->
```c
int massimo = INT_MAX;
int rotto = massimo + 1;  // VIETATO: overflow con segno -> comportamento indefinito!
```

Per prevenire l'overflow hai due strategie sicure:

1. **Controllare prima dell'operazione**, riformulando la disuguaglianza senza mai far traboccare il calcolo. Per esempio, se `a` e `b` sono positivi, invece di calcolare `a + b` e controllare dopo (troppo tardi!), verifica `a <= INT_MAX - b`. Poiché `INT_MAX - b` è certamente dentro l'intervallo di `int`, questo controllo è completamente sicuro.
2. **Promuovere a un tipo più ampio** prima di calcolare: se `a` e `b` sono `int`, scrivere `(long long)a + b` esegue la somma in `long long` (che ha almeno 64 bit) evitando l'overflow di `int`. Fai attenzione a non scrivere `(long long)(a + b)`, perché in quel caso la somma avverrebbe comunque prima in `int`!

### Aritmetica modulare degli interi senza segno

Gli interi **senza segno** (`unsigned int`, `unsigned long`, `size_t`) seguono una regola completamente diversa e **definita dallo standard C23**: non vanno mai in overflow nel senso di comportamento indefinito. Quando il risultato esce da `0..UINT_MAX`, viene ridotto automaticamente modulo $2^N$ (dove $N$ è il numero di bit del tipo), avvolgendosi come il contachilometri di un'auto:

- `UINT_MAX + 1U` vale esattamente `0U`.
- `0U - 1U` vale esattamente `UINT_MAX` (`4294967295U` con `unsigned int` a 32 bit).

Anche se questo comportamento è definito, può comunque generare errori logici insidiosi — per esempio quando sottrai una quantità da un contatore `unsigned` che vale `0` e ti ritrovi un numero di miliardi invece di un numero negativo.

### Imprecisione della virgola mobile e `<float.h>`

Passiamo ora ai numeri in **virgola mobile** (`float` e `double`), che rappresentano i numeri reali in base binaria tramite mantissa ed esponente con un numero finito di bit. Proprio come in base 10 la frazione $1/3$ non ha una scrittura decimale finita (`0.333333...`), in base 2 molte frazioni decimali comuni — come `0.1`, `0.2` e `0.3` — sono periodiche e vengono quindi memorizzate con una piccolissima approssimazione.

Di conseguenza, in C l'espressione `0.1 + 0.2 == 0.3` può risultare **falsa (`0`)**! Stampando `0.1 + 0.2` con diciassette cifre decimali (`%.17f`), scoprirai che vale circa `0.30000000000000004`, mentre `0.3` vale circa `0.29999999999999999`.

Per conoscere con esattezza i limiti e la precisione dei tipi in virgola mobile sulla tua piattaforma, la libreria standard fornisce l'header `<float.h>` con queste costanti principali (i valori concreti dipendono dall'implementazione, di solito lo standard IEEE 754):

| Costante (`float` / `double`) | Significato | Valori tipici (IEEE 754) |
|---|---|---|
| `FLT_DIG` / `DBL_DIG` | cifre decimali significative garantite | `6` / `15` |
| `FLT_EPSILON` / `DBL_EPSILON` | minima differenza tra `1.0` e il valore successivo | $\approx 1.19 \times 10^{-7}$ / $\approx 2.22 \times 10^{-16}$ |
| `FLT_MIN` / `DBL_MIN` | più piccolo valore positivo normalizzato | $\approx 1.18 \times 10^{-38}$ / $\approx 2.23 \times 10^{-308}$ |
| `FLT_MAX` / `DBL_MAX` | più grande valore finito rappresentabile | $\approx 3.40 \times 10^{38}$ / $\approx 1.80 \times 10^{308}$ |

Proprio perché i calcoli in virgola mobile accumulano piccoli errori di arrotondamento, **non confrontare mai due risultati `double` con `==`**. Verifica invece che la loro distanza assoluta, calcolata con `fabs` di `<math.h>`, sia inferiore o uguale a una tolleranza scelta in base al problema:

<!-- cod: id=3.6-c tipo=frammento -->
```c
bool vicini = (fabs(a - b) <= 1e-12);
```

Per stampare numeri molto piccoli o molto grandi come `DBL_EPSILON` o `DBL_MAX` in notazione scientifica, `printf` mette a disposizione lo specificatore `%e` (che formatta un `double` nella forma `1.234567e-16`).

> **Se vieni da Python** — In Python gli interi (`int`) hanno precisione arbitraria e crescono automaticamente in memoria senza mai andare in overflow. In C gli interi hanno dimensione fissa e l'overflow di un intero con segno è comportamento indefinito. Al contrario, i numeri in virgola mobile (`float` in Python corrisponde a `double` in C) soffrono esattamente dello stesso fenomeno di `0.1 + 0.2 != 0.3` in entrambi i linguaggi.

### Esempio guidato

Il programma seguente evita un overflow di `int` nel calcolo del numero di celle di una griglia promuovendo a `long long`, mostra in modo sicuro l'aritmetica modulare su `unsigned int`, mette a confronto `0.1 + 0.2` con `0.3` sia tramite `==` sia tramite `fabs` con tolleranza, e stampa le costanti principali di `<float.h>`.

<!-- cod: id=3.6-a tipo=programma -->
```c
#include <float.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>

int main(void) {
    int righe = 60'000;
    int colonne = 45'000;
    long long celle_totali = (long long)righe * colonne;
    printf("Griglia %d x %d: %lld celle (INT_MAX = %d)\n",
           righe, colonne, celle_totali, INT_MAX);

    unsigned int contatore = UINT_MAX - 2U;
    unsigned int avanzato = contatore + 5U;
    unsigned int arretrato = 3U - 5U;
    printf("Contatore unsigned: (UINT_MAX - 2U) + 5U = %u, 3U - 5U = %u\n",
           avanzato, arretrato);

    constexpr double TOLLERANZA = 1e-9;
    double misura = 0.1 + 0.2;
    double riferimento = 0.3;
    bool confronto_diretto = (misura == riferimento);
    bool entro_tolleranza = (fabs(misura - riferimento) <= TOLLERANZA);
    printf("0.1 + 0.2 = %.17f\n", misura);
    printf("0.3       = %.17f\n", riferimento);
    printf("Uguali con == : %d | entro 1e-9 : %d\n",
           confronto_diretto, entro_tolleranza);

    printf("float  -> cifre=%d, eps=%e, min=%e, max=%e\n",
           FLT_DIG, FLT_EPSILON, FLT_MIN, FLT_MAX);
    printf("double -> cifre=%d, eps=%e, min=%e, max=%e\n",
           DBL_DIG, DBL_EPSILON, DBL_MIN, DBL_MAX);
    return 0;
}
```

```output
Griglia 60000 x 45000: 2700000000 celle (INT_MAX = 2147483647)
Contatore unsigned: (UINT_MAX - 2U) + 5U = 2, 3U - 5U = 4294967294
0.1 + 0.2 = 0.30000000000000004
0.3       = 0.29999999999999999
Uguali con == : 0 | entro 1e-9 : 1
float  -> cifre=6, eps=1.192093e-07, min=1.175494e-38, max=3.402823e+38
double -> cifre=15, eps=2.220446e-16, min=2.225074e-308, max=1.797693e+308
```

Esaminiamo i blocchi del programma:

- Il prodotto di `righe = 60'000` per `colonne = 45'000` (scritti con i separatori di cifre del C23) vale `2700000000`, che supera `INT_MAX` (`2147483647` su `int` a 32 bit): applicare il cast `(long long)` prima della moltiplicazione evita l'overflow e calcola il valore esatto.
- Su `unsigned int`, aggiungere `5U` a `UINT_MAX - 2U` supera il limite massimo di `3` unità e riparte da `2`, mentre `3U - 5U` scende sotto zero e si avvolge su `4294967294` (`UINT_MAX - 1U`): è aritmetica modulare perfettamente definita.
- `0.1 + 0.2` e `0.3` differiscono sulla diciassettesima cifra decimale: `==` produce `0`, mentre il confronto con `fabs` e tolleranza `1e-9` produce `1`. Infine `<float.h>` documenta cifre garantite, epsilon e intervallo di `float` e `double` sulla macchina in uso.

> **Approfondimento — Perché i controlli dopo l'overflow non funzionano**
> Potresti pensare di scrivere `int s = a + b;` e poi controllare se `s < a` per scoprire se è avvenuto un overflow con segno. È un grave errore: siccome lo standard C23 stabilisce che l'overflow con segno non deve mai accadere in un programma valido, un compilatore moderno con le ottimizzazioni attive può assumere che, per `b > 0`, `a + b` sia *sempre* maggiore di `a` e **rimuovere completamente il tuo controllo**! L'unico modo corretto e portabile di proteggersi è verificare i limiti *prima* di eseguire l'operazione, oppure calcolare in un tipo più ampio.

### Esercizio 3.6 — Prevenzione dell'overflow e controllo di tolleranza in virgola mobile

**Descrizione**

Scrivi un programma C che includa `<stdio.h>`, `<limits.h>`, `<float.h>` e `<math.h>` ed esegua tre verifiche numeriche senza provocare alcun comportamento indefinito. Primo: a partire dai due valori interi `a = 2'000'000'000` e `b = 500'000'000`, verifica con un controllo preventivo (senza mai calcolare `a + b` in `int`) se la loro somma rientra nell'intervallo di `int` memorizzando l'esito in una variabile `bool`, poi calcola la somma esatta in `long long` tramite cast esplicito. Secondo: partendo dal valore massimo rappresentabile da `unsigned int` (`UINT_MAX`), aggiungi `1U` e sottrai `1U` da `0U` per osservare l'aritmetica modulare degli interi senza segno. Terzo: somma `0.1 + 0.1 + 0.1` in un `double` e confrontalo con `0.3`, stampando entrambi i valori con `%.17f`; salva in variabili l'esito del confronto diretto con `==`, l'errore assoluto tramite `fabs` e l'esito del confronto con tolleranza `1e-12`, poi stampa `FLT_DIG`, `DBL_DIG`, `FLT_EPSILON` e `DBL_EPSILON` (usando `%e` per l'errore assoluto e per gli epsilon). Stampa l'output esattamente come nell'esempio di esecuzione (riferito alle piattaforme desktop comuni con `int` a 32 bit e virgola mobile IEEE 754).

**Concetti da tenere a mente**

- overflow degli interi con segno e comportamento indefinito
- prevenzione dell'overflow con controllo preventivo e promozione a `long long`
- aritmetica modulare degli interi senza segno
- virgola mobile e confronto con tolleranza tramite `fabs`
- costanti di precisione di `<float.h>`

**Domande guida**

1. Come puoi riformulare il controllo su `a`, `b` e `INT_MAX` per verificare se la somma rientra in `int` senza mai calcolare `a + b`?
2. Perché castare `a` in `long long` prima di sommare `b` evita l'overflow che avverrebbe scrivendo `(long long)(a + b)`?
3. In che cosa il comportamento di `UINT_MAX + 1U` differisce profondamente da quello di `INT_MAX + 1`?
4. Perché `0.1 + 0.1 + 0.1 == 0.3` può risultare falso in C e quale ruolo svolge `fabs` nel confronto con tolleranza?
5. Quale informazione forniscono rispettivamente `DBL_DIG` e `DBL_EPSILON` definite in `<float.h>`?

**Esempio di esecuzione**

```output
Somma sicura in int: 0
Somma esatta in long long: 2500000000
Unsigned UINT_MAX + 1U: 0
Unsigned 0U - 1U: 4294967295
0.1 + 0.1 + 0.1 = 0.30000000000000004
0.3             = 0.29999999999999999
Confronto con == : 0
Errore assoluto  : 5.551115e-17
Confronto tolleranza (1e-12): 1
Precisione cifre: float=6, double=15
Epsilon: float=1.192093e-07, double=2.220446e-16
```

## Riepilogo

- Un'**espressione** combina operandi e operatori per produrre un valore o un effetto collaterale. Gli operatori aritmetici sono `+`, `-`, `*`, `/` e `%` (oltre a `+` e `-` unari).
- Quando entrambi gli operandi di `/` sono interi, la divisione è intera e tronca verso lo zero (`7 / 2 == 3`, `-7 / 2 == -3`). L'operatore modulo `%` accetta solo interi e rispetta `(a / b) * b + (a % b) == a`, mantenendo il segno del dividendo `a`. Dividere o calcolare il resto per zero su interi provoca **comportamento indefinito**.
- Gli assegnamenti composti (`+=`, `-=`, `*=`, `/=`, `%=`) e gli operatori `++` e `--` (prefisso `++x` contro postfisso `x++`) aggiornano le variabili in modo conciso. La **precedenza degli operatori** e l'associatività determinano il raggruppamento, ma non l'ordine di valutazione delle sotto-espressioni (**comportamento non specificato**). Non modificare e leggere la stessa variabile senza ordinamento nella stessa espressione.
- Gli operatori relazionali (`<`, `<=`, `>`, `>=`), di uguaglianza (`==`, `!=`) e logici (`&&`, `||`, `!`) restituiscono `int` pari a `1` (vero) o `0` (falso). Gli intervalli vanno sempre scritti con `&&` (come `a <= x && x <= b`). Nel capitolo successivo userai queste condizioni per guidare le decisioni del programma e scoprirai la valutazione a corto circuito (lo vedremo nel capitolo 4).
- Nelle espressioni miste il C applica la **conversione implicita** (promozioni intere da `char`/`short`/`bool` a `int`, poi conversioni aritmetiche usuali). Il **cast esplicito** `(tipo)espressione` ha precedenza superiore a `*`, `/` e `%` e va applicato prima della divisione (`(double)a / b`). Evita di mescolare `signed` e `unsigned`.
- Le funzioni matematiche `fabs`, `sqrt`, `pow`, `floor`, `ceil`, `round` e `fmod` si trovano in `<math.h>`, lavorano su `double` e si collegano in modo portabile aggiungendo `-lm` alla fine del comando di compilazione.
- L'**overflow** degli interi con segno provoca comportamento indefinito e si previene controllando i limiti prima del calcolo o promuovendo a `long long`; gli interi senza segno seguono invece l'aritmetica modulare definita. I numeri in **virgola mobile** (descritti dalle costanti di `<float.h>`) sono approssimati in binario e vanno confrontati con `fabs(a - b) <= tolleranza`, mai con `==`.

## Errori comuni

- **Aspettarsi un risultato decimale dalla divisione tra due interi o applicare il cast troppo tardi**: `5 / 2` vale `2`, non `2.5`, e `(double)(a / b)` converte solo il quoziente già troncato; scrivi `(double)a / b`.
- **Confondere `=` con `==` o concatenare confronti**: `=` assegna mentre `==` confronta; scrivere `0 <= x <= 10` viene interpretato come `(0 <= x) <= 10` ed è sempre vero. Usa sempre `0 <= x && x <= 10`.
- **Modificare e leggere la stessa variabile più volte nella stessa espressione**: espressioni come `i = i++ + 1` o `printf("%d %d", i, i++)` provocano comportamento indefinito; separa sempre l'aggiornamento in un'istruzione distinta.
- **Dimenticare `-lm` alla fine del comando di compilazione**: quando includi `<math.h>`, omettere `-lm` (o metterlo prima del file `.c`) genera errori del collegatore sui sistemi in cui la libreria matematica è separata.
- **Confrontare due risultati in virgola mobile con `==`**: a causa della rappresentazione binaria finita, `0.1 + 0.2 == 0.3` può essere falso; confronta sempre con `fabs(a - b) <= tolleranza`.
- **Ignorare il rischio di overflow sugli interi con segno**: sommare o moltiplicare `int` senza verificare prima i limiti `INT_MIN..INT_MAX` (o senza promuovere a `long long`) provoca comportamento indefinito e rende inaffidabili eventuali controlli scritti dopo il calcolo.

## Prima di proseguire

- [ ] So prevedere il risultato di espressioni aritmetiche, relazionali e logiche usando precedenza, associatività e parentesi, senza scrivere modifiche non sequenziate.
- [ ] So distinguere divisione intera e divisione in virgola mobile e usare `%` anche in presenza di operandi negativi.
- [ ] So scrivere condizioni composte e intervalli con `&&`, `||` e `!` evitando il confronto concatenato e lo scambio tra `=` e `==`.
- [ ] So prevedere le conversioni implicite e usare il cast esplicito nel punto corretto, evitando trappole tra `signed` e `unsigned`.
- [ ] So usare `fabs`, `sqrt`, `pow`, `floor`, `ceil`, `round` e `fmod` di `<math.h>` compilando con `-lm`.
- [ ] So distinguere comportamento indefinito, dipendente dall'implementazione e non specificato, prevenire l'overflow degli interi con segno e confrontare valori `double` con una tolleranza tramite `fabs` e `<float.h>`.
