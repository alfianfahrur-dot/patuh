"""Unit tests for the pure Baku Mutu logic (no DB/network)."""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import baku_mutu as bm  # noqa: E402

SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "baku_mutu_seed.json")


def _load():
    with open(SEED, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------- evaluation -----------------------------
def test_eval_maks_sesuai_mendekati_melebihi():
    assert bm.evaluate_result(50, "maks", baku_mutu=100, ambang=0.8) == bm.STATUS_SESUAI
    assert bm.evaluate_result(85, "maks", baku_mutu=100, ambang=0.8) == bm.STATUS_MENDEKATI
    assert bm.evaluate_result(120, "maks", baku_mutu=100, ambang=0.8) == bm.STATUS_MELEBIHI
    # exactly at limit = still memenuhi but mendekati
    assert bm.evaluate_result(100, "maks", baku_mutu=100, ambang=0.8) == bm.STATUS_MENDEKATI


def test_eval_rentang_ph():
    assert bm.evaluate_result(7, "rentang", baku_mutu=9, baku_mutu_min=6) == bm.STATUS_SESUAI
    assert bm.evaluate_result(5.5, "rentang", baku_mutu=9, baku_mutu_min=6) == bm.STATUS_MELEBIHI
    assert bm.evaluate_result(9.5, "rentang", baku_mutu=9, baku_mutu_min=6) == bm.STATUS_MELEBIHI


def test_eval_negatif():
    assert bm.evaluate_result("Negatif", "negatif") == bm.STATUS_SESUAI
    assert bm.evaluate_result("Positif", "negatif") == bm.STATUS_MELEBIHI


def test_eval_loq_text_is_sesuai():
    assert bm.evaluate_result("< LOQ", "maks", baku_mutu=5) == bm.STATUS_SESUAI
    assert bm.evaluate_result("tidak terdeteksi", "maks", baku_mutu=5) == bm.STATUS_SESUAI
    assert bm.evaluate_result("ttd", "maks", baku_mutu=5) == bm.STATUS_SESUAI


def test_eval_unit_mismatch():
    # value is fine numerically but unit differs -> do not compare
    st = bm.evaluate_result(2, "maks", baku_mutu=100, satuan_meta="mg/L", satuan_input="kg/ton")
    assert st == bm.STATUS_SATUAN_BEDA


def test_eval_empty_is_not_scored():
    assert bm.evaluate_result("", "maks", baku_mutu=5) == bm.STATUS_TIDAK_DINILAI
    assert bm.evaluate_result(None, "maks", baku_mutu=5) == bm.STATUS_TIDAK_DINILAI


# ----------------------------- debit parsing -----------------------------
def test_debit_matches_domestik():
    assert bm.debit_matches(120, "Volume air limbah domestik > 50 m3/hari") is True
    assert bm.debit_matches(10, "Volume air limbah domestik > 50 m3/hari") is False
    assert bm.debit_matches(10, "3 < volume <= 50 m3/hari") is True
    assert bm.debit_matches(2, "3 < volume <= 50 m3/hari") is False
    assert bm.debit_matches(2, "Volume <= 3 m3/hari") is True


def test_debit_matches_tekstil_ranges_and_thousands():
    assert bm.debit_matches(50, "Debit < 100 m3/hari") is True
    assert bm.debit_matches(500, "Debit 100 - 1.000 m3/hari") is True
    assert bm.debit_matches(1500, "Debit 100 - 1.000 m3/hari") is False
    assert bm.debit_matches(1500, "Debit > 1.000 m3/hari") is True


# ----------------------------- suggestion ranking -----------------------------
def test_rank_suggestion_domestik_variant_by_debit():
    data = _load()
    regmap = {r["id"]: r for r in data["regulasi"]}
    res = bm.rank_suggestions(data["standar"], regmap, kategori="air_limbah", q="hotel", debit=120)
    assert res, "harus ada hasil"
    top = res[0]
    assert "> 50" in (top["sub_kategori"] or "")
    assert any("Debit" in a for a in top["alasan_cocok"])  # reason includes debit match


def test_rank_suggestion_tekstil_variant():
    data = _load()
    regmap = {r["id"]: r for r in data["regulasi"]}
    res = bm.rank_suggestions(data["standar"], regmap, kategori="air_limbah", q="tekstil", debit=500)
    assert res
    assert "100 - 1.000" in (res[0]["sub_kategori"] or "")


def test_rank_hides_zero_signal_when_query_given():
    data = _load()
    regmap = {r["id"]: r for r in data["regulasi"]}
    res = bm.rank_suggestions(data["standar"], regmap, kategori="air_limbah", q="hotel")
    # every returned result should have at least one matched reason or a score > 0
    assert all(r["skor"] > 0 for r in res)


def test_map_seed_param_shapes():
    counter = {"n": 0}

    def _id():
        counter["n"] += 1
        return f"id{counter['n']}"

    data = _load()
    # a domestik standar with pH (rentang) + BOD (maks)
    std = next(s for s in data["standar"] if s["id"] == "AL-DOM-NK-MA-GT50")
    params = [bm.map_seed_param(p, _id) for p in std["parameter"]]
    ph = next(p for p in params if p["kode"] == "pH")
    assert ph["tipe"] == "rentang" and ph["baku_mutu_min"] == 6 and ph["baku_mutu"] == 9
    bod = next(p for p in params if p["kode"] == "BOD5")
    assert bod["tipe"] == "maks" and bod["baku_mutu"] == 30
