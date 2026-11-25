## 19.3 Visibilità tra file: `static`, `extern` e `inline`

Quando un programma è formato da più unità di traduzione, non basta sapere *dove* un identificatore è visibile dentro un singolo file (la visibilità vista nel capitolo 7): occorre anche stabilire se lo stesso nome, dichiarato in file `.c` diversi, indica la stessa funzione o lo stesso oggetto oppure entità distinte. Questa proprietà si chiama **collegamento** (*linkage*): è la proprietà che stabilisce se un identificatore dichiarato in più unità di traduzione indica lo stesso oggetto o funzione (esterno, interno o assente).

In C esistono esattamente tre tipi di collegamento:

- **Collegamento esterno** (*external linkage*): è il comportamento predefinito per funzioni e variabili dichiarate a livello di file (fuori da qualsiasi funzione). Il simbolo viene esportato nel file oggetto e può essere collegato da altre unità di traduzione. Proprio per questo due file `.c` non possono definire entrambi una funzione non-`static` con lo stesso nome: il collegatore rifiuterebbe il duplicato.
- **Collegamento interno** (*internal linkage*): si ottiene qualificando con `static` una funzione o una variabile a livello di file. Il simbolo resta privato alla sola unità di traduzione in cui è definito e non è visibile al collegatore dall'esterno. Due file `.c` diversi possono quindi avere ciascuno una propria funzione `static int32_t helper(...)` senza alcun conflitto.
- **Nessun collegamento** (*no linkage*): riguarda parametri di funzione e variabili locali dichiarate dentro un blocco. Ogni dichiarazione indica un'entità distinta, visibile solo nel blocco.

Fai attenzione a non confondere i due significati di `static`:

- **Dentro una funzione** (capitolo 7): `static` cambia la *durata di vita* della variabile locale (da automatica a statica, cioè persistente per tutta l'esecuzione), ma la variabile continua a non avere collegamento ed è visibile solo in quella funzione.
- **A livello di file** (fuori da tutte le funzioni): `static` cambia il *collegamento* da esterno a interno, rendendo la funzione o la variabile privata al file `.c`.

In un modulo ben progettato, ogni funzione ausiliaria e ogni variabile di supporto che non fa parte dell'interfaccia pubblica dichiarata nel `.h` va marcata `static`. Questo riduce i simboli esposti al minimo indispensabile e impedisce collisioni accidentali quando il progetto cresce.

Come si condivide invece una costante o un dato definito in un file `.c` con altri file `.c`? Con la parola chiave `extern`. Scrivere `extern const int32_t LIMITE;` in un file di intestazione è una pura *dichiarazione*: informa il compilatore che esiste un oggetto `LIMITE` di tipo `const int32_t` con collegamento esterno, ma non riserva memoria. L'unica *definizione* (con l'inizializzatore) viene collocata in un solo file `.c`:

<!-- cod: id=19.3-b tipo=frammento -->
```c
/* in modulo.h: sola dichiarazione */
extern const int32_t LIMITE;

/* in modulo.c: unica definizione */
const int32_t LIMITE = 100;
```

In generale, usa `extern` quasi esclusivamente per costanti o tabelle `const` di sola lettura: condividere stato globale mutabile tra file rende il programma difficile da ragionare e da verificare. Ricorda inoltre che, a differenza delle variabili, i prototipi di funzione a livello di file hanno già collegamento esterno per default, quindi scrivere `extern` davanti a un prototipo è lecito ma superfluo.

Resta un caso frequente: piccole funzioni molto semplici (due o tre righe) che vuoi mettere direttamente nell'header affinché il compilatore possa sostituirle nel punto di chiamata eliminando il costo della chiamata di funzione. Se mettessi una normale funzione nell'header, violeresti la regola di definizione unica appena due file `.c` lo includessero. Il C offre la parola chiave `inline` con due modelli ben precisi:

1. **`static inline` nell'header**: è il modello più semplice e più usato. Ogni unità di traduzione riceve una propria definizione con collegamento interno; nessun simbolo esterno viene esportato e quindi non esistono mai conflitti al collegamento.
2. **`inline` nell'header + `extern inline` in esattamente un file `.c`**: la definizione `inline` (senza `static`) nell'header fornisce al compilatore il corpo da espandere, ma *non* emette una definizione esterna nel file oggetto. Se il compilatore sceglie di non espandere la funzione (per esempio con ottimizzazioni spente `-O0`) oppure se il programma prende l'indirizzo della funzione tramite un puntatore a funzione, il collegatore ha bisogno di un simbolo esterno reale. Per emetterlo una sola volta si scrive una dichiarazione `extern inline` (o una definizione non-`inline`) con la stessa firma in esattamente un file `.c`.

