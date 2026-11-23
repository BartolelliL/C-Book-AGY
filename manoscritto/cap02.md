# Capitolo 2 — Variabili e tipi

> **In questo capitolo imparerai a:**
> - Dichiarare e inizializzare variabili dei tipi fondamentali del C23
> - Scegliere lo specificatore di formato corretto in `printf` per ciascun tipo
> - Definire valori immutabili con `const` e costanti a tempo di compilazione con `constexpr`
> - Determinare la dimensione e i limiti numerici dei tipi con `sizeof` e `<limits.h>`

> **Ti servono:** il capitolo 1 (codice sorgente, compilatore, eseguibile, struttura di un programma con `#include` e `main`, stampa con `printf` e sequenze di escape).

I programmi che hai scritto nel capitolo 1 stampavano sempre lo stesso testo fisso, scritto a mano dentro `printf`. Per un programma reale questo non basta: un'applicazione deve ricordare dati come un punteggio, una temperatura, una sigla o uno stato acceso/spento, e poterli aggiornare mentre è in esecuzione.

In C ogni dato memorizzato dal programma vive in memoria con un nome preciso e una forma ben definita. A differenza di altri linguaggi, il C ti chiede di dichiarare in anticipo che tipo di valore vuoi conservare: un numero intero, un numero con parte frazionaria, un singolo carattere oppure un valore vero o falso. Questa scelta non è burocrazia, ma il modo con cui il compilatore calcola esattamente quanta memoria riservare e controlla che tu non mescoli dati incompatibili.

In questo capitolo impari a creare e aggiornare variabili, a scegliere il tipo di dato giusto per ogni informazione, a stampare i valori con la formattazione desiderata e a proteggere i parametri che non devono cambiare. Imparerai infine a interrogare il linguaggio stesso per conoscere quanti byte occupa ciascun tipo e quali limiti numerici supporta il sistema su cui stai lavorando.

## 2.1 Dichiarare e inizializzare variabili

Finora hai stampato soltanto testi già scritti nel codice sorgente. Immagina invece di voler tenere traccia dei punti vita di un personaggio durante una partita o del numero di posti ancora disponibili in un'aula: il valore parte da un numero iniziale e cambia nel corso dell'esecuzione. Per gestire informazioni che variano nel tempo, il programma ha bisogno di riservare un po' di memoria e darle un nome riconoscibile.

In C un oggetto in memoria dotato di nome e tipo il cui valore può essere letto e modificato durante l'esecuzione si chiama **variabile** (*variable*). Puoi pensarla come un'etichetta associata a una precisa area della memoria del computer, nella quale il programma registra un dato e può sostituirlo in seguito con un altro dato dello stesso tipo.

```text
Memoria del programma
+-----------------------+
|          100          |  <-- punti_vita (tipo: int)
+-----------------------+
```

Prima di usare una variabile devi presentarla al compilatore tramite una **dichiarazione** (*declaration*): un costrutto che introduce il nome e il tipo di una variabile, di una funzione o di un tipo nel programma. La sintassi di base indica prima il tipo di dato, poi il nome della variabile (detto *identificatore*) e infine il punto e virgola:

<!-- cod: id=2.1-b tipo=frammento -->
```c
int punti_vita;
```

Qui `int` indica un numero intero (lo studierai insieme agli altri tipi nella prossima sotto-sezione) e `punti_vita` è il nome scelto da te. Una dichiarazione come questa riserva lo spazio in memoria, ma non vi scrive ancora alcun numero preciso.

Per dare subito un valore alla variabile nel momento stesso in cui la definisci, si usa l'**inizializzazione** (*initialization*): l'assegnazione del valore iniziale a una variabile nel momento stesso in cui viene definita. Si scrive con il simbolo `=`:

<!-- cod: id=2.1-c tipo=frammento -->
```c
int punti_vita = 100;
```

Una volta che la variabile esiste, puoi cambiare il suo contenuto in qualsiasi istruzione successiva con un *assegnamento*, scrivendo soltanto il nome della variabile senza ripetere il tipo:

<!-- cod: id=2.1-d tipo=frammento -->
```c
punti_vita = 75;
```

Fai attenzione a distinguere i due momenti: `int punti_vita = 100;` dichiara e inizializza la variabile una volta sola; `punti_vita = 75;` aggiorna la variabile già esistente. Se scrivessi di nuovo `int punti_vita = 75;` nello stesso blocco di codice, il compilatore segnalerebbe un errore di ridefinizione, perché starebbe cercando di creare una seconda variabile con lo stesso nome.

Per scegliere i nomi delle variabili devi rispettare le regole del linguaggio C sugli identificatori:

- un identificatore può contenere solo lettere (`a`-`z`, `A`-`Z`), cifre (`0`-`9`) e il trattino basso (`_`);
- non può mai iniziare con una cifra (`2posti` non è valido, mentre `posti_2` sì);
- non può coincidere con una parola chiave del linguaggio (come `int`, `return` o `void`);
- maiuscole e minuscole sono considerate diverse (`punti` e `Punti` sono due nomi distinti).

Inoltre, in questo libro adottiamo una convenzione precisa: nomi descrittivi in italiano, senza lettere accentate, scritti in `snake_case` (parole minuscole separate da `_`, come `punti_vita` o `posti_liberi`). Evita nomi generici come `a` o `x` quando un nome chiaro rende subito comprensibile il programma.

C'è una regola fondamentale che conviene seguire fin dal primo giorno: inizializza sempre ogni variabile locale nel momento in cui la dichiari. Che cosa succede se dichiari `int punti_vita;` dentro `main` e provi a stamparla prima di averle assegnato un valore? Secondo lo standard C23, una variabile locale non inizializzata ha una rappresentazione indeterminata e leggerne il valore prima di scriverlo provoca *comportamento indefinito* (lo vedremo nel capitolo 3). In pratica lo standard non garantisce nulla: il programma potrebbe stampare un numero casuale rimasto in memoria, comportarsi diversamente a ogni esecuzione o fallire in modo imprevisto. Con i flag `-Wall -Wextra -Wpedantic -Werror` il compilatore ti avvisa quasi sempre di questo errore, ma la difesa migliore è l'abitudine di scrivere sempre un valore iniziale.

Come puoi visualizzare sullo schermo il valore contenuto in una variabile `int`? Nel capitolo 1 hai usato `printf` per stampare testo fisso. Per inserire un numero intero nel testo, metti il segnaposto `%d` dentro la stringa di `printf` e aggiungi la variabile come secondo argomento dopo la virgola:

<!-- cod: id=2.1-e tipo=frammento -->
```c
printf("Punti vita: %d\n", punti_vita);
```

