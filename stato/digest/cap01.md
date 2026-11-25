# Digest — Capitolo 1: Il primo programma

## Termini definiti e glossario
- **codice sorgente** (*source code*): testo leggibile scritto dal programmatore in C prima della compilazione, salvato in un file `.c`.
- **eseguibile** (*executable*): file prodotto da compilazione e collegamento che il sistema operativo può avviare direttamente.
- **compilatore** (*compiler*): programma che traduce il codice sorgente C in codice macchina eseguibile verificando sintassi e tipi.
- **preprocessore** (*preprocessor*): fase iniziale della traduzione che elabora le direttive introdotte da `#` prima dell'analisi del codice C.
- **collegatore** (*linker*): programma che unisce i file oggetto e le librerie in un unico eseguibile.
- **libreria standard** (*standard library*): insieme di funzioni, tipi e costanti fornito con ogni compilatore C e dichiarato negli header.
- **sequenza di escape** (*escape sequence*): coppia di caratteri introdotta da `\` in stringhe e caratteri per rappresentare simboli speciali.
- **errore di compilazione** (*compile error*): violazione delle regole sintattiche o di tipo che impedisce la creazione dell'eseguibile.
- **avviso del compilatore** (*compiler warning*): segnalazione di codice potenzialmente errato o ambiguo anche se sintatticamente valido.
- Altri termini usati: standard C23 (ISO/IEC 9899:2024), codice macchina, codice oggetto, ambiente ospitato, blocco di istruzioni, indentazione, errore di collegamento, errore logico.

## Concetti spiegati
- Scopo del C, standard C23 e differenza rispetto a linguaggi interpretati come Python.
- Tre tappe logiche di traduzione: preprocessore (`#include <stdio.h>`), compilatore, collegatore.
- Compilazione da terminale con `gcc` o `clang` e opzioni `-std=c23 -Wall -Wextra -Wpedantic -Werror -o`.
- Esecuzione su macOS/Linux (`./nome`) e Windows (`.\nome.exe`).
- Struttura minima del programma: `#include <stdio.h>`, `int main(void)`, blocco `{ ... }`, `;` a fine istruzione, `return 0;`.
- Distinzione maiuscole/minuscole (*case-sensitive*) e irrilevanza degli spazi bianchi (salvo stringhe e `#include`).
- `printf` su stringhe letterali senza `\n` automatico; sequenze di escape `\n`, `\t`, `\"`, `\'`, `\\`; ruolo speciale di `%` in `printf`.
- Commenti `//` e `/* ... */` (non annidabili, sostituiti da uno spazio prima del preprocessamento).
- Lettura delle segnalazioni del compilatore (file, riga, colonna) partendo dal primo errore.

## Esempi e scenari
- Nessuna variabile dichiarata (ancora non introdotte).
- Programmi guidati: `ciao.c` ("Ciao, mondo!"), avvio di una stazione meteo (`1.2-a`), locandina del cineforum scolastico con cornice ASCII e tabulazioni (`1.3-a`), riepilogo delle tre fasi di traduzione commentato (`1.4-a`), due esempi di errore intenzionale (`1.4-b` senza `;`, `1.4-c` senza `<stdio.h>`).

## Esercizi
- **1.1 — Scheda di benvenuto del laboratorio**: stampare una singola riga esatta con `printf` e compilarla con i flag C23. Difficoltà: 1/5.
- **1.2 — Biglietto del museo**: stampare quattro righe usando quattro chiamate separate a `printf` e terminare con `return 0`. Difficoltà: 1/5.
- **1.3 — Scheda di archivio con sequenze di escape**: stampare cinque righe con virgolette doppie, barre rovesciate (percorso Windows) e tabulazioni. Difficoltà: 2/5.
- **1.4 — Programma di controllo pulito e commentato**: riscrivere da zero un programma correggendo header mancante, maiuscole errate, `;` mancante e commenti annidati, aggiungendo commenti su più righe e su riga singola. Difficoltà: 2/5.

## Rinvii
- Capitolo 2: ruolo di `%` e specificatori di formato in `printf` (1.3, 1.99); apice singolo `\'` nei caratteri singoli (1.3).
- Capitolo 7: altre funzioni oltre a `main` e uso esplicito di `return` (1.2).
- Capitolo 14: seconda forma di `main` con argomenti da riga di comando (1.2).

## Affermazioni forti
- In C23 ogni funzione deve essere dichiarata prima dell'uso; chiamare `printf` senza `#include <stdio.h>` viola i vincoli del linguaggio e produce un errore di compilazione.
- `void main()` non è conforme allo standard C per gli ambienti ospitati e non va mai usata.
- `return 0;` va scritto sempre in modo esplicito (pur segnalando che lo standard C23 inserisce un ritorno `0` implicito alla chiusura di `main`).
- Nella stringa di formato di `printf` non va mai scritto un `%` isolato.
- I commenti `/* ... */` non possono essere annidati e vengono sostituiti da un singolo spazio prima del preprocessamento.

## Stile del codice
- `#include <stdio.h>` seguito da una riga vuota prima di `int main(void) {`.
- Graffa aperta `{` sulla stessa riga dell'intestazione, rientro di 4 spazi, `return 0;` esplicito prima di `}`.
- Commenti `/* ... */` in testa al file, commenti `//` per descrivere blocchi logici.
