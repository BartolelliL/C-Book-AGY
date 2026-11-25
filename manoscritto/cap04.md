# Capitolo 4 — Decisioni

> **In questo capitolo imparerai a:**
> - Scrivere selezioni semplici e annidate con `if` ed `else`
> - Sfruttare la valutazione a corto circuito di `&&` e `||` per scrivere condizioni sicure
> - Scegliere tra catene di `if-else` e il costrutto `switch` con `break` e `default`
> - Usare l'operatore condizionale `?:` quando rende un'espressione più leggibile

> **Ti servono:** i capitoli 1–3 (variabili, tipi fondamentali `int`, `double`, `char` e `bool`, costanti `const` e `constexpr`, espressioni, operatori relazionali e logici, precedenza, comportamento indefinito e funzioni `fabs` e `sqrt` di `<math.h>`).

Tutti i programmi che hai scritto finora hanno seguito un percorso unico: dalla prima riga di `main` fino a `return 0;`, ogni istruzione veniva eseguita sempre e comunque, nello stesso ordine. Un programma reale, però, non può comportarsi allo stesso modo in ogni situazione: deve classificare una misura, applicare tariffe diverse a seconda dei dati, segnalare un valore non valido oppure evitare un'operazione pericolosa come una divisione per zero.

Nel capitolo 3 hai imparato a scrivere condizioni con gli operatori relazionali (`<`, `<=`, `>`, `>=`), di uguaglianza (`==`, `!=`) e logici (`&&`, `||`, `!`), ottenendo `1` quando una condizione è vera e `0` quando è falsa. Ora quel risultato diventa lo strumento con cui il programma decide quale strada imboccare.

In questo capitolo imparerai a governare le scelte del programma con i costrutti di selezione del C23: `if` ed `else` per le condizioni generali, la valutazione a corto circuito per proteggere espressioni delicate, `switch` per smistare valori interi discreti e l'operatore condizionale `?:` per scegliere tra due valori dentro una singola espressione.

## 4.1 Scegliere con `if` ed `else`

Un programma scritto come una semplice lista di istruzioni esegue sempre gli stessi passi, indipendentemente dai valori contenuti nelle variabili. Per reagire ai dati — per esempio decidere se una temperatura è normale o troppo alta, oppure se un valore rientra nei limiti ammessi — devi poter scegliere quali istruzioni eseguire e quali saltare. L'ordine con cui vengono eseguite le istruzioni di un programma attraverso selezioni, cicli (lo vedremo nel capitolo 6) e chiamate di funzione (lo vedremo nel capitolo 7) si chiama **flusso di controllo** (*control flow*).

Il costrutto fondamentale per deviare il flusso di controllo è l'istruzione `if`. La sua idea è immediata: controlla una condizione e, se risulta vera, esegue un blocco di istruzioni racchiuso tra parentesi graffe `{ ... }`; se invece è falsa, salta l'intero blocco e prosegue con l'istruzione successiva.

<!-- cod: id=4.1-b tipo=frammento -->
```c
if (temperatura >= 38.0) {
    printf("Febbre alta.\n");
}
```

In C la condizione va sempre racchiusa tra parentesi tonde e può essere qualsiasi espressione scalare, non soltanto un `bool` o un confronto con `==` o `<`. La regola è netta: il C considera **falsa** un'espressione che vale zero (`0`, `0.0`, `false`, `'\0'`) e **vera** qualsiasi espressione diversa da zero. Per chiarezza, tuttavia, conviene scrivere condizioni esplicite: `if (tentativi > 0)` o `if (attivo)` (quando `attivo` è un `bool`) sono molto più leggibili di `if (tentativi)`.

Spesso non basta fare qualcosa quando la condizione è vera: vuoi eseguire un blocco alternativo quando la condizione è falsa. In quel caso aggiungi il ramo `else`:

<!-- cod: id=4.1-c tipo=frammento -->
```c
if (punteggio >= 60) {
    printf("Prova superata.\n");
} else {
    printf("Prova non superata.\n");
}
```

Quando invece devi classificare un valore in più fasce mutuamente esclusive — cioè tali che al più una sola fascia possa valere alla volta — puoi concatenare più condizioni con `else if` e chiudere con un `else` finale per il caso residuo:

<!-- cod: id=4.1-d tipo=frammento -->
```c
if (voto < 6) {
    printf("Insufficiente\n");
} else if (voto < 8) {
    printf("Discreto\n");
} else {
    printf("Ottimo\n");
}
```

Il programma valuta le condizioni dall'alto verso il basso e si ferma alla prima vera. Se `voto` vale `5`, esegue il primo blocco e ignora tutti gli altri. Se `voto` vale `7`, la prima condizione è falsa, la seconda è vera e il ramo `else` finale non viene eseguito. Proprio perché il secondo controllo viene raggiunto solo quando `voto < 6` è falso, non serve scrivere `voto >= 6 && voto < 8`: basta ordinare le soglie in modo crescente (o decrescente) per ottenere condizioni brevi e senza sovrapposizioni. Nota la differenza rispetto a una sequenza di `if` separati senza `else`: in quel caso verrebbero valutate tutte le condizioni una dopo l'altra e potrebbero eseguirsi più blocchi per lo stesso valore.

Puoi anche inserire un `if` all'interno del blocco di un altro `if` o `else`: si parla di selezioni **annidate** (*nested*). Sono utili quando una seconda decisione ha senso soltanto all'interno di un ramo della prima — per esempio, verificare una condizione di allarme solo se il valore rientra già nella fascia di febbre alta.

