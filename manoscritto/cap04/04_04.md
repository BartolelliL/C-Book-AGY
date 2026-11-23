## 4.4 L'operatore condizionale `?:`

Capita spesso di dover scegliere semplicemente tra **due valori** in base a una condizione: per esempio il massimo tra due numeri, uno sconto applicato o nullo, oppure un carattere `'S'` o `'N'`. Con `if / else` devi prima dichiarare la variabile (senza poterla rendere `const`), poi assegnarle un valore in un ramo e un altro valore nell'`else`. Per queste scelte dirette tra due valori, il C offre l'**operatore condizionale** `?:`, l'unico operatore ternario (cioè con tre operandi) del linguaggio.

La sua sintassi è:

```text
condizione ? expr_vero : expr_falso
```

La differenza fondamentale rispetto a `if / else` è che `if / else` è un'**istruzione** (esegue blocchi di codice e non produce un valore), mentre `?:` è un'**espressione** che produce un valore utilizzabile ovunque sia ammessa un'espressione: nell'inizializzazione di una variabile, dentro una chiamata a `printf` o in un calcolo più ampio.

Come funziona la valutazione? Prima viene valutata `condizione`. Tra `condizione` e il ramo scelto esiste un punto di sequenza: se `condizione` è diversa da zero (vera), viene valutata **esclusivamente** `expr_vero` e il suo valore è il risultato dell'intero operatore; se `condizione` vale zero (falsa), viene valutata **esclusivamente** `expr_falso`. Il ramo non scelto non viene mai valutato, esattamente come avviene nella valutazione a corto circuito.

Che tipo ha il risultato di `?:`? Se `expr_vero` ed `expr_falso` hanno tipi aritmetici diversi (per esempio un `int` e un `double`), il C determina il tipo risultante applicando le **conversioni aritmetiche usuali** che hai visto nel capitolo 3: per esempio `flag ? 10 : 2.5` produce sempre un `double` (`10.0` oppure `2.5`), indipendentemente da quale ramo viene scelto a tempo di esecuzione.

Un punto critico a cui fare molta attenzione è la **precedenza degli operatori**: `?:` ha una precedenza molto bassa, superiore soltanto agli operatori di assegnamento (`=`, `+=`, ...), e ha associatività da destra a sinistra. Di conseguenza, quando inserisci `?:` dentro un'espressione aritmetica o di confronto, devi **sempre racchiuderlo tra parentesi tonde**:

<!-- cod: id=4.4-b tipo=frammento -->
```c
int totale = base + (consegna_rapida ? 10 : 0);
```

Senza parentesi, il compilatore raggrupperebbe `base + consegna_rapida` come condizione del `?:`, ottenendo un risultato completamente sbagliato.

Riassumiamo la regola precisa secondo lo standard C23:

- L'operatore condizionale `condizione ? expr_vero : expr_falso` è un'espressione: valuta `condizione` e poi valuta esclusivamente `expr_vero` (se `condizione` è diversa da zero) oppure `expr_falso` (se `condizione` vale zero).
- Ha precedenza molto bassa (superiore solo agli assegnamenti) e associatività da destra a sinistra, perciò va racchiuso tra parentesi quando compare dentro espressioni più ampie.
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

In una gara di salto in lungo un atleta registra due salti validi (`double salto_1 = 6.45;` e `double salto_2 = 6.78;` in metri), con vento a favore `double vento_ms = 1.6;` e `bool categoria_junior = true;`. Scrivi un programma C che usi l'operatore condizionale `?:` per inizializzare direttamente sette variabili `const`: `miglior_salto` (massimo tra i due salti), `peggior_salto` (minimo tra i due salti), `scarto` (differenza non negativa tra i due salti calcolata con `?:`), `soglia_qualifica` (`6.50` per junior, `7.10` altrimenti), `esito_vento` (`'V'` se `vento_ms <= 2.0`, `'I'` altrimenti), `punti_base` (`100` se `miglior_salto >= soglia_qualifica`, `60` altrimenti) e `punti_totali` (`punti_base + (esito_vento == 'V' ? 15 : 0)`, con parentesi esplicite attorno a `?:`). Usa poi un'istruzione `if / else` leggibile (senza annidare `?:`) per stampare l'esito finale di qualificazione. Produci l'output esatto dell'esempio di esecuzione.

**Concetti da tenere a mente**

- operatore condizionale `?:`
- inizializzazione diretta di variabili `const` tramite `?:`
- precedenza bassa di `?:` e uso delle parentesi tonde
- scelta equilibrata tra `?:` e `if / else`

**Domande guida**

1. Perché puoi inizializzare direttamente una variabile `const` usando `?:` mentre non potresti farlo direttamente con un'istruzione `if / else`?
2. Che cosa cambierebbe nel risultato di `punti_base + (esito_vento == 'V' ? 15 : 0)` se togliessi le parentesi tonde attorno all'operatore condizionale?
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
