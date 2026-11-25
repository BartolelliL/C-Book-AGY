## 1.2 La struttura di un programma C

Hai visto nella sotto-sezione precedente che bastano sei righe per creare ed eseguire un programma C. In quelle sei righe, però, non c'è nulla di superfluo: ogni elemento svolge un compito preciso e segue regole rigide. Conoscere la struttura di base fin da subito ti evita di copiare righe "a memoria" senza sapere perché siano lì.

La prima riga di quasi tutti i programmi che scriverai all'inizio è `#include <stdio.h>`. Il simbolo `#` indica una direttiva del preprocessore: prima ancora che inizi la compilazione vera e propria, il preprocessore inserisce nel sorgente le dichiarazioni contenute nell'header `stdio.h` (abbreviazione di *standard input/output*). Le parentesi angolari `<` e `>` segnalano che si tratta di un header della libreria standard fornito con il compilatore. In C23 vige una regola precisa: per chiamare una funzione della libreria standard come `printf`, è obbligatorio includere prima l'header che la dichiara. Secondo lo standard C23 ogni funzione deve essere dichiarata prima dell'uso; chiamare `printf` senza includere `<stdio.h>` viola i vincoli del linguaggio e produce un errore di compilazione.

Subito dopo gli `#include` compare la definizione della funzione `main`:

<!-- cod: id=1.2-b tipo=frammento -->
```c
int main(void) {
    // istruzioni del programma
    return 0;
}
```

Ogni programma C destinato a essere eseguito su un normale sistema operativo (quello che lo standard chiama *ambiente ospitato*) deve definire la funzione `main` come punto di ingresso. Quando avvii l'eseguibile, il sistema operativo cerca proprio `main` e inizia a eseguire le istruzioni scritte al suo interno, una dopo l'altra dall'alto verso il basso.

Osserva le tre parole dell'intestazione `int main(void)`:

- `int` indica il tipo di valore che `main` restituirà al termine dell'esecuzione: un numero intero;
- `main` è il nome obbligatorio della funzione di ingresso;
- `void` dentro le parentesi tonde specifica esplicitamente che questa versione di `main` non riceve argomenti (vedremo come ricevere argomenti da riga di comando più avanti nel libro).

La forma standard senza argomenti da riga di comando è `int main(void)`. Secondo lo standard C23 questa firma è completamente definita per gli ambienti ospitati, mentre varianti diffuse in vecchi manuali come `void main()` non sono conformi allo standard e non vanno mai usate.

Tutto ciò che `main` deve fare è racchiuso tra una parentesi graffa aperta `{` e una parentesi graffa chiusa `}`: questa coppia delimita un blocco di istruzioni. All'interno del blocco, ogni istruzione semplice — come una chiamata a `printf` o l'istruzione `return 0;` — deve terminare obbligatoriamente con il punto e virgola (`;`). Il punto e virgola svolge in C il ruolo che il punto fermo svolge in italiano: indica al compilatore dove finisce un'istruzione e dove può iniziare la successiva.

L'ultima istruzione del blocco è `return 0;`. Il valore intero restituito da `main` comunica al sistema operativo l'esito dell'esecuzione: `0` segnala che il programma si è concluso correttamente, mentre un valore diverso da `0` indica un errore. Lo standard C23 definisce con precisione che `return 0` (e, per la sola funzione `main`, anche il raggiungimento della parentesi graffa di chiusura) equivalgono a una terminazione con successo; il significato specifico di codici non nulli arbitrari è invece dipendente dall'implementazione del sistema operativo. In questo libro scriverai sempre `return 0;` in modo esplicito, così che la fine del programma sia sempre chiara a colpo d'occhio.

Infine, tieni presenti due regole pratiche sulla scrittura del codice:

1. **Maiuscole e minuscole**: il linguaggio C distingue sempre tra lettere maiuscole e minuscole (*case-sensitive*). Per il compilatore `main`, `Main` e `MAIN` sono tre nomi diversi, e lo stesso vale per `printf` e `Printf`. La grammatica delle istruzioni e questa distinzione sono fissate dallo standard C23.
2. **Spazi bianchi e indentazione**: il compilatore ignora gli spazi aggiuntivi e i ritorni a capo tra un elemento sintattico e l'altro (tranne dentro le stringhe e nelle direttive `#include`). Tuttavia, chi legge il codice — a partire da te tra qualche giorno — ha bisogno di riconoscere a vista la struttura dei blocchi. Per questo in tutto il libro useremo uno stile uniforme: parentesi graffa di apertura `{` sulla stessa riga dell'intestazione e rientro (indentazione) di 4 spazi per tutte le istruzioni dentro il blocco.

