# Digest — Capitolo 7: Funzioni

## Termini definiti e glossario
- **Funzione** (*function*): blocco di codice dotato di nome, parametri e tipo di ritorno che svolge un compito definito e può essere richiamato ogni volta che serve.
- **Parametro** (*parameter*): variabile dichiarata nell'intestazione di una funzione che riceve il valore fornito alla chiamata.
- **Argomento** (*argument*): espressione passata tra parentesi nel punto in cui si chiama una funzione.
- **Prototipo** (*prototype*): dichiarazione di funzione che specifica nome, tipo di ritorno e tipi dei parametri senza il corpo, chiusa da `;`.
- **Passaggio per valore** (*pass by value*): meccanismo per cui una funzione riceve una copia del valore di ciascun argomento.
- **Visibilità** (*scope*): regione del codice sorgente in cui un identificatore può essere usato (di blocco o di file).
- **Durata di vita** (*storage duration*): intervallo di tempo durante l'esecuzione in cui la memoria di un oggetto esiste ed è valida (automatica o statica).
- **Ricorsione** (*recursion*): tecnica in cui una funzione richiama se stessa su un sottoproblema più piccolo fino a un **caso base** (*base case*) tramite un **passo ricorsivo** (*recursive step*).
- Altri termini del glossario usati: *occultamento* (*shadowing*), pila delle chiamate, progettazione dall'alto verso il basso (*top-down*), comportamento indefinito, comportamento non specificato, conversione implicita.

## Concetti spiegati
- Definizione di funzione: tipo di ritorno (anche `void`), nome, lista parametri (obbligatorio `(void)` per nessun parametro per compatibilità C17/C11, anche se in C23 `f()` equivale a `f(void)`), corpo; `return` anticipato e rischio di comportamento indefinito se manca `return` in funzione non `void`.
- Separazione dichiarazione/definizione tramite prototipi prima di `main`; conversioni implicite sugli argomenti.
- Passaggio per valore: modificare un parametro altera solo la copia locale; ordine di valutazione degli argomenti non specificato (evitare effetti collaterali incrociati come `somma(n, ++n)`).
- Valore assoluto intero in `<stdlib.h>`: `abs`, `labs`, `llabs` (e comportamento indefinito su `INT_MIN`, `LONG_MIN`, `LLONG_MIN`).
- Visibilità (di blocco vs di file) e occultamento (*shadowing*); durata di vita automatica (non azzerata) vs `static` locale (visibilità di blocco, durata statica, inizializzata una sola volta con espressione costante o a `0`, stato interno nascosto).
- Ricorsione: caso base, passo ricorsivo convergente, indipendenza dei frame sulla pila delle chiamate, ricorsione infinita (stack overflow -> comportamento indefinito), ricorsione esponenziale (Fibonacci ingenuo vs iterazione).
- Progettazione *top-down*: contratto (scopo, precondizioni, garanzie), separazione tra validazione input, funzioni di calcolo pure (no I/O, no stato nascosto) e presentazione output, composizione.

## Esempi e scenari
- **7.1**: rilevazioni velocità stradale (`kmh_a_ms`, `supera_limite`, `stampa_separatore`).
- **7.2**: confronti quote/altitudini e raddoppio (`tenta_raddoppio`, `raddoppia`, `abs`, `labs`).
- **7.3**: sportello ticket (`genera_ticket` con `static int prossimo`, `contatore_automatico`, blocco annidato).
- **7.4**: `fattoriale` (`long long`) e `mcd_ricorsivo` (Euclide).
- **7.5**: preventivo ordine di cancelleria (`calcola_subtotale`, `calcola_sconto`, `calcola_iva`, `stampa_riepilogo`).

## Esercizi
- **7.1 — Scheda di un lotto di terreno rettangolare**: definire `stampa_intestazione`, `calcola_area`, `calcola_perimetro`, `e_quadrato` (con `fabs` e tolleranza `1e-9`). Difficoltà: 2/5.
- **7.2 — Percorso di un rover con prototipi, passaggio per valore e `abs`/`labs`/`llabs`**: 4 funzioni con prototipi prima di `main` su coordinate `long` ed energia `long long`. Difficoltà: 3/5.
- **7.3 — Registratore di consumi elettrici con variabili `static` locali**: 3 funzioni con stato `static` locale (`aggiorna_totale_wh`, `aggiorna_picco_wh`, `conta_oltre_soglia`). Difficoltà: 3/5.
- **7.4 — Potenza veloce, somma delle cifre e stampa binaria con ricorsione**: 3 funzioni ricorsive pure senza cicli (`potenza_veloce`, `somma_cifre_ric`, `stampa_binario_ric` in risalita). Difficoltà: 4/5.
- **7.5 — Validatore di calendario e distanza tra due date**: 5 funzioni pure composte (`e_bisestile`, `giorni_del_mese`, `data_valida`, `giorno_dell_anno`, `giorni_dal_1900`) + `labs`. Difficoltà: 3/5.

## Rinvii
- Richiami ai capitoli precedenti: cap. 2–6 in apertura; cap. 6 (visibilità nei cicli, algoritmo di Euclide e Fibonacci iterativo).
- Rinvii in avanti: cap. 10 (puntatori per restituire più valori o modificare variabili del chiamante / più stati indipendenti); cap. 11 (pila delle chiamate); cap. 12 (`struct`); cap. 13 (rappresentazione binaria interi con segno e `INT_MIN`); cap. 17 (alberi / *divide et impera*); cap. 19 (`static` a livello di file).

## Affermazioni forti
- Scrivere sempre esplicitamente `(void)` per funzioni senza parametri.
- In C il passaggio è sempre per valore, senza eccezioni.
- Mai scrivere variabili globali mutabili (evitare il più possibile); ok `constexpr` a livello di file.
- Evitare l'occultamento (*shadowing*) usando nomi distinti.
- Non passare mai `INT_MIN`/`LONG_MIN`/`LLONG_MIN` a `abs`/`labs`/`llabs` senza controllo.
- Tenere le funzioni di calcolo pure prive di `fgets`/`printf`.

## Stile del codice
- Standard C23 (`bool`, `constexpr`, separatori di cifre nei testi esercizi); `07_01`, `07_02`, `07_03`, `07_04`, `07_05` usano `return 0;` in `main` (quando non leggono input) mentre gli esercizi con input usano `EXIT_SUCCESS`/`EXIT_FAILURE` e `stderr`.
- Nomi di funzione e parametri in `snake_case` italiano senza accenti (`kmh_a_ms`, `e_quadrato`), prototipi con nomi dei parametri sempre inclusi.