Durante l'esecuzione, `printf` sostituisce `%d` con il valore intero contenuto in `punti_vita`. Nella sotto-sezione 2.3 studierai in modo completo tutti questi segnaposti (che si chiamano specificatori di formato).

> **Se vieni da Python** — In Python crei una variabile semplicemente scrivendo `punti_vita = 100`, senza dichiarare alcun tipo, e puoi poi assegnarle anche una stringa. In C ogni variabile ha un tipo fisso dichiarato in anticipo (`int punti_vita = 100;`) e non può cambiare tipo durante l'esecuzione.

### Esempio guidato

Il programma seguente gestisce i punti vita di un personaggio: dichiara e inizializza la variabile `punti_vita` a `100`, stampa il valore iniziale, aggiorna la variabile a `75` con un assegnamento successivo e stampa il nuovo valore.

<!-- cod: id=2.1-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    int punti_vita = 100;
    printf("Punti vita iniziali: %d\n", punti_vita);

    punti_vita = 75;
    printf("Punti vita dopo il colpo: %d\n", punti_vita);
    return 0;
}
```

```output
Punti vita iniziali: 100
Punti vita dopo il colpo: 75
```

Analizziamo il programma passo dopo passo:

- Alla riga `int punti_vita = 100;` dichiari la variabile intera `punti_vita` e la inizializzi subito a `100`. In memoria viene riservato lo spazio per un intero e vi viene salvato il valore `100`.
- La prima chiamata a `printf` sostituisce `%d` con il valore corrente di `punti_vita` (`100`) e va a capo grazie a `\n`.
- Alla riga `punti_vita = 75;` esegui un assegnamento: non stai creando una nuova variabile (infatti non c'è `int` davanti), ma stai sovrascrivendo il vecchio valore `100` con `75`.
- La seconda chiamata a `printf` legge di nuovo `punti_vita` e stampa il valore aggiornato (`75`).

### Esercizio 2.1 — Aggiornare il contatore di un'aula studio

**Descrizione**

Scrivi un programma C che dichiari e inizializzi una variabile intera `posti_liberi` al valore `24` e stampi `Posti liberi iniziali: 24`. Successivamente assegna alla stessa variabile il valore `18` e stampa `Posti liberi dopo la pausa: 18`. Infine assegna il valore `0` e stampa `Posti liberi a fine giornata: 0`. Ogni riga deve terminare con un ritorno a capo.

**Concetti da tenere a mente**

- variabile
- dichiarazione e inizializzazione
- assegnamento successivo
- stampa di un intero con `%d`

**Domande guida**

1. Qual è la differenza tra inizializzare una variabile nella sua dichiarazione e assegnarle un nuovo valore più avanti nel programma?
2. Quando aggiorni il valore di una variabile già dichiarata, devi riscrivere il tipo di dato davanti al suo nome?
3. Perché è buona regola inizializzare sempre una variabile locale nel momento in cui la dichiari?

**Esempio di esecuzione**

```output
Posti liberi iniziali: 24
Posti liberi dopo la pausa: 18
Posti liberi a fine giornata: 0
```

## 2.2 I tipi fondamentali: `int`, `double`, `char` e `bool`

Un programma non lavora soltanto con numeri interi. Per catalogare un libro in una biblioteca, per esempio, ti servono informazioni molto diverse: l'anno di pubblicazione è un intero, il peso in chilogrammi ha una parte frazionaria, la sezione è una singola lettera (`'S'` per scienze, `'N'` per narrativa) e la disponibilità al prestito è un semplice sì o no. In memoria, però, il computer memorizza tutto come sequenze di bit (zero e uno). Come fa il programma a sapere se una certa sequenza di bit rappresenta il numero `65`, la lettera `'A'` oppure un pezzo di un numero con la virgola?

La risposta è il **tipo di dato** (*data type*): l'insieme di valori rappresentabili e di operazioni lecite su un oggetto o su un'espressione. In C ogni variabile deve dichiarare esplicitamente il proprio tipo di dato. Grazie a questa informazione il compilatore stabilisce quanti byte riservare in memoria, come interpretare i bit contenuti in quei byte e quali operazioni permettere o rifiutare.

### Interi: `int` e i modificatori di tipo

Il tipo principale per i numeri interi (positivi, negativi e zero) è `int`. Quando però un programma ha bisogno di intervalli più ampi oppure sa in anticipo che un valore non sarà mai negativo (come un conteggio), il C mette a disposizione cinque modificatori da anteporre o combinare con `int`:

- `short` (o `short int`): intero con intervallo almeno pari a quello di 16 bit;
- `long` (o `long int`): intero con intervallo almeno pari a quello di 32 bit;
- `long long` (o `long long int`): intero con intervallo almeno pari a quello di 64 bit;
- `signed`: intero con segno (è il comportamento predefinito per `short`, `int`, `long` e `long long`);
- `unsigned`: intero senza segno, capace di rappresentare solo valori maggiori o uguali a zero, raddoppiando così il valore positivo massimo a parità di bit.

Secondo lo standard C23, le ampiezze minime garantite sono: almeno 8 bit per `char`, almeno 16 bit per `short` e `int`, almeno 32 bit per `long` e almeno 64 bit per `long long`. Le dimensioni esatte oltre questi minimi sono *dipendenti dall'implementazione* (cambiano a seconda del sistema operativo e dell'architettura, come verificherai nella sotto-sezione 2.5). Per scrivere letterali interi grandi senza confondere gli zeri, puoi usare i suffissi `L` (per `long`), `LL` (per `long long`), `U` (per `unsigned`) e i separatori di cifre con apice singolo:

<!-- cod: id=2.2-b tipo=frammento -->
```c
long popolazione = 59'000'000L;
unsigned int tentativi = 3U;
```

> **C23** — L'apice singolo come separatore di cifre nei letterali numerici (come `1'000'000` o `59'000'000L`) è una novità dello standard C23: migliora la leggibilità del codice sorgente e non altera in alcun modo il valore del numero né ciò che viene stampato. Se compili con uno standard più vecchio (C17 o C11), rimuovi semplicemente gli apici singoli (`1000000`).

### Numeri con parte frazionaria: `double` e `float`

Per rappresentare numeri reali con parte frazionaria, come `3.14` o `0.85`, il C usa numeri in *virgola mobile* (ne studierai il funzionamento e i limiti di precisione nel capitolo 3). I due tipi principali sono `double` (doppia precisione) e `float` (precisione singola).

Nella grande maggioranza dei programmi la scelta predefinita è `double`: offre una precisione molto più elevata e un intervallo più ampio rispetto a `float`. Inoltre in C i letterali con il punto decimale come `1.25` hanno automaticamente tipo `double` (per scrivere un letterale `float` occorre il suffisso `f`, come `1.25f`). Ricorda che nel codice sorgente C il separatore decimale è sempre il punto `.`, mai la virgola.

### Singoli caratteri: `char`

Per memorizzare un singolo simbolo (una lettera, una cifra, un segno di punteggiatura) si usa il tipo `char`. Secondo lo standard C23, `char` occupa sempre esattamente 1 byte (`sizeof(char) == 1`, con almeno 8 bit per byte). Il fatto che il tipo `char` semplice sia con segno (`signed`) oppure senza segno (`unsigned`) è invece *dipendente dall'implementazione*.

I letterali di carattere si scrivono racchiusi tra **apici singoli**: `'A'`, `'7'`, `'?'`. Fai molta attenzione a non confonderli con le stringhe, che usano invece i **doppi apici** (`"A"`): `'A'` è un singolo `char`, mentre `"A"` è una sequenza di caratteri terminata da un carattere speciale (lo vedremo nel capitolo 9). Scrivere `char sezione = "S";` invece di `char sezione = 'S';` è un errore molto comune che il compilatore segnala subito.

### Valori booleani: `bool`, `true` e `false`

Quando un dato può assumere soltanto due stati — vero o falso, acceso o spento, disponibile o in prestito — il tipo corretto è `bool`, insieme ai due valori `true` e `false`. Una variabile di tipo `bool` può contenere esclusivamente `0` (`false`) oppure `1` (`true`).

> **C23** — In C23 `bool`, `true` e `false` sono parole chiave predefinite del linguaggio e si usano direttamente senza includere alcun header aggiuntivo. Con compilatori configurati su standard precedenti (C17 o C11) occorre invece aggiungere `#include <stdbool.h>` in cima al file.

