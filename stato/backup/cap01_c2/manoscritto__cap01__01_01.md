## 1.1 Dal codice sorgente all'eseguibile

Prima di scrivere la tua prima riga di C, vale la pena chiarire perché questo linguaggio è ancora così diffuso dopo oltre cinquant'anni. Quando si sviluppa un sistema operativo, il firmware di un dispositivo elettronico o un programma che deve elaborare milioni di dati al secondo, non basta che il codice funzioni: bisogna controllare con precisione quanta memoria usa e in che modo dialoga con l'hardware. Il C nasce proprio con questo scopo: offre un insieme compatto di istruzioni, vicine al funzionamento reale del processore, senza aggiungere strati nascosti tra il tuo codice e la macchina.

Nel corso dei decenni il linguaggio è stato aggiornato più volte dall'organizzazione internazionale ISO, che pubblica un documento ufficiale chiamato standard. Lo standard stabilisce con precisione quali costrutti appartengono al linguaggio e come deve comportarsi un programma valido su qualunque computer. In questo libro useremo lo standard **C23** (ISO/IEC 9899:2024), la revisione più recente del C, che mantiene la compatibilità con la tradizione del linguaggio ma rende il codice più sicuro e leggibile.

Un computer, però, non esegue direttamente il testo scritto in C. Il processore comprende soltanto sequenze numeriche in binario, dette codice macchina. Per questo motivo, quando programmi in C lavori sempre con due file distinti:

- il **codice sorgente** (*source code*): il testo leggibile scritto dal programmatore in un linguaggio di programmazione prima della compilazione, salvato in un file con estensione `.c` (per esempio `ciao.c`);
- l'**eseguibile** (*executable*): il file prodotto dalla compilazione e dal collegamento che il sistema operativo può avviare direttamente.

Puoi pensare al codice sorgente come alla ricetta scritta in italiano e all'eseguibile come al piatto già pronto da servire: ogni volta che cambi anche una sola virgola nella ricetta, devi cucinarla di nuovo se vuoi ottenere un piatto aggiornato. Allo stesso modo, in C ogni modifica al file `.c` ha effetto solo dopo aver rigenerato l'eseguibile.

Il programma che trasforma il codice sorgente in un eseguibile è il **compilatore** (*compiler*): un programma che traduce il codice sorgente C in codice macchina eseguibile verificando sintassi e tipi. In realtà la traduzione completa avviene in tre tappe logiche consecutive, che il compilatore coordina automaticamente per te:

```text
ciao.c  -->  [Preprocessore]  -->  [Compilatore]  -->  [Collegatore]  -->  ciao (eseguibile)
sorgente      espande #...          traduce in          unisce codice       pronto da
                                    codice oggetto      e librerie          eseguire
```

1. Il **preprocessore** (*preprocessor*) è la fase iniziale della traduzione che elabora le direttive introdotte dal simbolo `#` prima che il compilatore analizzi il codice C.
2. Il compilatore vero e proprio legge il testo preparato dal preprocessore, controlla che rispetti le regole grammaticali e di tipo del C e lo traduce in un file intermedio in codice macchina (detto codice oggetto).
3. Il **collegatore** (*linker*) è il programma che unisce i file oggetto e le librerie — in particolare la **libreria standard** (*standard library*), cioè l'insieme di funzioni, tipi e costanti fornito con ogni compilatore C e dichiarato negli header — in un unico eseguibile pronto per il sistema operativo.

La regola pratica che ne deriva è fondamentale: la traduzione del codice sorgente in eseguibile attraversa sempre preprocessore, compilatore e collegatore, e attivare gli avvisi del compilatore aiuta a intercettare molti difetti prima ancora di avviare il programma. Dal punto di vista dello standard C23, le fasi logiche della traduzione sono definite con precisione, mentre i nomi delle opzioni da riga di comando e la forma esatta dei messaggi mostrati sullo schermo dipendono dall'implementazione del compilatore che stai usando.

Per non dipendere da un singolo ambiente grafico e lavorare allo stesso modo su macOS, Linux e Windows, in questo libro compilerai i programmi dal terminale. I due compilatori più diffusi e aderenti al C23 sono `gcc` e `clang`. Supponendo di aver salvato il tuo codice nel file `ciao.c`, il comando di compilazione è:

```text
gcc -std=c23 -Wall -Wextra -Wpedantic -Werror ciao.c -o ciao
```

Se usi `clang`, sostituisci semplicemente `gcc` con `clang`: le opzioni sono identiche. Ecco il significato di ciascuna parte del comando:

