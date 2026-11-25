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
