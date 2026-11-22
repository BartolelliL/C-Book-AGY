#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
libro.py - strumenti di controllo per la pipeline del libro di C.

Solo libreria standard, Python 3.8 o superiore.

Comando principale (quello che userai quasi sempre):
    python3 scripts/libro.py avanti

Altri comandi: diagnosi, prossimo, stato, approva, riapri, controlla, unisci,
soluzioni, indice, fine. Vedi LEGGIMI.md.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from subprocess import PIPE

RADICE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def p(*parti):
    return os.path.join(RADICE, *parti)


def rel(path):
    return os.path.relpath(path, RADICE)


def nn(n):
    return "%02d" % int(n)


# ----------------------------------------------------------------------------
# Input/output di base
# ----------------------------------------------------------------------------

def leggi(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def scrivi(path, testo):
    cartella = os.path.dirname(path)
    if cartella:
        os.makedirs(cartella, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(testo)


def leggi_json(path):
    """Ritorna (dato, errore). errore e' None se tutto ok."""
    if not os.path.exists(path):
        return None, "file mancante: " + rel(path)
    try:
        return json.loads(leggi(path)), None
    except ValueError as e:
        return None, "JSON non valido in %s: %s" % (rel(path), e)


def scrivi_json(path, dato):
    scrivi(path, json.dumps(dato, ensure_ascii=False, indent=2) + "\n")


def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


_CFG = None


def cfg():
    global _CFG
    if _CFG is None:
        d, e = leggi_json(p("config.json"))
        if e:
            sys.exit("ERRORE: " + e)
        _CFG = d
    return _CFG


# ----------------------------------------------------------------------------
# Stato della pipeline
# ----------------------------------------------------------------------------

STATO_PATH = p("stato", "stato.json")


def stato_vuoto():
    return {
        "p1": {"verificato": False, "approvato": False, "hash": None, "modificato": False},
        "n_capitoli": None,
        "capitoli": {},
        "p2b": {"verificato": False},
        "pilota": {"approvato": False},
        "p6": {"unito": False, "audit": False, "applicato": False, "p5_capitoli": [], "chiuso": False},
        "p7": {"verificato": False},
        "finale": {"approvato": False},
        "fine": False,
    }


def carica_stato():
    if os.path.exists(STATO_PATH):
        d, e = leggi_json(STATO_PATH)
        if e:
            sys.exit("ERRORE: " + e)
        base = stato_vuoto()
        base.update(d)
        return base
    return stato_vuoto()


def salva_stato(st):
    scrivi_json(STATO_PATH, st)


def git_commit(messaggio):
    if not cfg().get("git_autocommit", True):
        return
    if not os.path.isdir(p(".git")):
        return
    try:
        subprocess.run(["git", "add", "-A"], cwd=RADICE, stdout=PIPE, stderr=PIPE)
        subprocess.run(["git", "commit", "-q", "-m", messaggio], cwd=RADICE, stdout=PIPE, stderr=PIPE)
    except Exception:
        pass


# ----------------------------------------------------------------------------
# Conoscenze sul linguaggio C (usate dai controlli di progressione)
# ----------------------------------------------------------------------------

KEYWORDS = set("""auto break case char const constexpr continue default do double else enum extern
float for goto if inline int long nullptr register restrict return short signed sizeof static
static_assert struct switch typedef typeof union unsigned void volatile while bool true false
alignas alignof _Generic typeof_unqual""".split())

FUNZIONI = set("""printf fprintf sprintf snprintf scanf sscanf fscanf puts putchar getchar fgets fputs
fputc fgetc getc putc ungetc fopen fclose fread fwrite fseek ftell rewind fflush feof ferror perror
remove rename tmpfile setvbuf malloc calloc realloc free exit abort atexit atoi atol atof strtol
strtoul strtod strtoll abs labs llabs div rand srand qsort bsearch getenv system strlen strcpy
strncpy strcat strncat strcmp strncmp strchr strrchr strstr strtok memcpy memmove memset memcmp
strdup strerror isalpha isdigit isalnum isspace isupper islower ispunct isprint toupper tolower
sqrt pow sin cos tan floor ceil fabs round trunc log log10 exp fmod time clock difftime localtime
strftime mktime assert memchr strspn strcspn strpbrk strtoull strtoimax raise signal va_start va_arg va_end va_copy offsetof vsnprintf vfprintf vprintf fgetpos fsetpos clearerr freopen setjmp longjmp strcoll fmax fmin hypot cbrt isnan isinf""".split())

TIPI = set("""size_t ptrdiff_t FILE int8_t int16_t int32_t int64_t uint8_t uint16_t uint32_t uint64_t
intptr_t uintptr_t intmax_t uintmax_t time_t clock_t va_list jmp_buf max_align_t sig_atomic_t fpos_t ldiv_t""".split())

COSTANTI = set("""NULL EOF EXIT_SUCCESS EXIT_FAILURE RAND_MAX INT_MAX INT_MIN UINT_MAX LONG_MAX LONG_MIN
ULONG_MAX LLONG_MAX LLONG_MIN CHAR_BIT CHAR_MAX SHRT_MAX SHRT_MIN DBL_MAX DBL_MIN DBL_EPSILON
FLT_MAX FLT_MIN FLT_EPSILON SIZE_MAX BUFSIZ stdin stdout stderr SEEK_SET SEEK_CUR SEEK_END
CLOCKS_PER_SEC INT8_MAX INT16_MAX INT32_MAX INT64_MAX UINT8_MAX UINT16_MAX UINT32_MAX UINT64_MAX
FILENAME_MAX errno EINVAL ENOMEM ERANGE ENOENT EDOM __FILE__ __LINE__ __func__ __VA_ARGS__ SIGINT SIGSEGV INTPTR_MAX PTRDIFF_MAX""".split())

HEADER_OK = set("""stdio.h stdlib.h string.h math.h ctype.h limits.h float.h stdint.h stdbool.h time.h
assert.h stddef.h errno.h inttypes.h stdckdint.h stdarg.h locale.h signal.h setjmp.h iso646.h""".split())

CATEGORIE_REGISTRO = ["parola chiave", "header", "funzione", "tipo", "costante", "sintassi", "concetto"]

PATTERN_VIETATI = [
    (r"\bgets\s*\(", "gets() e' stata rimossa dallo standard (C11): usa fgets()"),
    (r"\bvoid\s+main\s*\(", "main deve restituire int"),
    (r"fflush\s*\(\s*stdin\s*\)", "fflush(stdin) ha comportamento indefinito"),
    (r"\b(getch|getche|clrscr|kbhit)\s*\(", "funzione non standard, non portabile"),
    (r"\b(itoa|strlcpy|strlcat|sleep|usleep|strcasecmp|stricmp)\s*\(", "funzione non standard: non disponibile su tutti i sistemi"),
    (r"\bM_PI\b|\bM_E\b", "M_PI/M_E non sono standard C: definisci una costante"),
    (r'\bscanf\s*\(\s*"[^"]*%s', "scanf con %s senza larghezza e' insicuro: usa fgets()"),
]

# apostrofo usato al posto dell'accento (perche', e', piu', citta'): vietato nella prosa del libro
RE_APOSTROFO_ACCENTO = re.compile(r"(?<![A-Za-z0-9_'\\])(?:e'|[A-Za-z]{2,}[aeiou]')(?=\s|[.,;:!?)\]]|$)")

VIETATI_ESECUZIONE = [
    r"\bsystem\s*\(", r"\bpopen\s*\(", r"\bexec[lv]p?e?\s*\(", r"\bfork\s*\(", r"\bsocket\s*\(",
    r"\bunlink\s*\(", r"\brmdir\s*\(", r"\bchmod\s*\(", r"\bchown\s*\(", r"\bkill\s*\(",
]


def pulisci_c(codice):
    """Toglie commenti e contenuto di stringhe/caratteri (lascia '""' e "' '")."""
    out = []
    i = 0
    n = len(codice)
    while i < n:
        c = codice[i]
        if codice.startswith("//", i):
            j = codice.find("\n", i)
            i = n if j < 0 else j
        elif codice.startswith("/*", i):
            j = codice.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
        elif c == '"':
            j = i + 1
            while j < n and codice[j] != '"':
                j += 2 if codice[j] == "\\" else 1
            out.append('""')
            i = j + 1
        elif c == "'":
            j = i + 1
            while j < n and codice[j] != "'":
                j += 2 if codice[j] == "\\" else 1
            out.append("' '")
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def pericoloso(codice):
    """Ritorna una motivazione se il codice non va eseguito, altrimenti None."""
    pulito = pulisci_c(codice)
    for pat in VIETATI_ESECUZIONE:
        if re.search(pat, pulito):
            return "usa una funzione vietata nella sandbox (%s)" % pat
    for m in re.finditer(r'\b(fopen|remove|rename|freopen)\s*\(\s*"([^"]*)"', codice):
        percorso = m.group(2)
        if percorso.startswith("/") or percorso.startswith("~") or ".." in percorso:
            return "percorso file non consentito: %s" % percorso
    return None


def analizza_progressione(codice, n, reg, non_trattati):
    """Controlla che il codice usi solo elementi gia' introdotti fino al capitolo n."""
    problemi = []

    def controlla_nome(nome, cat):
        if nome in reg:
            if reg[nome] > n:
                problemi.append(("errore", "%s '%s' e' introdotta/o solo nel capitolo %d" % (cat, nome, reg[nome])))
        elif nome in non_trattati:
            problemi.append(("errore", "%s '%s' e' tra gli elementi NON trattati nel libro" % (cat, nome)))
        else:
            problemi.append(("avviso", "%s '%s' non e' presente nel registro" % (cat, nome)))

    for h in re.findall(r"#\s*include\s*<([^>]+)>", codice):
        if h not in HEADER_OK:
            problemi.append(("errore", "header <%s> non standard o non portabile" % h))
        else:
            controlla_nome(h, "header")

    pulito = pulisci_c(codice)
    definiti = set(re.findall(
        r"\b[A-Za-z_]\w*\s+\**\s*([A-Za-z_]\w*)\s*\([^;{)]*\)\s*\{", pulito))
    visti = set()
    for m in re.finditer(r"[A-Za-z_]\w*", pulito):
        t = m.group(0)
        pre = pulito[max(0, m.start() - 2):m.start()]
        if pre.endswith(".") or pre.endswith("->"):
            continue
        if t in KEYWORDS:
            cat = "parola chiave"
        elif t in TIPI:
            cat = "tipo"
        elif t in COSTANTI:
            cat = "costante"
        elif t in FUNZIONI:
            if t in definiti:
                continue
            if not pulito[m.end():].lstrip().startswith("("):
                continue
            cat = "funzione"
        else:
            continue
        if t in visti:
            continue
        visti.add(t)
        controlla_nome(t, cat)
    return problemi


# ----------------------------------------------------------------------------
# Compilatore e sandbox
# ----------------------------------------------------------------------------

_TC = None

PROVA_C23 = "int main(void) { bool b = true; return !b; }\n"
PROVA_SAN = ("#include <stdio.h>\n#include <stdlib.h>\n"
             "int main(void) { int *a = malloc(4 * sizeof *a); if (!a) return 1; a[0] = 7; "
             "printf(\"%d\\n\", a[0]); free(a); return 0; }\n")


def _limiti():
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
        resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
    except Exception:
        pass


def _run(cmd, **kw):
    return subprocess.run(cmd, stdout=PIPE, stderr=PIPE, encoding="utf-8", errors="replace", **kw)


def prova_compilazione(exe, flags, codice, eseguire=False):
    """Compila (ed eventualmente esegue) un programma di prova. Ritorna (ok, log)."""
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "t.c")
        out = os.path.join(d, "t")
        scrivi(src, codice)
        try:
            r = _run([exe] + flags + ["-o", out, src, "-lm"], cwd=d, timeout=60)
        except Exception as e:
            return False, str(e)
        if r.returncode != 0:
            return False, r.stderr
        if eseguire:
            try:
                r2 = _run([out], cwd=d, timeout=20)
            except Exception as e:
                return False, str(e)
            if r2.returncode != 0 or "Sanitizer" in r2.stderr:
                return False, r2.stderr
        return True, ""


def toolchain():
    """Trova compilatore, flag dello standard e (se possibile) sanitizer."""
    global _TC
    if _TC is not None:
        return _TC
    c = cfg()
    tc = {"exe": None, "std": None, "flags": [], "sanitizer": False}
    for nome in c["compilatori"]:
        exe = shutil.which(nome)
        if not exe:
            continue
        for std in ("-std=c23", "-std=c2x"):
            ok, _ = prova_compilazione(exe, [std], PROVA_C23, True)
            if ok:
                tc["exe"], tc["std"] = exe, std
                break
        if tc["exe"]:
            break
    if tc["exe"]:
        flags = ["-Wall", "-Wextra", "-Wpedantic"]
        if c.get("warning_come_errori", True):
            flags.append("-Werror")
        tc["flags"] = [tc["std"]] + flags
        if c.get("usa_sanitizer", True):
            san = ["-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-g"]
            ok, _ = prova_compilazione(tc["exe"], tc["flags"] + san, PROVA_SAN, True)
            if ok:
                tc["flags"] = tc["flags"] + san
                tc["sanitizer"] = True
    _TC = tc
    return tc


def file_soluzione(e):
    """Ritorna {nome_file: codice} della soluzione di riferimento di un esercizio."""
    sf = e.get("soluzione_file")
    if isinstance(sf, dict) and sf:
        return dict(sf)
    s = e.get("soluzione_riferimento")
    return {"main.c": s} if isinstance(s, str) else {}


NOME_FILE_OK = re.compile(r"^[A-Za-z0-9_]+\.(c|h)$")


def compila_ed_esegui(codice, stdin_text, timeout=None):
    """Compila ed esegue in una cartella temporanea. `codice` e' una stringa (un solo file)
    oppure un dizionario {nome_file: codice} (piu' file). Ritorna un dizionario con l'esito."""
    files = codice if isinstance(codice, dict) else {"prog.c": codice}
    tc = toolchain()
    if not tc["exe"]:
        return {"compila": False, "log": "nessun compilatore C trovato (esegui: python3 scripts/libro.py diagnosi)"}
    timeout = timeout or cfg().get("timeout_esecuzione_secondi", 10)
    with tempfile.TemporaryDirectory() as d:
        exe = os.path.join(d, "prog_eseguibile")
        for nome, cod in files.items():
            if not NOME_FILE_OK.match(nome):
                return {"compila": False, "log": "nome di file non valido: %s" % nome}
            scrivi(os.path.join(d, nome), cod if cod.endswith("\n") else cod + "\n")
        sorgenti = sorted(nome for nome in files if nome.endswith(".c"))
        if not sorgenti:
            return {"compila": False, "log": "nessun file .c da compilare"}
        cmd = [tc["exe"]] + tc["flags"] + ["-I", d, "-o", exe] + sorgenti + ["-lm"]
        try:
            r = _run(cmd, cwd=d, timeout=60)
        except subprocess.TimeoutExpired:
            return {"compila": False, "log": "timeout durante la compilazione"}
        if r.returncode != 0:
            return {"compila": False, "log": r.stderr[:1500]}
        env = dict(os.environ)
        env["UBSAN_OPTIONS"] = "print_stacktrace=0"
        try:
            r2 = _run([exe], input=stdin_text or "", cwd=d, timeout=timeout, env=env,
                      preexec_fn=_limiti if os.name == "posix" else None)
        except subprocess.TimeoutExpired:
            return {"compila": True, "timeout": True}
        return {"compila": True, "timeout": False, "uscita": r2.returncode,
                "stdout": r2.stdout[:100000], "stderr": r2.stderr[:1500]}


def norm_output(s):
    s = (s or "").replace("\r\n", "\n").strip("\n")
    return "\n".join(r.rstrip() for r in s.split("\n")).strip()


def norm_ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def prime_righe(s, k=6):
    righe = (s or "").strip().split("\n")
    return "\n".join(righe[:k])


# ----------------------------------------------------------------------------
# Lettura dei blocchi di codice dai file Markdown
# ----------------------------------------------------------------------------

RE_APERTURA = re.compile(r"^```\s*([A-Za-z0-9_+-]*)\s*$")
RE_MARCATORE = re.compile(r"<!--\s*cod:\s*(.*?)\s*-->")


def parse_params(s):
    d = {}
    for m in re.finditer(r'(\w+)=("([^"]*)"|\S+)', s):
        d[m.group(1)] = m.group(3) if m.group(3) is not None else m.group(2)
    return d


def estrai_blocchi(testo):
    righe = testo.split("\n")
    blocchi = []
    in_blocco = False
    cur = None
    for i, r in enumerate(righe):
        if not in_blocco:
            m = RE_APERTURA.match(r)
            if m:
                marker = None
                j = i - 1
                while j >= 0 and righe[j].strip() == "":
                    j -= 1
                if j >= 0:
                    mm = RE_MARCATORE.search(righe[j])
                    if mm:
                        marker = parse_params(mm.group(1))
                cur = {"lang": m.group(1).lower(), "inizio": i, "marker": marker, "buf": []}
                in_blocco = True
        else:
            if r.strip() == "```":
                cur["fine"] = i
                cur["codice"] = "\n".join(cur.pop("buf"))
                blocchi.append(cur)
                in_blocco = False
            else:
                cur["buf"].append(r)
    for k, b in enumerate(blocchi):
        if b["lang"] in ("input", "output") and k > 0:
            a = blocchi[k - 1]
            tra = righe[a["fine"] + 1:b["inizio"]]
            if all(not t.strip() for t in tra):
                base = a if a["lang"] == "c" else a.get("padre")
                if base is not None and base["lang"] == "c":
                    base[b["lang"]] = b["codice"]
                    b["padre"] = base
    return blocchi, righe


def prosa(testo):
    """Testo senza blocchi di codice e senza marcatori."""
    out = []
    dentro = False
    for r in testo.split("\n"):
        if RE_APERTURA.match(r) and not dentro:
            dentro = True
            continue
        if dentro:
            if r.strip() == "```":
                dentro = False
            continue
        if RE_MARCATORE.search(r):
            continue
        out.append(r)
    return "\n".join(out)


# ----------------------------------------------------------------------------
# Validazione dei file JSON prodotti dagli agenti
# ----------------------------------------------------------------------------

def _tipo(v, tipi):
    if isinstance(v, bool) and bool not in tipi:
        return False
    return isinstance(v, tipi)


def reg_da_macro(m):
    reg = {}
    for r in m.get("registro", []):
        if not isinstance(r, dict):
            continue
        nome = r.get("nome")
        cap = r.get("capitolo")
        if isinstance(nome, str) and isinstance(cap, int):
            nome = nome.strip().strip("<>")
            if nome not in reg or cap < reg[nome]:
                reg[nome] = cap
    return reg


def valida_macro(m, c):
    err, avv = [], []
    if not isinstance(m, dict):
        return ["la radice del JSON deve essere un oggetto"], avv
    if not _tipo(m.get("titolo"), (str,)) or not m.get("titolo"):
        err.append("manca 'titolo' (testo)")
    caps = m.get("capitoli")
    if not isinstance(caps, list):
        return err + ["manca 'capitoli' (lista)"], avv
    if not (c["capitoli_min"] <= len(caps) <= c["capitoli_max"]):
        err.append("numero di capitoli %d fuori dall'intervallo %d-%d" % (len(caps), c["capitoli_min"], c["capitoli_max"]))
    for i, cap in enumerate(caps, 1):
        w = "capitolo %d" % i
        if not isinstance(cap, dict):
            err.append("%s: deve essere un oggetto" % w)
            continue
        if cap.get("n") != i:
            err.append("%s: il campo 'n' deve valere %d" % (w, i))
        if not _tipo(cap.get("titolo"), (str,)) or not cap.get("titolo"):
            err.append("%s: manca 'titolo'" % w)
        if cap.get("tipo") not in ("teoria", "progetto"):
            err.append("%s: 'tipo' deve essere 'teoria' o 'progetto'" % w)
        ob = cap.get("obiettivi")
        if not isinstance(ob, list) or len(ob) < 3 or not all(isinstance(x, str) and x for x in ob):
            err.append("%s: 'obiettivi' deve avere almeno 3 frasi" % w)
        ar = cap.get("argomenti")
        if not isinstance(ar, list) or len(ar) < 1:
            err.append("%s: 'argomenti' deve essere una lista non vuota" % w)
        pr = cap.get("prerequisiti")
        if not isinstance(pr, list) or not all(isinstance(x, int) and 1 <= x < i for x in pr):
            err.append("%s: 'prerequisiti' deve contenere solo numeri di capitoli precedenti" % w)
        ss = cap.get("sotto_sezioni")
        if not isinstance(ss, list) or not (c["sotto_sezioni_min"] <= len(ss) <= c["sotto_sezioni_max"]):
            err.append("%s: servono da %d a %d sotto_sezioni" % (w, c["sotto_sezioni_min"], c["sotto_sezioni_max"]))
        else:
            for k, s in enumerate(ss, 1):
                if not isinstance(s, dict) or s.get("id") != "%d.%d" % (i, k) or not s.get("titolo"):
                    err.append("%s: sotto_sezione %d deve avere id '%d.%d' e un titolo" % (w, k, i, k))
    if caps and c.get("progetto_finale", True):
        if not isinstance(caps[-1], dict) or caps[-1].get("tipo") != "progetto":
            err.append("l'ultimo capitolo deve essere di tipo 'progetto'")
    n = len(caps)
    reg = m.get("registro")
    rmin = c.get("registro_min", 40)
    gmin = c.get("glossario_min", 30)
    if not isinstance(reg, list) or len(reg) < rmin:
        err.append("'registro' deve essere una lista di almeno %d elementi" % rmin)
    else:
        for k, r in enumerate(reg):
            if (not isinstance(r, dict) or not isinstance(r.get("nome"), str) or not r.get("nome")
                    or r.get("categoria") not in CATEGORIE_REGISTRO
                    or not isinstance(r.get("capitolo"), int) or not (1 <= r["capitolo"] <= max(n, 1))):
                err.append("registro[%d]: servono 'nome', 'categoria' (una tra: %s) e 'capitolo' valido"
                           % (k, ", ".join(CATEGORIE_REGISTRO)))
                if len(err) > 30:
                    break
    nt = m.get("non_trattati")
    if not isinstance(nt, list) or not all(isinstance(x, str) for x in nt):
        err.append("'non_trattati' deve essere una lista di testi (anche vuota)")
        nt = []
    gl = m.get("glossario")
    if not isinstance(gl, list) or len(gl) < gmin:
        err.append("'glossario' deve avere almeno %d termini" % gmin)
    else:
        visti = set()
        for k, g in enumerate(gl):
            if (not isinstance(g, dict) or not g.get("termine") or not g.get("definizione")
                    or not isinstance(g.get("capitolo"), int) or not (1 <= g["capitolo"] <= max(n, 1))
                    or not isinstance(g.get("sinonimi_vietati"), list)):
                err.append("glossario[%d]: servono 'termine', 'definizione', 'capitolo', 'sinonimi_vietati' (lista)" % k)
            else:
                t = g["termine"].lower()
                if t in visti:
                    err.append("glossario: termine duplicato '%s'" % g["termine"])
                visti.add(t)
            if len(err) > 40:
                break
    if isinstance(reg, list) and not err:
        nomi = set(reg_da_macro(m).keys())
        mancanti = sorted(k for k in KEYWORDS if k not in nomi and k not in nt)
        if mancanti:
            avv.append("parole chiave C23 ne' registrate ne' in 'non_trattati': " + ", ".join(mancanti))
    return err[:40], avv


def valida_blueprint(b, n, macro, c):
    err, avv = [], []
    if not isinstance(b, dict):
        return ["la radice deve essere un oggetto"], avv
    if b.get("capitolo") != n:
        err.append("'capitolo' deve valere %d" % n)
    cm = macro["capitoli"][n - 1]
    if b.get("titolo") != cm["titolo"]:
        avv.append("il titolo differisce dalla macro-scaletta")
    for campo, minimo in (("obiettivi", 3), ("regole", 1), ("errori_comuni", 3)):
        v = b.get(campo)
        if not isinstance(v, list) or len(v) < minimo:
            err.append("'%s' deve essere una lista di almeno %d elementi" % (campo, minimo))
    ci = b.get("concetti_introdotti")
    if not isinstance(ci, list) or len(ci) < 2 or not all(
            isinstance(x, dict) and x.get("termine") and x.get("definizione") for x in ci):
        err.append("'concetti_introdotti' deve contenere almeno 2 oggetti {termine, definizione}")
    if not isinstance(b.get("concetti_richiesti"), list):
        err.append("'concetti_richiesti' deve essere una lista (anche vuota)")
    reg = reg_da_macro(macro)
    fu = b.get("funzioni_usate")
    if not isinstance(fu, list):
        err.append("'funzioni_usate' deve essere una lista (anche vuota)")
    else:
        for k, f in enumerate(fu):
            if not isinstance(f, dict) or not f.get("nome") or not f.get("firma") or not f.get("header"):
                err.append("funzioni_usate[%d]: servono 'nome', 'firma', 'header', 'descrizione'" % k)
                continue
            nome = f["nome"]
            if nome not in reg:
                err.append("funzioni_usate: '%s' non e' nel registro della macro-scaletta" % nome)
            elif reg[nome] > n:
                err.append("funzioni_usate: '%s' e' introdotta solo nel capitolo %d" % (nome, reg[nome]))
    ss = b.get("sotto_sezioni")
    ids_macro = [s["id"] for s in cm["sotto_sezioni"]]
    ex = b.get("esercizi")
    if not isinstance(ex, list) or not ex:
        err.append("'esercizi' deve essere una lista non vuota")
        ex = []
    ids_ex = [e.get("id") for e in ex if isinstance(e, dict)]
    if not isinstance(ss, list):
        err.append("'sotto_sezioni' deve essere una lista")
    else:
        if [s.get("id") for s in ss if isinstance(s, dict)] != ids_macro:
            err.append("gli id delle sotto_sezioni devono essere esattamente: " + ", ".join(ids_macro))
        for s in ss:
            if not isinstance(s, dict):
                continue
            w = "sotto_sezione %s" % s.get("id")
            if not isinstance(s.get("contenuti"), list) or len(s["contenuti"]) < 2:
                err.append("%s: 'contenuti' deve avere almeno 2 elementi" % w)
            if not s.get("titolo"):
                err.append("%s: manca 'titolo'" % w)
            if not isinstance(s.get("esempio_guidato"), str) or not s["esempio_guidato"]:
                err.append("%s: 'esempio_guidato' deve descrivere l'esempio (testo)" % w)
            if not isinstance(s.get("approfondimento"), str):
                err.append("%s: 'approfondimento' deve essere un testo (anche vuoto)" % w)
            if s.get("esercizio_id") not in ids_ex:
                err.append("%s: 'esercizio_id' non corrisponde a nessun esercizio" % w)
    for e in ex:
        if not isinstance(e, dict):
            err.append("esercizi: ogni elemento deve essere un oggetto")
            continue
        w = "esercizio %s" % e.get("id")
        if not isinstance(e.get("id"), str) or not re.match(r"^%d\.\d+$" % n, e["id"]):
            err.append("%s: l'id deve avere forma '%d.k'" % (w, n))
        if e.get("tipo") not in ("esercizio", "progetto"):
            err.append("%s: 'tipo' deve essere 'esercizio' o 'progetto'" % w)
        if not e.get("titolo"):
            err.append("%s: manca 'titolo'" % w)
        if not isinstance(e.get("descrizione"), str) or len(e["descrizione"]) < 40:
            err.append("%s: 'descrizione' troppo corta" % w)
        ct = e.get("concetti_da_tenere_a_mente")
        if not isinstance(ct, list) or not (2 <= len(ct) <= 6):
            err.append("%s: servono da 2 a 6 'concetti_da_tenere_a_mente'" % w)
        dg = e.get("domande_guida")
        if not isinstance(dg, list) or not (3 <= len(dg) <= 6) or not all(isinstance(x, str) and x.strip().endswith("?") for x in dg):
            err.append("%s: servono da 3 a 6 'domande_guida', ognuna deve finire con '?'" % w)
        if not isinstance(e.get("difficolta"), int) or not (1 <= e["difficolta"] <= 5):
            err.append("%s: 'difficolta' deve essere un intero da 1 a 5" % w)
        if e.get("tipo") == "progetto":
            if not isinstance(e.get("fasi"), list) or len(e["fasi"]) < 3:
                err.append("%s: un progetto richiede almeno 3 'fasi'" % w)
        ver = e.get("verificabile", True)
        if not isinstance(ver, bool):
            err.append("%s: 'verificabile' deve essere true o false" % w)
        elif ver:
            files = file_soluzione(e)
            if not files or not any(nm.endswith(".c") and isinstance(cd, str) and "main" in cd for nm, cd in files.items()):
                err.append("%s: serve 'soluzione_riferimento' (programma C completo con main) oppure 'soluzione_file' ({nome_file: codice} con almeno un .c che contiene main)" % w)
            elif not all(NOME_FILE_OK.match(nm) and isinstance(cd, str) for nm, cd in files.items()):
                err.append("%s: 'soluzione_file': nomi ammessi solo lettere, cifre, _ con estensione .c o .h" % w)
            eio = e.get("esempi_io")
            if not isinstance(eio, list) or not eio or not all(
                    isinstance(x, dict) and isinstance(x.get("input"), str) and isinstance(x.get("output"), str) for x in eio):
                err.append("%s: servono 'esempi_io' (lista di {input, output})" % w)
            t = e.get("test")
            if not isinstance(t, list) or not all(
                    isinstance(x, dict) and isinstance(x.get("input"), str) and isinstance(x.get("output"), str) for x in t):
                err.append("%s: 'test' deve essere una lista di {input, output} (anche vuota)" % w)
        elif not e.get("motivo_non_verificabile"):
            err.append("%s: se 'verificabile' e' false serve 'motivo_non_verificabile'" % w)
    return err[:40], avv


# ----------------------------------------------------------------------------
# Caricamento dati
# ----------------------------------------------------------------------------

def carica_macro():
    return leggi_json(p("stato", "macro_scaletta.json"))


def carica_bp(n):
    return leggi_json(p("stato", "blueprint", "cap%s.json" % nn(n)))


def file_attesi(n, bp):
    f = ["%s_00.md" % nn(n)]
    for s in bp["sotto_sezioni"]:
        k = int(s["id"].split(".")[1])
        f.append("%s_%s.md" % (nn(n), nn(k)))
    f.append("%s_99.md" % nn(n))
    return f


def dir_cap(n):
    return p("manoscritto", "cap%s" % nn(n))


# ----------------------------------------------------------------------------
# Verifica dei blueprint (incluse le soluzioni di riferimento)
# ----------------------------------------------------------------------------

def verifica_soluzioni(n, bp, macro):
    err, avv = [], []
    reg = reg_da_macro(macro)
    nt = set(macro.get("non_trattati", []))
    for e in bp.get("esercizi", []):
        if not isinstance(e, dict) or e.get("verificabile", True) is not True:
            continue
        w = "esercizio %s" % e.get("id")
        sol = file_soluzione(e)
        pr = None
        for nm, cd in sol.items():
            pr = pericoloso(cd)
            if pr:
                err.append("%s: soluzione (%s) %s" % (w, nm, pr))
                break
        if pr:
            continue
        for nm, cd in sol.items():
            for liv, msg in analizza_progressione(cd, n, reg, nt):
                (err if liv == "errore" else avv).append("%s (soluzione, %s): %s" % (w, nm, msg))
            for pat, msg in PATTERN_VIETATI:
                if re.search(pat, cd):
                    err.append("%s (soluzione, %s): %s" % (w, nm, msg))
        casi = list(e.get("esempi_io", [])) + list(e.get("test", []))
        if not casi:
            casi = [{"input": "", "output": None}]
        for k, caso in enumerate(casi, 1):
            r = compila_ed_esegui(sol, caso.get("input", ""))
            if not r["compila"]:
                err.append("%s: la soluzione non compila:\n%s" % (w, prime_righe(r["log"], 8)))
                break
            if r.get("timeout"):
                err.append("%s: timeout nel caso %d" % (w, k))
                continue
            if r["uscita"] != 0:
                err.append("%s: caso %d termina con codice %s %s" % (w, k, r["uscita"], prime_righe(r["stderr"], 3)))
                continue
            if caso.get("output") is not None and norm_output(r["stdout"]) != norm_output(caso["output"]):
                err.append("%s: caso %d, output diverso.\n  atteso:\n%s\n  ottenuto:\n%s" % (
                    w, k, prime_righe(caso["output"], 4), prime_righe(r["stdout"], 4)))
    return err, avv


# ----------------------------------------------------------------------------
# Controlli sui file di un capitolo
# ----------------------------------------------------------------------------

def righe_utili(codice):
    out = []
    for r in codice.split("\n"):
        t = re.sub(r"\s+", "", r)
        if len(t) > 8 and t not in ("{", "}", "return0;"):
            out.append(t)
    return out


def controlla_capitolo(n, c, macro, bp):
    """Controlli strutturali, di progressione, di glossario, di soluzioni esposte."""
    err, avv = [], []
    reg = reg_da_macro(macro)
    nt = set(macro.get("non_trattati", []))
    cartella = dir_cap(n)
    attesi = file_attesi(n, bp)
    mancanti = [f for f in attesi if not os.path.exists(os.path.join(cartella, f))]
    if mancanti:
        return ["file mancanti in manoscritto/cap%s/: %s" % (nn(n), ", ".join(mancanti))], avv, {}
    extra = [f for f in os.listdir(cartella) if f.endswith(".md") and f not in attesi]
    if extra:
        avv.append("file non previsti nella cartella del capitolo: " + ", ".join(sorted(extra)))
    esercizi = {e["id"]: e for e in bp["esercizi"]}
    soluzioni = [(e["id"], righe_utili("\n".join(file_soluzione(e).values()))) for e in bp["esercizi"]
                 if e.get("verificabile", True) is True]
    glos = macro.get("glossario", [])
    ids_blocchi = set()
    info = {"programmi": 0, "frammenti": 0, "errori_voluti": 0, "tracce": 0, "parole": 0}
    pmin, pmax = c["parole_sezione"]
    codici_libro = []

    for f in attesi:
        path = os.path.join(cartella, f)
        testo = leggi(path)
        blocchi, righe = estrai_blocchi(testo)
        pr = prosa(testo)
        parole = len(re.findall(r"\w+", pr))
        info["parole"] += parole
        loc = f
        trovati = [x.group(0) for x in RE_APOSTROFO_ACCENTO.finditer(pr) if x.group(0).lower() != "po'"]
        if trovati:
            err.append("%s: apostrofo al posto dell'accento (%s%s): scrivi le lettere accentate corrette (e, e, a, i, o, u con accento)"
                       % (loc, ", ".join(sorted(set(trovati))[:4]), "..." if len(set(trovati)) > 4 else ""))
        m = re.match(r"%s_(\d\d)\.md$" % nn(n), f)
        k = int(m.group(1))
        # --- struttura
        if k == 0:
            if not re.search(r"^#\s+Capitolo\s+%d\b" % n, testo, re.M):
                err.append("%s: manca il titolo '# Capitolo %d - ...'" % (loc, n))
        elif k == 99:
            if not re.search(r"^##\s+Riepilogo", testo, re.M):
                err.append("%s: manca la sezione '## Riepilogo'" % loc)
        else:
            sid = "%d.%d" % (n, k)
            if not re.search(r"^##\s+%s\s" % re.escape(sid), testo, re.M):
                err.append("%s: manca il titolo '## %s <titolo>'" % (loc, sid))
            if not re.search(r"^###\s+Esempio guidato", testo, re.M):
                err.append("%s: manca '### Esempio guidato'" % loc)
            mes = re.search(r"^###\s+(Esercizio|Progetto)\s+%s\b" % re.escape(sid), testo, re.M)
            if not mes:
                err.append("%s: manca '### Esercizio %s - <titolo>' (o '### Progetto %s ...')" % (loc, sid, sid))
            else:
                riga_es = testo[:mes.start()].count("\n")
                sez = "\n".join(righe[riga_es:])
                for et in ("**Descrizione**", "**Concetti da tenere a mente**", "**Domande guida**"):
                    if et not in sez:
                        err.append("%s: nell'esercizio manca l'etichetta %s" % (loc, et))
                mdg = re.search(r"\*\*Domande guida\*\*(.*?)(\n\*\*|\Z)", sez, re.S)
                if mdg and mdg.group(1).count("?") < 3:
                    err.append("%s: le domande guida devono essere almeno 3" % loc)
                ex = None
                for e in bp["sotto_sezioni"]:
                    if e["id"] == sid:
                        ex = esercizi.get(e["esercizio_id"])
                if ex:
                    for caso in ex.get("esempi_io", []):
                        if caso.get("input", "").strip() and norm_ws(caso["input"]) not in norm_ws(sez):
                            err.append("%s: l'esempio di esecuzione dell'esercizio non contiene l'input previsto dal blueprint" % loc)
                        if caso.get("output", "").strip() and norm_ws(caso["output"]) not in norm_ws(sez):
                            err.append("%s: l'esempio di esecuzione dell'esercizio non contiene l'output previsto dal blueprint" % loc)
                for b in blocchi:
                    if b["lang"] == "c" and b["inizio"] >= riga_es:
                        tipo = (b["marker"] or {}).get("tipo", "programma")
                        if tipo != "traccia":
                            err.append("%s riga %d: nell'esercizio non sono ammessi blocchi C (solo tipo=traccia con TODO): niente soluzioni" % (loc, b["inizio"] + 1))
                        elif b["codice"].count("\n") + 1 > 25 or "TODO" not in b["codice"]:
                            err.append("%s riga %d: una traccia deve avere al massimo 25 righe e contenere TODO" % (loc, b["inizio"] + 1))
            if parole < pmin or parole > pmax:
                avv.append("%s: %d parole di prosa (previsto %d-%d)" % (loc, parole, pmin, pmax))
        # --- blocchi di codice
        for b in blocchi:
            if b["lang"] != "c":
                continue
            where = "%s riga %d" % (loc, b["inizio"] + 1)
            mk = b["marker"]
            if not mk or "id" not in mk:
                err.append("%s: blocco C senza marcatore '<!-- cod: id=... tipo=... -->' sulla riga precedente" % where)
                continue
            if mk["id"] in ids_blocchi:
                err.append("%s: id di blocco duplicato '%s'" % (where, mk["id"]))
            ids_blocchi.add(mk["id"])
            tipo = mk.get("tipo", "programma")
            if tipo not in ("programma", "frammento", "errore", "traccia"):
                err.append("%s: tipo '%s' non valido (programma, frammento, errore, traccia)" % (where, tipo))
                continue
            if tipo == "errore":
                info["errori_voluti"] += 1
                continue
            for pat, msg in PATTERN_VIETATI:
                if re.search(pat, b["codice"]):
                    err.append("%s: %s" % (where, msg))
            if tipo == "traccia":
                info["tracce"] += 1
                continue
            for liv, msg in analizza_progressione(b["codice"], n, reg, nt):
                (err if liv == "errore" else avv).append("%s: %s" % (where, msg))
            if tipo == "frammento":
                info["frammenti"] += 1
            else:
                info["programmi"] += 1
            codici_libro.append((where, b["codice"]))
        # --- glossario
        for g in glos:
            for sin in g.get("sinonimi_vietati", []):
                if sin and re.search(r"(?<!\w)%s(?!\w)" % re.escape(sin), pr, re.I):
                    err.append("%s: usa '%s' ma il termine ufficiale del glossario e' '%s'" % (loc, sin, g["termine"]))
            if g.get("capitolo", 0) > n and len(g["termine"]) >= 5 and re.search(
                    r"(?<!\w)%s(?!\w)" % re.escape(g["termine"]), pr, re.I):
                avv.append("%s: usa il termine '%s' che il glossario introduce al capitolo %d" % (loc, g["termine"], g["capitolo"]))
    # --- soluzioni esposte negli esempi
    for where, cod in codici_libro:
        mie = set(righe_utili(cod))
        for eid, sol in soluzioni:
            if len(sol) >= 5:
                comuni = sum(1 for r in sol if r in mie)
                if comuni / float(len(sol)) >= 0.7:
                    err.append("%s: l'esempio assomiglia alla soluzione dell'esercizio %s (>=70%% di righe in comune): cambia l'esempio" % (where, eid))
    return err, avv, info


def verifica_codice(n, bp):
    """Compila ed esegue i blocchi C del capitolo."""
    err, avv = [], []
    cartella = dir_cap(n)
    gruppi = {}
    for f in file_attesi(n, bp):
        path = os.path.join(cartella, f)
        if not os.path.exists(path):
            continue
        blocchi, _ = estrai_blocchi(leggi(path))
        for b in blocchi:
            if b["lang"] != "c" or not b["marker"] or "id" not in b["marker"]:
                continue
            tipo = b["marker"].get("tipo", "programma")
            where = "%s riga %d (id %s)" % (f, b["inizio"] + 1, b["marker"]["id"])
            if tipo == "programma" and b["marker"].get("gruppo"):
                gruppi.setdefault((f, b["marker"]["gruppo"]), []).append((where, b))
                continue
            if tipo == "programma":
                pr = pericoloso(b["codice"])
                if pr:
                    err.append("%s: %s" % (where, pr))
                    continue
                r = compila_ed_esegui(b["codice"], b.get("input", ""))
                if not r["compila"]:
                    err.append("%s: non compila:\n%s" % (where, prime_righe(r["log"], 8)))
                    continue
                if r.get("timeout"):
                    err.append("%s: timeout (programma troppo lento o in attesa di input: aggiungi un blocco ```input)" % where)
                    continue
                atteso_exit = int(b["marker"].get("exit", 0)) if str(b["marker"].get("exit", "0")).lstrip("-").isdigit() else 0
                if r["uscita"] != atteso_exit:
                    err.append("%s: codice di uscita %s invece di %s %s" % (where, r["uscita"], atteso_exit, prime_righe(r["stderr"], 3)))
                    continue
                if "output" in b:
                    if norm_output(r["stdout"]) != norm_output(b["output"]):
                        err.append("%s: l'output mostrato nel libro e' diverso da quello reale.\n  nel libro:\n%s\n  reale:\n%s" % (
                            where, prime_righe(b["output"], 4), prime_righe(r["stdout"], 4)))
                elif r["stdout"].strip():
                    avv.append("%s: il programma stampa qualcosa ma non c'e' un blocco ```output" % where)
            elif tipo == "errore":
                r = compila_ed_esegui(b["codice"], "")
                if r["compila"]:
                    err.append("%s: e' marcato 'errore' ma compila senza problemi" % where)
    for (f, gid), membri in gruppi.items():
        where = "%s gruppo '%s'" % (f, gid)
        files = {}
        ok = True
        for w_, b in membri:
            nome = b["marker"].get("file", "")
            if not NOME_FILE_OK.match(nome):
                err.append("%s: serve file=<nome>.c o .h (solo lettere, cifre, _) nel marcatore" % w_)
                ok = False
            elif nome in files:
                err.append("%s: nome di file duplicato nel gruppo: %s" % (w_, nome))
                ok = False
            else:
                files[nome] = b["codice"]
        if not ok:
            continue
        if not any(nm.endswith(".c") and re.search(r"\bmain\b", cd) for nm, cd in files.items()):
            err.append("%s: nessun file .c del gruppo contiene main" % where)
            continue
        pr = None
        for nm, cd in files.items():
            pr = pericoloso(cd)
            if pr:
                err.append("%s: file %s %s" % (where, nm, pr))
                break
        if pr:
            continue
        inp = ""
        out_atteso = None
        for _, b in membri:
            if "input" in b:
                inp = b["input"]
            if "output" in b:
                out_atteso = b["output"]
        r = compila_ed_esegui(files, inp)
        if not r["compila"]:
            err.append("%s: non compila:\n%s" % (where, prime_righe(r["log"], 8)))
        elif r.get("timeout"):
            err.append("%s: timeout" % where)
        elif r["uscita"] != 0:
            err.append("%s: codice di uscita %s %s" % (where, r["uscita"], prime_righe(r["stderr"], 3)))
        elif out_atteso is not None:
            if norm_output(r["stdout"]) != norm_output(out_atteso):
                err.append("%s: l'output mostrato nel libro e' diverso da quello reale.\n  nel libro:\n%s\n  reale:\n%s" % (
                    where, prime_righe(out_atteso, 4), prime_righe(r["stdout"], 4)))
        elif r["stdout"].strip():
            avv.append("%s: il programma stampa qualcosa ma non c'e' un blocco ```output" % where)
    return err, avv


def valuta_capitolo(n, c, macro, bp):
    """Assembla, controlla, compila. Salva stato/verifica_capNN.json. Ritorna (errori, avvisi)."""
    e1, a1, info = controlla_capitolo(n, c, macro, bp)
    e2, a2 = ([], [])
    if not e1 or all("file mancanti" not in x for x in e1):
        e2, a2 = verifica_codice(n, bp)
    err = e1 + e2
    avv = a1 + a2
    if not toolchain()["exe"]:
        err.append("nessun compilatore C trovato: esegui 'python3 scripts/libro.py diagnosi'")
    if not err:
        assembla(n, bp)
    scrivi_json(p("stato", "verifica_cap%s.json" % nn(n)), {"capitolo": n, "errori": err, "avvisi": avv, "info": info})
    return err, avv


def assembla(n, bp=None):
    cartella = dir_cap(n)
    if not os.path.isdir(cartella):
        return None
    files = sorted(f for f in os.listdir(cartella) if f.endswith(".md"))
    testo = "\n\n".join(leggi(os.path.join(cartella, f)).strip() for f in files) + "\n"
    dest = p("manoscritto", "cap%s.md" % nn(n))
    scrivi(dest, testo)
    return dest


# ----------------------------------------------------------------------------
# Riassunti degli stati (deterministici)
# ----------------------------------------------------------------------------

def costruisci_stati(macro, bps, c):
    n_tot = len(macro["capitoli"])
    reg = macro.get("registro", [])
    glos = macro.get("glossario", [])
    massimo = c.get("riassunto_stati_max_caratteri", 24000)
    for n in range(1, n_tot + 1):
        blocchi = []
        for k in range(1, n):
            cap = macro["capitoli"][k - 1]
            righe = ["## Capitolo %d - %s" % (k, cap["titolo"])]
            el = [r["nome"] + " (" + r["categoria"] + ")" for r in reg if r.get("capitolo") == k]
            if el:
                righe.append("Elementi del linguaggio introdotti: " + "; ".join(el))
            tg = [g["termine"] for g in glos if g.get("capitolo") == k]
            if tg:
                righe.append("Termini del glossario introdotti: " + ", ".join(tg))
            ci = [x["termine"] for x in bps[k]["concetti_introdotti"]]
            righe.append("Concetti spiegati: " + ", ".join(ci))
            tit = [e["titolo"] for e in bps[k]["esercizi"]]
            righe.append("Esercizi gia' svolti dal lettore: " + "; ".join(tit))
            blocchi.append("\n".join(righe))
        testo = "\n\n".join(blocchi)
        if len(testo) > massimo:
            blocchi2 = [b.split("\nEsercizi gia'")[0] for b in blocchi]
            testo = "\n\n".join(blocchi2)
        permessi = sorted(["%s (%s)" % (r["nome"], r["categoria"]) for r in reg if r.get("capitolo", 99) <= n])
        out = ["# Stato delle conoscenze all'inizio del capitolo %d" % n, "",
               "Questo file e' generato automaticamente da scripts/libro.py: NON modificarlo.", "",
               "## Cosa il lettore ha gia' visto (capitoli 1-%d)" % (n - 1 if n > 1 else 0), "",
               testo if testo else "(niente: e' il primo capitolo)", "",
               "## Elementi del linguaggio utilizzabili nel capitolo %d (cumulativo)" % n, "",
               "; ".join(permessi), "",
               "## Elementi NON trattati nel libro (vietati)", "",
               "; ".join(macro.get("non_trattati", [])) or "(nessuno)", ""]
        scrivi(p("stato", "stati", "cap%s.md" % nn(n)), "\n".join(out))


# ----------------------------------------------------------------------------
# Patch dell'audit
# ----------------------------------------------------------------------------

GRAVITA = ("bloccante", "alta", "media", "bassa")


def valida_audit(d, n=None):
    err = []
    if not isinstance(d, dict):
        return ["la radice deve essere un oggetto"]
    if d.get("verdetto") not in ("ok", "da_correggere"):
        err.append("'verdetto' deve essere 'ok' o 'da_correggere'")
    pt = d.get("patch")
    if not isinstance(pt, list):
        return err + ["'patch' deve essere una lista (anche vuota)"]
    if d.get("verdetto") == "ok" and pt:
        err.append("verdetto 'ok' ma ci sono patch")
    for i, x in enumerate(pt):
        w = "patch[%d]" % i
        if not isinstance(x, dict):
            err.append("%s: deve essere un oggetto" % w)
            continue
        for campo in ("id", "file", "gravita", "tipo", "problema", "certezza"):
            if not x.get(campo):
                err.append("%s: manca '%s'" % (w, campo))
        if x.get("gravita") not in GRAVITA:
            err.append("%s: 'gravita' deve essere una tra %s" % (w, ", ".join(GRAVITA)))
        if x.get("certezza") not in ("alta", "media"):
            err.append("%s: 'certezza' deve essere 'alta' o 'media'" % w)
        f = x.get("file", "")
        if not isinstance(f, str) or not f.startswith("manoscritto/") or ".." in f:
            err.append("%s: 'file' deve essere un percorso dentro manoscritto/" % w)
        elif n is not None and not re.match(r"^manoscritto/cap%s/" % nn(n), f):
            err.append("%s: il file non appartiene al capitolo %d" % (w, n))
        elif not os.path.exists(p(f)):
            err.append("%s: il file '%s' non esiste" % (w, f))
    return err[:30]


def applica_patch(d, etichetta, ciclo):
    """Applica le patch esatte e sicure. Ritorna (applicate, residui)."""
    applicate, residui = [], []
    backup = p("stato", "backup", etichetta)
    for x in d.get("patch", []):
        f = p(x["file"])
        testo = leggi(f)
        old, new = x.get("old_text"), x.get("new_text")
        motivo = None
        if x.get("certezza") != "alta":
            motivo = "certezza media: richiede verifica"
        elif not isinstance(old, str) or not isinstance(new, str) or old == "":
            motivo = "nessuna sostituzione esatta proposta"
        elif testo.count(old) != 1:
            motivo = "old_text trovato %d volte (deve essere 1)" % testo.count(old)
        if motivo:
            y = dict(x)
            y["motivo_residuo"] = motivo
            residui.append(y)
            continue
        os.makedirs(backup, exist_ok=True)
        bk = os.path.join(backup, x["file"].replace("/", "__"))
        if not os.path.exists(bk):
            shutil.copy(f, bk)
        scrivi(f, testo.replace(old, new, 1))
        applicate.append(x["id"])
    return applicate, residui


def cap_da_file(percorso):
    m = re.search(r"cap(\d\d)", percorso)
    return int(m.group(1)) if m else None


# ----------------------------------------------------------------------------
# Verifica automatica dei passi (rileva da solo cosa e' stato prodotto)
# ----------------------------------------------------------------------------

def breve(x, k=3):
    """Prime k righe non vuote di un messaggio, su una riga sola."""
    righe = [r.strip() for r in str(x).split("\n") if r.strip()]
    return " | ".join(righe[:k])


def ha_errori(path):
    d, e = leggi_json(path)
    return bool(d and d.get("errori"))


def init_capitoli(st, n):
    st["n_capitoli"] = n
    for i in range(1, n + 1):
        st["capitoli"].setdefault(str(i), {"fase": "blueprint", "ciclo": 1, "errori_aperti": False,
                                           "gravi_ciclo": False, "audit_applicato": 0, "note": []})


def tutti_bp(macro, n_tot):
    bps = {}
    for i in range(1, n_tot + 1):
        b, e = carica_bp(i)
        if e:
            return None
        bps[i] = b
    return bps


def cmd_verifica(stampa=True):
    c = cfg()
    st = carica_stato()
    out = []
    cambiato = False

    def dire(msg):
        out.append(msg)

    # ---------------- P1
    macro_path = p("stato", "macro_scaletta.json")
    if st["p1"]["approvato"] and os.path.exists(macro_path):
        if st["p1"].get("hash") and hash_file(macro_path) != st["p1"]["hash"]:
            if not st["p1"].get("modificato"):
                st["p1"]["modificato"] = True
                cambiato = True
            dire("ATTENZIONE: stato/macro_scaletta.json e' stato modificato dopo l'approvazione. "
                 "Se la modifica e' voluta, rilancia: python3 scripts/libro.py approva 1")
    if not st["p1"]["verificato"] and os.path.exists(macro_path):
        m, e = carica_macro()
        if e:
            scrivi_json(p("stato", "verifica_p1.json"), {"errori": [e], "avvisi": []})
            dire("P1: " + e)
        else:
            err, avv = valida_macro(m, c)
            scrivi_json(p("stato", "verifica_p1.json"), {"errori": err, "avvisi": avv})
            if err:
                dire("P1: la macro-scaletta ha %d errori (vedi stato/verifica_p1.json)" % len(err))
                for x in err[:8]:
                    dire("   - " + x)
            else:
                st["p1"]["verificato"] = True
                init_capitoli(st, len(m["capitoli"]))
                cambiato = True
                dire("P1: macro-scaletta valida (%d capitoli)." % len(m["capitoli"]))
                for x in avv:
                    dire("   avviso: " + x)
    if not st["p1"]["verificato"]:
        salva_stato(st)
        return finisci(out, stampa)

    macro, _ = carica_macro()
    n_tot = st["n_capitoli"]

    # ---------------- P2
    for n in range(1, n_tot + 1):
        cp = st["capitoli"][str(n)]
        if cp["fase"] != "blueprint":
            continue
        bp, e = carica_bp(n)
        if e:
            if "mancante" not in e:
                dire("P2 cap %d: %s" % (n, e))
                scrivi_json(p("stato", "verifica_bp_cap%s.json" % nn(n)), {"errori": [e], "avvisi": []})
                cp["errori_aperti"] = True
            continue
        err, avv = valida_blueprint(bp, n, macro, c)
        if not err:
            e2, a2 = verifica_soluzioni(n, bp, macro)
            err += e2
            avv += a2
        scrivi_json(p("stato", "verifica_bp_cap%s.json" % nn(n)), {"errori": err, "avvisi": avv})
        if err:
            cp["errori_aperti"] = True
            cambiato = True
            dire("P2 cap %d: blueprint con %d errori (vedi stato/verifica_bp_cap%s.json)" % (n, len(err), nn(n)))
            for x in err[:6]:
                dire("   - " + breve(x))
        else:
            cp["fase"] = "stesura"
            cp["errori_aperti"] = False
            cambiato = True
            dire("P2 cap %d: blueprint valido, soluzioni compilate e testate." % n)
            for x in avv:
                dire("   avviso: " + x)

    # ---------------- P2B
    tutti_ok = all(st["capitoli"][str(n)]["fase"] != "blueprint" for n in range(1, n_tot + 1))
    if tutti_ok and not st["p2b"]["verificato"]:
        bps_r = tutti_bp(macro, n_tot)
        if bps_r:
            scrivi_riepilogo_blueprint(macro, bps_r)
        d, e = leggi_json(p("stato", "coerenza_blueprint.json"))
        if e is None:
            if not isinstance(d, dict) or d.get("verdetto") not in ("ok", "corretto", "da_decidere") or not isinstance(d.get("problemi"), list):
                dire("P2B: coerenza_blueprint.json non ha il formato richiesto (verdetto, problemi).")
            elif d["verdetto"] == "da_decidere":
                dire("P2B: l'agente segnala problemi che richiedono una TUA decisione:")
                for x in d["problemi"]:
                    if isinstance(x, dict) and not x.get("applicata"):
                        dire("   - [cap %s] %s -> proposta: %s" % (",".join(str(c_) for c_ in (x.get("capitoli") or [])), x.get("descrizione"), x.get("correzione_proposta")))
                dire("   Decidi, poi chiedi all'agente di applicare (o modifica a mano i blueprint) e cancella stato/coerenza_blueprint.json.")
            else:
                bps = {}
                ricontrollo_ko = False
                for n in range(1, n_tot + 1):
                    bp, e2 = carica_bp(n)
                    err = valida_blueprint(bp, n, macro, c)[0] if not e2 else [e2]
                    if not err:
                        err = verifica_soluzioni(n, bp, macro)[0]
                    if err:
                        st["capitoli"][str(n)]["fase"] = "blueprint"
                        st["capitoli"][str(n)]["errori_aperti"] = True
                        scrivi_json(p("stato", "verifica_bp_cap%s.json" % nn(n)), {"errori": err, "avvisi": []})
                        dire("P2B: dopo le correzioni il blueprint del cap %d non e' piu' valido." % n)
                        ricontrollo_ko = True
                    bps[n] = bp
                if not ricontrollo_ko:
                    costruisci_stati(macro, bps, c)
                    st["p2b"]["verificato"] = True
                    cambiato = True
                    dire("P2B: coerenza dei blueprint verificata; riassunti degli stati generati in stato/stati/.")

    # ---------------- capitoli: P3 / P4 / P5
    if st["p2b"]["verificato"]:
        pil = c["capitolo_pilota"]
        for n in range(1, n_tot + 1):
            cp = st["capitoli"][str(n)]
            if not st["pilota"]["approvato"] and n != pil:
                continue
            bp, e = carica_bp(n)
            if e:
                continue
            ciclo = cp["ciclo"]
            if cp["fase"] == "stesura":
                mancanti = [f for f in file_attesi(n, bp) if not os.path.exists(os.path.join(dir_cap(n), f))]
                if len(mancanti) == len(file_attesi(n, bp)):
                    continue
                err, avv = valuta_capitolo(n, c, macro, bp)
                if err:
                    cp["errori_aperti"] = True
                    dire("P3 cap %d: %d errori (vedi stato/verifica_cap%s.json)" % (n, len(err), nn(n)))
                    for x in err[:6]:
                        dire("   - " + breve(x))
                else:
                    cp["fase"] = "audit"
                    cp["errori_aperti"] = False
                    dire("P3 cap %d: stesura valida, codice compilato ed eseguito." % n)
                    for x in avv[:6]:
                        dire("   avviso: " + x)
                cambiato = True
            if cp["fase"] == "audit":
                af = p("audit", "cap%s_c%d_audit.json" % (nn(n), ciclo))
                if os.path.exists(af) and cp.get("audit_applicato") != ciclo:
                    d, e = leggi_json(af)
                    err = [e] if e else valida_audit(d, n)
                    if err:
                        dire("P4 cap %d: il file di audit non e' valido:" % n)
                        for x in err[:6]:
                            dire("   - " + x)
                        continue
                    applicate, residui = applica_patch(d, "cap%s_c%d" % (nn(n), ciclo), ciclo)
                    scrivi_json(p("audit", "cap%s_c%d_residui.json" % (nn(n), ciclo)),
                                {"capitolo": n, "ciclo": ciclo, "residui": residui, "applicate": applicate})
                    cp["audit_applicato"] = ciclo
                    cp["gravi_ciclo"] = any(x.get("gravita") in ("bloccante", "alta") for x in d.get("patch", []))
                    err, avv = valuta_capitolo(n, c, macro, bp)
                    dire("P4 cap %d (ciclo %d): %d patch applicate, %d da gestire con P5." % (n, ciclo, len(applicate), len(residui)))
                    if residui or err:
                        cp["fase"] = "p5"
                        cp["errori_aperti"] = bool(err)
                        for x in err[:6]:
                            dire("   - dopo le patch: " + breve(x))
                    else:
                        decidi_dopo_ciclo(cp, c, n, dire)
                    cambiato = True
            elif cp["fase"] == "p5":
                pf = p("audit", "cap%s_c%d_p5.json" % (nn(n), ciclo))
                if os.path.exists(pf):
                    err, avv = valuta_capitolo(n, c, macro, bp)
                    if err:
                        cp["errori_aperti"] = True
                        dire("P5 cap %d: restano %d errori (vedi stato/verifica_cap%s.json)" % (n, len(err), nn(n)))
                        for x in err[:6]:
                            dire("   - " + breve(x))
                    else:
                        cp["errori_aperti"] = False
                        dire("P5 cap %d: correzioni verificate." % n)
                        d, _ = leggi_json(pf)
                        if isinstance(d, dict) and d.get("non_risolti"):
                            cp["note"].append("P5 ciclo %d: problemi non risolti, vedi %s" % (ciclo, rel(pf)))
                            dire("   ATTENZIONE: P5 dichiara problemi non risolti (richiedono la tua decisione): " + rel(pf))
                        decidi_dopo_ciclo(cp, c, n, dire)
                    cambiato = True

    # ---------------- fase globale
    tutti_chiusi = st["p2b"]["verificato"] and all(
        st["capitoli"][str(n)]["fase"] == "chiuso" for n in range(1, n_tot + 1))
    if tutti_chiusi and st["pilota"]["approvato"]:
        g = st["p6"]
        if not g["unito"]:
            cmd_unisci(silenzioso=True)
            g["unito"] = True
            cambiato = True
            dire("Tutti i capitoli sono chiusi: creato stato/manoscritto_unito.md per la revisione globale (P6).")
        elif not g["audit"]:
            d, e = carica_audit_globale()
            if d is not None or e is not None:
                err = [e] if e else valida_audit(d, None)
                if err:
                    dire("P6: il file di audit globale non e' valido:")
                    for x in err[:6]:
                        dire("   - " + x)
                else:
                    applicate, residui = applica_patch(d, "globale", 1)
                    scrivi_json(p("audit", "globale_residui.json"), {"residui": residui, "applicate": applicate})
                    tocc = sorted(set(cap_da_file(x["file"]) for x in d.get("patch", []) if cap_da_file(x["file"])))
                    da_p5 = set(cap_da_file(x["file"]) for x in residui)
                    for n in tocc:
                        bp, _ = carica_bp(n)
                        err, avv = valuta_capitolo(n, c, macro, bp)
                        if err:
                            da_p5.add(n)
                            for x in err[:4]:
                                dire("   - cap %d dopo le patch globali: %s" % (n, breve(x)))
                    g["audit"] = True
                    g["p5_capitoli"] = sorted(x for x in da_p5 if x)
                    if not g["p5_capitoli"]:
                        g["chiuso"] = True
                    cambiato = True
                    dire("P6: %d patch applicate, %d da gestire; capitoli per P5: %s" % (
                        len(applicate), len(residui), g["p5_capitoli"] or "nessuno"))
        elif not g["chiuso"]:
            ancora = []
            for n in g["p5_capitoli"]:
                pf = p("audit", "globale_p5_cap%s.json" % nn(n))
                if os.path.exists(pf):
                    bp, _ = carica_bp(n)
                    err, avv = valuta_capitolo(n, c, macro, bp)
                    if err:
                        ancora.append(n)
                        dire("P5 globale cap %d: restano %d errori." % (n, len(err)))
                        for x in err[:4]:
                            dire("   - " + breve(x))
                else:
                    ancora.append(n)
            g["p5_capitoli"] = ancora
            if not ancora:
                g["chiuso"] = True
                dire("P6: revisione globale chiusa.")
            cambiato = True
        if g["chiuso"] and not st["p7"]["verificato"]:
            ok, msgs = verifica_p7(macro, st)
            for x in msgs:
                dire(x)
            if ok:
                st["p7"]["verificato"] = True
                cambiato = True

    if cambiato:
        salva_stato(st)
        git_commit("libro.py verifica")
    return finisci(out, stampa)


def decidi_dopo_ciclo(cp, c, n, dire):
    if cp.get("gravi_ciclo") and cp["ciclo"] < c.get("max_cicli_audit", 2):
        cp["ciclo"] += 1
        cp["fase"] = "audit"
        cp["audit_applicato"] = 0
        dire("   cap %d: c'erano problemi gravi, serve un nuovo audit (ciclo %d)." % (n, cp["ciclo"]))
    else:
        cp["fase"] = "chiuso"
        cp["errori_aperti"] = False
        dire("   cap %d: CHIUSO." % n)


def finisci(out, stampa):
    if stampa:
        for r in out:
            print(r)
    return out


def carica_commenti():
    """Unisce docente/commenti/capNN.json (e il vecchio docente/commenti.json). Ritorna (dict, errore)."""
    tot = {}
    cart = p("docente", "commenti")
    files = []
    if os.path.isdir(cart):
        files += sorted(os.path.join(cart, f) for f in os.listdir(cart) if f.endswith(".json"))
    if os.path.exists(p("docente", "commenti.json")):
        files.append(p("docente", "commenti.json"))
    for f in files:
        d, e = leggi_json(f)
        if e:
            return None, e
        if not isinstance(d, dict):
            return None, "%s deve essere un oggetto {id_esercizio: commento}" % rel(f)
        tot.update(d)
    return tot, None


def carica_audit_globale():
    """Unisce audit/globale/*.json (e audit/globale_audit.json). (None, None) se non ci sono file."""
    files = []
    cart = p("audit", "globale")
    if os.path.isdir(cart):
        files += sorted(os.path.join(cart, f) for f in os.listdir(cart) if f.endswith(".json"))
    if os.path.exists(p("audit", "globale_audit.json")):
        files.append(p("audit", "globale_audit.json"))
    if not files:
        return None, None
    patch, visti = [], set()
    for f in files:
        d, e = leggi_json(f)
        if e:
            return None, e
        if not isinstance(d, dict) or not isinstance(d.get("patch"), list):
            return None, "%s: deve contenere 'patch' (lista, anche vuota)" % rel(f)
        base = os.path.splitext(os.path.basename(f))[0]
        for x in d["patch"]:
            if isinstance(x, dict):
                x = dict(x)
                idp = str(x.get("id", ""))
                if idp in visti or not idp:
                    idp = base + "_" + idp
                x["id"] = idp
                visti.add(idp)
            patch.append(x)
    return {"verdetto": "ok" if not patch else "da_correggere", "patch": patch}, None


def scrivi_riepilogo_blueprint(macro, bps):
    """Riepilogo compatto di tutti i blueprint + segnali automatici (per P2B)."""
    righe = ["# Riepilogo dei blueprint (generato da scripts/libro.py: NON modificare)", ""]
    intro = {}
    for n in sorted(bps):
        for x in bps[n]["concetti_introdotti"]:
            intro.setdefault(x["termine"].strip().lower(), []).append(n)
    gl = dict((g["termine"].strip().lower(), g["capitolo"]) for g in macro.get("glossario", []))
    segnali = []
    for term, caps in sorted(intro.items()):
        if len(caps) > 1:
            segnali.append("Concetto '%s' introdotto in piu' capitoli: %s" % (term, ", ".join(str(c_) for c_ in caps)))
        if term in gl and gl[term] not in caps:
            segnali.append("Termine '%s': il glossario lo introduce al cap. %d ma i blueprint lo introducono al cap. %s" % (
                term, gl[term], ", ".join(str(c_) for c_ in caps)))
    media = {}
    for n in sorted(bps):
        d = [e["difficolta"] for e in bps[n]["esercizi"]]
        media[n] = sum(d) / float(len(d))
    for n in sorted(bps):
        if n > 1 and media[n] < media[n - 1] - 1.0:
            segnali.append("Difficolta' media degli esercizi in calo: cap. %d = %.1f, cap. %d = %.1f" % (n - 1, media[n - 1], n, media[n]))
    righe.append("## Segnali automatici")
    righe.append("")
    righe.extend(["- " + s for s in segnali] if segnali else ["- nessuno"])
    righe.append("")
    for n in sorted(bps):
        b = bps[n]
        righe.append("## Capitolo %d - %s" % (n, b["titolo"]))
        righe.append("- Obiettivi: " + "; ".join(b["obiettivi"]))
        righe.append("- Concetti introdotti: " + ", ".join(x["termine"] for x in b["concetti_introdotti"]))
        righe.append("- Concetti richiesti: " + (", ".join(b["concetti_richiesti"]) or "-"))
        righe.append("- Funzioni usate: " + (", ".join(f["nome"] for f in b["funzioni_usate"]) or "-"))
        righe.append("- Regole: " + "; ".join("%s: %s" % (r.get("id", ""), str(r.get("enunciato", ""))[:110]) for r in b["regole"]))
        righe.append("- Esercizi: " + "; ".join("%s %s (diff. %s)" % (e["id"], e["titolo"], e["difficolta"]) for e in b["esercizi"]))
        righe.append("")
    scrivi(p("stato", "riepilogo_blueprint.md"), "\n".join(righe))


def verifica_p7(macro, st):
    msgs = []
    c = cfg()
    d, e = carica_commenti()
    ok = True
    if e is None and isinstance(d, dict) and d:
        richiesti = []
        for n in range(1, st["n_capitoli"] + 1):
            bp, _ = carica_bp(n)
            for ex in bp["esercizi"]:
                if ex.get("verificabile", True) is True:
                    richiesti.append(ex["id"])
        mancanti = [i for i in richiesti if not isinstance(d.get(i), str) or len(d[i].strip()) < 20]
        if mancanti:
            ok = False
            msgs.append("P7: mancano commenti (almeno 20 caratteri) per gli esercizi: " + ", ".join(mancanti))
    else:
        ok = False
        msgs.append("P7: " + (e or "mancano i commenti: serve docente/commenti/capNN.json per ogni capitolo"))
    m, e2 = leggi_json(p("apparati", "metadati.json"))
    if e2 is None and isinstance(m, dict):
        for campo in ("titolo", "sottotitolo", "descrizione", "parole_chiave", "livello", "requisiti_software"):
            if not m.get(campo):
                ok = False
                msgs.append("P7: metadati.json: manca '%s'" % campo)
    else:
        ok = False
        msgs.append("P7: " + (e2 or "apparati/metadati.json non valido"))
    if ok:
        cmd_soluzioni(silenzioso=True)
        cmd_indice(silenzioso=True)
        msgs.append("P7: commenti e metadati validi; generati docente/soluzioni_commentate.md e apparati/indice_analitico.md.")
    return ok, msgs


# ----------------------------------------------------------------------------
# Prossimo passo
# ----------------------------------------------------------------------------

PROMPT = {
    "P1": "prompts/P1_macro_scaletta.md",
    "P1R": "prompts/P1R_revisione_macro.md",
    "P2": "prompts/P2_blueprint.md",
    "P2B": "prompts/P2B_coerenza_blueprint.md",
    "P3": "prompts/P3_stesura.md",
    "P4": "prompts/P4_audit.md",
    "P5": "prompts/P5_correzioni.md",
    "P6D": "prompts/P6D_digest.md",
    "P6": "prompts/P6_coerenza_globale.md",
    "P7": "prompts/P7_commenti.md",
    "P7M": "prompts/P7M_metadati.md",
}


def fmt_capitoli(lista):
    """[3,4,5,9] -> '3-5,9'"""
    lista = sorted(set(int(x) for x in lista))
    parti = []
    i = 0
    while i < len(lista):
        j = i
        while j + 1 < len(lista) and lista[j + 1] == lista[j] + 1:
            j += 1
        parti.append(str(lista[i]) if i == j else "%d-%d" % (lista[i], lista[j]))
        i = j + 1
    return ",".join(parti)


def messaggio(codice, **par):
    extra = ""
    for k, v in par.items():
        if isinstance(v, (list, tuple)):
            v = fmt_capitoli(v)
        extra += " %s=%s" % (k, v)
    base = ("Leggi CONVENZIONI.md per intero (in particolare il paragrafo 8 sul lavoro a capitoli), "
            "poi esegui esattamente le istruzioni di %s" % PROMPT[codice])
    return base + (" con" + extra if extra else "") + "."


def lotto(c, codice):
    try:
        return max(1, int(c.get("lotto_capitoli", {}).get(codice, 3)))
    except (TypeError, ValueError):
        return 3


def compito_capitolo(n, cp):
    f = cp["fase"]
    if f == "stesura":
        return 0, "P3", {}
    if f == "audit":
        return 1, "P4", {"CICLO": cp["ciclo"]}
    if f == "p5":
        return 2, "P5", {"SORGENTE": "capitolo", "CICLO": cp["ciclo"]}
    return None


def capitoli_commenti_incompleti(st):
    """Capitoli per cui mancano (o sono troppo brevi) i commenti alle soluzioni."""
    com, _ = carica_commenti()
    com = com if isinstance(com, dict) else {}
    out = []
    for n in range(1, (st["n_capitoli"] or 0) + 1):
        bp, e = carica_bp(n)
        if e:
            continue
        ids = [x["id"] for x in bp["esercizi"] if x.get("verificabile", True) is True]
        if any(not isinstance(com.get(i), str) or len(com[i].strip()) < 20 for i in ids):
            out.append(n)
    return out


def decidi_prossimo(c, st):
    M = c["modelli"]

    def task(codice, capitoli=None, **par):
        pp = {}
        if capitoli is not None:
            pp["CAPITOLI"] = capitoli
        pp.update(par)
        parti = [codice] + ["%s=%s" % (k, fmt_capitoli(v) if isinstance(v, (list, tuple)) else v) for k, v in pp.items()]
        return {"tipo": "agente", "titolo": " ".join(parti), "modello": M[codice],
                "messaggio": messaggio(codice, **pp)}

    def umano(titolo, istruzioni, comando=None):
        return {"tipo": "umano", "titolo": titolo, "istruzioni": istruzioni, "comando": comando}

    if not st["p1"]["verificato"]:
        return task("P1")
    if st["p1"].get("modificato"):
        return umano("Macro-scaletta modificata dopo l'approvazione",
                     "Apri stato/macro_scaletta.json: se la modifica e' voluta riapprova, altrimenti ripristina il file (git).",
                     "python3 scripts/libro.py approva 1")
    if not st["p1"]["approvato"]:
        if not os.path.exists(p("stato", "revisione_p1.md")):
            return task("P1R")
        return umano("CHECKPOINT UMANO 1 - Approva la macro-scaletta",
                     "Leggi stato/macro_scaletta.json (capitoli, obiettivi, glossario, registro) e stato/revisione_p1.md "
                     "(critica di un secondo modello). Ogni errore qui si propaga a tutto il libro: correggi a mano oppure "
                     "cancella stato/revisione_p1.md e rilancia P1 chiedendo le correzioni.",
                     "python3 scripts/libro.py approva 1")
    n_tot = st["n_capitoli"]
    da_fare = [n for n in range(1, n_tot + 1) if st["capitoli"][str(n)]["fase"] == "blueprint"]
    if da_fare:
        return task("P2", da_fare[:lotto(c, "P2")])
    if not st["p2b"]["verificato"]:
        return task("P2B")
    pil = c["capitolo_pilota"]
    if not st["pilota"]["approvato"]:
        t = compito_capitolo(pil, st["capitoli"][str(pil)])
        if t:
            return task(t[1], [pil], **t[2])
        return umano("CHECKPOINT UMANO 2 - Approva il capitolo pilota (%d)" % pil,
                     "Leggi manoscritto/cap%s.md con attenzione (stile, chiarezza, esercizi). Se non va, modifica i prompt "
                     "o CONVENZIONI.md e rifai il capitolo con: python3 scripts/libro.py riapri %d stesura. "
                     "Se va bene, approva: la prima sotto-sezione diventera' l'esempio di stile per tutti gli altri capitoli "
                     "(puoi indicare un altro file: approva pilota manoscritto/cap%s/%s_02.md)." % (nn(pil), pil, nn(pil), nn(pil)),
                     "python3 scripts/libro.py approva pilota")
    cand = []
    for n in range(1, n_tot + 1):
        t = compito_capitolo(n, st["capitoli"][str(n)])
        if t:
            cand.append((n, t))
    if cand:
        if c.get("ordine", "per_passo") == "per_passo":
            minprio = min(t[0] for _, t in cand)
            sel = [(n, t) for n, t in cand if t[0] == minprio]
            prima = sel[0][1]
            stessi = [n for n, t in sel if t[1] == prima[1] and t[2] == prima[2]]
            capitoli = stessi[:lotto(c, prima[1])]
        else:
            capitoli = [cand[0][0]]
            prima = cand[0][1]
        return task(prima[1], capitoli, **prima[2])
    g = st["p6"]
    if not g["audit"]:
        da_digest = [n for n in range(1, n_tot + 1)
                     if not os.path.exists(p("stato", "digest", "cap%s.md" % nn(n)))]
        if da_digest:
            return task("P6D", da_digest[:lotto(c, "P6D")])
        return task("P6")
    if not g["chiuso"]:
        elenco = list(g["p5_capitoli"])
        mancanti = [n for n in elenco if not os.path.exists(p("audit", "globale_p5_cap%s.json" % nn(n)))]
        return task("P5", (mancanti or elenco)[:lotto(c, "P5")], SORGENTE="globale")
    if not st["p7"]["verificato"]:
        da = capitoli_commenti_incompleti(st)
        if da:
            return task("P7", da[:lotto(c, "P7")])
        return task("P7M")
    if not st["finale"]["approvato"]:
        return umano("CHECKPOINT UMANO 3 - Lettura finale e congelamento",
                     "Leggi il libro per intero (manoscritto/cap*.md), docente/soluzioni_commentate.md e apparati/. "
                     "Se qualcosa non va usa: python3 scripts/libro.py riapri <capitolo> stesura. Quando e' tutto a posto approva.",
                     "python3 scripts/libro.py approva finale")
    if not st["fine"]:
        return umano("Costruzione del file finale", "Genera il libro completo in un unico file Markdown.",
                     "python3 scripts/libro.py fine")
    return umano("FINITO", "Il libro e' in consegna/libro_completo.md. Soluzioni per il docente in docente/.", None)


def par_str(par):
    return " ".join("%s=%s" % (k, v) for k, v in par.items())


def stampa_prossimo(t):
    print("")
    print("=" * 72)
    if t["tipo"] == "agente":
        print("PROSSIMO PASSO : " + t["titolo"])
        print("MODELLO        : " + t["modello"])
        print("SESSIONE       : nuova (chiudi la precedente)")
        print("-" * 72)
        print("Incolla in Antigravity questo messaggio:")
        print("")
        print("    " + t["messaggio"])
        print("")
        print("-" * 72)
        print("Quando l'agente ha finito, lancia:  python3 scripts/libro.py avanti")
    else:
        print("PASSO UMANO: " + t["titolo"])
        print("-" * 72)
        print(t["istruzioni"])
        if t.get("comando"):
            print("")
            print("Quando sei pronto:  " + t["comando"])
    print("=" * 72)


def cmd_stato(st=None):
    st = st or carica_stato()
    if not st["p1"]["verificato"]:
        print("Stato: macro-scaletta non ancora valida.")
        return
    macro, _ = carica_macro()
    print("%-4s %-46s %-10s %s" % ("Cap", "Titolo", "Fase", "Ciclo"))
    for n in range(1, st["n_capitoli"] + 1):
        cp = st["capitoli"][str(n)]
        tit = macro["capitoli"][n - 1]["titolo"][:44]
        marca = " *pilota*" if n == cfg()["capitolo_pilota"] else ""
        print("%-4d %-46s %-10s %d%s" % (n, tit, cp["fase"], cp["ciclo"], marca))
    print("Approvazioni: macro-scaletta=%s, pilota=%s, finale=%s" % (
        st["p1"]["approvato"], st["pilota"]["approvato"], st["finale"]["approvato"]))


# ----------------------------------------------------------------------------
# Comandi
# ----------------------------------------------------------------------------

def cmd_avanti(args):
    righe = cmd_verifica(stampa=True)
    st = carica_stato()
    if righe:
        print("")
    if st["p1"]["verificato"]:
        cmd_stato(st)
    stampa_prossimo(decidi_prossimo(cfg(), st))


def cmd_prossimo(args):
    stampa_prossimo(decidi_prossimo(cfg(), carica_stato()))


def cmd_approva(args):
    st = carica_stato()
    what = args.cosa
    if what == "1":
        mp = p("stato", "macro_scaletta.json")
        if not st["p1"]["verificato"]:
            sys.exit("La macro-scaletta non e' ancora valida: lancia prima 'avanti'.")
        st["p1"]["approvato"] = True
        st["p1"]["hash"] = hash_file(mp)
        st["p1"]["modificato"] = False
        salva_stato(st)
        git_commit("macro-scaletta approvata")
        print("Macro-scaletta approvata e 'congelata'. Se la modifichi dopo, i controlli ti avvisano.")
    elif what == "pilota":
        c = cfg()
        pil = c["capitolo_pilota"]
        cp = st["capitoli"].get(str(pil))
        if not cp or cp["fase"] != "chiuso":
            sys.exit("Il capitolo pilota non e' ancora chiuso: lancia 'avanti'.")
        sorgente = args.file or p("manoscritto", "cap%s" % nn(pil), "%s_01.md" % nn(pil))
        if not os.path.isabs(sorgente):
            sorgente = p(sorgente)
        if not os.path.exists(sorgente):
            sys.exit("File non trovato: " + sorgente)
        shutil.copy(sorgente, p("stato", "esempio_stile.md"))
        st["pilota"]["approvato"] = True
        salva_stato(st)
        git_commit("capitolo pilota approvato")
        print("Pilota approvato. Esempio di stile salvato in stato/esempio_stile.md (da ora lo usano tutti i capitoli).")
    elif what == "finale":
        st["finale"]["approvato"] = True
        salva_stato(st)
        git_commit("libro approvato")
        try:
            subprocess.run(["git", "tag", "-f", "libro-congelato"], cwd=RADICE, stdout=PIPE, stderr=PIPE)
        except Exception:
            pass
        print("Libro approvato e congelato. Ora: python3 scripts/libro.py fine")
    else:
        sys.exit("Uso: approva 1 | approva pilota [file] | approva finale")


def cmd_riapri(args):
    st = carica_stato()
    n = str(args.capitolo)
    if n not in st["capitoli"]:
        sys.exit("Capitolo inesistente.")
    fase = args.fase
    if fase not in ("blueprint", "stesura", "audit"):
        sys.exit("Fasi ammesse: blueprint, stesura, audit")
    cp = st["capitoli"][n]
    cp["fase"] = fase
    cp["errori_aperti"] = False
    if fase == "audit":
        cp["ciclo"] = cp["ciclo"] + 1
        cp["audit_applicato"] = 0
    st["p6"] = stato_vuoto()["p6"]
    st["p7"]["verificato"] = False
    st["finale"]["approvato"] = False
    st["fine"] = False
    if fase == "blueprint":
        st["p2b"]["verificato"] = False
    salva_stato(st)
    print("Capitolo %s riaperto alla fase '%s'. Lancia: python3 scripts/libro.py avanti" % (n, fase))


def cmd_controlla_macro(args):
    """Controlla la macro-scaletta SENZA modificare lo stato (sicuro per gli agenti)."""
    m, e = carica_macro()
    if e:
        sys.exit(e)
    err, avv = valida_macro(m, cfg())
    scrivi_json(p("stato", "verifica_p1.json"), {"errori": err, "avvisi": avv})
    print("Macro-scaletta: %d errori, %d avvisi" % (len(err), len(avv)))
    for x in err:
        print("ERRORE : " + x)
    for x in avv:
        print("avviso : " + x)
    sys.exit(1 if err else 0)


def cmd_controlla_bp(args):
    """Controlla il blueprint di un capitolo (e compila le soluzioni) SENZA modificare lo stato."""
    macro, e = carica_macro()
    if e:
        sys.exit(e)
    n = args.capitolo
    bp, e = carica_bp(n)
    if e:
        sys.exit(e)
    err, avv = valida_blueprint(bp, n, macro, cfg())
    if not err:
        e2, a2 = verifica_soluzioni(n, bp, macro)
        err += e2
        avv += a2
    scrivi_json(p("stato", "verifica_bp_cap%s.json" % nn(n)), {"errori": err, "avvisi": avv})
    print("Blueprint capitolo %d: %d errori, %d avvisi" % (n, len(err), len(avv)))
    for x in err:
        print("ERRORE : " + x)
    for x in avv:
        print("avviso : " + x)
    sys.exit(1 if err else 0)


def cmd_controlla(args):
    c = cfg()
    macro, e = carica_macro()
    if e:
        sys.exit(e)
    bp, e = carica_bp(args.capitolo)
    if e:
        sys.exit(e)
    err, avv = valuta_capitolo(args.capitolo, c, macro, bp)
    print("Capitolo %d: %d errori, %d avvisi" % (args.capitolo, len(err), len(avv)))
    for x in err:
        print("ERRORE : " + x)
    for x in avv:
        print("avviso : " + x)
    print("Dettagli in stato/verifica_cap%s.json" % nn(args.capitolo))
    sys.exit(1 if err else 0)


def cmd_unisci(silenzioso=False):
    st = carica_stato()
    parti = []
    for n in range(1, (st["n_capitoli"] or 0) + 1):
        cart = dir_cap(n)
        if not os.path.isdir(cart):
            continue
        for f in sorted(os.listdir(cart)):
            if f.endswith(".md"):
                parti.append("<!-- file: manoscritto/cap%s/%s -->\n\n%s" % (nn(n), f, leggi(os.path.join(cart, f)).strip()))
    scrivi(p("stato", "manoscritto_unito.md"), "\n\n".join(parti) + "\n")
    if not silenzioso:
        print("Creato stato/manoscritto_unito.md")


def cmd_soluzioni(silenzioso=False):
    st = carica_stato()
    com, _ = carica_commenti()
    com = com if isinstance(com, dict) else {}
    out = ["# Soluzioni commentate (solo per il docente)", "",
           "Le soluzioni sono state compilate ed eseguite sui casi di prova del blueprint.", ""]
    for n in range(1, st["n_capitoli"] + 1):
        bp, _ = carica_bp(n)
        out.append("## Capitolo %d - %s" % (n, bp["titolo"]))
        out.append("")
        for e in bp["esercizi"]:
            out.append("### %s - %s" % (e["id"], e["titolo"]))
            out.append("")
            if e.get("verificabile", True) is True:
                files = file_soluzione(e)
                for nm in sorted(files):
                    if len(files) > 1:
                        out.append("**%s**" % nm)
                        out.append("")
                    out.append("```c")
                    out.append(files[nm].rstrip("\n"))
                    out.append("```")
                    out.append("")
                if com.get(e["id"]):
                    out.append(com[e["id"]].strip())
                    out.append("")
            else:
                out.append("Non verificabile automaticamente: " + str(e.get("motivo_non_verificabile", "")))
                out.append("")
    scrivi(p("docente", "soluzioni_commentate.md"), "\n".join(out))
    if not silenzioso:
        print("Creato docente/soluzioni_commentate.md")


def cmd_indice(silenzioso=False):
    st = carica_stato()
    macro, _ = carica_macro()
    sezioni = []
    for n in range(1, st["n_capitoli"] + 1):
        cart = dir_cap(n)
        if not os.path.isdir(cart):
            continue
        for f in sorted(os.listdir(cart)):
            m = re.match(r"(\d\d)_(\d\d)\.md$", f)
            if m and m.group(2) not in ("00", "99"):
                sezioni.append(("%d.%d" % (int(m.group(1)), int(m.group(2))), prosa(leggi(os.path.join(cart, f)))))
    righe = ["# Indice analitico", ""]
    for g in sorted(macro["glossario"], key=lambda x: x["termine"].lower()):
        trovate = [sid for sid, txt in sezioni if re.search(r"(?<!\w)%s(?!\w)" % re.escape(g["termine"]), txt, re.I)]
        if trovate:
            righe.append("- **%s**: %s" % (g["termine"], ", ".join(trovate[:12])))
    righe.append("")
    scrivi(p("apparati", "indice_analitico.md"), "\n".join(righe))
    if not silenzioso:
        print("Creato apparati/indice_analitico.md")


def cmd_fine(args):
    c = cfg()
    st = carica_stato()
    if not st["finale"]["approvato"]:
        sys.exit("Prima approva il libro: python3 scripts/libro.py approva finale")
    mp = p("stato", "macro_scaletta.json")
    if hash_file(mp) != st["p1"]["hash"]:
        sys.exit("La macro-scaletta e' stata modificata dopo l'approvazione.")
    macro, _ = carica_macro()
    meta, _ = leggi_json(p("apparati", "metadati.json"))
    meta = meta or {}
    parti = ["# " + meta.get("titolo", macro["titolo"])]
    if meta.get("sottotitolo"):
        parti.append("### " + meta["sottotitolo"])
    parti.append("")
    if meta.get("descrizione"):
        parti.append(meta["descrizione"])
        parti.append("")
    parti.append("## Indice")
    parti.append("")
    corpo = []
    for n in range(1, st["n_capitoli"] + 1):
        bp, _ = carica_bp(n)
        err, avv = valuta_capitolo(n, c, macro, bp)
        if err:
            sys.exit("Il capitolo %d non supera piu' i controlli: lancia 'controlla %d'." % (n, n))
        testo = leggi(p("manoscritto", "cap%s.md" % nn(n)))
        corpo.append(testo.strip())
        for r in testo.split("\n"):
            if re.match(r"^#\s+Capitolo", r):
                parti.append("- " + r[2:].strip())
            elif re.match(r"^##\s+\d+\.\d+\s", r):
                parti.append("    - " + r[3:].strip())
    parti.append("")
    parti.extend(["\n\n".join(corpo), ""])
    ind = p("apparati", "indice_analitico.md")
    if os.path.exists(ind):
        parti.append(leggi(ind))
    testo = "\n".join(parti)
    if re.search(r"soluzione_riferimento", testo):
        sys.exit("Il libro contiene tracce di soluzioni: controlla.")
    scrivi(p("consegna", "libro_completo.md"), testo)
    st["fine"] = True
    salva_stato(st)
    git_commit("libro completo generato")
    print("Creato consegna/libro_completo.md (%d parole circa)." % len(re.findall(r"\w+", prosa(testo))))


def cmd_diagnosi(args):
    print("Python        : %s" % sys.version.split()[0])
    ok = True
    if sys.version_info < (3, 8):
        print("  ERRORE: serve Python 3.8 o superiore")
        ok = False
    tc = toolchain()
    if tc["exe"]:
        print("Compilatore   : %s %s" % (tc["exe"], tc["std"]))
        print("Sanitizer     : %s" % ("attivo (ASan+UBSan)" if tc["sanitizer"] else "non disponibile (i controlli girano comunque)"))
    else:
        ok = False
        print("Compilatore   : NON TROVATO")
        print("  macOS: esegui 'xcode-select --install'. Linux: installa gcc o clang.")
    if tc["exe"]:
        flags = [tc["std"]]
        prove = [
            ("bool/true/false", "int main(void){bool b=true;return !b;}"),
            ("nullptr", "int main(void){int *p=nullptr;return p!=nullptr;}"),
            ("constexpr", "int main(void){constexpr int x=3;return x-3;}"),
            ("typeof", "int main(void){int a=1;typeof(a) b=1;return b-a;}"),
            ("auto (deduzione di tipo)", "int main(void){auto x=1;return x-1;}"),
            ("letterali binari 0b", "int main(void){return 0b101-5;}"),
            ("separatori di cifre", "int main(void){return 1'000-1000;}"),
            ("[[maybe_unused]]", "int main(void){[[maybe_unused]] int x=1;return 0;}"),
        ]
        sup = {}
        for nome, cod in prove:
            ok2, _ = prova_compilazione(tc["exe"], flags, cod, True)
            sup[nome] = ok2
        print("Novita' C23 supportate dal tuo compilatore:")
        for nome, v in sup.items():
            print("   %-28s %s" % (nome, "si" if v else "NO"))
        scrivi_json(p("stato", "diagnosi.json"), {"compilatore": tc["exe"], "std": tc["std"], "sanitizer": tc["sanitizer"], "c23": sup})
        # autotest della sandbox
        r = compila_ed_esegui('#include <stdio.h>\nint main(void){printf("ciao\\n");return 0;}\n', "")
        t1 = r.get("compila") and norm_output(r.get("stdout")) == "ciao"
        r = compila_ed_esegui("int main(void){int x;return 0;}\n", "")
        t2 = not r.get("compila")
        r = compila_ed_esegui('#include <stdio.h>\nint main(void){char b[8];fgets(b,8,stdin);printf("%s",b);return 0;}\n', "abc\n")
        t3 = r.get("compila") and norm_output(r.get("stdout")) == "abc"
        print("Autotest sandbox: esecuzione=%s, warning bloccanti=%s, input da stdin=%s" % (
            "ok" if t1 else "FALLITO", "ok" if t2 else "non attivi", "ok" if t3 else "FALLITO"))
        ok = ok and t1 and t3
    print("Git           : %s" % ("trovato" if shutil.which("git") else "non trovato (consigliato)"))
    if shutil.which("git") and not os.path.isdir(p(".git")):
        print("  Suggerimento: nella cartella del progetto esegui 'git init' per avere la cronologia.")
    for f in ("CONVENZIONI.md", "PROGRAMMA.md", "config.json") + tuple(PROMPT.values()):
        if not os.path.exists(p(f)):
            print("  MANCA: " + f)
            ok = False
    print("")
    print("Esito diagnosi: " + ("TUTTO OK" if ok else "CI SONO PROBLEMI DA RISOLVERE"))
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description="Strumenti per la pipeline del libro di C")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("avanti", help="verifica quanto prodotto e mostra il prossimo messaggio da incollare")
    sub.add_parser("verifica", help="solo verifica")
    sub.add_parser("prossimo", help="mostra il prossimo passo senza verificare")
    sub.add_parser("stato", help="tabella di avanzamento")
    sub.add_parser("diagnosi", help="controlla l'ambiente (compilatore, C23, file)")
    a = sub.add_parser("approva", help="approva un checkpoint umano")
    a.add_argument("cosa", help="1 | pilota | finale")
    a.add_argument("file", nargs="?", default=None, help="solo per 'pilota': file da usare come esempio di stile")
    r = sub.add_parser("riapri", help="riporta un capitolo a una fase precedente")
    r.add_argument("capitolo", type=int)
    r.add_argument("fase", help="blueprint | stesura | audit")
    k = sub.add_parser("controlla", help="controlla a mano un capitolo")
    k.add_argument("capitolo", type=int)
    sub.add_parser("controlla-macro", help="controlla la macro-scaletta (non modifica lo stato)")
    kb = sub.add_parser("controlla-bp", help="controlla il blueprint di un capitolo (non modifica lo stato)")
    kb.add_argument("capitolo", type=int)
    sub.add_parser("unisci", help="unisce i capitoli in stato/manoscritto_unito.md")
    sub.add_parser("soluzioni", help="rigenera docente/soluzioni_commentate.md")
    sub.add_parser("indice", help="rigenera apparati/indice_analitico.md")
    sub.add_parser("fine", help="genera consegna/libro_completo.md")
    args = ap.parse_args()
    if args.cmd in (None, "avanti"):
        cmd_avanti(args)
    elif args.cmd == "verifica":
        cmd_verifica()
    elif args.cmd == "prossimo":
        cmd_prossimo(args)
    elif args.cmd == "stato":
        cmd_stato()
    elif args.cmd == "diagnosi":
        cmd_diagnosi(args)
    elif args.cmd == "approva":
        cmd_approva(args)
    elif args.cmd == "riapri":
        cmd_riapri(args)
    elif args.cmd == "controlla":
        cmd_controlla(args)
    elif args.cmd == "controlla-macro":
        cmd_controlla_macro(args)
    elif args.cmd == "controlla-bp":
        cmd_controlla_bp(args)
    elif args.cmd == "unisci":
        cmd_unisci()
    elif args.cmd == "soluzioni":
        cmd_soluzioni()
    elif args.cmd == "indice":
        cmd_indice()
    elif args.cmd == "fine":
        cmd_fine(args)


if __name__ == "__main__":
    main()
