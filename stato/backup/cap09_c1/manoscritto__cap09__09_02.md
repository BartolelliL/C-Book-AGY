## 9.2 Elaborare stringhe con `<string.h>`

Scrivere ogni volta un ciclo manuale per misurare, confrontare o cercare dentro una stringa sarebbe lungo e ripetitivo. La libreria standard del C raccoglie queste operazioni nell'header `<string.h>`. Le funzioni di `<string.h>` sono veloci e ben collaudate, ma richiedono attenzione: tutte presumono che le stringhe in ingresso siano terminate da `'\0'` e che tu rispetti la capacità dei buffer di destinazione.

### Misurare la lunghezza: `strlen`

La funzione `strlen(s)` restituisce un `size_t` pari al numero di caratteri di `s` che precedono il terminatore nullo `'\0'`. A differenza di `sizeof`, `strlen` non conosce la capacità del buffer: scorre la stringa byte per byte finché non incontra `'\0'`.

Questa proprietà ha una conseguenza pratica importante: **non chiamare mai `strlen(s)` nella condizione di un ciclo `for`**.

<!-- cod: id=9.2-b tipo=frammento -->
```c
// Inefficiente: ricalcola strlen(s) a ogni iterazione
for (size_t i = 0; i < strlen(s); ++i) { ... }

// Corretto: calcola la lunghezza una sola volta prima del ciclo
size_t lun = strlen(s);
for (size_t i = 0; i < lun; ++i) { ... }
```

Su una stringa di lunghezza $n$, chiamare `strlen(s)` a ogni iterazione trasforma un semplice attraversamento lineare in un lavoro proporzionale a $n \cdot n$. Se invece salvi il valore in una variabile `size_t lun = strlen(s);` (oppure controlli direttamente `s[i] != '\0'`), scorri la stringa una sola volta.

### Confrontare stringhe: `strcmp` e `strncmp`

Come per qualunque altro array (capitolo 8), non puoi confrontare due stringhe con `s1 == s2`: quell'espressione non confronta i caratteri delle due stringhe. Per confrontare il contenuto di due stringhe in ordine lessicografico (cioè carattere per carattere secondo il valore numerico di ciascun byte interpretato come `unsigned char`) si usano:

- `strcmp(s1, s2)` confronta interamente `s1` e `s2`.
- `strncmp(s1, s2, n)` confronta al più i primi `n` caratteri di `s1` e `s2` (utile per verificare un prefisso).

Entrambe restituiscono un `int` il cui **segno** indica il risultato del confronto:

- `< 0` se `s1` precede `s2` in ordine lessicografico;
- `0` se le due stringhe (o i primi `n` caratteri) sono uguali;
- `> 0` se `s1` segue `s2`.

Lo standard C23 definisce solo il segno del valore restituito, non la sua grandezza: non scrivere mai `strcmp(a, b) == 1` o `strcmp(a, b) == -1`, ma confronta sempre con `0` (`< 0`, `== 0`, `> 0`).

### Cercare caratteri, sottostringhe e prefissi

`<string.h>` mette a disposizione due famiglie di funzioni di ricerca:

1. **Funzioni di ricerca che segnalano presenza o assenza tramite `nullptr`**:
   - `strchr(s, c)` cerca la **prima** occorrenza del carattere `(char)c` in `s` (incluso `'\0'`);
   - `strrchr(s, c)` cerca l'**ultima** occorrenza del carattere `(char)c` in `s`;
   - `strstr(s1, s2)` cerca la prima occorrenza della sottostringa `s2` dentro `s1`;
   - `strpbrk(s1, s2)` cerca in `s1` il primo carattere che appartiene all'insieme di caratteri contenuti in `s2`.

   Tutte e quattro restituiscono `nullptr` se la ricerca fallisce, oppure un puntatore alla posizione trovata. Imparerai a usare direttamente quel puntatore nel capitolo 10; in questo capitolo puoi già verificare se un carattere o una sottostringa è presente confrontando il risultato con `!= nullptr` (o `== nullptr`).