> **Se vieni da Python** — Tre differenze immediate rispetto a Python: primo, in Python gli interi crescono senza un limite fisso, mentre in C ogni tipo intero ha uno spazio finito in byte; secondo, in Python non esiste un tipo `char` distinto da una stringa lunga 1; terzo, i valori booleani in Python hanno l'iniziale maiuscola (`True` e `False`), mentre in C23 sono tutti minuscoli (`true` e `false`).

### Esempio guidato

Il programma seguente descrive un volume di una biblioteca dichiarando una variabile per ciascun tipo fondamentale: un `int` per l'anno di pubblicazione, un `long` con separatore di cifre per il codice di catalogo, un `double` per il peso in chilogrammi, un `char` per la sezione e un `bool` per la disponibilità al prestito.

<!-- cod: id=2.2-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    int anno_pubblicazione = 2024;
    long codice_catalogo = 1'045'280L;
    double peso_kg = 0.65;
    char sezione = 'S';
    bool disponibile = true;

    printf("Anno: %d\n", anno_pubblicazione);
    printf("Codice catalogo: %ld\n", codice_catalogo);
    printf("Peso (kg): %f\n", peso_kg);
    printf("Sezione: %c\n", sezione);
    printf("Disponibile (1=vero, 0=falso): %d\n", disponibile);
    return 0;
}
```

```output
Anno: 2024
Codice catalogo: 1045280
Peso (kg): 0.650000
Sezione: S
Disponibile (1=vero, 0=falso): 1
```

Osserva alcuni dettagli importanti dell'esecuzione:

- Il valore `1'045'280L` viene stampato come `1045280`: gli apici singoli servono solo a rendere leggibile il codice sorgente e spariscono in compilazione. Per un `long` usiamo `%ld` (studierai la tabella completa nella prossima sotto-sezione).
- Con `%f` il numero `0.65` viene stampato per impostazione predefinita con sei cifre decimali (`0.650000`). Nella sotto-sezione 2.3 vedrai come scegliere quante cifre decimali mostrare.
- La variabile `sezione` usa gli apici singoli (`'S'`) e viene stampata con `%c`.
- La variabile `disponibile` ha tipo `bool` e valore `true`: quando la passi a `printf` con `%d`, viene visualizzata come `1` (mentre `false` verrebbe visualizzato come `0`).

> **Approfondimento — Perché preferire `double` a `float` e come funziona `char`**
> Un `float` occupa in genere 4 byte e garantisce circa 6-7 cifre decimali significative, mentre un `double` occupa di solito 8 byte e arriva a circa 15-17 cifre significative. Sui computer moderni i calcoli in `double` hanno prestazioni analoghe a quelli in `float` e evitano errori di arrotondamento rapidi; inoltre, quando passi un `float` a `printf`, il C lo converte comunque automaticamente in `double`. Conviene usare `float` solo quando devi memorizzare milioni di numeri e lo spazio in memoria è critico.
> Quanto a `char`, in C è tecnicamente un piccolo tipo intero: ogni carattere è rappresentato da un codice numerico. Nella codifica ASCII (usata dai sistemi comuni), per esempio, `'A'` corrisponde al numero `65`, `'B'` a `66` e `'0'` a `48`. È per questo che `char` appartiene alla famiglia dei tipi interi, pur essendo usato principalmente per rappresentare singoli simboli.

### Esercizio 2.2 — Scheda di un satellite meteorologico

**Descrizione**

Scrivi un programma C che memorizzi i dati di un satellite meteorologico in cinque variabili inizializzate con il tipo più adatto: `codice_orbita` (`long`, valore `1'450'000` scritto con il separatore di cifre del C23), `anno_lancio` (`int`, valore `2025`), `quota_km` (`double`, valore `824.5`), `classe_orbita` (`char`, valore `'P'`) e `attivo` (`bool`, valore `true`). Stampa i cinque dati su righe separate esattamente come mostrato nell'esempio di esecuzione (usando `%f` per `quota_km` e `%d` per `attivo`).

**Concetti da tenere a mente**

- tipo di dato
- tipi `int`, `long`, `double`, `char` e `bool` (C23)
- letterali di carattere tra apici singoli
- separatore di cifre C23

**Domande guida**

1. Quale differenza sintattica distingue un carattere singolo da una stringa letterale?
2. Perché in C23 puoi usare `bool`, `true` e `false` senza includere nessun header dedicato?
3. L'uso del separatore di cifre con apice singolo nel letterale numerico modifica in qualche modo ciò che viene stampato a schermo?
4. Quale valore numerico stampa `printf` quando visualizza una variabile `bool` con valore `true` usando `%d`?

**Esempio di esecuzione**

```output
Codice orbita: 1450000
Anno di lancio: 2025
Quota (km): 824.500000
Classe: P
Attivo (1=vero, 0=falso): 1
```

## 2.3 Stampare valori con gli specificatori di formato

Nelle sotto-sezioni precedenti hai già usato `%d`, `%ld`, `%f` e `%c` dentro `printf` per stampare variabili di tipi diversi. Ora è il momento di capire con precisione come funziona questo meccanismo, quali codici esistono per ogni tipo e come controllare l'aspetto dell'output (cifre decimali, colonne allineate, simbolo percentuale).

Un **specificatore di formato** (*format specifier*) è un segnaposto introdotto da `%` in funzioni come `printf` (e `sscanf`, che incontrerai nel capitolo 5) che indica come interpretare o stampare un valore. Quando chiami `printf`, il primo argomento è una *stringa di formato*: `printf` la legge da sinistra a destra, stampa i caratteri normali così come sono e, ogni volta che incontra uno specificatore di formato, prende il successivo argomento dalla lista dopo la virgola, lo converte in testo secondo lo specificatore e lo inserisce in quella posizione.

Puoi inserire più specificatori nella stessa chiamata a `printf`: il primo specificatore si abbina al primo argomento dopo la stringa di formato, il secondo al secondo argomento e così via, nello stesso identico ordine.

<!-- cod: id=2.3-b tipo=frammento -->
```c
int giorno = 14;
int mese = 11;
printf("Data: %d/%d\n", giorno, mese);
```

### Mappa degli specificatori principali

La tabella seguente raccoglie gli specificatori di formato che userai più spesso nel corso del libro:

| Specificatore | Tipo dell'argomento | Uso principale |
|---|---|---|
| `%d` | `int` (anche `char`, `short`, `bool` promossi) | Interi con segno in base 10 |
| `%u` | `unsigned int` | Interi senza segno in base 10 |
| `%ld` | `long` | Interi `long` con segno |
| `%lu` | `unsigned long` | Interi `unsigned long` |
| `%lld` | `long long` | Interi `long long` con segno |
| `%llu` | `unsigned long long` | Interi `unsigned long long` |
| `%f` | `double` (anche `float` promosso) | Numeri in virgola mobile in notazione decimale |
| `%c` | `char` (promosso a `int`) | Singolo carattere |
| `%zu` | `size_t` | Dimensioni in byte restituite da `sizeof` (sotto-sezione 2.5) |
| `%%` | *(nessun argomento)* | Stampa il carattere letterale `%` |

Nota l'ultima riga: poiché `%` introduce sempre uno specificatore di formato, se vuoi stampare davvero un simbolo di percentuale (per esempio `68%`) devi scrivere `%%` nella stringa di formato. Scrivere un `%` isolato seguito da uno spazio o da un ritorno a capo non è valido.

### Precisione, larghezza di campo e allineamento

Senza opzioni aggiuntive, `%f` stampa sempre sei cifre dopo il punto decimale (come `0.650000`) e tutti i valori occupano solo i caratteri strettamente necessari. Quando vuoi stampare tabelle leggibili o limitare le cifre decimali, puoi inserire tra `%` e la lettera finale alcuni modificatori di formattazione:

- **Precisione decimale** (`.N` prima di `f`): indica quante cifre stampare dopo il punto decimale, arrotondando il valore visualizzato. Per esempio `%.1f` stampa una cifra decimale (`21.8`) e `%.2f` ne stampa due (`4.35`).
- **Larghezza minima di campo** (un numero intero subito dopo `%`): riserva almeno quel numero di caratteri, aggiungendo spazi a sinistra (allineamento a destra) se il valore è più corto. Per esempio `%6u` stampa `42` preceduto da quattro spazi (`    42`), e `%6.2f` combina larghezza minima 6 e 2 cifre decimali (`  4.35`, contando anche il punto decimale tra i 6 caratteri). Se il valore è più lungo della larghezza minima, non viene mai troncato: viene stampato per intero.
- **Allineamento a sinistra** (`-` subito dopo `%`): sposta gli eventuali spazi di riempimento a destra del valore anziché a sinistra. Per esempio `%-10c` stampa il carattere `'N'` seguito da nove spazi.

### Corrispondenza tra tipo e specificatore

In C la funzione `printf` non sa da sola quali tipi le hai passato dopo la stringa di formato: si fida ciecamente degli specificatori che hai scritto tu. La regola dello standard C23 è severa: ogni specificatore di formato deve corrispondere esattamente al tipo dell'argomento corrispondente (tenuto conto delle promozioni predefinite descritte nell'approfondimento più sotto).

Fornire a `printf` un argomento di tipo incompatibile con lo specificatore (per esempio usare `%d` per un `double` o per un `long long`), oppure passare meno argomenti rispetto agli specificatori presenti nella stringa, provoca **comportamento indefinito**. Il programma potrebbe stampare numeri privi di senso oppure arrestarsi in modo anomalo.

Fortunatamente, i compilatori moderni ispezionano le stringhe di formato di `printf`: compilando sempre con `-Wall -Wextra -Wpedantic -Werror`, il compilatore segnala immediatamente la mancata corrispondenza tra specificatore e tipo di argomento e ti blocca prima ancora di eseguire il programma.

### Esempio guidato

Il programma seguente stampa un bollettino meteorologico con colonne allineate. Usa `%d` insieme a `%%` per l'umidità, `%.1f` e `%.2f` con larghezza minima per temperatura e pressione, `%u` per i millimetri di pioggia annui e `%-10c` per mostrare l'allineamento a sinistra della zona.

<!-- cod: id=2.3-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    char zona = 'N';
    double temperatura_c = 18.4;
    double pressione_hpa = 1013.25;
    int umidita = 64;
    unsigned int pioggia_mm = 780U;

    printf("=== BOLLETTINO METEO ===\n");
    printf("Zona        : %-10c(settore)\n", zona);
    printf("Temperatura : %7.1f C\n", temperatura_c);
    printf("Pressione   : %7.2f hPa\n", pressione_hpa);
    printf("Umidita     : %7d%%\n", umidita);
    printf("Pioggia anno: %7u mm\n", pioggia_mm);
    return 0;
}
```