Secondo lo standard C23, le regole di collegamento e il modello `inline`/`extern inline` sono definiti con precisione: usare una funzione `inline` non-`static` senza fornire alcuna definizione esterna nel programma può provocare un errore del collegatore, mentre fornire definizioni `inline` diverse tra unità di traduzione causa **comportamento indefinito**.

### Esempio guidato

Questo esempio su tre file (`contatore.h`, `contatore.c`, `main.c`) combina tutti gli strumenti di collegamento: una costante condivisa `extern const`, una funzione ausiliaria `static` privata a `contatore.c`, un helper `static inline` nell'header e una funzione `inline` con definizione esterna `extern inline` di cui `main.c` prende esplicitamente l'indirizzo.

<!-- cod: id=19.3-a tipo=programma gruppo=cont file=contatore.h -->
```c
#ifndef CONTATORE_H
#define CONTATORE_H

#include <stdint.h>

extern const int32_t SOGLIA_MASSIMA;

static inline int32_t raddoppia(int32_t x) {
    return x * 2;
}

inline int32_t limita_valore(int32_t x, int32_t max_val) {
    return (x > max_val) ? max_val : x;
}

int32_t normalizza_punteggio(int32_t grezzo);

#endif
```

<!-- cod: id=19.3-c tipo=programma gruppo=cont file=contatore.c -->
```c
#include "contatore.h"

const int32_t SOGLIA_MASSIMA = 100;

extern inline int32_t limita_valore(int32_t x, int32_t max_val);

static int32_t aggiusta_negativo(int32_t x) {
    return (x < 0) ? 0 : x;
}

int32_t normalizza_punteggio(int32_t grezzo) {
    int32_t non_neg = aggiusta_negativo(grezzo);
    return limita_valore(non_neg, SOGLIA_MASSIMA);
}
```

<!-- cod: id=19.3-d tipo=programma gruppo=cont file=main.c -->
```c
#include <inttypes.h>
#include <stdio.h>
#include "contatore.h"

typedef int32_t (*limita_fn)(int32_t, int32_t);

int main(void) {
    limita_fn fn = limita_valore;
    int32_t a = normalizza_punteggio(-15);
    int32_t b = normalizza_punteggio(65);
    int32_t c = raddoppia(b);

    printf("Soglia condivisa: %" PRId32 "\n", SOGLIA_MASSIMA);
    printf("Normalizzati: %" PRId32 ", %" PRId32 "\n", a, b);
    printf("Raddoppiato e limitato: %" PRId32 "\n", fn(c, SOGLIA_MASSIMA));
    return 0;
}
```

```output
Soglia condivisa: 100
Normalizzati: 0, 65
Raddoppiato e limitato: 100
```

Osserva il ruolo di ogni qualificatore:

- `SOGLIA_MASSIMA` è dichiarata `extern const` in `contatore.h` e definita una sola volta in `contatore.c`: sia `contatore.c` sia `main.c` leggono lo stesso oggetto.
- `aggiusta_negativo` è `static` in `contatore.c`: non compare in `contatore.h` e un altro file `.c` potrebbe definire una propria funzione `static` con lo stesso nome senza collisioni.
- `raddoppia` è `static inline`: ogni unità di traduzione che include `contatore.h` può chiamarla senza esportare simboli al collegatore.
- `limita_valore` è `inline` in `contatore.h` e ha `extern inline` in `contatore.c`: quando `main.c` ne assegna l'indirizzo al puntatore a funzione `fn`, il collegatore trova la definizione esterna emessa da `contatore.o`.

> **Approfondimento — Il modello `inline` del C23 rispetto al C++**
> Chi conosce il C++ spesso si aspetta che scrivere `inline` in un header generi automaticamente un simbolo esterno unificato dal collegatore. In C non funziona così: una definizione `inline` priva di `static` nell'header è un'alternativa a disposizione del compilatore, non una definizione esterna. Se compili senza ottimizzazioni (`-O0`) o prendi l'indirizzo della funzione e dimentichi `extern inline` in un file `.c`, il collegatore segnala un simbolo non risolto. Per piccoli helper di modulo, `static inline` nell'header è quasi sempre la scelta più semplice e sicura.

