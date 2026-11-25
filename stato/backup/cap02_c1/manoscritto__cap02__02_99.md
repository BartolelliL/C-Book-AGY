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
