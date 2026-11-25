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
