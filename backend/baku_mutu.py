"""Pure, importable & unit-testable logic for the Baku Mutu (effluent/emission
standard) suggestion + evaluation engine. No DB / network access here."""
import re
from typing import Optional

# Statuses used across evaluation
STATUS_SESUAI = "sesuai"        # memenuhi
STATUS_MENDEKATI = "mendekati"  # mendekati batas (masih memenuhi, perlu perhatian)
STATUS_MELEBIHI = "melebihi"    # melebihi baku mutu
STATUS_SATUAN_BEDA = "satuan_tidak_cocok"
STATUS_TIDAK_DINILAI = "tidak_dinilai"

LOQ_TOKENS = ("< loq", "<loq", "loq", "ttd", "tidak terdeteksi", "tt", "nd", "n.d", "<")


def tokenize(text: str) -> list:
    """Lowercase + split into alphanumeric tokens."""
    if not text:
        return []
    return [t for t in re.split(r"[^a-z0-9]+", str(text).lower()) if t]


# ----------------------------- parameter mapping -----------------------------
def map_seed_param(sp: dict, new_id) -> dict:
    """Map a seed parameter object into the monitoring-point parameter shape.
    baku_mutu = upper bound (maks), baku_mutu_min = lower bound (min)."""
    tipe = sp.get("tipe", "maks")
    return {
        "id": new_id(),
        "kode": sp.get("kode"),
        "nama": sp.get("nama"),
        "satuan": sp.get("satuan", "") or "",
        "tipe": tipe,
        "baku_mutu": sp.get("maks"),
        "baku_mutu_min": sp.get("min"),
        "teks": sp.get("teks"),
        "periode": sp.get("periode"),
        "override": False,
    }


# ----------------------------- evaluation -----------------------------
def _is_number(x) -> bool:
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


def evaluate_result(nilai, tipe: str = "maks", baku_mutu=None, baku_mutu_min=None,
                    teks: Optional[str] = None, satuan_meta: str = "",
                    satuan_input: Optional[str] = None, ambang: float = 0.8) -> str:
    """Return status for a single parameter result.

    - tipe 'maks': sesuai if v <= ambang*batas, mendekati if ambang*batas < v <= batas,
      melebihi if v > batas.
    - tipe 'rentang': sesuai if min <= v <= maks else melebihi.
    - tipe 'negatif': sesuai only if the value text is 'negatif'.
    - '< LOQ'/'tidak terdeteksi'/'ttd' treated as memenuhi (sesuai).
    Units: if an input unit is provided and differs from the stored unit, do not
    compare -> STATUS_SATUAN_BEDA.
    """
    # unit guard
    if satuan_input is not None and str(satuan_input).strip() and satuan_meta is not None:
        if str(satuan_input).strip().lower() != str(satuan_meta).strip().lower():
            return STATUS_SATUAN_BEDA

    # empty / missing
    if nilai is None or (isinstance(nilai, str) and nilai.strip() == ""):
        return STATUS_TIDAK_DINILAI

    if tipe == "negatif":
        low = str(nilai).strip().lower()
        return STATUS_SESUAI if low in ("negatif", "negative", "neg") else STATUS_MELEBIHI

    # non-numeric text handling (LOQ / not detected)
    if not _is_number(nilai):
        low = str(nilai).strip().lower()
        if any(tok in low for tok in LOQ_TOKENS):
            return STATUS_SESUAI  # below detection -> memenuhi
        return STATUS_TIDAK_DINILAI

    v = float(nilai)

    if tipe == "rentang":
        lo = float(baku_mutu_min) if baku_mutu_min is not None else None
        hi = float(baku_mutu) if baku_mutu is not None else None
        if lo is not None and v < lo:
            return STATUS_MELEBIHI
        if hi is not None and v > hi:
            return STATUS_MELEBIHI
        return STATUS_SESUAI

    # default tipe == "maks"
    hi = float(baku_mutu) if baku_mutu is not None else None
    lo = float(baku_mutu_min) if baku_mutu_min is not None else None
    if lo is not None and v < lo:
        return STATUS_MELEBIHI
    if hi is None:
        return STATUS_SESUAI
    if v > hi:
        return STATUS_MELEBIHI
    if v >= ambang * hi:
        return STATUS_MENDEKATI
    return STATUS_SESUAI


# ----------------------------- debit / numeric condition parsing -----------------------------
def _norm_numbers(text: str) -> str:
    """Normalise '1.000' -> '1000' (dot thousand separator) and lower-case."""
    if not text:
        return ""
    t = str(text).lower()
    # remove dot used as thousand separator (digit.digit3)
    t = re.sub(r"(\d)\.(\d{3})", r"\1\2", t)
    t = t.replace(",", ".")
    return t


def debit_matches(debit: float, kondisi: str):
    """Evaluate whether `debit` satisfies the numeric range described in `kondisi`.
    Returns True/False, or None when no numeric constraint is parseable."""
    if debit is None:
        return None
    t = _norm_numbers(kondisi)
    if not t:
        return None
    nums = re.findall(r"\d+(?:\.\d+)?", t)
    if not nums:
        return None

    # range "a - b"
    m = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", t)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return a <= debit <= b

    # "a < x <= b"
    m = re.search(r"(\d+(?:\.\d+)?)\s*<\s*[a-z ]*?<=\s*(\d+(?:\.\d+)?)", t)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return a < debit <= b

    ok = None
    for op, val in re.findall(r"(<=|>=|<|>)\s*(\d+(?:\.\d+)?)", t):
        v = float(val)
        res = {
            "<=": debit <= v, ">=": debit >= v, "<": debit < v, ">": debit > v,
        }[op]
        ok = res if ok is None else (ok and res)
    return ok


