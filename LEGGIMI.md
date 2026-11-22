# Pipeline per scrivere il libro di C (solo Google Antigravity, con orchestratore)

Questo pacchetto ti permette di scrivere il libro **mandando pochi messaggi a Google Antigravity**. In ogni messaggio
l'**orchestratore** (Gemini 4 Neon, in alternativa Argon o Claude Opus 5.5) divide il lavoro tra **sub-agenti esecutori**
(Claude Sonnet 5.5 o Gemini 4 Hydrogen), uno per capitolo. Non devi decidere tu cosa fare dopo: uno script controlla
il lavoro e ti dice il prossimo messaggio da incollare.

## 1. Preparazione (una volta sola)

1. Serve **Python 3.8 o superiore** e un **compilatore C** (macOS: `xcode-select --install`; Linux: `gcc` o `clang`;
   Windows: WSL).
2. Nel terminale, nella cartella del progetto:
   ```
   git init
   python3 scripts/libro.py diagnosi
   ```
   `diagnosi` controlla Python, compilatore, supporto a C23 (e quali novita' C23 il tuo compilatore capisce) e i file.
   Deve finire con "TUTTO OK". Se il compilatore non conosce `-std=c23` usa `-std=c2x` da solo.
3. Apri la cartella come workspace in **Antigravity**. In Antigravity trova dove si scelgono il **modello Orchestrator**
   (planner) e il **modello Executor**: sono due impostazioni separate. Orchestratore consigliato: **Gemini 4 Neon**
   (vanno bene anche Argon o Claude Opus 5.5; Carbon escluso). Per l'executor ti dice lo script, passo per passo.
4. (Facoltativo) prima di partire modifica `PROGRAMMA.md` (capitoli), la tabella iniziale di `CONVENZIONI.md`
   (lettori, soluzioni, lingua) e `config.json` (limiti, dimensione dei lotti).

## 2. Il ciclo (sempre lo stesso)

```
python3 scripts/libro.py avanti
```

1. Il comando controlla cio' che e' stato prodotto e ti mostra: la tabella di avanzamento, **orchestratore ed esecutori da
   selezionare** e **il messaggio esatto da incollare**, con i capitoli del lotto (es. `CAPITOLI=3-5`).
2. In Antigravity apri una **sessione nuova**, imposta i modelli indicati, incolla il messaggio (solo quello).
3. Aspetta che l'orchestratore finisca. Poi torna al punto 1.

Se ci sono stati errori, `avanti` te lo dice e ripropone lo stesso passo: i sub-agenti riconoscono da soli il
rilancio (leggono i file di esito con gli errori) e correggono solo quelli.

## 3. I passi

| Passo | Cosa fa | Esecutori | Quante volte |
|---|---|---|---|
| P1 | Macro-scaletta (capitoli, obiettivi, registro degli elementi del linguaggio, glossario) + revisione indipendente | Sonnet 5.5 (scrive), Hydrogen (revisiona) | 1 |
| **Checkpoint 1** | **Tu** leggi macro-scaletta e `stato/revisione_p1.md`, poi `approva 1` | tu | 1 |
| P2 | Scheda tecnica dei capitoli con esercizi e soluzioni di riferimento (compilate e provate dallo script) | Sonnet 5.5 | 1 messaggio ogni 5 capitoli |
| P2B | Coerenza tra le schede (lavora su un riepilogo generato dallo script) | Hydrogen | 1 |
| P3 | Stesura dei capitoli (testo, codice, esercizi senza soluzioni) | Sonnet 5.5 | 1 messaggio ogni 3 capitoli |
| P4 | Audit indipendente (famiglia di modelli diversa da chi ha scritto) con revisione delle patch gravi da parte dell'orchestratore | Hydrogen | 1-2 giri per capitolo, 4 capitoli a messaggio |
| P5 | Correzioni mirate (solo se servono) | Sonnet 5.5 | se serve |
| **Checkpoint 2** | **Tu** leggi il **capitolo pilota** e approvi (`approva pilota`) | tu | 1 |
| P6 | Revisione di coerenza su tutto il libro (per digest) | Hydrogen | 1 |
| P7 | Commenti alle soluzioni per il docente e metadati | Hydrogen | 1 |
| **Checkpoint 3** | **Tu** leggi tutto, `approva finale`, poi `fine` crea il file finale | tu | 1 |

**Il capitolo pilota** (`capitolo_pilota` in `config.json`, ora il 10, sui puntatori) e' il primo capitolo scritto e
controllato fino in fondo, da solo, prima di tutti gli altri. Se ti convince, la sua prima sotto-sezione diventa l'esempio
di stile per tutto il libro; se no, correggi prompt o regole e rifai il capitolo.

L'ordine lo decide lo script: prima il pilota, poi tutte le stesure, poi tutti gli audit.
**Quanti messaggi?** Con 22 capitoli circa 30-40 in tutto (invece di 100+), perche' ogni messaggio copre piu' capitoli.
La dimensione dei lotti e' in `config.json` (`lotto_capitoli`): abbassala se esaurisci le quote, alzala se hai margine.

## 4. Perche' due famiglie di modelli

Chi scrive (P1, P2, P3, P5) e' **Claude Sonnet 5.5**; chi controlla (P2B, P4, P6) e' **Gemini 4 Hydrogen** sotto la guida di
Neon. Modelli di famiglie diverse tendono a non ripetere gli stessi errori: e' il motivo per cui lo script ti chiede di
cambiare executor tra un passo e l'altro. Se in Antigravity non riuscissi a cambiare l'executor tra una sessione e l'altra,
puoi usare Sonnet 5.5 per tutto: funziona, ma l'audit perde l'indipendenza tra modelli (restano i controlli dello script e i
tuoi checkpoint).

## 5. Cosa controlla lo script in automatico (e cosa no)

**Controllato da script (affidabile):** il codice di ogni esempio e di ogni soluzione (anche su piu' file) compila senza
warning (`-Wall -Wextra -Wpedantic -Werror`), viene eseguito (con sanitizer se disponibili) e l'output mostrato nel libro e'
identico a quello reale; nessun elemento del linguaggio o della libreria usato prima del capitolo in cui lo introduci; header e
funzioni non portabili vietati; termini del glossario e sinonimi vietati; struttura dei file; **nessuna soluzione negli
esercizi** (nemmeno un esempio guidato che la somigli); gli esempi di esecuzione coincidono con il blueprint.

**Non garantito da script:** la correttezza delle spiegazioni, la bonta' didattica, la qualita' dell'italiano. Qui lavorano
l'audit del secondo modello (P4, P6) e **tu** nei tre checkpoint. Leggi con attenzione soprattutto il capitolo pilota e i
capitoli su puntatori, memoria dinamica, puntatori a funzione, tabelle hash e il progetto finale.

## 6. Regole d'oro

- **Una sessione = un messaggio.** Apri una sessione nuova per ogni passo.
- **Non modificare i file mentre un orchestratore lavora.** I sub-agenti lavorano in parallelo su capitoli diversi.
- Incolla **solo** il messaggio che ti mostra `avanti`: tutte le istruzioni sono nei file in `prompts/` e in `CONVENZIONI.md`
  (paragrafo 8: orchestrazione).
- Non modificare `stato/macro_scaletta.json` dopo averla approvata (lo script se ne accorge). Se serve cambiarla,
  modifica e rilancia `approva 1`.
- Lo script fa un commit Git a ogni passo: puoi sempre tornare indietro.
- Solo tu lanci `avanti`, `approva`, `riapri`, `fine`: gli agenti possono lanciare soltanto `controlla-macro`,
  `controlla-bp N` e `controlla N`, che non toccano lo stato.

## 7. Se qualcosa va storto

| Situazione | Cosa fare |
|---|---|
| Quota esaurita o sessione interrotta | Aspetta, o riduci `lotto_capitoli`, poi **reincolla lo stesso messaggio**: i sub-agenti completano solo cio' che manca |
| L'orchestratore scrive lui i file, o legge tutto il libro | Interrompi e rilancia: ricordagli il paragrafo 8 di `CONVENZIONI.md` (non scrive file, non legge capitoli interi) |
| Un sub-agente dice di aver eseguito i controlli ma non e' vero | Nessun problema: `avanti` li rifa sempre lui |
| Un capitolo non ti convince | `python3 scripts/libro.py riapri N stesura` (oppure `blueprint`, `audit`) e poi `avanti` |
| Vuoi controllare a mano un capitolo | `python3 scripts/libro.py controlla N` |
| Vuoi vedere dove sei | `python3 scripts/libro.py stato` |
| Hai modificato un file a mano | `avanti` lo ricontrolla (i capitoli chiusi vengono ricontrollati alla fine) |
| Lo script segnala `P5 dichiara problemi non risolti` | Sono dubbi che spettano a te: apri il file `audit/..._p5.json` e decidi |

## 8. Cartelle

```
CONVENZIONI.md   regole condivise + orchestrazione (§8)        PROGRAMMA.md   capitoli proposti (input di P1)
prompts/         i prompt P1-P7                                 config.json    limiti, modelli, lotti
scripts/libro.py controlli e avanzamento                        stato/         macro-scaletta, blueprint, esiti dei controlli, digest
manoscritto/     il libro, un file per sotto-sezione            audit/         rapporti di audit e correzioni
docente/         commenti e soluzioni per il docente (NON nel libro)    apparati/  indice analitico e metadati
consegna/        libro_completo.md (file finale)
```

## 9. Comandi

Dell'utente: `avanti` · `stato` · `prossimo` · `diagnosi` · `approva 1 | pilota | finale` · `riapri N fase` · `unisci` ·
`soluzioni` · `indice` · `fine`. Anche degli agenti: `controlla-macro` · `controlla-bp N` · `controlla N`.
(Tutti con `python3 scripts/libro.py <comando>`.)

## 10. Nota sull'affidabilita' del pacchetto

Gli script sono stati provati con un libro finto di 10 capitoli (limiti ridotti nel test) e con agenti simulati, su Linux con
GCC 13 e Python 3.12: macchina a stati, lotti di capitoli, sandbox (anche a piu' file), controlli, patch, apparati e file finale
funzionano. **Non e' stato provato con Antigravity vero ne' su macOS.** In particolare non so con certezza: se Antigravity
lascia scegliere orchestratore ed executor per ogni sessione, quanti sub-agenti lancia davvero in parallelo, e quanta quota
consuma ogni lotto. I primi due giri veri (P1 e il capitolo pilota) servono anche a scoprirlo. Se qualcosa non torna, incolla
qui l'output di `python3 scripts/libro.py diagnosi` e di `avanti`.
