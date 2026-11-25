# Digest — Capitolo 3: Operatori ed espressioni

## Termini definiti e glossario
- **espressione** (*expression*): combinazione di operandi e operatori valutata per produrre un valore o un effetto collaterale.
- **divisione intera**: divisione tra due operandi interi tramite `/` che tronca la parte frazionaria verso lo zero.
- **virgola mobile** (*floating point*): rappresentazione binaria approssimata dei numeri reali tramite mantissa ed esponente (`float`, `double`).
- **modulo** (`%`): operatore che restituisce il resto della divisione intera (solo operandi interi).
- **assegnamento composto**: operatore (`+=`, `-=`, `*=`, `/=`, `%=`) che combina un'operazione aritmetica e l'assegnamento.
- **precedenza degli operatori** (*operator precedence*): regola che stabilisce il raggruppamento degli operatori in assenza di parentesi.
- **associatività**: regola che stabilisce il raggruppamento tra operatori di pari precedenza.
- **conversione implicita** (*implicit conversion*): trasformazione automatica di un valore da un tipo a un altro (promozioni intere e conversioni aritmetiche usuali).
- **cast esplicito** (*explicit cast*): operatore `(tipo)` posto davanti a un'espressione per forzare la conversione.
- **overflow**: superamento dell'intervallo rappresentabile da un tipo numerico.
- **comportamento indefinito / dipendente dall'implementazione / non specificato**: le tre categorie dello standard C23 definite formalmente in 3.6.

## Concetti spiegati
- Operatori aritmetici binari (`+`, `-`, `*`, `/`, `%`) e unari (`+`, `-`); identità `(a / b) * b + (a % b) == a` e segno del resto uguale a quello del dividendo `a`.
- Divisione intera per zero e `INT_MIN / -1` come comportamento indefinito.
- Assegnamenti composti (parentesi implicite su `expr`), incremento/decremento prefisso (`++x`) e postfisso (`x++`).
- Precedenza, associatività e distinzione dall'ordine di valutazione (modifiche non sequenziate vietate: `i = i++ + 1`).
- Operatori relazionali (`<`, `<=`, `>`, `>=`), uguaglianza (`==`, `!=`) e logici (`&&`, `||`, `!`) con risultato `int` (`0` o `1`); leggi di De Morgan; divieto di concatenare confronti (`10 <= x <= 20`).
- Promozioni intere (`char`, `short`, `bool` -> `int`), conversioni aritmetiche usuali, troncamento verso zero da `double` a `int`, rischi di espressioni miste `signed`/`unsigned`, cast tardivo `(double)(a / b)`.
- `<math.h>` con `-lm` alla fine del comando: `fabs`, `sqrt`, `pow`, `floor`, `ceil`, `round`, `fmod`; errori di dominio.
- Overflow `signed` (comportamento indefinito) vs aritmetica modulare `unsigned` (definita modulo $2^N$); `<float.h>` (`FLT_*`, `DBL_*`), `%e`, confronto con tolleranza `fabs(a - b) <= tol`.

## Esempi e scenari
- Variabili ricorrenti: `SECONDI_TOTALI`, `saldo`, `eta`, `altezza_cm`, `somma`, `voto_1..3`, `dx`, `dy`, `righe`, `colonne`, `TOLLERANZA`.
- Programmi guidati: conversione secondi (`3.1-a`), salvadanaio e incremento (`3.2-a`), accesso a una giostra (`3.3-a`), media voti e `sizeof(a + b)` (`3.4-a`), distanza cartesiana e arrotondamenti (`3.5-a`), griglia anti-overflow e `<float.h>` (`3.6-a`).

## Esercizi
- **3.1 — Confezionamento di libri in scatole e bancali**: usare `/`, `%`, `*` e divisione `double` per scatole, bancali e peso medio. Difficoltà: 2/5.
- **3.2 — Punteggio di una gara ciclistica a tappe**: assegnamenti composti, `++` prefisso/postfisso separati e precedenza con/senza parentesi. Difficoltà: 2/5.
- **3.3 — Verifica di sicurezza prima del volo di un drone**: espressioni booleane con intervalli e operatori logici senza `if`. Difficoltà: 2/5.
- **3.4 — Percentuali e seggi di un sondaggio scolastico**: confronto tra divisione intera, cast tardivo, cast corretto, troncamento `(int)` e promozione `short`. Difficoltà: 3/5.
- **3.5 — Preventivo per la pavimentazione di una terrazza**: `<math.h>` (`sqrt`, `ceil`, `floor`, `fmod`, `round`, `fabs`, `pow`) con `-lm`. Difficoltà: 3/5.
- **3.6 — Prevenzione dell'overflow e controllo di tolleranza in virgola mobile**: controllo preventivo `INT_MAX`, somma in `long long`, `unsigned` modulare e `<float.h>`. Difficoltà: 4/5.

## Rinvii
- Capitolo 4: controlli condizionali contro divisione per zero (3.1), valutazione a corto circuito di `&&` e `||` (3.3), decisioni (3.0, 3.99).
- Capitolo 13: operatore `^` sui bit (3.5).

## Affermazioni forti
- Divisione e modulo per zero su interi e `INT_MIN / -1` provocano comportamento indefinito.
- Modificare e leggere la stessa variabile senza ordinamento nella stessa espressione è comportamento indefinito.
- L'overflow sugli interi con segno provoca comportamento indefinito; i controlli dopo l'overflow (`s < a`) sono errati perché il compilatore può eliminarli.
- Non confrontare mai due `double` con `==`: usare `fabs(a - b) <= tolleranza`.
- `-lm` va sempre messo alla fine del comando di compilazione.

## Stile del codice
- Header in ordine alfabetico (`<float.h>`, `<limits.h>`, `<math.h>`, `<stddef.h>`, `<stdio.h>`).
- Cast espliciti senza spazio tra tipo e operando (`(double)somma`).
- Costanti `constexpr` in `MAIUSCOLO` per tolleranze e fattori di conversione; variabili `bool` per condizioni intermedie.
