# Capitolo 12 — Strutture, enumerazioni, typedef

> **In questo capitolo imparerai a:**
> - Modellare entità composite con `struct` e tipi simbolici con `enum` e `typedef`
> - Accedere ai campi tramite puntatori a `struct` con l'operatore `->`
> - Gestire array dinamici di `struct` e strutture annidate senza perdite di memoria
> - Scegliere tra passaggio per valore e passaggio per puntatore a `const struct`

> **Ti servono:** array e inizializzatori designati (capitolo 8), stringhe (capitolo 9), puntatori e `const` (capitolo 10), allocazione dinamica sullo heap con `malloc`, `realloc`, `free` e `strdup` (capitolo 11).

Finora nei tuoi programmi ogni variabile rappresentava un singolo dato: un numero intero, un valore in virgola mobile, un carattere, un booleano, oppure un array di elementi tutti dello stesso tipo. Nel capitolo 11 hai imparato a riservare memoria sullo heap a tempo di esecuzione per gestire collezioni di lunghezza variabile. Nella pratica, però, i dati reali sono raramente numeri isolati: un libro ha un titolo, un anno di pubblicazione e un prezzo; una rilevazione meteorologica unisce il codice della stazione, la quota, la temperatura e lo stato del sensore; un evento in agenda combina una data, un orario, una durata e una descrizione.

Senza uno strumento dedicato, per rappresentare un'entità con più proprietà saresti costretto a dichiarare molte variabili sciolte o a mantenere sincronizzati più array paralleli, uno per ciascuna proprietà. È un approccio fragile: basta dimenticare di aggiornare uno degli array durante un inserimento o uno scambio per corrompere silenziosamente l'intera raccolta di dati.

In questo capitolo impari a costruire tipi di dato personalizzati con `struct`, a dare nomi leggibili a insiemi finiti di costanti intere con `enum` e a creare alias di tipo compatti con `typedef`. Vedrai poi come combinare le strutture con i puntatori, con gli array dinamici sullo heap e con le funzioni, gettando le basi per tutte le strutture dati che realizzerai nella seconda parte del libro.

## 12.1 Raggruppare dati con `struct`

Immagina di dover scrivere un programma che gestisce le rilevazioni di una stazione meteorologica: per ogni misura devi conservare il codice della stazione (una stringa), la quota in metri (un `int`), la temperatura rilevata (un `double`) e un'indicazione che dice se il sensore è attivo (un `bool`). Con gli strumenti visti finora avresti due strade, entrambe scomode: dichiarare quattro variabili separate per ogni rilevazione (`codice_1`, `quota_1`, `temp_1`, `attiva_1`, poi `codice_2`, `quota_2`, e così via), oppure costruire quattro array paralleli di uguale lunghezza. Nel primo caso il codice diventa presto illeggibile e ogni funzione che elabora una rilevazione dovrebbe ricevere quattro parametri separati; nel secondo caso basta scambiare due elementi in tre array dimenticando il quarto per disallineare in modo irreparabile i dati.

Quando più valori di tipo anche diverso descrivono insieme una stessa entità logica, il C offre un tipo aggregato apposito: la **struttura** (*struct*), cioè un tipo aggregato definito con `struct` che raggruppa più campi, anche di tipi diversi, sotto un unico nome. Ogni singola variabile dichiarata all'interno di una `struct` (o di una `union`, che vedremo nel capitolo 13) si chiama **campo** (*field*).

Per creare un tipo struttura si scrive la parola chiave `struct`, seguita da un'etichetta (*tag*) che ne costituisce il nome, dalle parentesi graffe contenenti le dichiarazioni dei campi e da un punto e virgola finale obbligatorio:

<!-- cod: id=12.1-b tipo=frammento -->
```c
struct rilevazione_meteo {
    char codice[16];
    int quota;
    double temperatura;
    bool attiva;
};
```

Questa definizione non crea ancora alcuna variabile in memoria: descrive al compilatore il modello del nuovo tipo `struct rilevazione_meteo`, elencando nome e tipo di ciascun campo. Dimenticare il punto e virgola dopo la parentesi graffa di chiusura è uno degli errori di sintassi più frequenti e genera segnalazioni fuorvianti sulle righe successive.

In memoria i campi di una struttura sono disposti esattamente nell'ordine in cui compaiono nella definizione:

```text
struct rilevazione_meteo
+------------------+---------+---------------+----------+
| codice[0..15]    | quota   | temperatura   | attiva   |
| (16 byte)        | (4 byte)| (8 byte)      | (1 byte) |
+------------------+---------+---------------+----------+
^ indirizzo base della struttura
```

Una volta definito il tipo, puoi dichiarare una o più variabili di tipo `struct rilevazione_meteo` esattamente come fai con i tipi fondamentali. Per leggere o modificare un singolo campo si usa l'**operatore punto** (`.`): dato il nome della variabile struttura seguito da `.` e dal nome del campo, ottieni il campo stesso come se fosse una normale variabile del suo tipo.

<!-- cod: id=12.1-c tipo=frammento -->
```c
struct rilevazione_meteo r;
strcpy(r.codice, "STZ-04");
r.quota = 820;
r.temperatura = 14.5;
r.attiva = true;
```

Osserva che per `r.codice`, che è un array di `char`, valgono le regole viste nel capitolo 9: non puoi assegnare una stringa con `=` dopo la dichiarazione, ma usi `strcpy` (oppure `snprintf`). Per gli altri campi usi il normale assegnamento `=`.

Come per gli array, è sempre buona norma inizializzare la struttura nel momento in cui la dichiari. Il C offre tre forme di inizializzazione:

1. **Inizializzazione per posizione**: i valori tra parentesi graffe vengono associati ai campi nell'ordine esatto della definizione:
   `struct rilevazione_meteo r1 = {"STZ-01", 1250, 12.4, true};`
2. **Inizializzatore designato** (già visto sugli array nel capitolo 8): davanti a ciascun valore indichi `.nome_campo = valore`, in qualunque ordine:
   `struct rilevazione_meteo r2 = {.temperatura = 12.4, .codice = "STZ-01", .quota = 1250, .attiva = true};`
3. **Inizializzazione parziale o vuota**: se ometti alcuni campi in un inizializzatore, il compilatore azzera automaticamente tutti i campi mancanti (`0` per gli interi, `0.0` per i numeri in virgola mobile, `false` per i booleani, `'\0'` per i caratteri, `nullptr` per i puntatori). In C23 puoi scrivere l'inizializzatore vuoto `{}` per azzerare l'intera struttura.

> **C23** — L'inizializzatore vuoto `{}` (per esempio `struct rilevazione_meteo r = {};`) è stato standardizzato in C23 e azzera tutti i campi della struttura, esattamente come `{0}` negli standard precedenti. Se compili con un compilatore più vecchio in modalità C17 o C11, scrivi `{0}` al posto di `{}`.

Riassumiamo le regole fondamentali della definizione e dell'inizializzazione:

- `struct nome_tag { ... };` definisce un nuovo tipo struttura i cui campi sono memorizzati nell'ordine dichiarato.
- L'operatore punto (`s.campo`) accede in lettura o in scrittura al campo della variabile struttura `s`.
- Una struttura può essere inizializzata per posizione (`{v1, v2}`) o con inizializzatori designati (`{.campo1 = v1, .campo2 = v2}`); i campi omessi vengono azzerati automaticamente e in C23 `{}` azzera l'intera struttura.
- Secondo lo standard C23, la sequenza dei campi in memoria, l'operatore punto, gli inizializzatori designati, l'azzeramento dei campi omessi e `{}` hanno comportamento completamente definito. Al contrario, leggere un campo di una struttura automatica (dichiarata dentro una funzione) senza averlo prima inizializzato o assegnato provoca **comportamento indefinito**.

Infine, puoi misurare quanti byte occupa in memoria una struttura applicando `sizeof` al nome del tipo (`sizeof(struct rilevazione_meteo)`) oppure a una variabile (`sizeof(r)`). Potresti aspettarti che il risultato coincida sempre con la somma delle dimensioni dei singoli campi, ma spesso è leggermente maggiore: `sizeof(struct rilevazione_meteo)` è sempre maggiore o uguale alla somma delle dimensioni dei suoi campi. Questo accade perché il compilatore può inserire byte inutilizzati tra un campo e l'altro o in coda alla struttura per rispettare i vincoli di disposizione in memoria del processore (lo vedremo nel capitolo 13). Per questo motivo non devi mai stimare a mano la dimensione di una `struct` sommando le dimensioni dei campi: usa sempre `sizeof`.

> **Se vieni da Python** — In Python una classe raggruppa dati e operazioni associate, e puoi persino aggiungere nuovi campi a un oggetto durante l'esecuzione. In C una `struct` contiene soltanto i campi dati fissati nella sua definizione a tempo di compilazione, mentre le funzioni che lavorano su quei dati sono definite all'esterno della struttura.