> **Se vieni da Python** — In Python i blocchi di codice sono definiti dall'indentazione e non si usa il punto e virgola a fine riga. In C, invece, i blocchi sono sempre delimitati dalle parentesi graffe `{` e `}` e ogni istruzione semplice termina con `;`; l'indentazione non cambia il significato del programma per il compilatore, ma rimane indispensabile per la leggibilità.

### Esempio guidato

Il programma seguente simula il messaggio di avvio di una stazione meteo automatica. Usa tre chiamate consecutive a `printf` per stampare l'intestazione, lo stato dei sensori e la conferma di avvio, mostrando come le istruzioni vengano eseguite rigorosamente in sequenza.

<!-- cod: id=1.2-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    printf("=== Stazione Meteo ===\n");
    printf("Sensori: temperatura e pressione attivi.\n");
    printf("Avvio completato.\n");
    return 0;
}
```

```output
=== Stazione Meteo ===
Sensori: temperatura e pressione attivi.
Avvio completato.
```

Analizziamo il programma riga per riga:

- Riga 1: `#include <stdio.h>` dichiara `printf`, rendendola utilizzabile nel resto del file.
- Riga 3: `int main(void) {` apre la funzione di ingresso e il suo blocco di istruzioni. Nota la riga vuota precedente, che separa visivamente le direttive `#include` dal codice di `main`.
- Righe 4–6: tre chiamate distinte a `printf`, rientrate di 4 spazi e terminate ciascuna da `;`. Il programma le esegue esattamente nell'ordine in cui compaiono, producendo tre righe distinte grazie al `\n` finale di ciascuna stringa.
- Riga 7: `return 0;` conclude `main` restituendo `0` al sistema operativo.
- Riga 8: `}` chiude il blocco di `main`.

Se provassi a scambiare l'ordine delle righe 4 e 6, anche l'output sullo schermo cambierebbe ordine; se dimenticassi anche un solo `;`, il compilatore rifiuterebbe il file senza generare l'eseguibile.

> **Approfondimento — Perché scrivere sempre `int main(void)` e `return 0;`**
> In alcuni vecchi tutorial capita di incontrare `void main()` oppure `int main()` senza `return 0;`. La forma `void main()` non è conforme allo standard C per gli ambienti ospitati: il sistema operativo si aspetta un codice di uscita intero da `main`, e compilatori rigorosi con `-Wpedantic -Werror` rifiutano questa firma. Quanto a `return 0;`, è vero che lo standard C23 inserisce implicitamente un ritorno `0` se l'esecuzione raggiunge la `}` finale di `main`, ma questa eccezione vale *solo* per `main` e non per le altre funzioni che scriverai dal capitolo 7 in poi. Scrivere sempre `return 0;` ti abitua fin dall'inizio a rendere esplicito ciò che ogni funzione restituisce.

### Esercizio 1.2 — Biglietto del museo

**Descrizione**

Scrivi un programma C completo che stampi un biglietto d'ingresso di quattro righe usando una chiamata separata a `printf` per ogni riga. Le quattro righe devono essere esattamente `MUSEO DELLA SCIENZA`, `Ingresso: Mostra di Astronomia`, `Settore: Planetario` e `Stato: Valido`, ciascuna terminata da un ritorno a capo. Il programma deve terminare restituendo il codice di uscita che segnala successo.

**Concetti da tenere a mente**

- preprocessore
- struttura di `main`
- esecuzione sequenziale delle istruzioni
- valore restituito da `main`

**Domande guida**

1. In quale ordine vengono eseguite le istruzioni all'interno delle parentesi graffe di `main`?
2. Che cosa succederebbe all'output se dimenticassi il ritorno a capo in una delle prime tre stampe?
3. Quale simbolo chiude ogni singola istruzione di stampa in C?
4. Quale valore conviene restituire al termine di `main` per indicare che il programma si è concluso senza errori?

**Esempio di esecuzione**

```output
MUSEO DELLA SCIENZA
Ingresso: Mostra di Astronomia
Settore: Planetario
Stato: Valido
```
