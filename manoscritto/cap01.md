# Capitolo 1 — Il primo programma

> **In questo capitolo imparerai a:**
> - Compilare ed eseguire un programma C da riga di comando in modo indipendente dal sistema operativo
> - Spiegare il ruolo di `#include`, della funzione `main` e dell'istruzione `return`
> - Scrivere programmi che stampano testo formattato con `printf` e sequenze di escape
> - Distinguere gli errori di compilazione dagli avvisi e correggere i messaggi più comuni

> **Ti servono:** nessun prerequisito di programmazione in C; basta saper aprire un terminale e modificare un file di testo.

Ogni giorno usi programmi scritti in C senza accorgertene: il nucleo del sistema operativo del tuo computer o del tuo telefono, i driver che dialogano con la tastiera e la scheda video, i motori dei database e persino gli interpreti di molti altri linguaggi, come Python. Il C è nato negli anni Settanta per scrivere sistemi operativi e ancora oggi rimane il linguaggio di riferimento quando servono controllo diretto sulla macchina, efficienza e codice prevedibile.

Imparare a programmare in C significa capire che cosa succede davvero tra il testo che scrivi sullo schermo e le istruzioni che il processore esegue. A differenza di altri linguaggi che nascondono molti dettagli, il C ti chiede fin dal primo giorno di essere preciso: ogni simbolo ha un significato esatto e il programma deve attraversare una fase di traduzione prima di poter partire.

In questo primo capitolo costruirai il tuo modo di lavorare. Scriverai i tuoi primi programmi completi, li tradurrai in eseguibili direttamente dal terminale usando lo standard C23 e imparerai a leggere le segnalazioni del compilatore come uno strumento di aiuto, non come un ostacolo.

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
- `void` dentro le parentesi tonde specifica esplicitamente che questa versione di `main` non riceve argomenti; esiste anche una seconda forma che riceve argomenti da riga di comando (lo vedremo nel capitolo 14).

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
> In alcuni vecchi tutorial capita di incontrare `void main()` oppure `int main(void)` senza `return 0;`. La forma `void main()` non è conforme allo standard C per gli ambienti ospitati: il sistema operativo si aspetta un codice di uscita intero da `main`, e compilatori rigorosi con `-Wpedantic -Werror` rifiutano questa firma. Quanto a `return 0;`, è vero che lo standard C23 inserisce implicitamente un ritorno `0` se l'esecuzione raggiunge la `}` finale di `main`, ma questa eccezione vale *solo* per `main` e non per le altre funzioni che scriverai dal capitolo 7 in poi. Scrivere sempre `return 0;` ti abitua fin dall'inizio a rendere esplicito ciò che ogni funzione restituisce.

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

## 1.3 Stampare testo con `printf` e sequenze di escape

Finora hai usato `printf` per stampare brevi frasi semplici, ma un programma reale ha spesso bisogno di impaginare il testo: andare a capo nei punti giusti, allineare colonne, stampare virgolette intorno a un titolo oppure mostrare un percorso di file che contiene barre rovesciate. Per farlo in modo preciso devi conoscere il comportamento esatto di `printf` con le stringhe letterali e il funzionamento delle sequenze di escape.