In C, se il corpo di un `if` o di un `else` contiene una sola istruzione, il linguaggio permette di omettere le parentesi graffe. In questo libro adottiamo però una regola stilistica rigorosa: **racchiudi sempre ogni ramo di `if` e `else` tra parentesi graffe**, anche quando contiene una sola istruzione. Il motivo è pratico: senza graffe, aggiungere una seconda istruzione indentata in seguito crea un errore silenzioso (la seconda istruzione viene eseguita sempre, fuori dall'`if`), e negli `if` annidati si rischia di associare un `else` all'`if` sbagliato.

Riassumiamo la regola precisa secondo lo standard C23:

- L'istruzione `if (condizione) { ... }` esegue il proprio blocco se `condizione` viene valutata a un valore diverso da zero; l'eventuale ramo `else { ... }` viene eseguito se `condizione` vale zero.
- In una catena `if` / `else if` / `else` viene eseguito al più un solo ramo.
- Senza parentesi graffe un `else` si associa sempre all'`if` aperto più vicino; per evitare ambiguità si racchiude sempre ogni ramo tra parentesi graffe.
- La semantica di `if`, `else` e la regola di associazione dell'`else` all'`if` più interno sono comportamento completamente **definito** dallo standard C23.

Due errori sintattici molto frequenti meritano attenzione fin da subito. Il primo è inserire un punto e virgola subito dopo la condizione:

<!-- cod: id=4.1-e tipo=frammento -->
```c
// ERRORE: il punto e virgola chiude l'if con un'istruzione vuota
if (temperatura >= 38.0);
{
    printf("Febbre alta.\n");  // viene eseguita SEMPRE!
}
```

Quel punto e virgola isolato rappresenta un'istruzione vuota: il compilatore ritiene che il corpo dell'`if` finisca lì, mentre il blocco `{ ... }` successivo diventa un blocco indipendente eseguito in ogni caso, anche quando la condizione è falsa.

Il secondo errore è scrivere `=` (assegnamento) al posto di `==` (confronto di uguaglianza) dentro la condizione, come in `if (stato = 1)`. Poiché in C l'assegnamento è un'espressione il cui valore coincide con il valore assegnato, `stato = 1` modifica `stato` a `1` e produce `1` (cioè vero), entrando sempre nel ramo `if`. Compilare con `-Wall -Wextra` aiuta molto, perché il compilatore segnala con un avviso sia gli assegnamenti sospetti nelle condizioni sia gli `if` con corpo vuoto.

> **Se vieni da Python** — In Python i blocchi di `if` ed `else` dipendono dall'indentazione e per i rami intermedi si usa la parola chiave `elif`. In C l'indentazione serve solo a rendere il codice leggibile agli esseri umani: la condizione va sempre tra parentesi tonde, i blocchi sono delimitati da `{` e `}`, e i rami intermedi si scrivono con le due parole separate `else if`.

### Esempio guidato

Il programma seguente classifica una temperatura corporea in quattro fasce mutuamente esclusive (`ipotermia`, `normale`, `lieve alterazione`, `febbre alta`) mediante una catena `if` / `else if` / `else` con soglie ordinate in senso crescente. Nel ramo della febbre alta, un `if` annidato controlla se la temperatura raggiunge almeno `39.0` gradi oppure se sono presenti sintomi gravi, per segnalare la necessità di un controllo immediato.

<!-- cod: id=4.1-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    double temperatura = 38.2;
    bool sintomi_gravi = true;

    printf("Temperatura rilevata: %.1f C\n", temperatura);

    if (temperatura < 35.0) {
        printf("Fascia: ipotermia\n");
    } else if (temperatura < 37.5) {
        printf("Fascia: normale\n");
    } else if (temperatura < 38.0) {
        printf("Fascia: lieve alterazione\n");
    } else {
        printf("Fascia: febbre alta\n");
        if (temperatura >= 39.0 || sintomi_gravi) {
            printf("Avviso: richiesto controllo immediato.\n");
        } else {
            printf("Avviso: monitorare ogni due ore.\n");
        }
    }

    return 0;
}
```

```output
Temperatura rilevata: 38.2 C
Fascia: febbre alta
Avviso: richiesto controllo immediato.
```

Seguiamo passo dopo passo il flusso di controllo con `temperatura = 38.2` e `sintomi_gravi = true`:

- La prima condizione `temperatura < 35.0` è falsa (`38.2 < 35.0` vale `0`), quindi il programma passa al primo `else if`.
- Anche `temperatura < 37.5` e `temperatura < 38.0` sono false: si entra dunque nel ramo `else` finale, che copre tutte le temperature maggiori o uguali a `38.0` e stampa `Fascia: febbre alta`.
- All'interno di quel ramo si trova un `if` annidato. La condizione `temperatura >= 39.0 || sintomi_gravi` è vera perché `sintomi_gravi` è `true` (anche se `38.2 >= 39.0` è falso). Viene quindi stampato l'avviso di controllo immediato e il ramo `else` interno viene saltato.
- Ogni blocco, esterno e interno, usa le parentesi graffe: l'organizzazione delle decisioni è visibile a colpo d'occhio e priva di ambiguità.

> **Approfondimento — Il problema del dangling else**
> Che cosa succede se ometti le parentesi graffe in un `if` annidato? Considera questo frammento (scritto in modo intenzionalmente ingannevole):
>
> <!-- cod: id=4.1-f tipo=frammento -->
> ```c
> // ATTENZIONE: l'indentazione inganna!
> if (accesso_autorizzato)
>     if (livello >= 2)
>         printf("Accesso completo\n");
> else
>     printf("Accesso negato\n");
> ```
>
> Guardando l'indentazione, sembrerebbe che `else` appartenga al primo `if (accesso_autorizzato)`. In realtà lo standard C ignora l'indentazione e applica la regola del **dangling else** ("`else` pendente"): un `else` si lega sempre all'`if` aperto più vicino che non ha ancora un `else`. Il compilatore legge quindi il codice come se `else` fosse associato a `if (livello >= 2)`: quando `accesso_autorizzato` è falso non viene stampato nulla, mentre quando `accesso_autorizzato` è vero e `livello` vale `1` viene stampato `Accesso negato`. Racchiudendo sempre i rami tra `{` e `}` il problema scompare del tutto.

### Esercizio 4.1 — Tariffa di spedizione a scaglioni

**Descrizione**

Un corriere calcola il costo di spedizione a partire dal peso del pacco (`double peso_kg = 6.4;`) e dalla richiesta di consegna prioritaria (`bool prioritaria = true;`). Scrivi un programma C che usi `if`, `else if`, `else` e un `if` annidato secondo queste regole: se `peso_kg <= 0.0` stampa `Peso non valido.`; se `peso_kg > 25.0` stampa `Pacco fuori misura.`; altrimenti assegna la tariffa base e la fascia (`<= 2.0` kg: fascia `Leggero`, `5.00` euro; `<= 10.0` kg: fascia `Medio`, `9.50` euro; `<= 25.0` kg: fascia `Pesante`, `16.00` euro). Per i pacchi validi, se `prioritaria` è `true` aggiungi un supplemento di `4.50` euro, altrimenti `0.00` euro, e stampa peso, fascia, tariffa base, supplemento e totale con due cifre decimali esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- flusso di controllo
- catena `if` / `else if` / `else` mutuamente esclusiva
- selezione annidata con parentesi graffe obbligatorie
- ordine crescente delle soglie negli scaglioni

**Domande guida**

1. In quale ordine conviene controllare le fasce di peso affinché ogni condizione risulti semplice e priva di sovrapposizioni?
2. Perché conviene controllare prima i casi non validi (peso non positivo o superiore a `25.0` kg) rispetto al calcolo del supplemento?
3. Quale rischio corri se ometti le parentesi graffe attorno al blocco di un `if` che contiene un altro `if`/`else`?
4. Che cosa accadrebbe se scrivessi una sequenza di `if` separati senza `else` invece di una catena `if` / `else if` / `else`?

**Esempio di esecuzione**

```output
Peso pacco: 6.40 kg
Fascia: Medio
Tariffa base: 9.50 euro
Supplemento prioritaria: 4.50 euro
Totale spedizione: 14.00 euro
```

## 4.2 Condizioni composte e valutazione a corto circuito

Le decisioni reali dipendono spesso da più condizioni combinate insieme. Nel capitolo 3 hai conosciuto gli operatori logici `&&` (AND logico), `||` (OR logico) e `!` (NOT logico). Usandoli dentro un `if`, puoi verificare intervalli o combinare requisiti diversi in una sola condizione:

<!-- cod: id=4.2-b tipo=frammento -->
```c
if ((eta >= 16 && eta <= 18) || autorizzazione_speciale) {
    printf("Ammesso al laboratorio.\n");
}
```

Anche se `&&` ha precedenza maggiore di `||` e gli operatori relazionali hanno precedenza maggiore di entrambi, aggiungere parentesi esplicite attorno ai gruppi logici rende la condizione immediatamente leggibile e previene errori quando mescoli `&&` e `||`.

Gli operatori `&&` e `||`, però, hanno una proprietà molto più importante della semplice combinazione di valori di verità. Nel capitolo 3 hai visto che, in generale, il C non garantisce l'ordine in cui vengono valutati gli operandi di un operatore come `+` o `*`. Gli operatori `&&` e `||` fanno eccezione: valutano **sempre prima l'operando sinistro**, e se quel solo risultato basta a determinare l'esito finale, **non valutano affatto l'operando destro**. Questa proprietà si chiama **valutazione a corto circuito** (*short-circuit evaluation*).

Vediamo concretamente i due casi:

- In `a && b`: l'espressione è vera solo se entrambi gli operandi sono veri. Se `a` vale `0` (falso), il risultato è già garantito essere `0` qualunque cosa valga `b`, quindi `b` non viene valutato.
- In `a || b`: l'espressione è vera non appena almeno un operando è vero. Se `a` è diverso da `0` (vero), il risultato è già garantito essere `1` qualunque cosa valga `b`, quindi `b` non viene valutato.

Riassumiamo la regola secondo lo standard C23:

- Gli operatori logici `&&` e `||` valutano sempre prima l'operando sinistro e introducono un punto di sequenza prima dell'operando destro (tutti gli effetti del lato sinistro sono completati prima che il lato destro inizi).
- In `a && b`, se `a` vale `0`, `b` non viene valutato e il risultato è `0`; in `a || b`, se `a` è diverso da `0`, `b` non viene valutato e il risultato è `1`.
- L'ordine di valutazione da sinistra a destra, il punto di sequenza e la valutazione a corto circuito di `&&` e `||` sono comportamento **definito** dallo standard C23.

Perché questa garanzia è così preziosa? Perché ti permette di scrivere una **guardia** a sinistra che protegge un'operazione potenzialmente pericolosa a destra. Considera la divisione intera: nel capitolo 3 hai visto che dividere un intero per zero causa **comportamento indefinito**. Se vuoi verificare che la media di `n` voti (la cui somma è `somma`) sia almeno `6`, ma `n` potrebbe essere `0`, scrivi:

<!-- cod: id=4.2-c tipo=frammento -->
```c
if (n != 0 && somma / n >= 6) {
    printf("Media sufficiente.\n");
}
```

Quando `n` vale `0`, l'operando sinistro `n != 0` risulta falso (`0`). Grazie alla valutazione a corto circuito, la divisione `somma / n` non viene mai eseguita e il comportamento indefinito è evitato alla radice.

Lo stesso schema protegge le funzioni di `<math.h>` da argomenti fuori dal loro dominio matematico. La funzione `sqrt(x)` richiede `x >= 0.0` (passarle un valore negativo produce un errore di dominio). Puoi dunque scrivere:

<!-- cod: id=4.2-d tipo=frammento -->
```c
if (x >= 0.0 && sqrt(x) > 3.0) {
    printf("Radice maggiore di 3.\n");
}
```

Se `x` è negativo, `x >= 0.0` è falso e `sqrt(x)` non viene chiamata. Lo stesso schema di guardia ti tornerà utile in tutto il resto del libro ogni volta che dovrai verificare una precondizione prima di eseguire un'operazione delicata.

Un'altra cautela indispensabile dentro le condizioni di `if` riguarda i numeri in **virgola mobile**. Come hai visto nel capitolo 3, valori come `0.1 + 0.2` non sono esattamente uguali a `0.3` nella rappresentazione binaria di `double`. Dentro un `if`, quindi, non confrontare mai due risultati `double` con `==`: usa sempre `fabs` di `<math.h>` con una tolleranza adatta al problema, per esempio `if (fabs(a - b) <= 1e-9)`.

Infine, la valutazione a corto circuito impone una regola di igiene sul codice: **non inserire effetti collaterali (come `++`, `--` o assegnamenti) nell'operando destro di `&&` o `||`**. Osserva questo frammento sconsigliato:

<!-- cod: id=4.2-e tipo=frammento -->
```c
// SCONSIGLIATO: l'incremento di contatore può non avvenire!
if (flag && ++contatore > 5) {
    printf("Soglia superata.\n");
}
```

Se `flag` vale `false`, `++contatore` non viene mai eseguito; se `flag` vale `true`, viene eseguito. Un codice del genere è difficile da leggere e nasconde bug sottili perché il valore finale di `contatore` dipende dal fatto che il corto circuito sia scattato oppure no. Separa sempre l'aggiornamento della variabile in un'istruzione distinta, prima o dentro il blocco dell'`if`.

### Esempio guidato

Il programma seguente valuta i risultati di due studenti usando la valutazione a corto circuito come guardia contro la divisione intera per zero (`numero_prove > 0 && punti_totali / numero_prove >= 60`). Per il primo studente `numero_prove` è `0` e la divisione non viene eseguita; per il secondo `numero_prove` è `4` e la media viene calcolata in sicurezza. Infine il programma mostra una guardia analoga su `sqrt` per verificare il lato di un pannello quadrato a partire dalla sua area (ricorda di collegare la libreria matematica con `-lm` in compilazione).

<!-- cod: id=4.2-a tipo=programma -->
```c
#include <math.h>
#include <stdio.h>