2. **Funzioni che misurano un prefisso e restituiscono un `size_t`**:
   - `strcspn(s1, s2)` restituisce la lunghezza del prefisso iniziale di `s1` composto solo da caratteri **assenti** in `s2`;
   - `strspn(s1, s2)` restituisce la lunghezza del prefisso iniziale di `s1` composto **esclusivamente** da caratteri **presenti** in `s2`.

Con `strcspn` si scrive l'idioma standard più pulito per rimuovere il ritorno a capo lasciato da `fgets`:

<!-- cod: id=9.2-c tipo=frammento -->
```c
riga[strcspn(riga, "\n")] = '\0';
```

Se `riga` contiene `'\n'`, `strcspn(riga, "\n")` restituisce esattamente l'indice di `'\n'`, che viene sostituito con `'\0'`. Se `riga` non contiene `'\n'`, `strcspn` restituisce la lunghezza della stringa, cioè l'indice del terminatore nullo già presente, che viene riscritto con `'\0'` senza alcun danno. Con `strspn`, invece, puoi verificare che una stringa contenga solo caratteri permessi controllando `strspn(s, ammessi) == strlen(s)`.

### Copia e concatenazione: `strcpy`, `strncpy`, `strcat` e `strncat`

Come per il confronto, non puoi copiare una stringa con `dest = orig`. In `<string.h>` esistono quattro funzioni per copiare e accodare stringhe:

- `strcpy(dest, orig)` copia `orig` in `dest`, incluso `'\0'`, senza verificare la capacità di `dest`.
- `strcat(dest, orig)` accoda `orig` al termine di `dest`, incluso `'\0'`, senza verificare la capacità di `dest`.
- `strncpy(dest, orig, n)` copia al più `n` caratteri da `orig` in `dest`. Se `orig` è più corta di `n`, riempie i byte rimanenti con `'\0'`. **Attenzione**: se `orig` ha lunghezza maggiore o uguale a `n`, `strncpy` **non scrive alcun `'\0'` finale**, lasciando `dest` privo di terminatore nullo se non lo imposti tu esplicitamente.
- `strncat(dest, orig, n)` accoda al più `n` caratteri di `orig` al termine di `dest` e aggiunge **sempre** `'\0'` finale. **Attenzione**: il terzo argomento `n` non è la dimensione totale del buffer `dest`, ma il numero massimo di caratteri da aggiungere; perciò `dest` deve avere almeno `strlen(dest) + n + 1` byte di capacità totale (spesso si passa `sizeof(dest) - strlen(dest) - 1` dopo aver verificato che resti spazio).

Regola fondamentale dallo standard C23: in tutte e quattro le funzioni (`strcpy`, `strncpy`, `strcat`, `strncat`), sorgente e destinazione **non devono sovrapporsi in memoria** e la scrittura **non deve mai superare la capacità di `dest`**; violare una delle due condizioni provoca **comportamento indefinito**. Controlla sempre in anticipo la capacità disponibile prima di copiare o accodare.

> **Se vieni da Python** — In Python puoi confrontare e concatenare stringhe con `==` e `+`, e `len(s)` impiega tempo costante. In C devi usare funzioni come `strcmp`, `snprintf` o copie e concatenazioni controllate verificando sempre la capienza del buffer, e `strlen(s)` scorre la stringa fino a `'\0'`.

> **C23** — In C23 `strchr`, `strrchr`, `strstr` e `strpbrk` sono definite come macro generiche che preservano il qualificatore `const` del primo argomento: se passi una stringa `const char[]`, il risultato mantiene `const` evitando modifiche accidentali. Nei compilatori più vecchi (C11/C17) queste funzioni restituivano sempre `char *` anche quando il primo argomento era `const`.

### Esempio guidato

