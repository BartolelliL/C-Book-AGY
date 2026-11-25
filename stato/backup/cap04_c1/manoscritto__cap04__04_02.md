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

Il programma seguente valuta i risultati di due studenti usando la valutazione a corto circuito come guardia contro la divisione intera per zero (`numero_prove > 0 && punti_totali / numero_prove >= 60`). Per il primo studente `numero_prove` è `0` e la divisione non viene eseguita; per il secondo `numero_prove` è `4` e la media viene calcolata in sicurezza. Infine il programma mostra una guardia analoga su `sqrt` per verificare la diagonale di un pannello (ricorda di collegare la libreria matematica con `-lm` in compilazione).

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
> il compilatore valuta prima `somma / n >= 6`. Quando `n` vale `0`, la divisione intera per zero viene eseguita prima ancora di raggiungere `n != 0`, provocando **comportamento indefinito** (spesso l'arresto immediato del programma). Metti sempre per prima la condizione che rende sicura la valutazione del resto dell'espressione.

### Esercizio 4.2 — Controlli difensivi con valutazione a corto circuito

**Descrizione**

Scrivi un programma C che includa `<stdio.h>` e `<math.h>` (compilato con `-lm`) ed esegua tre controlli difensivi basati sulla valutazione a corto circuito. Primo: per il sensore A (`int campioni_a = 0;`, `int somma_a = 420;`) e il sensore B (`int campioni_b = 6;`, `int somma_b = 390;`), usa la condizione con guardia `campioni > 0 && somma / campioni >= 50` per stampare se ciascun sensore ha `media sufficiente`, `media insufficiente` oppure `nessun campione disponibile` (senza mai dividere per zero). Secondo: dati i coefficienti `double a = 1.0;`, `double b = -5.0;`, `double c = 6.0;`, calcola `double delta = b * b - 4.0 * a * c;` e usa `if (fabs(a) > 1e-12 && delta >= 0.0 && sqrt(delta) > 0.0)` per verificare la presenza di due radici reali distinte, calcolandole e stampandole con due cifre decimali (dalla minore alla maggiore). Terzo: verifica se `double tensione = 0.1 + 0.2;` coincide con `double nominale = 0.3;` entro una tolleranza di `1e-9` usando `fabs` e stampa l'esito esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- valutazione a corto circuito di `&&`
- ordine degli operandi nelle guardie
- prevenzione della divisione intera per zero e degli errori di dominio di `sqrt`
- confronto in virgola mobile con `fabs` e tolleranza dentro `if`

**Domande guida**

1. Perché nel controllo del sensore A la divisione `somma_a / campioni_a` non viene mai eseguita anche se `campioni_a` vale `0`?
2. Che cosa succederebbe se invertissi i due operandi scrivendo `somma_a / campioni_a >= 50 && campioni_a > 0`?
3. In che modo la catena di condizioni con `&&` su `a` e `delta` protegge la chiamata a `sqrt(delta)` da un argomento negativo?
4. Perché per verificare se la tensione corrisponde al valore nominale usi `fabs(tensione - nominale) <= 1e-9` invece di `tensione == nominale`?

**Esempio di esecuzione**

```output
Sensore A: nessun campione disponibile
Sensore B: media sufficiente (65)
Equazione: due radici reali distinte (x1 = 2.00, x2 = 3.00)
Tensione: entro la tolleranza nominale
```