int main(void) {
    int numero_prove_1 = 0;
    int punti_totali_1 = 240;

    if (numero_prove_1 > 0 && punti_totali_1 / numero_prove_1 >= 60) {
        printf("Studente 1: promosso (media %d)\n",
               punti_totali_1 / numero_prove_1);
    } else if (numero_prove_1 > 0) {
        printf("Studente 1: non promosso (media %d)\n",
               punti_totali_1 / numero_prove_1);
    } else {
        printf("Studente 1: nessuna prova svolta\n");
    }

    int numero_prove_2 = 4;
    int punti_totali_2 = 300;

    if (numero_prove_2 > 0 && punti_totali_2 / numero_prove_2 >= 60) {
        printf("Studente 2: promosso (media %d)\n",
               punti_totali_2 / numero_prove_2);
    } else if (numero_prove_2 > 0) {
        printf("Studente 2: non promosso (media %d)\n",
               punti_totali_2 / numero_prove_2);
    } else {
        printf("Studente 2: nessuna prova svolta\n");
    }

    double area = -9.0;
    if (area >= 0.0 && sqrt(area) > 3.0) {
        printf("Lato superiore a 3.0\n");
    } else {
        printf("Area non valida o lato non superiore a 3.0\n");
    }

    return 0;
}
```

```output
Studente 1: nessuna prova svolta
Studente 2: promosso (media 75)
Area non valida o lato non superiore a 3.0
```

Analizziamo che cosa accade nei tre controlli:

- Per lo studente 1, `numero_prove_1 > 0` è falso (`0`). La valutazione a corto circuito di `&&` interrompe subito la condizione senza valutare `punti_totali_1 / numero_prove_1`. Anche `else if (numero_prove_1 > 0)` è falso, quindi si esegue il ramo `else` finale.
- Per lo studente 2, `numero_prove_2 > 0` è vero (`4 > 0`). Solo a questo punto viene valutata la divisione `300 / 4`, che vale `75` (`>= 60`), e viene stampato l'esito positivo.
- Nell'ultimo controllo, `area` vale `-9.0`. La guardia `area >= 0.0` risulta falsa e impedisce la chiamata `sqrt(-9.0)`, portando il flusso direttamente al ramo `else`.

> **Approfondimento — Perché l'ordine degli operandi è decisivo**
> La protezione offerta dalla valutazione a corto circuito funziona soltanto se la guardia sta **a sinistra** dell'operazione protetta. Se inverti i due operandi e scrivi:
>
> <!-- cod: id=4.2-f tipo=frammento -->
> ```c
> // ERRORE: comportamento indefinito quando n vale 0!
> if (somma / n >= 6 && n != 0) {
>     printf("Media sufficiente.\n");
> }
> ```
>
> il programma valuta prima `somma / n >= 6`. Quando `n` vale `0`, la divisione intera per zero viene eseguita prima ancora di raggiungere `n != 0`, provocando **comportamento indefinito** (spesso l'arresto immediato del programma). Metti sempre per prima la condizione che rende sicura la valutazione del resto dell'espressione.

### Esercizio 4.2 — Controlli difensivi con valutazione a corto circuito

**Descrizione**

Scrivi un programma C che includa `<stdio.h>` e `<math.h>` (compilato con `-lm`) ed esegua tre controlli difensivi basati sulla valutazione a corto circuito. Primo: per il sensore A (`campioni_a = 0`, `somma_a = 420`) e il sensore B (`campioni_b = 6`, `somma_b = 390`), tutti `int`, usa una condizione con guardia per verificare se il numero di campioni è positivo e la media intera è almeno `50`, stampando se ciascun sensore ha `media sufficiente` (con il valore della media intera), `media insufficiente` (con il valore della media intera) oppure `nessun campione disponibile` (senza mai dividere per zero). Secondo: dati i coefficienti `double` di un'equazione di secondo grado `a = 1.0`, `b = -5.0`, `c = 6.0`, calcola il discriminante `delta` e usa un singolo `if` con guardie a corto circuito per verificare nell'ordine che `a` abbia valore assoluto maggiore di `1e-12`, che `delta` sia non negativo e che la radice quadrata di `delta` sia strettamente positiva; in tal caso calcola e stampa le due radici reali distinte con due cifre decimali (dalla minore alla maggiore). Terzo: verifica se `tensione = 0.1 + 0.2` (`double`) coincide con `nominale = 0.3` (`double`) entro una tolleranza di `1e-9` usando `fabs` e stampa l'esito esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- valutazione a corto circuito di `&&`
- ordine degli operandi nelle guardie
- prevenzione della divisione intera per zero e degli errori di dominio di `sqrt`
- confronto in virgola mobile con `fabs` e tolleranza dentro `if`

**Domande guida**

1. Perché nel controllo del sensore A la divisione `somma_a / campioni_a` non viene mai eseguita anche se `campioni_a` vale `0`?
2. Che cosa succederebbe se nel controllo del sensore A invertissi i due operandi di `&&`, verificando la media prima di controllare che `campioni_a` sia positivo?
3. In che modo la catena di condizioni con `&&` su `a` e `delta` protegge la chiamata a `sqrt(delta)` da un argomento negativo?
4. Perché per verificare se la tensione corrisponde al valore nominale non puoi confrontare i due valori con `==`, ma devi controllare la loro distanza assoluta rispetto alla tolleranza tramite `fabs`?

**Esempio di esecuzione**

```output
Sensore A: nessun campione disponibile
Sensore B: media sufficiente (65)
Equazione: due radici reali distinte (x1 = 2.00, x2 = 3.00)
Tensione: entro la tolleranza nominale
```

## 4.3 Scelte multiple con `switch`

Quando devi confrontare una stessa espressione con molti valori specifici — per esempio un codice di menu (`1`, `2`, `3`), una lettera di comando (`'A'`, `'B'`, `'C'`) o un giorno della settimana (`1`..`7`) — una lunga catena `if / else if / else` che ripete sempre lo stesso confronto con `==` diventa verbosa e ripetitiva. In questi casi il C mette a disposizione un costrutto dedicato: `switch`.

La regola di scelta tra `if / else if` e `switch` è chiara: usa `if / else if` quando confronti intervalli (`temperatura < 37.5`), condizioni complesse con `&&` e `||`, oppure valori `double`; usa `switch` quando smisti il flusso di controllo confrontando una singola espressione intera (o `char`) con un insieme finito di valori costanti discreti.

La forma di base di uno `switch` è composta dall'espressione di controllo tra parentesi tonde e da un blocco contenente etichette `case`, istruzioni `break;` e un'etichetta opzionale `default:`:

<!-- cod: id=4.3-b tipo=frammento -->
```c
switch (scelta) {
    case 1:
        printf("Avvio stampa\n");
        break;
    case 2:
        printf("Salvataggio dati\n");
        break;
    default:
        printf("Scelta non riconosciuta\n");
        break;
}
```

Quando il programma raggiunge lo `switch`, valuta l'espressione tra parentesi una sola volta e salta direttamente all'etichetta `case` il cui valore costante coincide con il risultato. Se nessun `case` corrisponde, salta all'etichetta `default` (se presente); se manca anche `default`, l'intero `switch` viene saltato senza eseguire nulla. Conviene inserire **sempre** il ramo `default`, anche quando ti aspetti soltanto certi valori: funge da rete di sicurezza per intercettare dati imprevisti o errori di logica.

Lo standard C impone vincoli precisi su ciò che puoi scrivere dentro uno `switch`:

- L'espressione di `switch (espressione)` deve avere un **tipo intero** (`int`, `long`, `char`, `bool` e le relative varianti con o senza segno; in seguito potrai usarvi anche le enumerazioni, lo vedremo nel capitolo 12). Non puoi mai usare un `double` o un `float` dentro uno `switch`: il compilatore segnala un errore di compilazione.
- Ogni etichetta `case` deve indicare un'**espressione costante intera** nota a tempo di compilazione: un letterale intero (`1`), un letterale carattere (`'A'`), oppure — in C23 — una costante dichiarata con `constexpr` (non una normale variabile `int`, e nemmeno una `const int` non `constexpr`).
- Tutte le etichette `case` di uno stesso `switch` devono avere valori **distinti**: duplicare un valore causa un errore di compilazione.

Una caratteristica fondamentale dello `switch` in C è che le etichette `case` sono semplici punti di ingresso, non blocchi separati. Una volta saltato a un `case`, il programma esegue tutte le istruzioni che trova fino a incontrare un'istruzione `break;` (che fa uscire dallo `switch`) oppure la parentesi graffa di chiusura dello `switch`. Se manca `break;`, l'esecuzione prosegue automaticamente dentro il ramo `case` successivo: questo meccanismo si chiama **fall-through**.

Il fall-through può essere sfruttato in modo pulito in due situazioni:

1. **Raggruppamento di etichette vuote**: quando più valori devono eseguire esattamente lo stesso codice, impili le etichette `case` una sotto l'altra senza istruzioni in mezzo, come `case 'a':` seguito subito da `case 'A':`. È un idioma standard e chiarissimo.
2. **Fall-through intenzionale dopo istruzioni**: quando un livello superiore include anche le azioni dei livelli inferiori (per esempio un abbonamento avanzato che eredita i vantaggi dei piani base). In C23 questo passaggio intenzionale si dichiara esplicitamente con l'**attributo** (*attribute*) standard `[[fallthrough]];` posto al posto di `break;`. Un **attributo** è un'annotazione standard C23 tra doppie parentesi quadre `[[...]]` che fornisce informazioni aggiuntive al compilatore.

> **C23** — L'attributo standard `[[fallthrough]];` è stato introdotto dallo standard C23. Nei compilatori che supportano solo standard precedenti (C17 o C11) la sintassi `[[fallthrough]];` non è disponibile e viene rifiutata dal compilatore: in quei casi si segnala il fall-through intenzionale con un commento esplicito come `/* fallthrough */` (che molti compilatori riconoscono per sopprimere gli avvisi).

Riassumiamo la regola precisa secondo lo standard C23:

- L'istruzione `switch (espressione)` accetta un'espressione di tipo intero (inclusi `char` e `bool`) e salta all'etichetta `case` con espressione costante intera corrispondente, oppure a `default` se nessuna etichetta coincide.
- Le etichette `case` di uno stesso `switch` devono essere tutte distinte.
- Senza `break` l'esecuzione prosegue nel ramo successivo (`fall-through`); se il `fall-through` dopo istruzioni è intenzionale, in C23 lo si segnala con `[[fallthrough]];`.
- I vincoli sui tipi interi, l'unicità delle costanti `case`, il meccanismo di `fall-through` e l'attributo standard `[[fallthrough]]` sono comportamento completamente **definito** dallo standard C23.

Un ultimo dettaglio pratico riguarda le variabili dichiarate dentro un ramo `case`. Se vuoi introdurre una variabile locale usata solo in un determinato `case`, racchiudi il codice di quel ramo tra parentesi graffe `{ ... }`:

<!-- cod: id=4.3-c tipo=frammento -->
```c
switch (modalita) {
    case 1: {
        int sconto = 10;
        printf("Sconto applicato: %d%%\n", sconto);
        break;
    }
    default:
        printf("Nessuno sconto\n");
        break;
}
```

Le parentesi graffe limitano la variabile `sconto` a quel solo ramo e impediscono al programma di saltare oltre la sua inizializzazione entrando in un `case` successivo (dove resterebbe visibile ma non inizializzata), evitando inoltre conflitti di nomi tra rami ed errori di compilazione negli standard precedenti al C23.

> **Se vieni da Python** — In Python il costrutto `match`/`case` non ha fall-through tra i rami: una volta completato un ramo, l'esecuzione esce automaticamente dal blocco. Nello `switch` del C, invece, l'esecuzione prosegue nel `case` successivo se non termini il ramo con `break;` (e in C23, quando vuoi davvero proseguire dopo delle istruzioni, lo dichiari con `[[fallthrough]];`).

### Esempio guidato

Il programma seguente utilizza due istruzioni `switch`. Il primo `switch` esamina il numero di un giorno della settimana (`1..7`) e raggruppa le etichette vuote per distinguere i giorni lavorativi (`1..5`) dal fine settimana (`6..7`), con un ramo `default` per eventuali numeri fuori intervallo. Il secondo `switch` esamina il livello di un abbonamento (`1..3`) e sfrutta il fall-through intenzionale annotato con `[[fallthrough]];` per elencare tutti i vantaggi cumulativi inclusi nel livello scelto.

<!-- cod: id=4.3-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    int giorno = 6;
    int livello_abbonamento = 3;

    switch (giorno) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
            printf("Giorno %d: lavorativo\n", giorno);
            break;
        case 6:
        case 7:
            printf("Giorno %d: fine settimana\n", giorno);
            break;
        default:
            printf("Giorno %d: valore non valido\n", giorno);
            break;
    }

    printf("Vantaggi abbonamento (livello %d):\n", livello_abbonamento);
    switch (livello_abbonamento) {
        case 3:
            printf("- Consulenza prioritaria\n");
            [[fallthrough]];
        case 2:
            printf("- Accesso ai laboratori serali\n");
            [[fallthrough]];
        case 1:
            printf("- Prestito libri della biblioteca\n");
            break;
        default:
            printf("- Livello non riconosciuto\n");
            break;
    }

    return 0;
}
```