def fuel_matches(bahan_bakar: str, standar: dict):
    """Soft fuel matching for genset/boiler. Returns True/False/None."""
    if not bahan_bakar:
        return None
    hay = " ".join([
        standar.get("sektor", ""), standar.get("sub_kategori", ""),
        standar.get("kondisi_penerapan", ""), " ".join(standar.get("kata_kunci", []) or []),
    ]).lower()
    bb = bahan_bakar.lower()
    groups = {
        "gas": ["gas"],
        "minyak": ["minyak", "cair", "solar", "diesel", "hsd", "mfo", "bakar cair"],
    }
    wanted = groups.get(bb, [bb])
    present = {k: any(w in hay for w in v) for k, v in groups.items()}
    if not (present["gas"] or present["minyak"]):
        return None  # standar not fuel-specific
    return any(w in hay for w in wanted)


# ----------------------------- relevance scoring -----------------------------
def score_standar(standar: dict, q_tokens: list):
    """Return (score, matched_keywords[]) for free-text relevance."""
    if not q_tokens:
        return 0, []
    kata_kunci = set(k.lower() for k in (standar.get("kata_kunci", []) or []))
    sektor = (standar.get("sektor", "") or "").lower()
    sub = (standar.get("sub_kategori", "") or "").lower()
    score = 0
    matched = []
    for tok in q_tokens:
        hit = False
        if tok in kata_kunci:
            score += 3
            hit = True
        if tok in sektor:
            score += 2
            hit = True
        if tok in sub:
            score += 1
            hit = True
        if hit and tok not in matched:
            matched.append(tok)
    return score, matched


def rank_suggestions(standards: list, regulasi_map: dict, kategori: Optional[str] = None,
                     q: str = "", debit: Optional[float] = None,
                     bahan_bakar: Optional[str] = None, kapasitas_kw: Optional[float] = None,
                     limit: int = 30) -> list:
    """Rank active standards by relevance. Each result carries alasan_cocok, regulasi
    info, perlu_verifikasi and variant hints. Standards confidently excluded by a
    supplied discriminator (e.g. debit) are dropped; unknown/unparseable are kept."""
    q_tokens = tokenize(q)
    has_signal = bool(q_tokens) or debit is not None or bool(bahan_bakar) or kapasitas_kw is not None
    results = []
    for s in standards:
        if s.get("aktif") is False:
            continue
        if kategori and s.get("kategori") != kategori:
            continue

        score, matched = score_standar(s, q_tokens)
        alasan = []
        sektor = s.get("sektor", "")
        signal_hit = score > 0

        # free-text reasons
        for kw in matched:
            alasan.append(f"Kata kunci '{kw}' cocok dengan {sektor}")

        # debit based variant filtering (domestik, tekstil, etc.)
        dm = debit_matches(debit, s.get("kondisi_penerapan", "")) if debit is not None else None
        if debit is not None and dm is False:
            continue  # confidently out of range
        if dm is True:
            score += 4
            signal_hit = True
            alasan.append(f"Debit {debit:g} m3/hari sesuai kondisi: {s.get('kondisi_penerapan')}")

        # fuel based soft matching (genset/boiler)
        fm = fuel_matches(bahan_bakar, s) if bahan_bakar else None
        if bahan_bakar and fm is False:
            continue
        if fm is True:
            score += 3
            signal_hit = True
            alasan.append(f"Bahan bakar '{bahan_bakar}' cocok")

        # capacity soft matching
        if kapasitas_kw is not None:
            cm = debit_matches(kapasitas_kw, s.get("kondisi_penerapan", ""))
            if cm is True:
                score += 2
                signal_hit = True
                alasan.append(f"Kapasitas {kapasitas_kw:g} kW sesuai kondisi")

        # when the user supplied any search signal, hide zero-signal entries
        if has_signal and not signal_hit:
            continue

        reg = regulasi_map.get(s.get("regulasi_id"), {})
        dicabut = (reg.get("status") == "dicabut")
        results.append({
            "id": s.get("id"),
            "kategori": s.get("kategori"),
            "sektor": sektor,
            "sub_kategori": s.get("sub_kategori"),
            "kondisi_penerapan": s.get("kondisi_penerapan"),
            "parameter": s.get("parameter", []),
            "kuantitas_air_limbah_maks": s.get("kuantitas_air_limbah_maks", []),
            "catatan": s.get("catatan", ""),
            "perlu_verifikasi": bool(s.get("perlu_verifikasi")),
            "diverifikasi": bool(s.get("diverifikasi_pada")),
            "regulasi": {"id": reg.get("id"), "judul": reg.get("judul"),
                         "status": reg.get("status"), "mencabut": reg.get("mencabut", [])},
            "regulasi_dicabut": dicabut,
            "skor": score,
            "alasan_cocok": alasan,
        })

    # sort: relevance desc, verified first, needs-verification last as tiebreak
    results.sort(key=lambda r: (r["skor"], r["diverifikasi"], not r["perlu_verifikasi"]), reverse=True)
    return results[:limit]