```output
=== BOLLETTINO METEO ===
Zona        : N         (settore)
Temperatura :    18.4 C
Pressione   : 1013.25 hPa
Umidita     :      64%
Pioggia anno:     780 mm
```

Osserva come ogni specificatore controlla l'aspetto della riga corrispondente:

- Nella prima riga `%-10c` stampa `'N'` allineato a sinistra in un campo largo 10 caratteri, lasciando nove spazi prima di `(settore)`.
- `%7.1f` riserva 7 caratteri totali per `18.4` (che occupa 4 caratteri, punto incluso), quindi aggiunge 3 spazi davanti.
- `%7.2f` stampa `1013.25`: poiché il numero occupa già esattamente 7 caratteri, non servono spazi aggiuntivi e le due righe risultano allineate sul bordo destro della colonna numerica.
- `%7d%%` allinea `64` a destra in 7 caratteri e stampa subito dopo un singolo `%` grazie alla coppia `%%`.
- `%7u` corrisponde esattamente al tipo `unsigned int` di `pioggia_mm` e mantiene lo stesso allineamento delle righe sopra.

> **Approfondimento — Le promozioni predefinite degli argomenti in `printf`**
> Potresti chiederti perché nella tabella degli specificatori `%f` vada bene sia per `double` sia per `float`, e perché `%d` si usi anche per `char`, `short` e `bool`. Il motivo è una regola dello standard C chiamata *promozione predefinita degli argomenti* (*default argument promotions*), applicata alle funzioni con numero variabile di argomenti come `printf` (le funzioni variadiche saranno approfondite nel capitolo 21): prima di raggiungere `printf`, ogni argomento intero più piccolo di `int` (cioè `bool`, `char`, `short`) viene convertito automaticamente in `int`, e ogni `float` viene convertito automaticamente in `double`. Ecco perché `printf` riceve sempre un `double` quando le passi un `float` e usa `%f` per entrambi.