Una stringa letterale in C è una sequenza di caratteri racchiusa tra virgolette doppie `"..."`. Quando passi una stringa letterale a `printf`, la funzione scrive sullo schermo (più precisamente, sull'uscita standard) esattamente i caratteri che contiene, **senza aggiungere alcun ritorno a capo automatico** alla fine. Se chiami `printf` due volte di seguito senza inserire `\n` nella prima stringa, la seconda stampa prosegue immediatamente sulla stessa riga, attaccata alla prima.

Questo comportamento ti offre piena libertà:

- puoi stampare più righe con una **sola** chiamata a `printf`, inserendo `\n` dove vuoi spezzare la riga;
- oppure puoi costruire una **singola** riga usando più chiamate consecutive a `printf`, mettendo `\n` soltanto nell'ultima.

Osserva i due stili a confronto in questo frammento:

<!-- cod: id=1.3-b tipo=frammento -->
```c
// Due righe prodotte da una sola chiamata
printf("Prima riga\nSeconda riga\n");

// Una sola riga costruita con due chiamate consecutive
printf("Stato: ");
printf("pronto\n");
```

In entrambi i casi hai il controllo totale su ogni singolo carattere stampato.

Come fa però il C a distinguere tra un carattere normale e un comando speciale come "vai a capo"? E come fai a scrivere virgolette doppie `"` *dentro* una stringa, se le virgolette doppie servono già a chiudere la stringa stessa? Se scrivessi `"Titolo: "Odissea""`, il compilatore penserebbe che la stringa termini prima di `Odissea` e segnalerebbe un errore di sintassi. Inoltre, i caratteri di controllo non si possono scrivere in modo diretto e affidabile dentro una stringa letterale: premere Invio spezza la riga del sorgente causando un errore di sintassi, mentre una tabulazione reale si confonderebbe con normali spazi.

Per risolvere entrambi i problemi, il C introduce la **sequenza di escape** (*escape sequence*): una coppia di caratteri introdotta dalla barra rovesciata `\` usata in stringhe e caratteri per rappresentare simboli speciali come l'a capo. Quando il compilatore incontra `\` dentro una stringa, non lo tratta come una normale barra rovesciata, ma lo combina con il carattere immediatamente successivo per produrre un singolo carattere speciale.

Le cinque sequenze di escape essenziali che userai più spesso sono:

| Sequenza | Significato | Effetto nell'output |
|---|---|---|
| `\n` | Ritorno a capo (*newline*) | Sposta il cursore all'inizio della riga successiva |
| `\t` | Tabulazione orizzontale (*tab*) | Avanza il cursore fino alla fermata di tabulazione successiva |
| `\"` | Virgolette doppie | Stampa il carattere `"` senza chiudere la stringa |
| `\'` | Apice singolo | Stampa il carattere `'` (utile soprattutto nei caratteri singoli, dal capitolo 2) |
| `\\` | Barra rovesciata | Stampa un singolo carattere `\` |

La regola definita dallo standard C23 è chiara: all'interno di una stringa letterale, queste sequenze di escape standard hanno un significato fisso e portabile su ogni sistema. Al contrario, scrivere una barra rovesciata seguita da un carattere che non forma una sequenza di escape riconosciuta (per esempio `\p` o `\c`, errore frequente quando si incolla un percorso di file di Windows senza raddoppiare le barre) viola la grammatica del linguaggio e non è portabile: con `-Wall -Wextra -Wpedantic -Werror` il compilatore lo segnala subito e blocca la compilazione. Per stampare una sola barra rovesciata `\` nel risultato finale, nel codice sorgente devi sempre scriverne due (`\\`).

Un'ultima attenzione riguarda il carattere `%`. Dentro la stringa passata a `printf`, il simbolo `%` ha un ruolo speciale perché introduce gli specificatori di formato usati per stampare valori (lo vedremo nel capitolo 2), inclusa la sequenza apposita per stampare il simbolo di percentuale stesso. Per questo motivo, nella stringa di formato di `printf`, non scrivere mai un `%` isolato (nemmeno seguito da uno spazio o da `\n`).

> **Se vieni da Python** — In Python la funzione `print()` aggiunge automaticamente un ritorno a capo al termine di ogni chiamata, a meno che tu non specifichi `end=""`. In C, `printf()` stampa letteralmente solo ciò che scrivi: se vuoi andare a capo devi inserire esplicitamente `\n`, e dimenticarlo è uno degli errori più frequenti quando si passa da Python al C.

### Esempio guidato

Il programma seguente stampa la locandina di un cineforum scolastico. Usa `\"` per racchiudere il titolo del film tra virgolette doppie, `\t` per allineare le colonne di giorno, orario e sala, `\\` per disegnare una piccola cornice decorativa e `\n` per separare con ordine tutte le righe.

<!-- cod: id=1.3-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    printf("/\\=== CINEFORUM D'ISTITUTO ===//\\\n");
    printf("Film in programma: \"Il pianeta silenzioso\"\n");
    printf("Giorno\tOrario\tSala\n");
    printf("Venerdi\t16:30\tAula Magna\n");
    printf("Sabato\t18:00\tSala Video\n");
    printf("\\//============================\\\\/\n");
    return 0;
}
```

```output
/\=== CINEFORUM D'ISTITUTO ===//\
Film in programma: "Il pianeta silenzioso"
Giorno	Orario	Sala
Venerdi	16:30	Aula Magna
Sabato	18:00	Sala Video
\//============================\\/
```

Osserva con attenzione ciascuna riga dell'esempio:

- Alla prima riga, `/\\` nel codice sorgente produce `/\` nell'output: la barra normale `/` non ha bisogno di escape, mentre la barra rovesciata `\` deve essere scritta come `\\`. Lo stesso vale in fondo alla riga per `//\\` (che stampa `//\`) seguito da `\n` per andare a capo.
- Alla seconda riga, `\"Il pianeta silenzioso\"` stampa le virgolette doppie attorno al titolo senza chiudere prematuramente la stringa letterale.
- Alle righe 3–5, `\t` inserisce una tabulazione orizzontale tra una colonna e la successiva. Nota che la larghezza visiva di una tabulazione dipende dalle impostazioni del terminale, ma il carattere prodotto nell'output è sempre un singolo carattere di tabulazione.
- All'ultima riga, `\\//` stampa `\//` e `\\\\/` stampa `\\/` (quattro barre rovesciate nel sorgente diventano due barre rovesciate sullo schermo).