- `-std=c23`: richiede al compilatore di applicare le regole dello standard C23;
- `-Wall -Wextra`: attiva un ampio insieme di controlli su costrutti sospetti o potenzialmente errati;
- `-Wpedantic`: segnala qualsiasi estensione non prevista dallo standard C23;
- `-Werror`: trasforma ogni avviso in un errore, impedendo di generare l'eseguibile finché il codice non è pulito;
- `ciao.c`: è il file di codice sorgente in ingresso;
- `-o ciao`: indica il nome del file eseguibile da creare (su Windows verrà creato `ciao.exe`).

Una volta terminata la compilazione senza segnalazioni, puoi avviare l'eseguibile dalla stessa cartella:

- su macOS e Linux: `./ciao`
- su Windows (Prompt dei comandi o PowerShell): `.\ciao.exe`

Il prefisso `./` (oppure `.\` su Windows) indica al terminale di cercare il programma nella cartella corrente.

> **Se vieni da Python** — In Python il codice si esegue direttamente tramite l'interprete, lanciando `python3 file.py` senza produrre un eseguibile separato. In C, invece, il codice sorgente va prima tradotto dal compilatore in un file eseguibile e solo in un secondo momento avviato; ogni volta che modifichi il file `.c`, devi ricompilare prima di rieseguire.

### Esempio guidato

Il programma seguente, che puoi salvare come `ciao.c`, è il più piccolo programma C completo capace di produrre un messaggio visibile sullo schermo: stampa una sola riga di saluto e termina correttamente.

<!-- cod: id=1.1-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    printf("Ciao, mondo!\n");
    return 0;
}
```

```output
Ciao, mondo!
```

Vediamo che cosa accade quando salvi questo testo in `ciao.c` e lo traduci dal terminale:

- La prima riga, `#include <stdio.h>`, è una direttiva per il preprocessore: rende disponibile al programma la dichiarazione di `printf`, la funzione della libreria standard che stampa testo sullo schermo.
- Le righe `int main(void) { ... }` definiscono `main`, il punto da cui parte l'esecuzione del programma. Analizzerai ogni dettaglio di questa struttura nella prossima sotto-sezione.
- L'istruzione `printf("Ciao, mondo!\n");` scrive sullo schermo i caratteri compresi tra le virgolette doppie; la coppia `\n` alla fine fa andare a capo il cursore.
- L'istruzione `return 0;` conclude `main` e comunica al sistema operativo che il programma è terminato senza errori.

Per provarlo sul tuo computer, apri il terminale nella cartella che contiene `ciao.c`, compila con `gcc -std=c23 -Wall -Wextra -Wpedantic -Werror ciao.c -o ciao` (oppure `clang` con le stesse opzioni) e avvia `./ciao` su macOS/Linux o `.\ciao.exe` su Windows. Sullo schermo apparirà esattamente `Ciao, mondo!`.

> **Approfondimento — Uno sguardo alle tre tappe della traduzione**
> Quando lanci un unico comando come `gcc -std=c23 ... ciao.c -o ciao`, il compilatore esegue in sequenza tutte e tre le tappe e cancella i file intermedi al termine. Nella prima tappa il preprocessore sostituisce la riga `#include <stdio.h>` copiando al suo posto le dichiarazioni contenute nell'header di sistema `stdio.h`. Nella seconda tappa il compilatore traduce l'intero testo risultante in un file oggetto in codice macchina: questo file contiene già le istruzioni di `main`, ma non contiene il codice vero e proprio di `printf`, bensì soltanto un riferimento al fatto che `main` vuole chiamarla. Nella terza tappa il collegatore risolve quel riferimento collegando il tuo file oggetto alla libreria standard del sistema, e assembla infine l'eseguibile completo.

### Esercizio 1.1 — Scheda di benvenuto del laboratorio

**Descrizione**

Scrivi un programma C completo che stampi esattamente la riga `Laboratorio di informatica: postazione pronta.` seguita da un ritorno a capo. Compilalo da riga di comando con `-std=c23 -Wall -Wextra -Wpedantic -Werror` ed eseguilo verificando che l'output corrisponda carattere per carattere, inclusi maiuscole, spazi e punteggiatura.

**Concetti da tenere a mente**

- codice sorgente
- compilatore
- eseguibile
- libreria standard

**Domande guida**

1. Quale file di intestazione devi includere per rendere disponibile la funzione di stampa?
2. Quale azione devi ripetere ogni volta che modifichi il codice sorgente prima di rieseguire il programma?
3. Perché è importante includere un ritorno a capo al termine del messaggio stampato?

**Esempio di esecuzione**

```output
Laboratorio di informatica: postazione pronta.
```