### Esercizio 19.3 — Moduli con helper `static` omonimi, tabelle `extern const` e funzioni `static inline` / `extern inline`

**Descrizione**

Scrivi un programma C organizzato su cinque file (`valuta.h`, `valuta.c`, `imposta.h`, `imposta.c`, `main.c`) che eserciti in modo completo il collegamento esterno, il collegamento interno con `static`, le dichiarazioni `extern` e le funzioni `inline` del C23.

1. In `valuta.h` (protetto da `VALUTA_H`) dichiara `extern const int32_t TASSI_MILLI[];` ed `extern const size_t NUM_VALUTE;`, definisci `static inline int64_t cent_da_euro(int64_t euro)` (`euro * 100`), definisci `inline int64_t satura_cent(int64_t v, int64_t lo, int64_t hi)` (limita `v` a `[lo, hi]`) e dichiara `bool converti_cent(int64_t cent, size_t cod_valuta, int64_t *out);`.
2. In `valuta.c` definisci `const int32_t TASSI_MILLI[] = {1000, 1080, 860};`, `const size_t NUM_VALUTE = 3;`, la dichiarazione esterna `extern inline int64_t satura_cent(int64_t v, int64_t lo, int64_t hi);`, una funzione privata `static int64_t applica_fattore(int64_t base, int32_t milli)` che calcola il prodotto scalato per `1000` con arrotondamento al centesimo più vicino (`(base >= 0) ? (base * (int64_t)milli + 500) / 1000 : (base * (int64_t)milli - 500) / 1000`), e `converti_cent` (che verifica `cod_valuta < NUM_VALUTE`).
3. In `imposta.h` (protetto da `IMPOSTA_H`) dichiara `extern const int32_t ALIQUOTA_PREDEFINITA_MILLI;` e `int64_t calcola_lordo_cent(int64_t netto_cent, int32_t aliquota_milli);`.
4. In `imposta.c` definisci `const int32_t ALIQUOTA_PREDEFINITA_MILLI = 220;`, una propria funzione privata `static int64_t applica_fattore(int64_t base, int32_t milli)` con lo STESSO nome di quella in `valuta.c` (dimostrando che `static` evita collisioni al collegamento) che calcola `base + (base * (int64_t)milli + 500) / 1000` (o `- 500` se negativo), e `calcola_lordo_cent` (usa `ALIQUOTA_PREDEFINITA_MILLI` quando `aliquota_milli < 0`).
5. In `main.c` assegna l'indirizzo di `satura_cent` a un puntatore a funzione `clamp_fn fn_satura = satura_cent;` (verificando al collegamento l'emissione del simbolo `extern inline`) e leggi da `stdin` i comandi `EURO <e>`, `CONV <cent> <cod>`, `IVA <cent> <aliquota_milli>` e `CLAMP <v> <lo> <hi>`, stampando l'output esatto dell'esempio.

**Concetti da tenere a mente**

- collegamento interno con `static` a livello di file per evitare collisioni tra funzioni omonime in file `.c` diversi
- dichiarazione `extern` nell'header associata a un'unica definizione `const` nel file `.c`
- differenza tra `static inline` (collegamento interno) e `inline` nell'header + `extern inline` in un solo `.c`
- verifica della definizione esterna di una funzione `inline` prendendone l'indirizzo tramite puntatore a funzione

**Domande guida**

1. Perché il programma si collega senza errori nonostante sia `valuta.c` sia `imposta.c` definiscano una funzione chiamata `applica_fattore`?
2. Che cosa accadrebbe al collegamento se rimuovessi `extern inline int64_t satura_cent(...);` da `valuta.c` mantenendo `fn_satura = satura_cent;` in `main.c`?
3. Perché nell'header `valuta.h` scrivi `extern const size_t NUM_VALUTE;` senza inizializzatore, riservando `= 3` al solo `valuta.c`?
4. Qual è la differenza di collegamento tra `cent_da_euro` (`static inline`) e `satura_cent` (`inline` + `extern inline`)?

**Esempio di esecuzione**

```input
EURO 15
CONV 1000 1
CONV 1000 9
IVA 1000 -1
IVA 500 100
CLAMP 2500 0 2000
```

```output
EURO 15 -> 1500 cent
CONV 1000 [1] -> 1080 cent
CONV ERRORE VALUTA 9
IVA 1000 -> 1220 cent
IVA 500 -> 550 cent
CLAMP -> 2000 cent
```