```output
Giorno 6: fine settimana
Vantaggi abbonamento (livello 3):
- Consulenza prioritaria
- Accesso ai laboratori serali
- Prestito libri della biblioteca
```

Osserva come lavorano i due `switch`:

- Nel primo `switch`, `giorno` vale `6`: il flusso salta direttamente a `case 6:`, prosegue attraverso l'etichetta vuota `case 7:`, stampa `Giorno 6: fine settimana` e si ferma grazie a `break;`.
- Nel secondo `switch`, `livello_abbonamento` vale `3`. Il flusso entra in `case 3:`, stampa il vantaggio del livello 3 e incontra `[[fallthrough]];`, proseguendo intenzionalmente in `case 2:`, poi in `case 1:`, fino al `break;` che evita di entrare anche in `default:`.
- Se cambiassi `livello_abbonamento` a `1`, verrebbe stampato solo il terzo vantaggio; se lo impostassi a `9`, entrerebbe in `default:`.

> **Approfondimento — Dimenticare `break` e il ruolo di `[[fallthrough]]`**
> Dimenticare un `break;` al termine di un ramo `case` è uno degli errori logici più frequenti in C: il programma compila senza errori, ma esegue silenziosamente anche le istruzioni del `case` successivo, sovrascrivendo risultati o stampando messaggi sbagliati. Quando attivi gli avvisi del compilatore (per esempio con `-Wextra`), il compilatore può segnalare i fall-through non annotati come sospetti. Scrivere `[[fallthrough]];` nei rari casi in cui il passaggio è voluto comunica chiaramente la tua intenzione sia a chi legge il codice sia al compilatore, permettendogli di avvisarti soltanto quando hai davvero dimenticato un `break;`.