### Esercizio 1.3 — Scheda di archivio con sequenze di escape

**Descrizione**

Scrivi un programma C completo che stampi una scheda di archivio di cinque righe usando le sequenze di escape per virgolette doppie, barre rovesciate, tabulazioni e ritorni a capo. La prima riga deve stampare `Archivio: "Progetto C"`; la seconda `Percorso: C:\progetti\capitolo_1\note.txt`; le ultime tre righe devono formare una tabella a due colonne separate da una singola tabulazione (`Voce` e `Stato`, `Sorgente` e `Pronto`, `Manuale` e `In attesa`). Ogni riga deve terminare con un ritorno a capo.

**Concetti da tenere a mente**

- sequenza di escape
- delimitatori delle stringhe letterali
- tabulazione orizzontale e ritorno a capo

**Domande guida**

1. Perché non puoi inserire direttamente virgolette doppie non precedute da barra rovesciata dentro una stringa?
2. Quante barre rovesciate servono nel codice sorgente per stampare una sola barra rovesciata a schermo?
3. Come puoi separare due colonne con una tabulazione senza inserire spazi a mano?
4. Preferisci scrivere una chiamata di stampa per ogni riga oppure combinare più righe in un'unica stringa, e perché?

**Esempio di esecuzione**

```output
Archivio: "Progetto C"
Percorso: C:\progetti\capitolo_1\note.txt
Voce	Stato
Sorgente	Pronto
Manuale	In attesa
```

## 1.4 Commenti, errori e avvisi del compilatore

Quando un programma supera una decina di righe, leggerlo a distanza di qualche giorno diventa faticoso se non contiene brevi note che spieghino *perché* è stato scritto in un certo modo. Inoltre, mentre scrivi codice C, incontrerai inevitabilmente segnalazioni del compilatore: saper scrivere commenti chiari e saper leggere errori e avvisi fa parte del lavoro quotidiano di chi programma.

### I commenti in C

Un commento è un testo rivolto ai lettori umani del codice sorgente, ignorato nell'eseguibile finale. Il C mette a disposizione due forme di commento:

1. **Commento su una riga**: inizia con `//` e si estende fino alla fine della riga corrente.
2. **Commento su più righe**: inizia con `/*` e termina al primo `*/` incontrato, anche dopo molte righe.

Le regole stabilite dallo standard C23 sono precise: i commenti `//` si chiudono al ritorno a capo, mentre i commenti `/* ... */` si chiudono al primo `*/` e **non possono essere annidati** uno dentro l'altro. Se apri un `/*` dentro un altro `/*`, il primo `*/` chiude l'intero blocco e il testo rimanente (compreso il secondo `*/`) viene letto come codice C, generando errori di sintassi. Lo standard C23 stabilisce inoltre che, durante le fasi iniziali della traduzione, prima del preprocessamento, ogni commento viene sostituito da un singolo spazio: per questo non puoi inserire un commento in mezzo a una parola chiave (per esempio `re/* nota */turn`), perché diventerebbe `re turn`.

Un buon commento spiega lo **scopo** di un programma o di un blocco di istruzioni, oppure chiarisce una scelta non ovvia. Evita invece i commenti ridondanti che traducono alla lettera la riga successiva: scrivere `// restituisce 0` sopra `return 0;` aggiunge solo rumore visivo senza dare alcuna informazione utile.

### Errori di compilazione e avvisi del compilatore

Quando lanci il compilatore, puoi ricevere due tipi distinti di segnalazioni:

- **errore di compilazione** (*compile error*): una violazione delle regole sintattiche o di tipo che impedisce al compilatore di produrre l'eseguibile;
- **avviso del compilatore** (*compiler warning*): una segnalazione di codice potenzialmente errato o ambiguo emessa dal compilatore durante la traduzione, anche quando il codice rispetta formalmente la grammatica.

Di norma un avviso non blocca la creazione dell'eseguibile, ma trascurarlo è rischioso perché molti avvisi nascondono difetti reali. Ecco perché nei nostri comandi usiamo sempre `-Wall -Wextra -Wpedantic -Werror`: le prime tre opzioni chiedono al compilatore di segnalare il maggior numero possibile di anomalie e scostamenti dallo standard C23, mentre `-Werror` trasforma ogni avviso in un errore, costringendoti a risolvere il problema prima di eseguire il programma. Come visto nella sotto-sezione 1.1, le fasi logiche della traduzione sono fissate dallo standard C23, mentre il testo esatto dei messaggi diagnostici e i nomi delle opzioni dipendono dall'implementazione del compilatore.

Quando il compilatore stampa una segnalazione, ti fornisce quasi sempre quattro informazioni utili: il nome del file sorgente, il numero di riga, il numero di colonna e la descrizione del problema rilevato. La strategia migliore per correggere è **partire sempre dal primo errore in alto**: un solo errore all'inizio del file — per esempio un punto e virgola mancante o una virgoletta non chiusa — può mandare fuori fase l'analisi del compilatore e provocare a cascata decine di segnalazioni false sulle righe successive. Correggi il primo problema, salva e ricompila.

All'inizio incontrerai quasi sempre gli stessi cinque errori tipici:

- **Punto e virgola mancante**: il compilatore segnala spesso il problema all'inizio della riga successiva, perché si accorge che l'istruzione precedente non era ancora stata chiusa.
- **Header omesso**: se dimentichi `#include <stdio.h>` e chiami `printf`, il compilatore segnala che la funzione `printf` non è dichiarata.
- **Maiuscole errate**: scrivere `Printf` o `Main` al posto di `printf` o `main` provoca una segnalazione di identificatore sconosciuto o di punto di ingresso mancante.
- **Virgolette non chiuse**: dimenticare `"` in fondo a una stringa fa sì che il compilatore segnali una stringa non terminata sulla riga corrente.
- **Parentesi tonde o graffe non bilanciate**: ogni `(` richiede una `)` corrispondente e ogni `{` richiede una `}` corrispondente.