### Esercizio 2.3 — Prospetto di un impianto fotovoltaico

**Descrizione**

Scrivi un programma C che dichiari e inizializzi i dati di un impianto fotovoltaico con i tipi appropriati: `numero_pannelli` (`unsigned int`, valore `12`), `energia_totale_wh` (`long long`, valore `12'450'800`), `potenza_kw` (`double`, valore `4.35`), `rendimento` (`double`, valore `21.8`) e `classe_efficienza` (`char`, valore `'A'`). Stampa la tabella esattamente come nell'esempio di esecuzione usando gli specificatori di formato corretti, larghezze minime di campo (`6` caratteri per pannelli, potenza e classe; `5` caratteri per il rendimento), precisione di `2` cifre decimali per la potenza e `1` cifra decimale per il rendimento, e `%%` per il simbolo percentuale.

**Concetti da tenere a mente**

- specificatore di formato
- larghezza minima di campo e precisione decimale
- corrispondenza tra tipo e specificatore in `printf`
- stampa del simbolo percentuale con `%%`

**Domande guida**

1. Quale specificatore di formato corrisponde a un `unsigned int` e quale a un `long long`?
2. Come si combinano larghezza minima di campo e numero di cifre decimali in uno specificatore per `double`?
3. Perché per stampare il simbolo `%` nella riga del rendimento devi raddoppiarlo nella stringa di formato?
4. Che cosa rischia di accadere se usi `%d` per stampare un valore di tipo `long long` o `double`?

**Esempio di esecuzione**

```output
=== IMPIANTO FOTOVOLTAICO ===
Pannelli installati :     12
Energia prodotta    : 12450800 Wh
Potenza nominale    :   4.35 kW
Rendimento          :  21.8%
Classe energetica   :      A
```

## 2.4 Costanti con `const` e `constexpr`

Quando scrivi un programma reale, molti valori non dovrebbero mai cambiare durante l'esecuzione: il numero massimo di posti in una sala, il prezzo del biglietto intero, il codice identificativo di un reparto. Se disseminassi numeri come `120` o `9.50` direttamente nelle chiamate a `printf` o nei calcoli, il codice diventerebbe difficile da capire (che cosa significa `120` in quel punto?) e rischioso da aggiornare (se il valore cambia, devi cercarlo e sostituirlo ovunque, rischiando di dimenticarne qualcuno o di modificare un altro `120` che indicava tutt'altro).

La soluzione è sostituire i numeri sparsi con una **costante** (*constant*): un valore o oggetto di sola lettura che non può essere modificato dopo la sua definizione. In questo libro i nomi delle costanti si scrivono tutti in MAIUSCOLO con parole separate da `_` (per esempio `POSTI_MASSIMI` o `PREZZO_INTERO`), così a colpo d'occhio si distinguono subito dalle variabili normali.

### Il qualificatore `const`

In C il modo classico per dichiarare un oggetto di sola lettura è anteporre il qualificatore `const` al tipo di dato:

<!-- cod: id=2.4-b tipo=frammento -->
```c
const int SPETTATORI_PRENOTATI = 84;
```

Una costante dichiarata con `const` va sempre inizializzata al momento della dichiarazione, perché dopo non potrai più assegnarle alcun valore. Se provi a scrivere un assegnamento successivo su `SPETTATORI_PRENOTATI`, il compilatore rifiuta di compilare il programma segnalando che stai tentando di modificare un oggetto di sola lettura.

Secondo lo standard C23, modificare direttamente un oggetto definito `const` è un errore di compilazione; aggirare il divieto con tecniche avanzate (che incontrerai solo nei capitoli sui puntatori) provoca invece **comportamento indefinito**.

### Lo specificatore `constexpr` in C23

Un oggetto `const` è *di sola lettura*, ma il suo valore iniziale potrebbe essere noto solo durante l'esecuzione del programma (per esempio letto dalla tastiera, come farai nel capitolo 5, o calcolato a partire da altre variabili). Quando invece un valore è davvero fisso e noto già prima che il programma parta — come la capienza di una sala o un parametro fisico — il C23 offre lo specificatore `constexpr`:

<!-- cod: id=2.4-c tipo=frammento -->
```c
constexpr int POSTI_MASSIMI = 120;
constexpr double PREZZO_INTERO = 9.50;
```

Un oggetto definito con `constexpr` è una costante il cui valore è garantito noto *a tempo di compilazione* (ed è automaticamente anche di sola lettura, quindi non serve scrivere `const` accanto a `constexpr`). Questo offre due vantaggi concreti:

1. il compilatore può usare quel valore in contesti che richiedono una costante nota in compilazione (come la dimensione di un array, che vedremo nel capitolo 8);
2. l'inizializzatore deve essere un'espressione costante e deve essere rappresentabile *esattamente* nel tipo dichiarato, senza troncamenti silenziosi.

> **C23** — Lo specificatore `constexpr` per gli oggetti è una novità dello standard C23. Se compili con compilatori configurati su standard precedenti (C17 o C11), usa `const` al posto di `constexpr`.

### Quando usare `constexpr` e quando `const`

Riassumendo la regola pratica:

- usa `constexpr` per i parametri fissi del programma il cui valore è scritto direttamente nel codice sorgente (o ricavato da altre costanti note in compilazione);
- usa `const` per i valori di sola lettura che non devono cambiare dopo l'inizializzazione, ma che non sono necessariamente fissi a tempo di compilazione (oppure quando vuoi proteggere un valore ricevuto da un input o da una funzione, come vedremo nei capitoli 5 e 7).

In entrambi i casi, il compilatore fa da sentinella e ti protegge da modifiche accidentali.

> **Se vieni da Python** — In Python non esistono costanti imposte dal linguaggio: scrivere `POSTI_MASSIMI = 120` in maiuscolo è solo una convenzione tra programmatori e nulla impedisce di riassegnare quel nome più avanti. In C, `const` e `constexpr` sono vincoli verificati direttamente dal compilatore.