### Esercizio 4.3 — Biglietteria ferroviaria con `switch` e `[[fallthrough]]`

**Descrizione**

Un sistema di biglietteria elabora un viaggio descritto da `char codice_treno = 'i';` (`'R'`/`'r'` = Regionale a `0.12` euro/km; `'I'`/`'i'` = Intercity a `0.18` euro/km; `'A'`/`'a'` = Alta Velocità a `0.26` euro/km; altro = codice non valido), `int distanza_km = 150;` e `int livello_servizio = 2;` (`3` = Executive, `2` = Business, `1` = Standard). Scrivi un programma C con due istruzioni `switch`: il primo `switch` su `codice_treno` raggruppa lettere maiuscole e minuscole, imposta la tariffa chilometrica (gestendo il caso imprevisto in `default`) e stampa categoria e prezzo base con due cifre decimali; il secondo `switch` su `livello_servizio` usa il fall-through intenzionale annotato con l'attributo C23 `[[fallthrough]];` per stampare i servizi cumulativi inclusi (`case 3`: `- Accesso lounge stazione`, `case 2`: `- Posto riservato con presa elettrica`, `case 1`: `- Trasporto bagaglio a mano`, `default`: `- Livello servizio non riconosciuto`). Stampa l'output esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- costrutto `switch`, `case`, `break` e `default`
- raggruppamento di etichette `case` vuote
- fall-through intenzionale
- attributo C23 `[[fallthrough]]`