### Esempio guidato

Il programma seguente mostra un uso pulito di entrambe le forme di commento: un commento su più righe in apertura per descrivere lo scopo del file e brevi commenti su singola riga dentro `main` per separare logicamente le stampe del riepilogo delle tre fasi di traduzione.

<!-- cod: id=1.4-a tipo=programma -->
```c
/*
 * Riepilogo delle tre tappe principali di traduzione in C.
 */
#include <stdio.h>

int main(void) {
    // Intestazione della tabella
    printf("=== Fasi di traduzione ===\n");

    // Elenco ordinato delle tappe
    printf("1. Preprocessore\n");
    printf("2. Compilatore\n");
    printf("3. Collegatore\n");
    return 0;
}
```

```output
=== Fasi di traduzione ===
1. Preprocessore
2. Compilatore
3. Collegatore
```

Questo file compila senza errori né avvisi con `-std=c23 -Wall -Wextra -Wpedantic -Werror`. Osserva che i commenti non ripetono "stampa una riga", ma indicano la funzione logica di ciascun blocco.

Vediamo ora due esempi di programmi che contengono errori intenzionali e vengono rifiutati dal compilatore. Il primo dimentica il punto e virgola alla fine della chiamata a `printf`:

<!-- cod: id=1.4-b tipo=errore -->
```c
#include <stdio.h>

int main(void) {
    printf("Manca il punto e virgola\n")
    return 0;
}
```

Qui il compilatore segnala che si aspettava un `;` prima di `return`, indicando la riga di `return 0;` o la fine della riga precedente: controlla sempre anche la riga immediatamente sopra a quella segnalata.

Il secondo programma dimentica invece la direttiva `#include <stdio.h>`:

<!-- cod: id=1.4-c tipo=errore -->
```c
int main(void) {
    printf("Manca l'header stdio.h\n");
    return 0;
}
```

In questo caso il compilatore segnala che la funzione `printf` non è dichiarata e interrompe la traduzione: per risolvere basta aggiungere `#include <stdio.h>` in cima al file.

> **Approfondimento — Errori di compilazione, di collegamento ed errori logici**
> Non tutti gli errori compaiono nello stesso momento. Gli **errori di compilazione** vengono scoperti durante la traduzione del file `.c` (per esempio un `;` mancante o una funzione non dichiarata). Gli **errori di collegamento** emergono nella tappa successiva, quando il collegatore non trova la definizione di una funzione necessaria per costruire l'eseguibile (per esempio se manca del tutto `main` o se hai scritto `Main` con la maiuscola). Infine ci sono gli **errori logici**: il programma compila e si collega senza alcun avviso, ma produce un risultato sbagliato — per esempio stampa una parola con un refuso o dimentica un `\n`. Il compilatore verifica le regole del linguaggio, non le tue intenzioni: per scovare gli errori logici devi sempre eseguire il programma e confrontare l'output reale con quello atteso.

### Esercizio 1.4 — Programma di controllo pulito e commentato

**Descrizione**

Una bozza di programma per stampare una scheda di verifica prima della consegna non compila perché omette `<stdio.h>`, scrive `Printf` con la lettera maiuscola, dimentica un punto e virgola e annida un commento `/* ... */` dentro un altro. Scrivi una versione corretta da zero che si apra con un commento su più righe sullo scopo del programma, includa almeno un commento su singola riga dentro `main`, compili senza errori né avvisi con `-std=c23 -Wall -Wextra -Wpedantic -Werror` e stampi esattamente le cinque righe dell'esempio di esecuzione (con una tabulazione tra `Esito:` e `Pronto per la consegna`).

**Concetti da tenere a mente**

- errore di compilazione
- avviso del compilatore
- commenti su singola riga e su più righe
- distinzione tra maiuscole e minuscole

**Domande guida**