### Esempio guidato

Il programma seguente mostra la configurazione di una sala cinematografica: usa `constexpr` per i parametri fissi della sala (`POSTI_MASSIMI`, `PREZZO_INTERO`, `SALA_CODICE`) e `const` per un dato di sola lettura legato alla proiezione della serata (`SPETTATORI_PRENOTATI`).

<!-- cod: id=2.4-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    constexpr int POSTI_MASSIMI = 120;
    constexpr double PREZZO_INTERO = 9.50;
    constexpr char SALA_CODICE = 'B';

    const int SPETTATORI_PRENOTATI = 84;

    printf("=== SALA CINEMATOGRAFICA %c ===\n", SALA_CODICE);
    printf("Capienza massima : %d posti\n", POSTI_MASSIMI);
    printf("Biglietto intero : %.2f euro\n", PREZZO_INTERO);
    printf("Prenotati stasera: %d spettatori\n", SPETTATORI_PRENOTATI);
    return 0;
}
```

```output
=== SALA CINEMATOGRAFICA B ===
Capienza massima : 120 posti
Biglietto intero : 9.50 euro
Prenotati stasera: 84 spettatori
```

Nota come il codice risulti subito leggibile: nella prima `printf` non appare una lettera isolata senza contesto, ma `SALA_CODICE`, e nelle righe successive `POSTI_MASSIMI`, `PREZZO_INTERO` e `SPETTATORI_PRENOTATI` rendono esplicito il significato di ogni numero.

Che cosa accade se provi a modificare una costante dopo averla dichiarata? Il programma seguente contiene un errore intenzionale: tenta di riassegnare `POSTI_MASSIMI`.

<!-- cod: id=2.4-d tipo=errore -->
```c
#include <stdio.h>

int main(void) {
    constexpr int POSTI_MASSIMI = 120;
    POSTI_MASSIMI = 150;
    printf("Posti: %d\n", POSTI_MASSIMI);
    return 0;
}
```

Questo file non produce alcun eseguibile: il compilatore blocca la traduzione segnalando che non è possibile assegnare un nuovo valore a una variabile di sola lettura (`POSTI_MASSIMI`). Lo stesso rifiuto avverrebbe con `const int POSTI_MASSIMI = 120;`.

> **Approfondimento — Controlli più severi di `constexpr` in C23**
> Con una variabile normale o anche con `const`, se scrivi `const int limite = 3.7;`, il compilatore converte silenziosamente `3.7` in `3` troncando la parte decimale (al massimo emettendo un avviso se hai abilitato opzioni aggiuntive). Con `constexpr int LIMITE = 3.7;`, invece, lo standard C23 impone un errore di compilazione vero e proprio: l'inizializzatore di un oggetto `constexpr` deve essere esattamente rappresentabile nel tipo scelto, senza perdita di valore né di precisione. È una rete di sicurezza molto utile contro errori di battitura nei parametri di configurazione.

### Esercizio 2.4 — Parametri di configurazione di una stampante 3D

**Descrizione**

Scrivi un programma C che definisca tramite `constexpr` quattro parametri hardware fissi di una stampante 3D: `LARGHEZZA_PIATTO_MM` (`int`, `220`), `ALTEZZA_MAX_MM` (`int`, `250`), `DIAMETRO_UGELLO_MM` (`double`, `0.40`) e `PROFILO_QUALITA` (`char`, `'M'`). Definisci poi tramite `const` due impostazioni di sola lettura della stampa corrente: `TEMPERATURA_ESTRUSORE` (`int`, `210`) e `VENTOLA_ATTIVA` (`bool`, `true`). Stampa il riepilogo esattamente come nell'esempio di esecuzione (con due cifre decimali per il diametro dell'ugello).

**Concetti da tenere a mente**

- costante
- qualificatore `const`
- specificatore `constexpr` (C23)
- nomi di costanti in MAIUSCOLO

**Domande guida**

1. In che cosa si distingue una costante definita con `constexpr` da un oggetto qualificato `const`?
2. Perché conviene raccogliere i parametri di configurazione in costanti con nomi chiari anziché scrivere i numeri direttamente dentro `printf`?
3. Che cosa fa il compilatore se provi a riassegnare una costante dopo la sua dichiarazione?
4. Quale specificatore di formato usi per mostrare il diametro dell'ugello esattamente con due cifre dopo la virgola?

**Esempio di esecuzione**

```output
=== CONFIGURAZIONE STAMPANTE 3D ===
Piatto (mm): 220 x 250
Ugello (mm): 0.40
Profilo: M
Temperatura estrusore (C): 210
Ventola attiva (1=vero, 0=falso): 1
```

## 2.5 Dimensione e limiti dei tipi: `sizeof` e `<limits.h>`

Nella sotto-sezione 2.2 hai visto che lo standard C23 garantisce soltanto l'ampiezza *minima* di ciascun tipo intero (per esempio almeno 16 bit per `int` e almeno 32 bit per `long`), mentre le dimensioni esatte possono cambiare da un computer all'altro o da un sistema operativo all'altro. Come puoi sapere con certezza quanti byte occupa un `int` o un `double` sulla macchina su cui compili, e qual è il numero più grande che un `long` o un `unsigned long` riesce a contenere?

Scrivere numeri fissi nel codice (come "un `long` occupa sempre 8 byte") è una cattiva abitudine che rende i programmi fragili. Il linguaggio C mette invece a disposizione due strumenti portabili: l'operatore `sizeof` per le dimensioni in byte e l'header `<limits.h>` per i limiti numerici dei tipi interi.

### L'operatore `sizeof` e il tipo `size_t`

L'operatore `sizeof` restituisce la dimensione in byte di un tipo di dato oppure di una variabile (o di un'espressione). Per i tipi fondamentali che conosci ora, il risultato viene calcolato direttamente a tempo di compilazione.

Puoi usarlo in due forme:

- `sizeof(tipo)`: con un nome di tipo le parentesi tonde sono obbligatorie (per esempio `sizeof(int)` o `sizeof(double)`);
- `sizeof variabile` oppure `sizeof(variabile)`: con una variabile le parentesi sono facoltative, anche se molti programmatori le scrivono comunque per uniformità.

Il valore restituito da `sizeof` non ha tipo `int`, bensì `size_t`: un tipo intero senza segno definito nell'header `<stddef.h>` (e reso disponibile anche da `<stdio.h>`, ma includere `<stddef.h>` rende esplicita la dipendenza nel codice). Per stampare un valore di tipo `size_t` con `printf` devi usare lo specificatore di formato **`%zu`**. Usare `%d` o `%u` al posto di `%zu` può provocare comportamento indefinito perché `size_t` ha spesso una dimensione diversa da `int` (sui sistemi a 64 bit `size_t` occupa tipicamente 8 byte, mentre `int` ne occupa 4).

<!-- cod: id=2.5-b tipo=frammento -->
```c
size_t dim_int = sizeof(int);
printf("Un int occupa %zu byte\n", dim_int);
```

### Cosa è garantito e cosa dipende dall'implementazione

Lo standard C23 stabilisce con precisione il confine tra regole universali e dettagli della piattaforma:

- **Garantito dallo standard (definito)**: `sizeof(char)` è *sempre* uguale a `1`; un byte contiene almeno 8 bit (`CHAR_BIT >= 8`); le ampiezze minime sono almeno 8 bit per `char`, almeno 16 bit per `short` e `int`, almeno 32 bit per `long` e almeno 64 bit per `long long`; il tipo restituito da `sizeof` è sempre `size_t`.
- **Dipendente dall'implementazione**: la dimensione esatta di `short`, `int`, `long`, `long long`, `float`, `double` e `bool`, così come i limiti numerici concreti oltre i minimi garantiti. Un esempio celebre riguarda proprio `long`: sui sistemi a 64 bit, `sizeof(long)` vale **4 byte** su Windows, ma **8 byte** su Linux e macOS. Anche il segno del tipo `char` semplice (`signed` o `unsigned`) dipende dall'implementazione.

Per questo motivo, quando in un programma hai bisogno di conoscere la dimensione di un tipo o l'intervallo di un intero, non devi mai indovinarli: interroga sempre `sizeof` e `<limits.h>`. (Quando invece ti serviranno tipi interi con un numero di bit esattamente prefissato, come 32 o 64 bit su qualunque sistema, userai `<stdint.h>`, che vedremo nel capitolo 13.)

### Le costanti di `<limits.h>`

Includendo `#include <limits.h>` hai accesso a un insieme completo di costanti che descrivono il numero di bit per byte e i valori minimo e massimo di tutti i tipi interi sulla piattaforma in uso. La tabella seguente elenca le costanti principali insieme allo specificatore di formato corretto per stamparle con `printf`:

