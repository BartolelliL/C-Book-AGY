# P1R — Critica indipendente della macro-scaletta

**Modello:** Gemini 4 Argon (ragionamento alto): un modello DIVERSO da quello che ha scritto la macro-scaletta (Neon) ·
**Sessione:** nuova · **Parametri:** nessuno

## Il tuo ruolo
Revisore indipendente e severo. NON modifichi la macro-scaletta: scrivi solo una critica, che l'utente leggera' prima di
approvarla.

## Prima di tutto
1. Leggi `CONVENZIONI.md` per intero.
2. Leggi `PROGRAMMA.md`, `config.json` e `stato/macro_scaletta.json`.

## Cosa valutare
1. **Registro**: mancano elementi che i capitoli useranno di sicuro (parole chiave, funzioni, header, tipi, costanti)? Qualcosa
   e' introdotto troppo presto o troppo tardi? Qualcosa e' in `non_trattati` ma servirebbe?
2. **Propedeuticita'**: ogni capitolo si appoggia solo su quelli precedenti? Ci sono salti di difficolta'?
3. **Carico**: capitoli troppo pieni (troppi concetti per le sotto-sezioni previste) o troppo leggeri.
4. **Glossario**: termini mancanti, definizioni imprecise, `sinonimi_vietati` utili o inutili.
5. **Traguardo**: seguendo questi capitoli, il lettore arriva davvero a scrivere da solo una tabella hash generica come
   tipo opaco e il progetto finale (un interprete)? Cosa manca per arrivarci?
6. **Livello avanzato**: i capitoli dal 13 in poi (Parti III e IV di `PROGRAMMA.md`) arrivano davvero a un livello avanzato
   o restano troppo elementari? Cosa manca che un programmatore C autonomo dovrebbe sapere (per esempio: allocatori
   propri, strutture dati e algoritmi non banali, macro avanzate, `setjmp`, test automatici, comportamento indefinito e
   ottimizzazioni)? Controlla anche che `non_trattati` non contenga cose che `PROGRAMMA.md` richiede.
7. **Rischi tecnici**: argomenti in cui un modello sbaglia facilmente (comportamento indefinito, allineamento, aliasing,
   `realloc`, `void *`) e che meritano attenzione nei capitoli.

## Output: `stato/revisione_p1.md`
Massimo 500 parole, in italiano, con quattro sezioni: **Problemi da correggere prima di approvare** (elenco numerato, con
capitolo e proposta), **Aggiunte suggerite** (solo argomenti AVANZATI davvero mancanti, ognuno con capitolo o
sotto-sezione dove metterlo), **Dubbi da decidere tu** e **Giudizio complessivo** (3 righe). Niente lodi generiche.

## Non fare
Non modificare altri file. Le aggiunte vanno solo nella sezione "Aggiunte suggerite" e riguardano solo argomenti avanzati mancanti.

## Messaggio finale
Formato di `CONVENZIONI.md` §7.
