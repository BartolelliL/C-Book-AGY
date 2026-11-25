## Riepilogo

- Un interprete completo separa la traduzione ed esecuzione in tre stadi distinti: l'**analizzatore lessicale** trasforma il codice sorgente in token tipizzati con coordinate `(riga, col)`; l'**analizzatore sintattico** a discesa ricorsiva costruisce l'**albero di sintassi astratta** rispettando precedenza e associatività; il **valutatore** esegue l'AST su una catena di **ambienti di esecuzione**.
- I valori a tempo di esecuzione (`valore_t`) e i nodi AST (`nodo_t`) sono modellati come **unioni etichettate** (`enum` + `union`), accedendo sempre a un campo solo dopo aver verificato l'etichetta. Tutti i nodi dell'AST e le copie degli identificatori vivono in un **allocatore ad arena** allineato ad `alignof(max_align_t)`, rilasciato in un colpo solo in `O(1)` anche quando il parser si arresta per un errore.
- Nell'analizzatore lessicale ogni carattere viene convertito a `unsigned char` prima di invocare `<ctype.h>`, i letterali interi usano `ckd_mul` e `ckd_add` contro gli overflow e gli operatori a due caratteri (`==`, `!=`, `<=`, `>=`, `&&`, `||`) vengono riconosciuti con uno sguardo in avanti di un carattere.
- Nell'analizzatore sintattico la stratificazione delle funzioni codifica i livelli di precedenza e i cicli `while` assicurano l'associatività a sinistra senza ricorsione sinistra; un contatore `MAX_PROF_PARSE` protegge lo stack da parentesi profondamente annidate.
- Il valutatore protegge il programma ospite C da qualsiasi comportamento indefinito usando `<stdckdint.h>`, intercettando `b == 0` e `INT64_MIN / -1` (e `% -1`), applicando il corto circuito su `&&`/`||` e imponendo guardie sui passi dei cicli (`MAX_PASSI`) e sulla profondità delle chiamate ricorsive (`MAX_PROF_CHIAMATE`).
- Gli ambienti delle variabili usano la **tabella hash generica come tipo opaco** (`void *`) con possesso completo di chiavi e valori; le funzioni predefinite sono registrate tramite **puntatori a funzione**; l'integrazione su più file coordina il rilascio deterministico con `goto cleanup` ed è verificata con test automatici e sanitizer.

## Errori comuni

- **Usare ricorsione sinistra o ricorsione destra nell'analizzatore sintattico**: chiamare subito `parse_somma` dentro `parse_somma` provoca ricorsione infinita e stack overflow; chiamare ricorsivamente `parse_somma` dopo `'-'` raggruppa `10 - 3 - 2` come `10 - (3 - 2) = 9` anziché `5`. Usa sempre un ciclo `while` per gli operatori binari associativi a sinistra.
- **Allocare i nodi dell'AST con `malloc` individuali senza un'arena**: quando il parser incontra un errore di sintassi a metà espressione è facilissimo dimenticare di liberare i sottoalberi parziali già costruiti. L'allocatore ad arena elimina il problema alla radice rilasciando tutto insieme.
- **Non proteggere l'interprete dai casi di comportamento indefinito provocati dal codice utente**: delegare direttamente `/`, `%`, `+` o `*` agli operatori C senza controllare divisore zero, `INT64_MIN / -1`, overflow con `<stdckdint.h>`, ricorsione infinita o cicli senza fine espone l'interprete a crash e risultati imprevedibili.
- **Dimenticare di distruggere l'ambiente locale di una chiamata di funzione su `return` anticipato o errore**: ogni chiamata `fn` alloca una nuova tabella hash; uscire prima della fine della funzione senza distruggerla genera perdite di memoria crescenti a ogni iterazione o chiamata ricorsiva.
- **Passare `char` con segno direttamente a `isspace`, `isalpha`, `isdigit` o `isalnum` nel lexer**: su sistemi in cui `char` è con segno, un byte con bit più significativo a `1` diventa un intero negativo diverso da `EOF` e provoca comportamento indefinito. Converti sempre a `(unsigned char)`.

## Prima di proseguire

- [ ] So progettare valori a tempo di esecuzione e nodi di un albero di sintassi astratta con unioni etichettate e gestirne la memoria con un allocatore ad arena.
- [ ] So scrivere un analizzatore lessicale senza allocazioni sullo heap con coordinate di riga/colonna, cast a `unsigned char` e parsing sicuro degli interi con `<stdckdint.h>`.
- [ ] So implementare un analizzatore sintattico a discesa ricorsiva che codifica precedenza e associatività a sinistra tramite cicli `while` e controlla la profondità massima di ricorsione.
- [ ] So costruire ambienti lessicali a catena sulla tabella hash generica opaca gestendo oscuramento, corto circuito e aritmetica priva di comportamento indefinito.
- [ ] So integrare controllo di flusso, funzioni ricorsive con `return`, funzioni predefinite via puntatori a funzione, `goto cleanup` e una suite di test automatici su più file verificata con AddressSanitizer e UndefinedBehaviorSanitizer.