| Costante | Significato | Specificatore in `printf` |
|---|---|---|
| `CHAR_BIT` | Numero di bit in un byte (di solito `8`) | `%d` |
| `CHAR_MIN`, `CHAR_MAX` | Minimo e massimo di `char` | `%d` |
| `SCHAR_MIN`, `SCHAR_MAX` | Minimo e massimo di `signed char` | `%d` |
| `UCHAR_MAX` | Massimo di `unsigned char` | `%d` |
| `SHRT_MIN`, `SHRT_MAX` | Minimo e massimo di `short` | `%d` |
| `USHRT_MAX` | Massimo di `unsigned short` | `%d` |
| `INT_MIN`, `INT_MAX` | Minimo e massimo di `int` | `%d` |
| `UINT_MAX` | Massimo di `unsigned int` | `%u` |
| `LONG_MIN`, `LONG_MAX` | Minimo e massimo di `long` | `%ld` |
| `ULONG_MAX` | Massimo di `unsigned long` | `%lu` |
| `LLONG_MIN`, `LLONG_MAX` | Minimo e massimo di `long long` | `%lld` |
| `ULLONG_MAX` | Massimo di `unsigned long long` | `%llu` |

Osserva un dettaglio sottile: per `UCHAR_MAX` e `USHRT_MAX` nella tabella compare `%d` (sui sistemi comuni dove `int` è più largo di `char` e `short`), perché — come hai letto nella sotto-sezione 2.3 — i valori di tipo `unsigned char` e `unsigned short` vengono promossi automaticamente a `int` quando vengono passati a `printf`. Al contrario, `UINT_MAX`, `ULONG_MAX` e `ULLONG_MAX` richiedono rispettivamente `%u`, `%lu` e `%llu`.

Nota anche che per i tipi senza segno non esistono costanti `*_MIN`: il loro valore minimo è sempre `0`.

### Esempio guidato

Il programma diagnostico seguente include `<stdio.h>`, `<stddef.h>` e `<limits.h>`, salva in variabili di tipo `size_t` le dimensioni di `char`, `int`, `long` e `double` ottenute con `sizeof` e stampa sia le dimensioni (con `%zu`) sia alcuni limiti numerici (`CHAR_BIT`, `INT_MIN`, `INT_MAX` e `ULONG_MAX`).

<!-- cod: id=2.5-a tipo=programma -->
```c
#include <limits.h>
#include <stddef.h>
#include <stdio.h>

int main(void) {
    size_t dim_char = sizeof(char);
    size_t dim_int = sizeof(int);
    size_t dim_long = sizeof(long);
    size_t dim_double = sizeof(double);

    printf("Bit per byte : %d\n", CHAR_BIT);
    printf("sizeof(char)   = %zu byte\n", dim_char);
    printf("sizeof(int)    = %zu byte\n", dim_int);
    printf("sizeof(long)   = %zu byte\n", dim_long);
    printf("sizeof(double) = %zu byte\n", dim_double);
    printf("Intervallo int : %d .. %d\n", INT_MIN, INT_MAX);
    printf("Massimo ulong  : %lu\n", ULONG_MAX);
    return 0;
}
```

```output
Bit per byte : 8
sizeof(char)   = 1 byte
sizeof(int)    = 4 byte
sizeof(long)   = 8 byte
sizeof(double) = 8 byte
Intervallo int : -2147483648 .. 2147483647
Massimo ulong  : 18446744073709551615
```

L'output riportato sopra è quello tipico di un sistema a 64 bit Linux o macOS. Se compili ed esegui lo stesso identico programma su Windows a 64 bit, vedrai due differenze del tutto legittime: `sizeof(long)` stamperà `4 byte` anziché `8 byte`, e `ULONG_MAX` stamperà `4294967295`. In entrambi i casi il programma è corretto e portabile, perché non fa ipotesi fisse ma legge i valori reali della piattaforma tramite `sizeof` e `<limits.h>`.

> **Approfondimento — Perché `sizeof` è un operatore e non una funzione**
> A prima vista `sizeof(double)` somiglia a una chiamata di funzione come `printf(...)`, ma `sizeof` è una parola chiave del linguaggio e un *operatore* vero e proprio. Te ne accorgi da due indizi: primo, una funzione in C non potrebbe mai ricevere un nome di tipo come `double` o `int` al posto di un valore; secondo, quando applichi `sizeof` a una variabile, le parentesi non sono obbligatorie (puoi scrivere `sizeof dim_int`, anche se `sizeof(dim_int)` resta più leggibile). Inoltre, per tutti i tipi visti in questo libro, `sizeof` viene valutato dal compilatore durante la traduzione, senza alcun costo durante l'esecuzione del programma.

### Esercizio 2.5 — Tabella di dimensioni e limiti dei tipi

