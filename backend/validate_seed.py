"""Standalone validator for baku_mutu_seed.json.

Checks:
- no duplicate standar / regulasi ids
- every regulasi_id referenced by a standar exists
- every parameter has kode, satuan, and a valid bound set for its tipe
  (maks -> maks; rentang -> min+maks; negatif -> teks)

Run: python validate_seed.py
Exit code 0 = valid, 1 = problems found.
"""
import json
import os
import sys

SEED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baku_mutu_seed.json")


def validate(path=SEED):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    errors = []

    reg_ids = [r["id"] for r in data.get("regulasi", [])]
    if len(reg_ids) != len(set(reg_ids)):
        errors.append("Duplicate regulasi id found")
    reg_set = set(reg_ids)

    std_ids = [s["id"] for s in data.get("standar", [])]
    dup = {x for x in std_ids if std_ids.count(x) > 1}
    if dup:
        errors.append(f"Duplicate standar id: {sorted(dup)}")

    for s in data.get("standar", []):
        sid = s.get("id")
        if s.get("regulasi_id") not in reg_set:
            errors.append(f"{sid}: regulasi_id '{s.get('regulasi_id')}' tidak ada")
        if s.get("kategori") not in ("air_limbah", "emisi", "udara_ambien"):
            errors.append(f"{sid}: kategori tidak valid '{s.get('kategori')}'")
        for p in s.get("parameter", []):
            pk = p.get("kode")
            if not pk:
                errors.append(f"{sid}: parameter tanpa kode ({p.get('nama')})")
            if p.get("satuan") is None:
                errors.append(f"{sid}:{pk}: tanpa satuan")
            tipe = p.get("tipe")
            if tipe == "maks":
                if p.get("maks") is None:
                    errors.append(f"{sid}:{pk}: tipe maks tanpa nilai maks")
            elif tipe == "rentang":
                if p.get("min") is None or p.get("maks") is None:
                    errors.append(f"{sid}:{pk}: tipe rentang butuh min & maks")
            elif tipe == "negatif":
                if not p.get("teks"):
                    errors.append(f"{sid}:{pk}: tipe negatif tanpa teks")
            else:
                errors.append(f"{sid}:{pk}: tipe tidak dikenal '{tipe}'")

    return errors, len(reg_ids), len(std_ids)


if __name__ == "__main__":
    errs, nreg, nstd = validate()
    print(f"regulasi={nreg} standar={nstd}")
    if errs:
        print(f"INVALID — {len(errs)} masalah:")
        for e in errs[:50]:
            print("  -", e)
        sys.exit(1)
    print("VALID — seed lolos semua pemeriksaan.")
    sys.exit(0)