**Domande guida**

1. Perché un carattere `char` come `codice_treno` può essere usato direttamente come espressione di uno `switch`?
2. Come puoi gestire sia `'I'` maiuscola sia `'i'` minuscola nello `switch` senza duplicare le istruzioni?
3. Quale differenza c'è tra dimenticare un `break` per errore e usare `[[fallthrough]];` in modo intenzionale?
4. Perché conviene inserire sempre un ramo `default` anche quando ti aspetti solo alcuni valori?

**Esempio di esecuzione**

```output
Categoria treno: Intercity
Distanza: 150 km
Prezzo base: 27.00 euro
Servizi inclusi (livello 2):
- Posto riservato con presa elettrica
- Trasporto bagaglio a mano
```

## 4.4 L'operatore condizionale `?:`

Capita spesso di dover scegliere semplicemente tra **due valori** in base a una condizione: per esempio il massimo tra due numeri, uno sconto applicato o nullo, oppure un carattere `'S'` o `'N'`. Con `if / else` devi prima dichiarare la variabile (senza poterla rendere `const`), poi assegnarle un valore in un ramo e un altro valore nell'`else`. Per queste scelte dirette tra due valori, il C offre l'**operatore condizionale** `?:`, l'unico operatore ternario (cioè con tre operandi) del linguaggio.

La sua sintassi è:

```text
condizione ? expr_vero : expr_falso
```

La differenza fondamentale rispetto a `if / else` è che `if / else` è un'**istruzione** (esegue blocchi di codice e non produce un valore), mentre `?:` è un'**espressione** che produce un valore utilizzabile ovunque sia ammessa un'espressione: nell'inizializzazione di una variabile, dentro una chiamata a `printf` o in un calcolo più ampio.

Come funziona la valutazione? Prima viene valutata `condizione`. Tra `condizione` e il ramo scelto esiste un punto di sequenza: se `condizione` è diversa da zero (vera), viene valutata **esclusivamente** `expr_vero` e il suo valore è il risultato dell'intero operatore; se `condizione` vale zero (falsa), viene valutata **esclusivamente** `expr_falso`. Il ramo non scelto non viene mai valutato, esattamente come avviene nella valutazione a corto circuito.

Che tipo ha il risultato di `?:`? Se `expr_vero` ed `expr_falso` hanno tipi aritmetici diversi (per esempio un `int` e un `double`), il C determina il tipo risultante applicando le **conversioni aritmetiche usuali** che hai visto nel capitolo 3: per esempio `flag ? 10 : 2.5` produce sempre un `double` (`10.0` oppure `2.5`), indipendentemente da quale ramo viene scelto a tempo di esecuzione.