**Descrizione**

Scrivi un programma C che includa `<stdio.h>`, `<stddef.h>` e `<limits.h>`, salvi in costanti di tipo `size_t` la dimensione in byte dei tipi `char`, `bool`, `short`, `int`, `long long` e `double` ottenuta con `sizeof`, e stampi il numero di bit per byte (`CHAR_BIT`) seguito dalla tabella delle dimensioni e dei limiti (`SCHAR_MIN`, `SCHAR_MAX`, `UCHAR_MAX`, `SHRT_MIN`, `SHRT_MAX`, `INT_MIN`, `INT_MAX`, `UINT_MAX`, `LLONG_MIN`, `LLONG_MAX`, `ULLONG_MAX`) esattamente nel formato mostrato nell'esempio di esecuzione (riferito alle piattaforme desktop comuni a 32/64 bit). Usa sempre `%zu` per i valori di tipo `size_t` e gli specificatori di formato esatti per ciascun limite.

**Concetti da tenere a mente**

- operatore `sizeof`
- tipo `size_t` e specificatore `%zu`
- costanti di `<limits.h>`
- comportamento dipendente dall'implementazione per le dimensioni dei tipi

**Domande guida**

1. Quale header standard definisce il tipo `size_t` e quale definisce le costanti come `CHAR_BIT` e `INT_MAX`?
2. Quale specificatore di formato è richiesto da `printf` per stampare un valore restituito da `sizeof`?
3. Perché in questo esercizio è più portabile usare `SCHAR_MIN` e `SCHAR_MAX` al posto di `CHAR_MIN` e `CHAR_MAX`?
4. Quale specificatore di formato devi scegliere rispettivamente per `UINT_MAX`, `LLONG_MIN` e `ULLONG_MAX`?
5. Perché le dimensioni e i limiti di `short`, `int` e `long long` non vanno mai scritti come numeri fissi nel codice quando servono i valori effettivi del sistema?

**Esempio di esecuzione**

```output
Bit per byte: 8
char       : 1 byte (signed: -128 .. 127, unsigned max: 255)
bool       : 1 byte
short      : 2 byte (-32768 .. 32767)
int        : 4 byte (-2147483648 .. 2147483647, unsigned max: 4294967295)
long long  : 8 byte (-9223372036854775808 .. 9223372036854775807, unsigned max: 18446744073709551615)
double     : 8 byte
```

## Riepilogo

- Una **variabile** è un oggetto in memoria dotato di nome e **tipo di dato** il cui valore può essere letto e modificato durante l'esecuzione. Va sempre presentata con una **dichiarazione** e, per le variabili locali, è buona regola fornirne sempre l'**inizializzazione** prima di leggerla.
- Gli identificatori usano lettere, cifre e `_`, non iniziano mai con una cifra e non coincidono con parole chiave. Nel libro adottiamo nomi descrittivi in italiano in `snake_case` per le variabili e in MAIUSCOLO per le costanti.
- I tipi fondamentali coprono interi (`int` con i modificatori `short`, `long`, `long long`, `signed`, `unsigned`), numeri in virgola mobile (`double` come scelta predefinita, `float`), singoli caratteri (`char`, sempre 1 byte, con letterali tra apici singoli come `'A'`) e valori booleani (`bool`, `true`, `false`, parole chiave native in C23).
- Nei letterali numerici il C23 consente l'apice singolo come separatore di cifre (per esempio `1'000'000`) senza alterare il valore.
- In `printf` ogni **specificatore di formato** (`%d`, `%u`, `%ld`, `%lu`, `%lld`, `%llu`, `%f`, `%c`, `%zu`, `%%`) deve corrispondere al tipo dell'argomento passato; precisione decimale (`.2`), larghezza minima di campo (`6`) e allineamento a sinistra (`-`) controllano l'aspetto dell'output.
- Una **costante** impedisce modifiche accidentali: `const` definisce un oggetto di sola lettura, mentre `constexpr` (C23) definisce una costante nota a tempo di compilazione con controlli severi sull'inizializzatore.
- L'operatore `sizeof` restituisce la dimensione in byte come valore di tipo `size_t` (da `<stddef.h>`, stampato con `%zu`), mentre `<limits.h>` fornisce i limiti numerici dei tipi interi sulla piattaforma in uso. Con queste basi potrai costruire calcoli e confronti tra valori (lo vedremo nel capitolo 3).

## Errori comuni

- **Leggere una variabile locale senza averla prima inizializzata**: il suo contenuto è indeterminato e leggerla provoca comportamento indefinito; assegna sempre un valore iniziale nella dichiarazione.
- **Usare uno specificatore di formato non coerente con il tipo dell'argomento in `printf`**: passare un `double`, un `long long` o il risultato di `sizeof` a `%d` (invece di `%f`, `%lld` o `%zu`) causa comportamento indefinito; compila sempre con `-Wall -Wextra -Wpedantic -Werror` per intercettarlo subito.
- **Usare i doppi apici (`"A"`) invece degli apici singoli (`'A'`) per un `char`**: `"A"` è una stringa, non un carattere singolo, e genera un errore o un avviso di tipo incompatibile.
- **Tentare di riassegnare una costante `const` o `constexpr`, oppure dichiararla senza inizializzatore**: il compilatore rifiuta qualsiasi modifica successiva e richiede un valore iniziale alla dichiarazione.
- **Riscrivere il tipo di dato davanti al nome quando vuoi solo aggiornare una variabile**: scrivere di nuovo `int punti_vita = 75;` nello stesso blocco provoca un errore di ridefinizione invece di un assegnamento.
- **Dare per scontato che `int` o `long` occupino sempre lo stesso numero di byte su qualunque macchina**: le dimensioni oltre i minimi garantiti dipendono dall'implementazione; usa sempre `sizeof` e le costanti di `<limits.h>`.

## Prima di proseguire

- [ ] So dichiarare, inizializzare e aggiornare una variabile rispettando le regole sugli identificatori e senza leggere variabili locali non inizializzate.
- [ ] So scegliere il tipo di dato adatto tra `int` (con eventuali modificatori), `double`, `char` e `bool`, distinguendo `'A'` da `"A"` e usando `true`/`false` e i separatori di cifre del C23.
- [ ] So abbinare ogni tipo al proprio specificatore di formato in `printf` (`%d`, `%u`, `%ld`, `%lu`, `%lld`, `%llu`, `%f`, `%c`, `%zu`, `%%`) e formattare precisione, larghezza minima e allineamento.
- [ ] So distinguere quando usare `constexpr` e quando usare `const` per definire valori immutabili.
- [ ] So usare `sizeof` con `size_t` (`%zu`) e le costanti di `<limits.h>` per conoscere dimensioni e limiti reali della piattaforma su cui compilo.