1. Perché un commento su più righe annidato dentro un altro interrompe la compilazione?
2. Quale indizio ti offre il compilatore quando dimentichi un punto e virgola o sbagli una lettera maiuscola?
3. In che cosa cambia la compilazione quando aggiungi le opzioni per gli avvisi e li tratti come errori?
4. Quali informazioni è davvero utile inserire nei commenti senza ripetere banalmente l'istruzione successiva?

**Esempio di esecuzione**

```output
=== Controllo programma ===
1) Compilato con "-Wall -Wextra -Wpedantic -Werror"
2) Nessun errore di compilazione
3) Nessun avviso del compilatore
Esito:	Pronto per la consegna
```

## Riepilogo

- Un programma C parte da un **codice sorgente** (`.c`) e viene tradotto in un **eseguibile** attraversando tre tappe: **preprocessore**, **compilatore** e **collegatore**.
- Compilare da terminale con `-std=c23 -Wall -Wextra -Wpedantic -Werror` garantisce l'aderenza allo standard C23 e trasforma ogni **avviso del compilatore** in un errore da risolvere subito.
- Per chiamare `printf` (funzione della **libreria standard**) è obbligatorio includere prima `#include <stdio.h>`.
- Ogni programma destinato a un ambiente ospitato inizia dalla funzione `int main(void)` e termina esplicitamente con `return 0;` per segnalare al sistema operativo la conclusione corretta.
- Le istruzioni semplici terminano con `;`, i blocchi sono delimitati da `{` e `}` e il linguaggio distingue sempre tra maiuscole e minuscole.
- `printf` non aggiunge un ritorno a capo automatico; per andare a capo o stampare simboli speciali si usano le **sequenze di escape** (`\n`, `\t`, `\"`, `\'`, `\\`). Il simbolo `%` dentro `printf` serve per stampare valori (lo vedremo nel capitolo 2).
- I commenti `//` terminano a fine riga, i commenti `/* ... */` non possono essere annidati e durante la traduzione vengono sostituiti da un singolo spazio.

## Errori comuni

- **Dimenticare il punto e virgola (`;`) a fine istruzione**: il compilatore segnala spesso il problema all'inizio della riga successiva; controlla sempre anche la riga sopra a quella indicata.
- **Omettere `#include <stdio.h>` prima di chiamare `printf`**: in C23 provoca un errore di compilazione per funzione non dichiarata.
- **Confondere maiuscole e minuscole**: scrivere `Printf` o `Main` al posto di `printf` o `main` genera errori perché il C tratta come diversi identificatori che differiscono anche solo per una lettera maiuscola.
- **Dimenticare `\n` in fondo alla stringa di `printf`**: le stampe successive restano incollate sulla stessa riga oppure si fondono con il prompt del terminale.
- **Annidare un commento `/* ... */` dentro un altro `/* ... */`**: il blocco si chiude al primo `*/` incontrato e la parte restante genera errori di sintassi.
- **Scrivere `"` o `\` dentro una stringa senza barra rovesciata davanti**: le virgolette chiudono la stringa in anticipo, mentre una barra rovesciata isolata forma una sequenza di escape non valida o diversa da quella voluta.

## Prima di proseguire

- [ ] So compilare ed eseguire un file `.c` da terminale con `gcc` o `clang` usando `-std=c23 -Wall -Wextra -Wpedantic -Werror`.
- [ ] So spiegare che cosa fanno preprocessore, compilatore e collegatore durante la traduzione.
- [ ] So scrivere da zero la struttura completa di un programma C con `#include <stdio.h>`, `int main(void)` e `return 0;`.
- [ ] So usare `printf` insieme alle sequenze di escape `\n`, `\t`, `\"`, `\'` e `\\` prevedendo l'output esatto.
- [ ] So distinguere un errore di compilazione da un avviso del compilatore e correggere gli errori sintattici più frequenti partendo dalla prima segnalazione.