Un punto critico a cui fare molta attenzione è la **precedenza degli operatori**: `?:` ha una precedenza molto bassa — tra gli operatori visti finora, superiore soltanto agli operatori di assegnamento (`=`, `+=`, ...) — e ha associatività da destra a sinistra. Di conseguenza, quando inserisci `?:` dentro un'espressione aritmetica o di confronto, devi **sempre racchiuderlo tra parentesi tonde**:

<!-- cod: id=4.4-b tipo=frammento -->
```c
int totale = base + (consegna_rapida ? 10 : 0);
```

Senza parentesi, il compilatore raggrupperebbe `base + consegna_rapida` come condizione del `?:`, ottenendo un risultato completamente sbagliato.

Riassumiamo la regola precisa secondo lo standard C23:

- L'operatore condizionale `condizione ? expr_vero : expr_falso` è un'espressione: valuta `condizione` e poi valuta esclusivamente `expr_vero` (se `condizione` è diversa da zero) oppure `expr_falso` (se `condizione` vale zero).
- Ha precedenza molto bassa (tra gli operatori visti finora, superiore solo agli assegnamenti) e associatività da destra a sinistra, perciò va racchiuso tra parentesi quando compare dentro espressioni più ampie.
- La valutazione esclusiva di uno solo dei due rami, il punto di sequenza dopo `condizione`, la precedenza e la determinazione del tipo risultante di `?:` sono comportamento completamente **definito** dallo standard C23.

Quando conviene usare `?:`? In tre situazioni tipiche in cui rende il codice più corto e più leggibile:

1. **Massimo o minimo tra due valori**: `int massimo = (a >= b) ? a : b;`.
2. **Inizializzazione diretta di una variabile `const`**: poiché una variabile `const` va inizializzata nel momento stesso in cui nasce, `?:` ti permette di calcolarne il valore in una sola riga senza dover rinunciare a `const`.
3. **Scelta tra due valori o caratteri semplici**: per esempio `char codice = residente ? 'R' : 'O';` o un supplemento condizionale.

Quando invece va **evitato**? Non annidare mai più operatori `?:` uno dentro l'altro in catene lunghe (come `a ? b : c ? d : e`) e non inserire dentro `?:` calcoli lunghi o effetti collaterali: il codice diventa subito difficile da decifrare. Appena la decisione ha più di due casi o richiede più passaggi, torna a `if / else if / else` o a `switch`.

> **Se vieni da Python** — In Python l'espressione condizionale mette la condizione al centro e si scrive `valore_vero if condizione else valore_falso`. In C la condizione viene sempre per prima, seguita da `?` e `:`: `condizione ? valore_vero : valore_falso`.

### Esempio guidato

Il programma seguente calcola la tariffa di un parcheggio. Usa l'operatore condizionale `?:` per quattro compiti adatti alla sua natura di espressione: inizializzare una `const double` con la tariffa oraria (residente oppure ordinaria), calcolare le ore fatturate come massimo tra ore effettive e minimo fatturabile (`1.0`), selezionare il codice di fascia (`'R'` o `'O'`) e sommare un eventuale supplemento notturno usando parentesi esplicite attorno a `?:`.

