# Revisione della macro-scaletta (P1R)

## Problemi da correggere prima di approvare

1. **Capitolo 14 (14.3) — Prerequisito `<math.h>` per `HUGE_VAL`**: l'anticipo di `errno.h`, `errno`, `ERANGE` e `HUGE_VAL` al capitolo 14 risolve il controllo dell'overflow in `strtol` e `strtod`, ma `HUGE_VAL` è dichiarata in `<math.h>` (introdotta nel capitolo 3), che non compare tra i `prerequisiti` del capitolo 14 (`[9, 10, 11, 12]`). *Proposta*: aggiungere `3` ai prerequisiti del capitolo 14 (o specificare negli argomenti di 14.3 l'inclusione di `<math.h>` per `HUGE_VAL`).
2. **Capitolo 19 (19.5) — Prerequisiti espliciti per la tabella hash opaca**: la sotto-sezione 19.5 riorganizza su più file la tabella hash generica del capitolo 18, che usa allocazione dinamica e `void *`, ma `prerequisiti` elenca solo `[7, 12, 16, 18]`. *Proposta*: aggiungere `11` e `15` ai prerequisiti del capitolo 19 per uniformità con i capitoli 20–26.
3. **Capitolo 21 (21.5) — Titolo della sotto-sezione e attributi C23**: gli attributi standard `[[nodiscard]]`, `[[maybe_unused]]` e `[[noreturn]]` sono stati inseriti negli argomenti di 21.5, il cui titolo è però `"Preprocessore: macro con argomenti, __FILE__ e __LINE__"`. Poiché gli attributi C23 sono costrutti sintattici del compilatore e non direttive del preprocessore, associarli al preprocessore nel titolo può confondere il lettore. *Proposta*: rinominare 21.5 in `"Preprocessore e attributi C23: macro con argomenti, __FILE__ e __LINE__"`.

## Aggiunte suggerite

- **Direttive `#error`, `#elifdef` e `#elifndef` (C23)**: ora che attributi C23, `<stdckdint.h>`, `strdup`/`strndup` e `campo array flessibile` sono stati integrati, l'unica aggiunta avanzata utile nel preprocessore riguarda `#error` e le nuove direttive C23 `#elifdef`/`#elifndef` per la compilazione condizionale. Inserirle nel registro e nella sotto-sezione 19.2 (o 21.5).

## Dubbi da decidere tu

- **Capitolo 26 (26.5)**: la sotto-sezione 26.5 prevede in un unico passo sia `if`/`while` sia le funzioni definite dall'utente (che richiedono stack di attivazione e ambienti locali annidati). Confermi di voler mantenere le funzioni definite dall'utente nel nucleo obbligatorio di 26.5, oppure preferisci limitare 26.5 a `if`, `while` e funzioni predefinite?
- **Autonomia dei blocchi multi-file nel Capitolo 26**: poiché il controllo automatico compila insieme i soli file appartenenti allo stesso `gruppo=` dentro il capitolo, in 26.4–26.6 preferisci riportare per intero i file `.h`/`.c` della tabella hash (cap. 19) e dell'arena (cap. 22) oppure usarne una versione compatta ridotta alle sole funzioni necessarie all'interprete?

## Giudizio complessivo

Le criticità della versione precedente (`errno`/`ERANGE` al capitolo 14, prerequisiti dei capitoli 20/23/26, calibratura degli esempi nel capitolo 23, allineamento degli allocatori nel capitolo 22, aggiunte C23 e glossario) sono state risolte.
La progressione didattica verso la tabella hash generica come tipo opaco e verso l'interprete finale è ora completa, coerente e priva di salti propedeutici.
I tre punti residui qui sopra sono rifiniture minori: la macro-scaletta è pronta per l'approvazione.