### Esempio guidato

Il programma seguente definisce `struct rilevazione_meteo`, inizializza la prima variabile con inizializzatori designati e la seconda con l'inizializzatore vuoto `{}` (C23), ne aggiorna poi i campi con l'operatore punto, stampa entrambe le rilevazioni e confronta `sizeof(struct rilevazione_meteo)` con la somma delle dimensioni dei singoli campi.

<!-- cod: id=12.1-a tipo=programma -->
```c
#include <stdio.h>
#include <string.h>

struct rilevazione_meteo {
    char codice[16];
    int quota;
    double temperatura;
    bool attiva;
};

int main(void) {
    struct rilevazione_meteo monte = {
        .codice = "ALPI-01",
        .quota = 1850,
        .temperatura = 6.5,
        .attiva = true
    };
    struct rilevazione_meteo valle = {};

    strcpy(valle.codice, "VAL-02");
    valle.quota = 240;
    valle.temperatura = 19.2;
    valle.attiva = false;

    printf("%s: quota %d m, %.1f C, attiva=%d\n",
           monte.codice, monte.quota, monte.temperatura, monte.attiva);
    printf("%s: quota %d m, %.1f C, attiva=%d\n",
           valle.codice, valle.quota, valle.temperatura, valle.attiva);

    size_t somma_campi = sizeof(monte.codice) + sizeof(monte.quota)
                       + sizeof(monte.temperatura) + sizeof(monte.attiva);
    printf("Somma dimensioni campi: %zu byte\n", somma_campi);
    printf("sizeof(struct rilevazione_meteo): %zu byte\n",
           sizeof(struct rilevazione_meteo));
    return 0;
}
```

```output
ALPI-01: quota 1850 m, 6.5 C, attiva=1
VAL-02: quota 240 m, 19.2 C, attiva=0
Somma dimensioni campi: 29 byte
sizeof(struct rilevazione_meteo): 40 byte
```

Esaminiamo i passaggi chiave:

- La definizione di `struct rilevazione_meteo` è posta fuori da `main` (con il punto e virgola finale) così che sia visibile in tutto il file sorgente.
- `monte` viene inizializzata con inizializzatori designati: ogni campo è esplicitamente nominato e l'array `codice` riceve direttamente la stringa letterale `"ALPI-01"` (incluso il terminatore nullo `'\0'` e i byte residui azzerati).
- `valle` viene inizializzata con `{}` (C23), azzerando tutti i suoi campi; subito dopo l'operatore punto permette di popolare ciascun campo in modo sicuro (`strcpy` per la stringa, `=` per i campi scalari).
- Le ultime righe calcolano `somma_campi` (`16 + 4 + 8 + 1 = 29` byte su un'architettura tipica a 64 bit) e la confrontano con `sizeof(struct rilevazione_meteo)` (`40` byte): la differenza è dovuta ai byte inutilizzati aggiunti dal compilatore tra i campi o in coda, un dettaglio dipendente dall'implementazione che approfondiremo nel capitolo 13.

> **Approfondimento — Perché preferire gli inizializzatori designati**
> Gli inizializzatori designati (`.campo = valore`) offrono due vantaggi decisivi rispetto all'inizializzazione posizionale. Primo, chi legge il codice capisce immediatamente che cosa rappresenta ogni numero senza dover tornare alla definizione della `struct`. Secondo, il codice resta corretto anche se in futuro riordini i campi o ne aggiungi di nuovi nella definizione della struttura: un'inizializzazione posizionale associerebbe i valori ai campi sbagliati o smetterebbe di compilare, mentre gli inizializzatori designati continuano a legare ogni valore al campo corretto e azzerano automaticamente eventuali nuovi campi aggiunti.

### Esercizio 12.1 — Gestione di un lotto di magazzino con struct e inizializzatori designati

**Descrizione**

Scrivi un programma C che definisca `struct lotto_merce` con quattro campi: `char codice[16];`, `int quantita;`, `double prezzo_unitario;` e `bool deperibile;`. In `main` dichiara un lotto costante di confronto `const struct lotto_merce riferimento = {.codice = "BASE-00", .quantita = 10, .prezzo_unitario = 5.00, .deperibile = false};` e un lotto `struct lotto_merce attivo = {};` (inizializzatore vuoto C23). Leggi dalla prima riga di `stdin` i dati iniziali di `attivo` (`codice`, `quantita >= 0`, `prezzo_unitario >= 0.0` e un intero `dep` pari a `0` o `1` da assegnare a `attivo.deperibile`, validati con `sscanf(riga, "%15s %d %lf %d %c", attivo.codice, &attivo.quantita, &attivo.prezzo_unitario, &dep, &extra) == 4`). Leggi poi fino a fine input una sequenza di movimenti (uno per riga): `CARICO <q>` (`q > 0`) somma `q` ad `attivo.quantita`; `SCARICO <q>` (`q > 0`) se `q > attivo.quantita` non modifica la quantità, incrementa `rifiutati` e stampa `Scarico rifiutato: disponibili <quantita>`, altrimenti sottrae `q` da `attivo.quantita`. In caso di input o comando non valido stampa su `stderr` e restituisci `EXIT_FAILURE`. Al termine stampa i campi di `attivo`, il numero di scarichi rifiutati, il valore totale (`quantita * prezzo_unitario`) e la differenza di valore rispetto a `riferimento`, esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- definizione di un tipo struttura con `struct` e dichiarazione dei campi
- inizializzatore designato `{.campo = valore}` e inizializzatore vuoto `{}` (C23)
- accesso in lettura e scrittura ai campi tramite l'operatore punto (`.`)
- coesione di campi di tipi diversi (`char[]`, `int`, `double`, `bool`) in un unico oggetto

**Domande guida**

1. Quali valori assumono inizialmente tutti i campi di `attivo` quando lo dichiari con l'inizializzatore vuoto `{}` in C23?
2. Perché per leggere `codice` con `sscanf` non serve l'operatore `&` davanti ad `attivo.codice` mentre è necessario davanti ad `attivo.quantita` e `attivo.prezzo_unitario`?
3. Come accedi ai singoli campi di `attivo` e di `riferimento` per calcolare la differenza tra i due valori economici?
4. Quale vantaggio offre raggruppare i quattro dati in `struct lotto_merce` rispetto a gestire quattro variabili separate per ciascun lotto?

**Esempio di esecuzione**

```input
LATTE-01 20 1.50 1
CARICO 10
SCARICO 35
SCARICO 12
```

```output
Scarico rifiutato: disponibili 30
Lotto: LATTE-01 (deperibile: si)
Quantita finale: 18, prezzo: 1.50 euro
Scarichi rifiutati: 1
Valore attivo: 27.00 euro (diff da BASE-00: -23.00 euro)
```

## 12.2 Enumerazioni con `enum` e alias con `typedef`

Molti campi di una struttura non rappresentano misure numeriche libere, ma una scelta tra poche opzioni predefinite: lo stato di un ordine (aperto, spedito, consegnato), il livello di priorità di una richiesta (bassa, media, alta, critica) o il giorno della settimana. Potresti codificare queste scelte con numeri interi (`0`, `1`, `2`, `3`), ma dopo poche righe di codice quei numeri diventano "numeri magici" opachi: leggendo `if (stato == 2)` non si capisce che cosa significhi `2` senza cercare un commento altrove nel programma.

Per dare nomi simbolici chiari a un insieme chiuso di valori interi, il C mette a disposizione l'**enumerazione** (*enumeration*): un tipo intero definito con `enum` che associa nomi simbolici a un insieme finito di costanti intere. La sintassi ricorda quella di `struct`, con la parola chiave `enum`, un'etichetta, l'elenco delle costanti separate da virgole tra parentesi graffe e il punto e virgola finale obbligatorio:

<!-- cod: id=12.2-b tipo=frammento -->
```c
enum stato_ordine {
    ORDINE_APERTO,      // vale 0
    ORDINE_SPEDITO,     // vale 1
    ORDINE_CONSEGNATO   // vale 2
};
```

Per convenzione le costanti di enumerazione si scrivono in MAIUSCOLO e spesso condividono un prefisso comune (`ORDINE_...`), perché a differenza dei campi di una `struct` le costanti di un `enum` sono visibili nello stesso spazio dei nomi delle variabili del blocco o del file: due `enum` diversi nello stesso ambito non possono definire una costante con lo stesso nome.

Se non indichi alcun valore esplicito, la prima costante vale `0` e ogni costante successiva vale `1` in più della precedente. Puoi però assegnare valori interi espliciti a una o più costanti; quelle che seguono riprendono a incrementare di `1` a partire dall'ultimo valore specificato:

<!-- cod: id=12.2-c tipo=frammento -->
```c
enum codice_esito {
    ESITO_OK = 0,
    ESITO_AVVISO = 10,
    ESITO_ERRORE,       // vale 11
    ESITO_CRITICO = 99
};
```

Le enumerazioni si sposano in modo naturale con il costrutto `switch` (capitolo 4). Invece di scrivere `case 0:`, `case 1:`, scrivi `case ORDINE_APERTO:`, `case ORDINE_SPEDITO:`: il codice si legge quasi come italiano e, attivando gli avvisi del compilatore, quest'ultimo può persino segnalarti se hai dimenticato di gestire un valore dell'enumerazione. È una pratica molto diffusa scrivere una breve funzione di supporto che converte un valore `enum` in una stringa costante (`const char *`) per stamparlo in forma leggibile.

Nelle enumerazioni ordinarie le costanti hanno tipo `int`, ma il tipo intero esatto usato dal compilatore per rappresentare una variabile di tipo `enum nome_tag` è **dipendente dall'implementazione** (il compilatore sceglie un tipo intero compatibile capace di contenere tutti i valori elencati). C23 ha introdotto la possibilità di fissare esplicitamente il tipo intero sottostante scrivendo `: tipo_intero` dopo l'etichetta:

<!-- cod: id=12.2-d tipo=frammento -->
```c
enum priorita : int {
    PRIORITA_BASSA = 0,
    PRIORITA_MEDIA = 1,
    PRIORITA_ALTA = 2,
    PRIORITA_CRITICA = 3
};
```

> **C23** — La sintassi con tipo sottostante fisso (`enum priorita : int { ... };`) è una novità di C23 e rende deterministica la dimensione e il segno del tipo enumerato. Su compilatori più vecchi (C17 o C11) ometti `: int` e scrivi semplicemente `enum priorita { ... };`.

Avrai notato nella sotto-sezione 12.1 un piccolo fastidio sintattico: ogni volta che dichiari una variabile, un parametro o un tipo di ritorno devi scrivere due parole, `struct rilevazione_meteo` oppure `enum priorita`. Questo accade perché in C le etichette di `struct` ed `enum` vivono in uno spazio di nomi separato rispetto ai nomi di tipo ordinari (come `int`, `double` o `size_t`).

Per rendere il codice più snello esiste la parola chiave `typedef`, che definisce un alias (sinonimo) per qualsiasi tipo esistente:

<!-- cod: id=12.2-e tipo=frammento -->
```c
typedef tipo_esistente nuovo_nome;
```

Applicata a una struttura o a un'enumerazione, `typedef` ti permette di scrivere il nome breve senza ripetere `struct` o `enum`. Puoi scrivere `typedef` su una riga separata oppure combinarlo direttamente con la definizione del tipo:

<!-- cod: id=12.2-f tipo=frammento -->
```c
typedef struct punto {
    double x;
    double y;
} punto_t;

typedef enum priorita : int {
    PRIORITA_BASSA = 0,
    PRIORITA_MEDIA = 1,
    PRIORITA_ALTA = 2
} priorita_t;
```

Da questo punto in poi `punto_t` è un alias esatto di `struct punto` e `priorita_t` è un alias esatto di `enum priorita`. Nel codice di questo libro usiamo spesso il suffisso `_t` per gli alias di tipo definiti dall'utente, evitando però nomi riservati dallo standard (come `size_t` o `ptrdiff_t`).

Due buone pratiche con `typedef` ti risparmieranno molti grattacapi:

1. **Mantieni sempre l'etichetta della `struct`**: scrivi `typedef struct punto { ... } punto_t;` e non `typedef struct { ... } punto_t;`. Avere l'etichetta torna indispensabile quando una struttura dovrà riferirsi a sé stessa tramite un puntatore (lo vedremo nel capitolo 17).
2. **Non nascondere un puntatore dentro un `typedef`**: evitare alias come `typedef struct punto *punto_ptr;` mantiene sempre visibile l'asterisco `*` nelle dichiarazioni e rende immediato capire quando una variabile è un puntatore (e quindi richiede `->`, controlli su `nullptr` e attenzione a `const`). L'unica eccezione disciplinata riguarda i tipi opachi, che vedremo nel capitolo 19.

Riassumiamo le regole di questa sotto-sezione:

- `enum nome_tag { COST_0, COST_1, ... };` definisce un tipo enumerazione intero e le sue costanti simboliche (di tipo `int` nelle enumerazioni ordinarie): la prima vale `0` se non specificato, e ogni successiva aumenta di `1`.
- In C23 è possibile fissare il tipo intero sottostante con `enum nome_tag : tipo_intero { ... };`. Quando il tipo sottostante non è indicato, la scelta del tipo intero compatibile è dipendente dall'implementazione.
- `typedef tipo_esistente nuovo_nome;` crea un alias tipizzato senza introdurre un tipo distinto.

### Esempio guidato

Il programma seguente definisce con `typedef` un'enumerazione C23 `priorita_t` a tipo sottostante `int` e una struttura `ticket_t` per una richiesta di assistenza. Una funzione traduce la priorità in testo tramite `switch`, mentre un'altra calcola il tempo massimo di risposta in ore.

<!-- cod: id=12.2-a tipo=programma -->
```c
#include <stdio.h>

typedef enum priorita : int {
    PRIORITA_BASSA = 0,
    PRIORITA_MEDIA = 1,
    PRIORITA_ALTA = 2,
    PRIORITA_CRITICA = 3
} priorita_t;

typedef struct ticket {
    int codice;
    priorita_t livello;
} ticket_t;

const char *nome_priorita(priorita_t p) {
    switch (p) {
        case PRIORITA_BASSA: return "Bassa";
        case PRIORITA_MEDIA: return "Media";
        case PRIORITA_ALTA: return "Alta";
        default: return "Critica";
    }
}
int ore_risposta(priorita_t p) {
    switch (p) {
        case PRIORITA_BASSA: return 72;
        case PRIORITA_MEDIA: return 24;
        case PRIORITA_ALTA: return 4;
        default: return 1;
    }
}
int main(void) {
    ticket_t t1 = {.codice = 401, .livello = PRIORITA_MEDIA};
    ticket_t t2 = {.codice = 402, .livello = PRIORITA_CRITICA};
    printf("Ticket #%d [%s]: risposta entro %d ore\n",
           t1.codice, nome_priorita(t1.livello), ore_risposta(t1.livello));
    printf("Ticket #%d [%s]: risposta entro %d ore\n",
           t2.codice, nome_priorita(t2.livello), ore_risposta(t2.livello));
    return 0;
}
```

```output
Ticket #401 [Media]: risposta entro 24 ore
Ticket #402 [Critica]: risposta entro 1 ore
```

Osserva come `enum` e `typedef` collaborano:

- `typedef enum priorita : int { ... } priorita_t;` definisce sia l'etichetta `enum priorita` con tipo sottostante `int` (C23), sia l'alias `priorita_t`.
- Nella struttura `ticket_t` il campo `livello` ha tipo `priorita_t`, quindi il suo significato è autoesplicativo anche in fase di inizializzazione (`.livello = PRIORITA_MEDIA`).
- Le funzioni `nome_priorita` e `ore_risposta` usano uno `switch` sui nomi simbolici: non compare alcun numero magico né in `main` né nelle funzioni di supporto.
- In `main` puoi scrivere direttamente `ticket_t t1` anziché `struct ticket t1`, rendendo le dichiarazioni e le firme delle funzioni più pulite.

> **Approfondimento — `typedef` crea un sinonimo, non un nuovo tipo**
> È importante non confondere `typedef` con la creazione di un nuovo tipo di dato. Se scrivi `typedef int metri_t;` e `typedef int secondi_t;`, per il compilatore `metri_t`, `secondi_t` e `int` sono esattamente lo stesso tipo: nulla impedisce di sommare un `metri_t` a un `secondi_t` o di passare l'uno al posto dell'altro. Al contrario, ogni definizione di `struct` o di `enum` introduce un tipo effettivamente distinto nel sistema dei tipi del C.

### Esercizio 12.2 — Smistamento di pacchi postali con enum e typedef

**Descrizione**

Scrivi un programma C che definisca con `typedef` un'enumerazione C23 con tipo intero sottostante fisso `typedef enum zona_consegna : int { ZONA_URBANA = 0, ZONA_NAZIONALE = 1, ZONA_ISOLE = 2, ZONA_ESTERO = 3 } zona_t;` e una struttura `typedef struct pacco { int id; zona_t zona; double peso_kg; } pacco_t;`. Dichiara prima di `main` i prototipi di due funzioni: `const char *nome_zona(zona_t z)` (restituisce `"Urbana"`, `"Nazionale"`, `"Isole"` o `"Estero"` tramite `switch`) e `double calcola_tariffa(pacco_t p)` (usa `switch (p.zona)`: base `4.00` + `0.50`/kg per `ZONA_URBANA`, base `6.50` + `0.80`/kg per `ZONA_NAZIONALE`, base `9.00` + `1.10`/kg per `ZONA_ISOLE`, base `14.00` + `2.00`/kg per `ZONA_ESTERO`). In `main` leggi dalla prima riga di `stdin` `n` (`1..50`) e dalle successive `n` righe `id codice_zona peso_kg` (`id > 0`, `codice_zona` intero in `0..3`, `peso_kg > 0.0`; in caso di errore stampa su `stderr` e restituisci `EXIT_FAILURE`). Per ogni riga costruisci un `pacco_t`, stampa `Pacco #<id> [<nome_zona>, <peso> kg]: <tariffa> euro`, aggiorna il conteggio della zona in `int conteggi[4] = {0};` e la somma delle tariffe, e al termine stampa il riepilogo per zona e l'incasso totale esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- definizione di un'enumerazione con `enum` e tipo sottostante esplicito (`: int` in C23)
- creazione di alias di tipo leggibili per `enum` e `struct` con `typedef`
- selezione su valori `enum` con `switch` e funzione di traduzione in stringa
- uso dei valori `enum` (`0..3`) come indici sicuri di un array di contatori

**Domande guida**

1. Quale vantaggio offre usare le costanti simboliche `ZONA_URBANA`..`ZONA_ESTERO` nello `switch` rispetto ai numeri `0..3`?
2. Che cosa garantisce la specifica C23 `: int` nella definizione di `enum zona_consegna : int`?
3. Perché conviene validare che `codice_zona` letto da `stdin` sia compreso tra `0` e `3` prima di convertirlo in `zona_t`?
4. Come permette `typedef` di scrivere `pacco_t` e `zona_t` nelle firme delle funzioni senza ripetere ogni volta `struct` ed `enum`?

**Esempio di esecuzione**

```input
3
101 0 2.0
102 2 5.0
103 3 1.5
```

```output
Pacco #101 [Urbana, 2.00 kg]: 5.00 euro
Pacco #102 [Isole, 5.00 kg]: 14.50 euro
Pacco #103 [Estero, 1.50 kg]: 17.00 euro
Riepilogo zone -> Urbana: 1, Nazionale: 0, Isole: 1, Estero: 1
Incasso totale: 36.50 euro
```

## 12.3 Puntatori a `struct` e operatore `->`

Nel capitolo 10 hai visto che per permettere a una funzione di modificare una variabile del chiamante (o di ispezionare un dato di grandi dimensioni senza copiarlo) si passa l'indirizzo della variabile mediante un puntatore. Con le strutture questa esigenza diventa la norma: una `struct` può contenere molti campi e array, e le funzioni che gestiscono un conto, un sensore o una scheda devono spesso aggiornarne lo stato sul posto.

Un puntatore a struttura si dichiara e si inizializza con le stesse regole di qualsiasi altro puntatore:

<!-- cod: id=12.3-b tipo=frammento -->
```c
punto_t pt = {.x = 3.0, .y = 4.0};
punto_t *p = &pt;        // puntatore che permette lettura e modifica
const punto_t *cp = &pt; // puntatore di sola lettura
```

Una volta ottenuto il puntatore `p`, come accedi al campo `x` della struttura puntata? Istintivamente potresti provare a scrivere `*p.x`, pensando di dereferenziare `p` e poi selezionare `x`. Questo però è un **errore di compilazione**: per la precedenza degli operatori del C, l'operatore punto `.` ha precedenza più alta dell'operatore unario di dereferenziazione `*`. Il compilatore interpreta quindi `*p.x` come `*(p.x)`, cercando un campo `x` dentro il puntatore `p` (che non è una struttura) e rifiutando il codice.

Per dereferenziare prima `p` e poi accedere al campo servono le parentesi tonde: `(*p).x`. Scrivere parentesi a ogni accesso è però scomodo e poco leggibile; per questo il C fornisce l'**operatore freccia** (`->`), una scrittura compatta e idiomatica che combina dereferenziazione e accesso al campo:

<!-- cod: id=12.3-c tipo=frammento -->
```c
p->x   // equivale esattamente a (*p).x
```

```text
  p (punto_t *)                 pt (punto_t)
+---------------+            +-------------------+
|   indirizzo   | ---------> | x: 3.0  | y: 4.0  |
+---------------+            +-------------------+
                                 ^         ^
                               p->x      p->y
```

Lo schema mostra il funzionamento di `p->campo`: il puntatore `p` memorizza l'indirizzo iniziale di `pt` e l'operatore `->` segue quell'indirizzo per raggiungere il campo richiesto all'interno dell'oggetto puntato.

L'operatore `->` si usa costantemente nelle funzioni che ricevono strutture tramite puntatore:

- **Puntatore modificabile (`tipo_t *p`)**: la funzione può leggere e modificare i campi della struttura originale del chiamante tramite `p->campo`.
- **Puntatore a costante (`const tipo_t *p`)**: la funzione può leggere `p->campo` senza copiare l'intera struttura, ma il compilatore impedisce qualsiasi modifica ai suoi campi.

Prima di applicare `->` a un puntatore ricevuto come parametro (o ottenuto da un'allocazione), controlla sempre che non sia nullo (`if (p == nullptr)`). Secondo lo standard C23, l'equivalenza tra `p->campo` e `(*p).campo` e le regole di precedenza di `.` e `->` rispetto a `*` e `&` sono completamente definite; al contrario, applicare `->` a un puntatore nullo, non inizializzato o già liberato provoca **comportamento indefinito**.

I puntatori a struttura si combinano in modo diretto anche con l'allocazione dinamica sullo heap (capitolo 11). Per allocare una singola struttura sullo heap scrivi `malloc(sizeof(*p))` (passando il tipo dell'oggetto puntato, non del puntatore!), controlli `p == nullptr`, inizializzi i campi tramite `->` e al termine rilasci il blocco con `free(p)` seguito da `p = nullptr;`. Infine, se hai bisogno dell'indirizzo di un singolo campo della struttura puntata — per esempio per passarlo a `sscanf` — scrivi semplicemente `&p->campo`, come spiegato nel box di approfondimento più avanti.

Riassumiamo le regole chiave:

- Dato un puntatore `p` a struttura (`struct tag *p` o `const struct tag *p`), `p->campo` equivale esattamente a `(*p).campo`.
- Le parentesi in `(*p).campo` sono obbligatorie perché `.` e `->` hanno precedenza più alta di `*` e `&`.
- Verifica sempre `p != nullptr` prima di usare `p->campo`: dereferenziare con `->` un puntatore nullo, non inizializzato o già liberato è comportamento indefinito.
- Per allocare una singola struttura sullo heap usa `malloc(sizeof(*p))`, controlla `nullptr` e libera il blocco con `free(p)`.

> **Se vieni da Python** — In Python si usa sempre l'operatore punto (`obj.campo`) perché ogni variabile è implicitamente un riferimento a un oggetto. In C si distingue sempre tra accesso diretto a un valore struttura (`s.campo`) e accesso indiretto tramite un puntatore a struttura (`p->campo`).

### Esempio guidato

Il programma seguente gestisce un conto corrente `conto_t` tramite tre funzioni: `deposita` e `preleva` ricevono `conto_t *` per modificare i campi sul posto, mentre `stampa_conto` riceve `const conto_t *` per la sola lettura. Tutte verificano `nullptr` prima di usare `->`. Nella seconda parte di `main`, un secondo conto viene allocato sullo heap con `malloc(sizeof(*secondo))`, aggiornato e liberato con `free`.

<!-- cod: id=12.3-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

typedef struct conto {
    int numero;
    double saldo;
    int operazioni;
} conto_t;

bool deposita(conto_t *c, double importo) {
    if (c == nullptr || importo <= 0.0) { return false; }
    c->saldo += importo;
    ++c->operazioni;
    return true;
}
bool preleva(conto_t *c, double importo) {
    if (c == nullptr || importo <= 0.0 || importo > c->saldo) { return false; }
    c->saldo -= importo;
    ++c->operazioni;
    return true;
}
void stampa_conto(const conto_t *c) {
    if (c != nullptr) {
        printf("Conto #%d: saldo=%.2f euro, operazioni=%d\n", c->numero, c->saldo, c->operazioni);
    }
}
int main(void) {
    conto_t principale = {.numero = 1001, .saldo = 150.0, .operazioni = 0};
    deposita(&principale, 50.0);
    preleva(&principale, 80.0);
    stampa_conto(&principale);
    conto_t *secondo = malloc(sizeof(*secondo));
    if (secondo == nullptr) { return EXIT_FAILURE; }
    secondo->numero = 2002; secondo->saldo = 0.0; secondo->operazioni = 0;
    deposita(secondo, 300.0);
    stampa_conto(secondo);
    free(secondo);
    return 0;
}
```

```output
Conto #1001: saldo=120.00 euro, operazioni=2
Conto #2002: saldo=300.00 euro, operazioni=1
```

Analizziamo i punti salienti dell'esempio:

- In `deposita` e `preleva` il controllo `c == nullptr` precede ogni accesso `c->saldo`: grazie alla valutazione a corto circuito (capitolo 4), se `c` è nullo `c->saldo` non viene mai valutato.
- In `main`, `principale` risiede sullo stack e ne passiamo l'indirizzo `&principale` alle funzioni: le modifiche su `c->saldo` e `c->operazioni` aggiornano direttamente `principale`.
- `stampa_conto` accetta `const conto_t *c`: questo dichiara esplicitamente che la funzione non altera lo stato del conto e consente di chiamarla anche su strutture `const`.
- `secondo` viene allocato sullo heap con `malloc(sizeof(*secondo))`, inizializzato campo per campo con `->`, passato direttamente alle stesse funzioni (è già un `conto_t *`) e infine liberato con `free(secondo);`.

> **Approfondimento — Precedenza tra `->` e `&`**
> Anche l'operatore indirizzo `&` ha precedenza inferiore rispetto a `->` (e a `.`). Per questo l'espressione `&p->saldo` viene raggruppata automaticamente dal compilatore come `&(p->saldo)`: accede prima al campo `saldo` della struttura puntata da `p` e poi ne calcola l'indirizzo (di tipo `double *`). Questa regola è particolarmente utile quando passi i campi di una struttura puntata a funzioni come `sscanf(riga, "%lf", &p->saldo)`.

### Esercizio 12.3 — Controllo di un'unità batteria tramite puntatori a struct e operatore ->

**Descrizione**

Scrivi un programma C che definisca `typedef struct batteria { char seriale[20]; int capacita_wh; int carica_wh; int cicli_completi; bool in_allarme; } batteria_t;` e dichiari prima di `main` i prototipi di tre funzioni che accedono ai campi tramite l'operatore `->` dopo aver verificato che il puntatore non sia `nullptr`: `bool ricarica_batteria(batteria_t *b, int wh)` (rifiuta e restituisce `false` se `b == nullptr || b->in_allarme || wh <= 0`; altrimenti aumenta `b->carica_wh` di `wh` senza superare `b->capacita_wh`, incrementa `b->cicli_completi` se `b->carica_wh == b->capacita_wh` e restituisce `true`), `bool scarica_batteria(batteria_t *b, int wh)` (rifiuta e restituisce `false` se `b == nullptr || b->in_allarme || wh <= 0 || wh > b->carica_wh`; altrimenti sottrae `wh` da `b->carica_wh`, imposta `b->in_allarme = true` se `b->carica_wh * 10 < b->capacita_wh` e restituisce `true`) e `void stampa_batteria(const batteria_t *b)` (stampa lo stato). In `main` leggi dalla prima riga `seriale capacita_wh carica_wh` (`capacita_wh > 0`, `0 <= carica_wh <= capacita_wh`) inizializzando `in_allarme` a `carica_wh * 10 < capacita_wh`, poi elabora i comandi `CARICA <wh>`, `SCARICA <wh>` e `RESET` (che imposta `in_allarme = false` tramite un puntatore `batteria_t *ptr = &unita;`) fino a fine input, stampando ogni esito e lo stato finale con `stampa_batteria(&unita)` esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- puntatori a `struct` (`batteria_t *` e `const batteria_t *`)
- operatore freccia (`p->campo`) equivalente a `(*p).campo`
- modifica sul posto della struttura del chiamante tramite passaggio per puntatore
- controllo difensivo `p != nullptr` prima di accedere ai campi con `->`

**Domande guida**

1. Perché all'interno di `ricarica_batteria` e `scarica_batteria` occorre scrivere `b->carica_wh` invece di `*b.carica_wh`?
2. Qual è la differenza tra il parametro `batteria_t *b` delle funzioni di modifica e il parametro `const batteria_t *b` di `stampa_batteria`?
3. Perché le modifiche effettuate su `b->carica_wh` e `b->in_allarme` si riflettono direttamente sulla variabile `unita` dichiarata in `main`?
4. In che modo il controllo `b->carica_wh * 10 < b->capacita_wh` verifica che la carica sia scesa sotto il 10% senza usare numeri in virgola mobile?

**Esempio di esecuzione**

```input
BAT-A1 1000 300
SCARICA 250
CARICA 200
RESET
CARICA 950
```

```output
SCARICA 250: ok (carica=50 Wh, allarme=1)
CARICA 200: rifiutata
RESET allarme eseguito
CARICA 950: ok (carica=1000 Wh, cicli=1)
Batteria BAT-A1: 1000/1000 Wh, cicli=1, allarme=0
```

## 12.4 Array di `struct` e strutture annidate

Una singola struttura descrive un'entità; nei programmi reali, però, gestisci quasi sempre collezioni di molte entità: tutti gli studenti di una classe, i prodotti di un catalogo o gli eventi di un'agenda. Sostituire più array paralleli (`char nomi[MAX][32]`, `int matricole[MAX]`, `double medie[MAX]`) con un unico array di strutture (`studente_t classe[MAX]`) porta subito un doppio vantaggio: tutti i campi di uno stesso elemento vivono insieme in memoria, uno accanto all'altro, e riordinare o passare la collezione a una funzione richiede di gestire un solo array anziché tre.

In memoria un array di strutture è una sequenza contigua di oggetti identici:

```text
classe[0]                 classe[1]                 classe[2]
+-----------------------+ +-----------------------+ +-----------------------+
| matricola | media     | | matricola | media     | | matricola | media     |
+-----------------------+ +-----------------------+ +-----------------------+
^ &classe[0]              ^ &classe[1]              ^ &classe[2]
```

Per accedere a un campo dell'elemento in posizione `i` combini l'operatore di indicizzazione `[]` con l'operatore punto `.`: scrivi `classe[i].media`. L'espressione `classe[i]` è una variabile di tipo `studente_t`, quindi su di essa si applica il punto. In modo equivalente, usando l'aritmetica dei puntatori vista nel capitolo 10, `(classe + i)` è un puntatore all'`i`-esimo elemento e puoi scrivere `(classe + i)->media`. Quando passi un array di strutture a una funzione che deve solo leggerlo, la firma segue lo schema consueto del capitolo 8: `void stampa_classe(const studente_t v[], size_t n)` (equivalente a `const studente_t *v, size_t n`).

Un'altra tecnica fondamentale per modellare dati reali è la **composizione**: una struttura può avere come campo un'altra struttura già definita in modo completo (una *struttura annidata*). Per esempio, un `evento_t` può contenere un campo `data` di tipo `data_t`:

<!-- cod: id=12.4-b tipo=frammento -->
```c
typedef struct data {
    int giorno;
    int mese;
    int anno;
} data_t;

typedef struct evento {
    data_t data;
    int partecipanti;
} evento_t;
```

Puoi inizializzare una struttura annidata con inizializzatori designati annidati (`evento_t ev = {.data = {.giorno = 15, .mese = 5, .anno = 2026}, .partecipanti = 30};`) e raggiungerne i campi più interni concatenando gli operatori `.` e `->`:

- da una variabile valore: `ev.data.anno`
- da un puntatore `evento_t *p = &ev`: `p->data.anno` (perché `p->data` è un valore `data_t`, non un puntatore).

Fai attenzione a un vincolo strutturale del C: una `struct` può contenere per valore solo tipi completi già definiti prima di essa, mai un campo del proprio stesso tipo (altrimenti la sua dimensione sarebbe infinita). Può invece contenere un *puntatore* al proprio stesso tipo, che ha dimensione fissa — ed è esattamente il meccanismo che useremo nel capitolo 17 per le liste concatenate e gli alberi.

Quando il numero di elementi non è noto a tempo di compilazione, puoi allocare un **array dinamico di strutture sullo heap** usando `malloc`, `calloc` e `realloc` (capitolo 11). La regola d'oro è usare sempre `sizeof(*arr)` per calcolare la dimensione di ciascun elemento, evitando errori se il tipo dovesse cambiare:

<!-- cod: id=12.4-c tipo=frammento -->
```c
size_t nuova_cap = (cap == 0) ? 2 : cap * 2;
articolo_t *tmp = realloc(arr, nuova_cap * sizeof(*arr));
if (tmp == nullptr) {
    /* gestisci l'errore liberando arr */
}
arr = tmp;
cap = nuova_cap;
```

C'è però una situazione che richiede attenzione speciale: quando ogni struttura dell'array contiene a sua volta un campo puntatore allocato sullo heap — per esempio `char *titolo` creato con `strdup`. In quel caso la memoria vive su due livelli distinti: l'array di strutture `arr` è un blocco sullo heap, e ciascun `arr[i].titolo` punta a un proprio blocco separato sullo heap.

Se alla fine chiamassi soltanto `free(arr)`, libereresti l'array contenente i puntatori ma perderesti tutti gli indirizzi delle stringhe, generando una **perdita di memoria**. D'altra parte, se liberassi `arr` prima di liberare `arr[i].titolo`, accedere ad `arr[i].titolo` dopo `free(arr)` sarebbe un **uso dopo la liberazione** (comportamento indefinito). L'ordine di rilascio è quindi obbligato, dall'interno verso l'esterno: prima un ciclo che chiama `free(arr[i].titolo)` per ogni elemento da `0` a `len - 1`, poi `free(arr)`.

Riassumiamo le regole principali:

- Una struttura può contenere array di dimensione fissa, puntatori o altre strutture già definite in modo completo (strutture annidate, accessibili concatenando `.` e `->`).
- Non è consentito che una struttura contenga per valore un campo del proprio stesso tipo incompleto (solo un puntatore a esso).
- Gli array dinamici di strutture sullo heap si allocano e si ridimensionano con `malloc`, `calloc` e `realloc` moltiplicando il numero di elementi per `sizeof(*arr)` e usando sempre un puntatore temporaneo con `realloc`.
- Se una struttura contiene campi puntatore allocati sullo heap, occorre liberare ogni campo puntatore con `free` prima di liberare la struttura o l'array che la ospita; omettere questo passaggio causa una perdita di memoria, invertirne l'ordine provoca comportamento indefinito.

### Esempio guidato

Il programma seguente costruisce sullo heap un array dinamico di `articolo_t`. Ogni articolo contiene una struttura annidata `dimensioni_t` e un campo `char *titolo` allocato sullo heap con `strdup`. Al crescere degli inserimenti l'array raddoppia la capacità con `realloc`, calcola il volume complessivo e infine rilascia la memoria nell'ordine corretto (prima ogni `titolo`, poi l'array).

<!-- cod: id=12.4-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct dimensioni { int largh; int alt; int prof; } dimensioni_t;
typedef struct articolo { char *titolo; dimensioni_t dim; } articolo_t;

void libera_catalogo(articolo_t *cat, size_t n) {
    for (size_t i = 0; i < n; ++i) { free(cat[i].titolo); }
    free(cat);
}
int main(void) {
    const char *nomi[3] = {"Scatola_A", "Cassa_B", "Pacco_C"};
    const dimensioni_t misure[3] = {{10, 20, 5}, {30, 10, 10}, {8, 8, 8}};
    articolo_t *cat = nullptr;
    size_t len = 0, cap = 0;
    for (size_t i = 0; i < 3; ++i) {
        if (len == cap) {
            size_t ncap = (cap == 0) ? 2 : cap * 2;
            articolo_t *tmp = realloc(cat, ncap * sizeof(*cat));
            if (tmp == nullptr) { libera_catalogo(cat, len); return EXIT_FAILURE; }
            cat = tmp; cap = ncap;
        }
        cat[len].titolo = strdup(nomi[i]);
        if (cat[len].titolo == nullptr) { libera_catalogo(cat, len); return EXIT_FAILURE; }
        cat[len].dim = misure[i];
        ++len;
    }
    long volume_tot = 0;
    for (size_t i = 0; i < len; ++i) {
        long vol = (long)cat[i].dim.largh * cat[i].dim.alt * cat[i].dim.prof;
        volume_tot += vol;
        printf("%s: %dx%dx%d (vol=%ld)\n",
               cat[i].titolo, cat[i].dim.largh, cat[i].dim.alt, cat[i].dim.prof, vol);
    }
    printf("Articoli: %zu (capacita: %zu), volume totale: %ld\n", len, cap, volume_tot);
    libera_catalogo(cat, len);
    return 0;
}
```

```output
Scatola_A: 10x20x5 (vol=1000)
Cassa_B: 30x10x10 (vol=3000)
Pacco_C: 8x8x8 (vol=512)
Articoli: 3 (capacita: 4), volume totale: 4512
```

Osserva attentamente la gestione della memoria nell'esempio:

- `articolo_t` incorpora per valore `dimensioni_t dim` e memorizza `char *titolo` come puntatore a una stringa sullo heap.
- Il ciclo di inserimento parte da `cat = nullptr`, `len = 0`, `cap = 0`: al primo elemento `realloc` alloca 2 posti, al terzo elemento raddoppia la capacità a 4 usando `sizeof(*cat)` e il puntatore temporaneo `tmp`.
- Se `realloc` o `strdup` fallisce, la funzione `libera_catalogo(cat, len)` rilascia subito i `len` titoli già allocati e l'array `cat`, prevenendo perdite di memoria anche sui rami di errore. Nota che al momento del fallimento di `strdup`, `len` non è ancora stato incrementato, quindi `libera_catalogo` libera esattamente gli elementi validi.
- Nel ciclo di stampa l'accesso ai campi della struttura annidata concatena `[]` e due operatori punto: `cat[i].dim.largh`.

> **Approfondimento — Campo `char nome[32]` incorporato o `char *nome` sullo heap?**
> Quando una struttura deve contenere una stringa, hai due alternative. Un array incorporato (`char nome[32]`) non richiede allocazioni separate né `free`, mantiene tutti i dati contigui in memoria e si copia automaticamente con `=`, ma impone una lunghezza massima fissa e spreca spazio per stringhe molto brevi. Un puntatore sullo heap (`char *nome` allocato con `strdup`) adatta la memoria alla lunghezza effettiva della stringa, ma richiede un controllo di allocazione, una liberazione esplicita e una cura particolare quando si copia la struttura (come vedrai nella prossima sotto-sezione).

### Esercizio 12.4 — Registro dinamico di eventi con struct annidate e stringhe sullo heap

**Descrizione**

Scrivi un programma C che definisca una struttura `typedef struct orario { int ore; int minuti; } orario_t;` annidata dentro `typedef struct evento { orario_t inizio; int durata_min; char *titolo; } evento_t;`. Leggi dalla prima riga di `stdin` un orario di filtro `ore minuti` (`0 <= ore <= 23`, `0 <= minuti <= 59`). Leggi poi fino a fine input un numero arbitrario di righe nel formato `ore minuti durata titolo` (`durata > 0` e `titolo` non vuoto, estratto con `%63s`), memorizzandole in un array dinamico `evento_t *agenda = nullptr;` gestito con `len` e `cap` che raddoppia di capacità (`0 -> 2 -> 4 -> ...`) tramite `realloc` e puntatore temporaneo, e duplicando `titolo` sullo heap con `strdup`. In caso di errore libera ogni `agenda[i].titolo` già allocato e poi `agenda`, stampa su `stderr` e restituisci `EXIT_FAILURE`. Terminata la lettura, scorri `agenda` e stampa tutti gli eventi il cui orario `inizio` è maggiore o uguale al filtro (`inizio.ore > filtro.ore || (inizio.ore == filtro.ore && inizio.minuti >= filtro.minuti)`), calcolando il numero di eventi selezionati e la somma delle loro durate. Infine libera tutti i campi `titolo` e l'array `agenda` e stampa il riepilogo esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- strutture annidate (`orario_t` dentro `evento_t`) e accesso concatenato `ev.inizio.ore`
- array dinamico di `struct` sullo heap ridimensionato con `realloc(agenda, nuova_cap * sizeof(*agenda))`
- campo puntatore `char *titolo` allocato sullo heap con `strdup`
- rilascio ordinato della memoria: prima `free(agenda[i].titolo)` per ogni elemento, poi `free(agenda)`

**Domande guida**

1. Come si accede al campo `minuti` dell'orario di inizio dell'`i`-esimo elemento dell'array `agenda`?
2. Che cosa succederebbe se a fine programma chiamassi soltanto `free(agenda)` senza aver prima chiamato `free(agenda[i].titolo)` in un ciclo?
3. Perché non potresti chiamare `free(agenda[i].titolo)` dopo aver già eseguito `free(agenda)`?
4. Come confronti correttamente due strutture `orario_t` per stabilire se un evento inizia a partire dall'orario di filtro?

**Esempio di esecuzione**

```input
10 30
09 15 45 Briefing
10 30 60 Laboratorio_C
14 00 30 Revisione_codice
10 00 20 Pausa
```

```output
10:30 (60 min) - Laboratorio_C
14:00 (30 min) - Revisione_codice
Eventi totali: 4 (capacita array: 4)
Selezionati da 10:30: 2 (durata totale: 90 min)
```

## 12.5 Copia, passaggio e restituzione di `struct`

Con gli array del capitolo 8 non puoi scrivere `b = a` per copiare un intero array in un altro, né restituire un array da una funzione. Con le strutture il comportamento del C è diverso: due variabili dello stesso tipo struttura possono essere assegnate direttamente con l'operatore `=`. Scrivere `s2 = s1;` copia tutti i campi di `s1` in `s2`, inclusi eventuali array a dimensione fissa incorporati nella struttura (come `char codice[16]`). Dopo l'assegnamento, `s1` e `s2` sono oggetti distinti: modificare un campo scalare o un array incorporato di `s2` non altera `s1`.

Al contrario, il C **non permette** di confrontare due strutture con `s1 == s2` oppure `s1 != s2`: il compilatore segnala un errore perché gli operatori di uguaglianza non sono definiti per le `struct`. Il motivo è legato anche ai byte inutilizzati che il compilatore può inserire tra i campi (capitolo 13), il cui contenuto può variare tra due strutture con gli stessi valori logici. Per confrontare due strutture scrivi sempre una funzione dedicata che confronta i campi uno per uno:

<!-- cod: id=12.5-b tipo=frammento -->
```c
bool vettore_uguale(const vettore2d_t *a, const vettore2d_t *b) {
    return a != nullptr && b != nullptr && a->x == b->x && a->y == b->y;
}
```

Proprio perché una `struct` può essere copiata con `=`, può anche essere **passata per valore** a una funzione e **restituita per valore** da una funzione. Questo rende molto espressive le funzioni di calcolo su piccoli tipi geometrici o matematici:

<!-- cod: id=12.5-c tipo=frammento -->
```c
vettore2d_t somma_vettori(vettore2d_t a, vettore2d_t b) {
    return (vettore2d_t){.x = a.x + b.x, .y = a.y + b.y};
}
```

Osserva l'espressione nel `return`: `(vettore2d_t){.x = a.x + b.x, .y = a.y + b.y}`. Questa sintassi si chiama **letterale composto** (*compound literal*) ed è composta dal nome del tipo tra parentesi tonde seguito da un inizializzatore tra parentesi graffe. Crea al volo un oggetto struttura senza nome, comodissimo per restituire una struttura da una funzione, per passarla direttamente come argomento (`somma_vettori((vettore2d_t){.x = 1.0, .y = 2.0}, v)`) o per riassegnare tutti i campi di una struttura esistente in una sola istruzione (`v = (vettore2d_t){.x = 0.0, .y = 0.0};`).

Come scegliere allora tra passaggio per valore (`tipo_t s`) e passaggio per puntatore a costante (`const tipo_t *s`) quando una funzione deve solo leggere una struttura? Segui una regola pratica semplice:

- **Passaggio per valore (`tipo_t s`)**: ideale per strutture piccole (1–3 campi scalari, come un punto 2D, un intervallo o una data), perché il costo della copia è trascurabile e il codice risulta più diretto.
- **Passaggio per puntatore a costante (`const tipo_t *s`)**: preferibile per strutture più grandi, per strutture che contengono array interni o quando vuoi rendere esplicito che l'oggetto non va copiato. Se la funzione deve modificare la struttura del chiamante, il puntatore non `const` (`tipo_t *s`) è ovviamente obbligatorio.

C'è infine un'insidia fondamentale da conoscere quando una struttura contiene un **campo puntatore allocato sullo heap** (come `char *testo`). L'assegnamento `n2 = n1;` esegue una **copia superficiale** (*shallow copy*): copia il valore del puntatore, cioè l'indirizzo di memoria, non il blocco di caratteri sullo heap. Il risultato è che `n1.testo` e `n2.testo` puntano esattamente alla stessa stringa:

```text
Copia superficiale (n2 = n1):
  n1.testo ---+
              +---> [ 'C' | 'i' | 'a' | 'o' | '\0' ]  (un solo blocco sullo heap)
  n2.testo ---+

Copia profonda (clona_nota(&n1, &n2)):
  n1.testo -------> [ 'C' | 'i' | 'a' | 'o' | '\0' ]  (blocco 1)
  n2.testo -------> [ 'C' | 'i' | 'a' | 'o' | '\0' ]  (blocco 2 indipendente)
```

Con la copia superficiale si verificano due gravi problemi: modificare i caratteri attraverso `n2.testo` modifica inaspettatamente anche `n1.testo` (aliasing involontario), e chiamare poi `free(n1.testo)` seguito da `free(n2.testo)` provoca una **doppia liberazione**, cioè comportamento indefinito. Per ottenere un clone realmente indipendente occorre scrivere una funzione di **copia profonda** (*deep copy*) che alloca una nuova copia di ciascun blocco sullo heap (per esempio con `strdup` o `malloc`) e controlla che l'allocazione sia riuscita.

Riassumiamo le regole di questa sotto-sezione:

- Due strutture dello stesso tipo si assegnano direttamente con `=`, si passano per valore e si restituiscono per valore (copiando anche eventuali array a dimensione fissa incorporati).
- Gli operatori `==` e `!=` non sono definiti per le strutture: il confronto va scritto campo per campo.
- Un letterale composto `(struct tag){.campo = valore}` crea un oggetto struttura senza nome (con durata di vita automatica se dichiarato dentro un blocco).
- Secondo lo standard C23, copia con `=`, passaggio/ritorno per valore, divieto di `==`/`!=` e durata di vita dei letterali composti sono completamente definiti; liberare due volte lo stesso blocco sullo heap condiviso in seguito a una copia superficiale provoca invece **comportamento indefinito**.

> **Se vieni da Python** — In Python l'assegnamento `b = a` tra due oggetti copia soltanto il riferimento allo stesso oggetto in memoria. In C l'assegnamento `s2 = s1` tra due variabili `struct` copia per valore tutti i campi in una struttura distinta; soltanto i campi puntatore all'interno della struttura risultano condivisi finché non esegui una copia profonda.

### Esempio guidato

Il programma seguente mostra entrambi i casi. Nella prima parte manipola piccole strutture `vettore2d_t` passate e restituite per valore con letterali composti e confrontate con `vettore_uguale`. Nella seconda parte definisce `nota_t` con un campo `char *testo` sullo heap e usa `clona_nota` per eseguire una copia profonda indipendente.

<!-- cod: id=12.5-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct vettore2d { double x; double y; } vettore2d_t;
typedef struct nota { int id; char *testo; } nota_t;

vettore2d_t somma_vettori(vettore2d_t a, vettore2d_t b) {
    return (vettore2d_t){.x = a.x + b.x, .y = a.y + b.y};
}
bool vettore_uguale(const vettore2d_t *a, const vettore2d_t *b) {
    return a != nullptr && b != nullptr && a->x == b->x && a->y == b->y;
}
bool clona_nota(const nota_t *orig, nota_t *dest) {
    if (orig == nullptr || dest == nullptr || orig->testo == nullptr) { return false; }
    char *copia = strdup(orig->testo);
    if (copia == nullptr) { return false; }
    *dest = (nota_t){.id = orig->id, .testo = copia};
    return true;
}
int main(void) {
    vettore2d_t v1 = {.x = 1.5, .y = 2.0};
    vettore2d_t s = somma_vettori(v1, (vettore2d_t){.x = 2.5, .y = -1.0});
    vettore2d_t atteso = {.x = 4.0, .y = 1.0};
    printf("Somma: (%.1f, %.1f), uguale ad atteso: %s\n",
           s.x, s.y, vettore_uguale(&s, &atteso) ? "si" : "no");
    nota_t n1 = {.id = 1, .testo = strdup("bozza")};
    nota_t n2 = {};
    if (n1.testo == nullptr || !clona_nota(&n1, &n2)) { free(n1.testo); return EXIT_FAILURE; }
    n2.testo[0] = 'B';
    printf("n1: #%d %s | n2: #%d %s\n", n1.id, n1.testo, n2.id, n2.testo);
    free(n1.testo);
    free(n2.testo);
    return 0;
}
```

```output
Somma: (4.0, 1.0), uguale ad atteso: si
n1: #1 bozza | n2: #1 Bozza
```

Analizziamo i punti chiave del programma:

- `somma_vettori` riceve due `vettore2d_t` per valore e restituisce un nuovo `vettore2d_t` costruito con un letterale composto. Anche nella chiamata in `main` il secondo argomento è un letterale composto passato al volo senza creare una variabile d'appoggio.
- `vettore_uguale` riceve due `const vettore2d_t *` e confronta i campi `x` e `y` (qui i valori `1.5 + 2.5 = 4.0` e `2.0 - 1.0 = 1.0` sono rappresentabili esattamente in binario; per calcoli generici in virgola mobile ricorda la tolleranza vista nel capitolo 3).
- `clona_nota` duplica `orig->testo` con `strdup` prima di popolare `*dest`: quando `main` modifica `n2.testo[0] = 'B'`, `n1.testo` rimane `"bozza"`, e le due chiamate finali a `free` rilasciano due blocchi distinti senza alcuna doppia liberazione.

> **Approfondimento — Durata di vita di un letterale composto**
> Quando scrivi un letterale composto come `(punto_t){.x = 3, .y = 4}` dentro una funzione, il compilatore crea un oggetto con **durata di vita automatica** associato al blocco corrente (esattamente come una variabile locale). Puoi persino prenderne l'indirizzo per passarlo a una funzione chiamata in quel blocco — per esempio `stampa_punto(&(punto_t){.x = 3, .y = 4});` — ma non devi mai restituire quell'indirizzo al chiamante: all'uscita dal blocco l'oggetto cessa di esistere e il puntatore diventerebbe non valido.

### Esercizio 12.5 — Operazioni su intervalli per valore, letterali composti e copia profonda di fasce

**Descrizione**

Scrivi un programma C che definisca `typedef struct intervallo { int min; int max; } intervallo_t;` e `typedef struct fascia { intervallo_t lim; char *etichetta; } fascia_t;`. Dichiara prima di `main` i prototipi di quattro funzioni: `intervallo_t crea_intervallo(int a, int b)` (restituisce per valore il letterale composto `(intervallo_t){.min = (a <= b ? a : b), .max = (a <= b ? b : a)}`), `bool intervallo_uguale(const intervallo_t *a, const intervallo_t *b)` (confronta campo per campo i due intervalli passati per puntatore a `const`), `bool intersezione(intervallo_t a, intervallo_t b, intervallo_t *out)` (calcola `lo = a.min > b.min ? a.min : b.min` e `hi = a.max < b.max ? a.max : b.max`; se `lo <= hi` assegna `*out = (intervallo_t){.min = lo, .max = hi}` e restituisce `true`, altrimenti `false`) e `bool clona_fascia(const fascia_t *orig, fascia_t *dest)` (copia `orig->lim` per assegnamento di `struct` e duplica `orig->etichetta` con `strdup` per ottenere una copia profonda indipendente). In `main` leggi due righe: dalla prima `a1 b1 nome` (`%31s`), dalla seconda `a2 b2 delta`. Crea `fascia_t f1` con `crea_intervallo(a1, b1)` e `strdup(nome)`, clonala in `fascia_t f2` con `clona_fascia(&f1, &f2)` e trasla `f2.lim` di `delta` (`f2.lim.min += delta; f2.lim.max += delta;`) modificando il primo carattere di `f2.etichetta` in `'@'` per dimostrare che `f1` resta invariata. Confronta `f1.lim` con `crea_intervallo(a2, b2)` tramite `intervallo_uguale`, calcola l'intersezione tra `f1.lim` e il secondo intervallo, stampa tutto come nell'esempio e libera entrambe le etichette.

**Concetti da tenere a mente**

- passaggio e restituzione di piccole `struct` per valore con letterali composti `(intervallo_t){...}`
- confronto campo per campo tramite puntatori a `const` (assenza di `==` tra `struct`)
- differenza tra copia superficiale (`=`) e copia profonda (`clona_fascia` con `strdup`) per `struct` con puntatori
- indipendenza in memoria del clone rispetto alla struttura originale

**Domande guida**

1. Perché non puoi confrontare direttamente due variabili `intervallo_t` scrivendo `i1 == i2` ma devi usare la funzione `intervallo_uguale`?
2. Che cosa accadrebbe a `f1.etichetta` e al momento delle due chiamate a `free` se copiassi `f2 = f1` con un semplice assegnamento invece di usare `clona_fascia`?
3. Come viene usato il letterale composto dentro `crea_intervallo` e `intersezione` per costruire un oggetto `intervallo_t` senza dichiarare una variabile temporanea?
4. Perché per `intervallo_t` (due soli `int`) è pratico il passaggio per valore mentre per `fascia_t` conviene il passaggio per puntatore a `const`?

**Esempio di esecuzione**

```input
30 10 Normale
20 40 5
```

```output
Originale f1: [10, 30] etichetta=Normale
Clone mod f2: [15, 35] etichetta=@ormale
Secondo intervallo: [20, 40] (uguale a f1: no)
Intersezione f1 e secondo: [20, 30]
```

## Riepilogo

- Una **struttura** (`struct nome_tag { ... };`) raggruppa più **campi** anche di tipi diversi nell'ordine dichiarato. Si accede ai campi di una variabile struttura con l'operatore punto (`s.campo`); l'inizializzazione può essere posizionale, con inizializzatori designati (`{.campo = valore}`) o, in C23, con `{}` per azzerare tutti i campi. La dimensione `sizeof(struct nome_tag)` è maggiore o uguale alla somma delle dimensioni dei campi per via dei byte inutilizzati inseriti dal compilatore in memoria (lo vedremo nel capitolo 13).
- Un'**enumerazione** (`enum nome_tag { ... };`) associa nomi simbolici a costanti intere (da `0` in poi, o con valori espliciti) e si abbina in modo naturale a `switch`. In C23 è possibile fissarne il tipo intero sottostante (`enum nome_tag : int { ... };`). La parola chiave `typedef` crea un alias compatto per un tipo esistente senza introdurre un tipo distinto: mantieni sempre l'etichetta della `struct` ed evita di nascondere puntatori dentro un `typedef` (salvo i tipi opachi che vedremo nel capitolo 19).
- Con un puntatore a struttura `p` si usa l'operatore freccia `p->campo`, equivalente a `(*p).campo`: le parentesi sono obbligatorie perché `.` e `->` hanno precedenza superiore a `*` e `&`. Verifica sempre `p != nullptr` prima di applicare `->`. Le funzioni ricevono `tipo_t *` per modificare una struttura sul posto e `const tipo_t *` per leggerla senza copiarla.
- Le strutture si possono raccogliere in array sullo stack o in array dinamici sullo heap (`malloc`, `calloc`, `realloc` con `sizeof(*arr)` e puntatore temporaneo) e possono contenere altre strutture complete come campi (strutture annidate, con accessi concatenati `v[i].campo.sottocampo` o `p->campo.sottocampo`). Se una struttura contiene puntatori allocati sullo heap, libera prima tutti i campi puntatore e solo dopo la struttura o l'array.
- Le strutture dello stesso tipo si copiano con `=`, si passano e si restituiscono per valore e si costruiscono al volo con i letterali composti `(tipo_t){...}`. Non esistono `==` e `!=` diretti tra strutture: il confronto va scritto campo per campo. Per strutture con campi puntatore sullo heap, `=` esegue una copia superficiale dell'indirizzo: serve una funzione di copia profonda (per esempio con `strdup` o `malloc`) per ottenere cloni indipendenti ed evitare doppie liberazioni.

## Errori comuni

- **Dimenticare il punto e virgola dopo la graffa di chiusura di `struct` o `enum`**: il compilatore segnala errori sintattici sulla dichiarazione successiva, spesso lontano dal punto reale del problema.
- **Scrivere `*p.campo` invece di `p->campo` (o `(*p).campo`)**: poiché `.` ha precedenza maggiore di `*`, il compilatore interpreta l'espressione come `*(p.campo)` e rifiuta il codice perché `p` è un puntatore, non una struttura.
- **Tentare di confrontare due strutture con `s1 == s2` o `s1 != s2`**: gli operatori di uguaglianza non sono applicabili alle `struct`; occorre sempre una funzione che confronti i singoli campi.
- **Liberare una `struct` o un array dinamico di `struct` senza aver prima liberato i campi puntatore interni**: chiamare soltanto `free(arr)` lascia sullo heap tutte le stringhe o i buffer puntati dai singoli elementi, provocando una perdita di memoria; liberare i campi dopo `free(arr)` provoca invece uso dopo la liberazione.
- **Copiare con `=` una `struct` che contiene puntatori sullo heap**: la copia superficiale fa condividere lo stesso blocco tra originale e copia, causando modifiche incrociate e doppia liberazione al momento di `free`.
- **Omettere `struct` senza `typedef` oppure nascondere un puntatore dentro un `typedef`**: senza `typedef` occorre scrivere `struct nome_tag`, mentre nascondere `*` dentro un alias rende poco visibili le dereferenziazioni e i qualificatori `const`.

## Prima di proseguire

- [ ] So definire una `struct`, inizializzarla con inizializzatori designati o `{}` (C23) e leggerne o modificarne i campi con l'operatore punto.
- [ ] So definire un'`enum` (anche con tipo sottostante esplicito in C23), usarla in uno `switch` e creare alias puliti con `typedef` senza nascondere puntatori.
- [ ] So dichiarare puntatori `tipo_t *` e `const tipo_t *`, accedere ai campi con `->` dopo il controllo `nullptr` e allocare/liberare una struttura sullo heap con `malloc(sizeof(*p))` e `free`.
- [ ] So gestire array dinamici di strutture e strutture annidate liberando sempre i campi puntatore allocati sullo heap prima di liberare l'array.
- [ ] So decidere quando passare una `struct` per valore o per `const tipo_t *`, usare i letterali composti, scrivere funzioni di confronto campo per campo e realizzare una copia profonda quando la struttura contiene puntatori.