<!-- cod: id=4.4-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    bool residente = false;
    bool fascia_notturna = true;
    double ore_effettive = 0.5;
    constexpr double MINIMO_ORE = 1.0;

    const double tariffa_oraria = residente ? 1.50 : 2.80;
    const double ore_fatturate = (ore_effettive >= MINIMO_ORE) ? ore_effettive : MINIMO_ORE;
    const char codice_fascia = residente ? 'R' : 'O';

    double costo_base = ore_fatturate * tariffa_oraria;
    double totale = costo_base + (fascia_notturna ? 2.00 : 0.00);

    printf("Codice fascia: %c\n", codice_fascia);
    printf("Tariffa oraria: %.2f euro\n", tariffa_oraria);
    printf("Ore fatturate: %.2f h\n", ore_fatturate);
    printf("Totale parcheggio: %.2f euro\n", totale);

    return 0;
}
```

```output
Codice fascia: O
Tariffa oraria: 2.80 euro
Ore fatturate: 1.00 h
Totale parcheggio: 4.80 euro
```

Esaminiamo le scelte fatte nel programma:

- `tariffa_oraria`, `ore_fatturate` e `codice_fascia` sono dichiarate `const` e inizializzate direttamente grazie a `?:`: nessuno può modificarle per errore nel resto di `main`.
- Poiché `ore_effettive` (`0.5`) è minore di `MINIMO_ORE` (`1.0`), l'espressione `(ore_effettive >= MINIMO_ORE) ? ore_effettive : MINIMO_ORE` sceglie `MINIMO_ORE`, cioè `1.0`.
- Nel calcolo di `totale`, le parentesi tonde attorno a `(fascia_notturna ? 2.00 : 0.00)` garantiscono che prima venga scelto il supplemento (`2.00` perché `fascia_notturna` è `true`) e poi lo si sommi a `costo_base` (`2.80`), ottenendo `4.80`.

> **Approfondimento — Variabili `const` e l'insidia della precedenza**
> Un vantaggio concreto di `?:` è l'inizializzazione di variabili `const`: con `if / else` dovresti dichiarare una variabile non costante e poi assegnarla nei due rami, perdendo la garanzia che non venga modificata in seguito. Attenzione però alla precedenza bassa di `?:`. Considera l'espressione senza parentesi `10 + flag ? 1 : 2` con `flag = 0`. Poiché `+` ha precedenza superiore a `?:`, il compilatore la raggruppa come `(10 + flag) ? 1 : 2`. La somma `10 + 0` vale `10` (diverso da zero, quindi vero), e l'intera espressione produce `1` invece dell'atteso `12`! Per ottenere `12` devi scrivere `10 + (flag ? 1 : 2)`.

### Esercizio 4.4 — Valutazione di una gara di salto in lungo con `?:`

**Descrizione**

In una gara di salto in lungo un atleta registra due salti validi (`double salto_1 = 6.45;` e `double salto_2 = 6.78;` in metri), con vento a favore `double vento_ms = 1.6;` e `bool categoria_junior = true;`. Scrivi un programma C che usi l'operatore condizionale `?:` per inizializzare direttamente sette variabili `const`: `miglior_salto` (massimo tra i due salti), `peggior_salto` (minimo tra i due salti), `scarto` (differenza non negativa tra i due salti calcolata con `?:`), `soglia_qualifica` (`6.50` per junior, `7.10` altrimenti), `esito_vento` (`'V'` se `vento_ms <= 2.0`, `'I'` altrimenti), `punti_base` (`100` se `miglior_salto >= soglia_qualifica`, `60` altrimenti) e `punti_totali` (ottenuto sommando a `punti_base` un bonus di `15` punti se `esito_vento` vale `'V'`, altrimenti `0`, racchiudendo `?:` tra parentesi tonde esplicite). Usa poi un'istruzione `if / else` leggibile (senza annidare `?:`) per stampare `Esito: Qualificato per la finale` se `miglior_salto` raggiunge o supera `soglia_qualifica`, altrimenti `Esito: Non qualificato`. Produci l'output esatto dell'esempio di esecuzione.

**Concetti da tenere a mente**

- operatore condizionale `?:`
- inizializzazione diretta di variabili `const` tramite `?:`
- precedenza bassa di `?:` e uso delle parentesi tonde
- scelta equilibrata tra `?:` e `if / else`

**Domande guida**

1. Perché puoi inizializzare direttamente una variabile `const` usando `?:` mentre non potresti farlo direttamente con un'istruzione `if / else`?
2. Che cosa cambierebbe nel calcolo di `punti_totali` se togliessi le parentesi tonde attorno all'operatore condizionale sommato a `punti_base`?
3. Come puoi calcolare la differenza non negativa tra `salto_1` e `salto_2` usando una sola espressione `?:` senza ricorrere a `fabs`?
4. In quali casi conviene comunque usare `if / else` invece di combinare più operatori `?:` annidati?

**Esempio di esecuzione**

```output
Miglior salto: 6.78 m
Peggior salto: 6.45 m
Scarto tra i salti: 0.33 m
Soglia qualifica: 6.50 m
Codice vento: V
Punti base: 100
Punti totali: 115
Esito: Qualificato per la finale
```

## Riepilogo

- Il **flusso di controllo** determina quali istruzioni vengono eseguite e in quale ordine. L'istruzione `if (condizione) { ... }` esegue il proprio blocco se `condizione` è diversa da zero e l'eventuale `else { ... }` se vale zero; in una catena `if / else if / else` viene eseguito al più un solo ramo. Racchiudi sempre ogni ramo tra parentesi graffe per evitare errori e il problema del *dangling else*.
- Gli operatori `&&` e `||` garantiscono la **valutazione a corto circuito**: valutano sempre prima l'operando sinistro e non valutano il destro se il risultato è già determinato (`0` per `&&`, diverso da `0` per `||`). Puoi usare questa garanzia come guardia per prevenire la divisione intera per zero (`n != 0 && somma / n >= 6`) e gli errori di dominio di `sqrt` (`x >= 0.0 && sqrt(x) > 3.0`). Non inserire effetti collaterali come `++` nell'operando destro.
- Dentro un `if`, confronta i numeri in virgola mobile usando `fabs(a - b) <= tolleranza`, mai con `==`.
- Il costrutto `switch (espressione)` confronta un'espressione di tipo intero (inclusi `char` e `bool`, mai `double`) con etichette `case` aventi espressioni costanti intere tutte distinte (in C23 anche `constexpr`), più un ramo `default` consigliato per intercettare valori imprevisti.
- Senza `break;`, lo `switch` prosegue nel ramo successivo (**fall-through**). Il raggruppamento di etichette `case` vuote è idiomatico; quando il fall-through dopo istruzioni è intenzionale, in C23 va dichiarato con l'**attributo** `[[fallthrough]];` (in C17/C11 con un commento esplicito). Per dichiarare variabili locali dentro un `case`, racchiudi il ramo in un blocco `{ ... }`.
- L'operatore condizionale `condizione ? expr_vero : expr_falso` è un'espressione che valuta un solo ramo in base a `condizione`. È utile per massimo/minimo, scelta tra due valori e inizializzazione diretta di variabili `const`, ma ha precedenza molto bassa: racchiudilo sempre tra parentesi dentro espressioni più ampie ed evita di annidarlo. Nel prossimo capitolo imparerai a leggere dati dalla tastiera per rendere dinamiche queste decisioni (lo vedremo nel capitolo 5).

## Errori comuni

- **Scrivere `=` (assegnamento) al posto di `==` (uguaglianza) dentro la condizione di un `if`**: `if (x = 1)` modifica `x` invece di confrontarla e risulta sempre vero; attiva `-Wall -Wextra` per far segnalare l'errore dal compilatore.
- **Inserire per errore un punto e virgola subito dopo `if (condizione);`**: il punto e virgola chiude il corpo dell'`if` con un'istruzione vuota, così il blocco successivo viene eseguito sempre, indipendentemente dalla condizione.
- **Omettere le parentesi graffe in `if`/`else` annidati**: senza graffe un `else` si associa sempre all'`if` aperto più vicino (*dangling else*), ignorando l'indentazione, e aggiungere una seconda istruzione in un ramo la lascia fuori dalla condizione.
- **Invertire l'ordine degli operandi in una guardia con `&&`**: scrivere `somma / n >= 6 && n != 0` esegue prima la divisione e provoca comportamento indefinito quando `n` è zero; la guardia deve sempre stare a sinistra.
- **Dimenticare `break;` al termine di un ramo `case` nello `switch`**: provoca un fall-through involontario che esegue anche i rami successivi; termina ogni ramo con `break;` oppure, se il passaggio è voluto, dichiaralo in C23 con `[[fallthrough]];`.
- **Usare `?:` dentro un'espressione aritmetica senza parentesi o annidare più `?:`**: espressioni come `a + flag ? 1 : 0` vengono raggruppate come `(a + flag) ? 1 : 0`; usa sempre le parentesi tonde attorno a `?:` e preferisci `if / else` per scelte articolate.

## Prima di proseguire

- [ ] So scrivere selezioni con `if`, `else if`, `else` e `if` annidati usando sempre le parentesi graffe e soglie ordinate senza sovrapposizioni.
- [ ] So sfruttare la valutazione a corto circuito di `&&` e `||` per scrivere guardie sicure prima di divisioni intere o chiamate a `sqrt`, evitando effetti collaterali nell'operando destro.
- [ ] So scegliere quando usare `switch` al posto di `if / else if`, usare `break` e `default`, raggruppare etichette `case` vuote e annotare il fall-through intenzionale con `[[fallthrough]];`.
- [ ] So usare l'operatore condizionale `?:` con parentesi esplicite per scegliere tra due valori o inizializzare una variabile `const`, evitando annidamenti illeggibili.