Il programma seguente legge due nomi di file di registro da `stdin`, rimuove `'\n'` con `strcspn`, verifica se il primo inizia con `"log_"` tramite `strncmp`, controlla la presenza del punto con `strrchr` e della sottostringa `"err"` con `strstr`, confronta i due nomi in ordine lessicografico con `strcmp` e infine compone un percorso etichettato controllando la capienza prima di `strcpy` e `strncat`.

<!-- cod: id=9.2-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char nome1[64];
    char nome2[64];
    char percorso[80] = "";

    if (fgets(nome1, (int)sizeof(nome1), stdin) == nullptr ||
        fgets(nome2, (int)sizeof(nome2), stdin) == nullptr) {
        fprintf(stderr, "Errore: servono due nomi di file.\n");
        return EXIT_FAILURE;
    }
    nome1[strcspn(nome1, "\n")] = '\0';
    nome2[strcspn(nome2, "\n")] = '\0';

    bool prefisso_log = (strncmp(nome1, "log_", 4) == 0);
    bool ha_punto = (strrchr(nome1, '.') != nullptr);
    bool contiene_err = (strstr(nome1, "err") != nullptr);

    printf("File 1: %s (lunghezza %zu)\n", nome1, strlen(nome1));
    printf("Prefisso log_: %s, punto: %s, contiene err: %s\n",
           prefisso_log ? "si" : "no", ha_punto ? "si" : "no",
           contiene_err ? "si" : "no");

    int cmp = strcmp(nome1, nome2);
    printf("Ordine: %s\n", cmp < 0 ? "nome1 prima di nome2"
                         : (cmp > 0 ? "nome1 dopo nome2" : "uguali"));

    const char DIR[] = "archivio/";
    if (strlen(DIR) + strlen(nome1) < sizeof(percorso)) {
        strcpy(percorso, DIR);
        size_t spazio = sizeof(percorso) - strlen(percorso) - 1;
        strncat(percorso, nome1, spazio);
        printf("Percorso: %s\n", percorso);
    } else {
        printf("Percorso troppo lungo per il buffer.\n");
    }
    return EXIT_SUCCESS;
}
```

```input
log_errore.txt
log_avvio.txt
```

```output
File 1: log_errore.txt (lunghezza 14)
Prefisso log_: si, punto: si, contiene err: si
Ordine: nome1 dopo nome2
Percorso: archivio/log_errore.txt
```

Osserva come lavorano insieme le funzioni di `<string.h>`:

- `strcspn(nome1, "\n")` individua subito l'eventuale ritorno a capo e lo sostituisce con `'\0'`.
- `strncmp(nome1, "log_", 4) == 0` controlla solo i primi 4 caratteri senza richiedere che l'intera stringa sia uguale a `"log_"`.
- `strrchr(nome1, '.') != nullptr` e `strstr(nome1, "err") != nullptr` rispondono in modo pulito a domande di presenza senza bisogno di manipolare direttamente i puntatori restituiti.
- `strcmp(nome1, nome2)` confronta `"log_errore.txt"` e `"log_avvio.txt"`: poiché `'e'` segue `'a'`, restituisce un intero maggiore di `0`, e controlliamo `cmp > 0` (mai `cmp == 1`).
- Prima di chiamare `strcpy` e `strncat` verifichiamo `strlen(DIR) + strlen(nome1) < sizeof(percorso)` (stretto `<`, per lasciare almeno un byte a `'\0'`), e calcoliamo lo spazio residuo `sizeof(percorso) - strlen(percorso) - 1` come terzo argomento di `strncat`.

> **Approfondimento — Insidie di `strncpy` e conservazione di `const` in C23**
> Molti principianti pensano che `strncpy` sia la versione "sicura" di `strcpy`, ma non lo è affatto: è stata progettata originariamente per campi di lunghezza fissa non necessariamente terminati da `'\0'`. Se scrivi `strncpy(dest, orig, sizeof(dest));` e `orig` ha almeno `sizeof(dest)` caratteri, `dest` rimane privo di `'\0'`; dovresti quindi scrivere comunque `dest[sizeof(dest) - 1] = '\0';`. Inoltre, se `orig` è corta e `dest` è grande, `strncpy` spreca tempo azzerando tutti i byte residui. Per copiare stringhe in modo chiaro e sicuro conviene quasi sempre controllare la lunghezza prima di `strcpy` oppure usare `snprintf` (sotto-sezione 9.4).
>
> Quanto a `strchr`, `strrchr`, `strstr` e `strpbrk`, nel capitolo 10 vedrai come il puntatore che restituiscono permette di estrarre estensioni o suddividere una stringa senza copiarla, e perché la novità C23 che preserva `const` impedisce di modificare per errore una stringa di sola lettura.

### Esercizio 9.2 — Filtro e ordine lessicografico di etichette con `<string.h>`

**Descrizione**

Scrivi un programma C che includa `<stdio.h>`, `<stdlib.h>` e `<string.h>` per analizzare un elenco di etichette. Leggi dalla prima riga di `stdin` la parola chiave `chiave` (buffer di `32` byte), rimuovi `'\n'` con `strcspn` e verifica che non sia vuota (`strlen(chiave) > 0`; altrimenti errore su `stderr` e `EXIT_FAILURE`). Leggi poi fino alla fine dell'input una sequenza di etichette (buffer di `48` byte), rimuovendo `'\n'` con `strcspn`. Ignora le righe vuote; un'etichetta è valida solo se tutti i suoi caratteri appartengono a `"abcdefghijklmnopqrstuvwxyz0123456789-_"` (verificato con `strspn(voce, ...) == strlen(voce)`): se non è valida incrementa `scartate` e passa alla successiva. Sulle etichette valide calcola: quante sono uguali a `chiave` (`strcmp == 0`), quante iniziano con `chiave` (`strncmp == 0`), quante contengono `chiave` (`strstr != nullptr`), quante contengono almeno un separatore `'-'` o `'_'` (`strpbrk != nullptr`), e mantieni la prima e l'ultima in ordine lessicografico (`strcmp` + `strcpy` in due buffer da `48` byte). Inoltre raccogli in un buffer `trovate[128] = ""` le etichette che contengono `chiave`, separate da `", "`, usando `strncat` solo quando c'è spazio sufficiente (controllando `strlen(trovate) + sep + strlen(voce) < sizeof(trovate)`). Se non ci sono etichette valide stampa `Nessuna etichetta valida.` e `Valide: 0, scartate: S`; altrimenti stampa il riepilogo esattamente come nell'esempio di esecuzione (usando `(nessuna)` se `trovate` è vuota).

**Concetti da tenere a mente**

- rimozione di `'\n'` con `strcspn` e validazione dell'alfabeto con `strspn`
- confronto esatto (`strcmp`) e per prefisso (`strncmp`)
- ricerca di sottostringhe (`strstr`) e di caratteri separatori (`strpbrk`)
- copia e concatenazione controllata con `strcpy` e `strncat`

**Domande guida**

1. In che modo il confronto `strspn(voce, caratteri_ammessi) == strlen(voce)` garantisce che l'intera etichetta contenga solo caratteri permessi?
2. Perché non puoi confrontare due etichette con `voce == chiave` ma devi usare `strcmp(voce, chiave) == 0`?
3. Quale controllo devi eseguire prima di chiamare `strncat` sul buffer `trovate` per evitare un buffer overflow e non aggiungere un separatore senza l'etichetta successiva?
4. Come gestisci l'inizializzazione di `prima_less` e `ultima_less` quando incontri la prima etichetta valida?

**Esempio di esecuzione**

```input
net
net-core
alpha
net_io
Bad!Tag
supernet

net
```

```output
Valide: 5, scartate: 1
Uguali a chiave: 1
Con prefisso chiave: 3
Contengono chiave: 4
Con separatore (- o _): 2
Prima lessicografica: alpha
Ultima lessicografica: supernet
Corrispondenze: net-core, net_io, supernet, net
```
