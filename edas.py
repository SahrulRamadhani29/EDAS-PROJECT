import numpy as np
import pandas as pd
import re


def _extract_numeric(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if text == "":
        return np.nan
    normalized = text.replace(",", ".")
    match = re.search(r"[-+]?\d*\.?\d+", normalized)
    if not match:
        return np.nan
    try:
        return float(match.group())
    except ValueError:
        return np.nan


def calculate_edas(criteria_df: pd.DataFrame, matrix_df: pd.DataFrame) -> dict:
    criteria = criteria_df.copy()
    matrix = matrix_df.copy()

    criteria_columns = ["Kode", "Nama Kriteria", "Jenis", "Bobot"]
    matrix_base_columns = ["Alternatif"]

    if not all(column in criteria.columns for column in criteria_columns):
        raise ValueError("Kolom tabel kriteria tidak lengkap.")

    criteria_codes = criteria["Kode"].astype(str).tolist()
    expected_matrix_columns = matrix_base_columns + criteria_codes
    if not all(column in matrix.columns for column in expected_matrix_columns):
        raise ValueError("Kolom tabel matriks keputusan tidak sesuai dengan kode kriteria.")

    criteria["Jenis"] = criteria["Jenis"].astype(str).str.strip().str.title()
    criteria["Bobot"] = pd.to_numeric(criteria["Bobot"], errors="coerce")

    decision_values = matrix[criteria_codes].apply(lambda col: col.map(_extract_numeric))
    if decision_values.isna().any().any():
        raise ValueError(
            "Semua nilai matriks keputusan harus mengandung angka valid. "
            "Contoh input diperbolehkan: '5 KM', '12 unit', '7.5'."
        )

    av_series = decision_values.mean(axis=0)
    if (av_series == 0).any():
        zero_av_cols = av_series[av_series == 0].index.tolist()
        raise ValueError(
            f"Nilai AV bernilai 0 pada kriteria: {', '.join(zero_av_cols)}. "
            "EDAS tidak dapat menghitung pembagian dengan AV=0."
        )

    benefit_mask = criteria.set_index("Kode").loc[criteria_codes, "Jenis"].eq("Benefit")
    av_values = av_series.values
    x_values = decision_values.values

    pda_values = np.zeros_like(x_values, dtype=float)
    nda_values = np.zeros_like(x_values, dtype=float)

    for idx, code in enumerate(criteria_codes):
        av_j = av_values[idx]
        x_j = x_values[:, idx]
        if benefit_mask.loc[code]:
            pda_values[:, idx] = np.maximum(0, (x_j - av_j) / av_j)
            nda_values[:, idx] = np.maximum(0, (av_j - x_j) / av_j)
        else:
            pda_values[:, idx] = np.maximum(0, (av_j - x_j) / av_j)
            nda_values[:, idx] = np.maximum(0, (x_j - av_j) / av_j)

    weights = criteria.set_index("Kode").loc[criteria_codes, "Bobot"].values

    sp_series = (pda_values * weights).sum(axis=1)
    sn_series = (nda_values * weights).sum(axis=1)

    max_sp = sp_series.max() if len(sp_series) else 0
    max_sn = sn_series.max() if len(sn_series) else 0

    nsp_series = np.zeros_like(sp_series, dtype=float) if max_sp == 0 else sp_series / max_sp
    nsn_series = np.ones_like(sn_series, dtype=float) if max_sn == 0 else 1 - (sn_series / max_sn)

    as_series = (nsp_series + nsn_series) / 2

    av_df = pd.DataFrame({"Kode": criteria_codes, "AV": av_series.values})
    pda_df = pd.DataFrame(pda_values, columns=criteria_codes)
    pda_df.insert(0, "Alternatif", matrix["Alternatif"].values)

    nda_df = pd.DataFrame(nda_values, columns=criteria_codes)
    nda_df.insert(0, "Alternatif", matrix["Alternatif"].values)

    sp_sn_df = pd.DataFrame(
        {
            "Alternatif": matrix["Alternatif"].values,
            "SP": sp_series,
            "SN": sn_series,
        }
    )

    score_df = pd.DataFrame(
        {
            "Alternatif": matrix["Alternatif"].values,
            "NSP": nsp_series,
            "NSN": nsn_series,
            "AS": as_series,
        }
    )

    ranking_df = score_df[["Alternatif", "AS"]].copy()
    ranking_df = ranking_df.sort_values(by="AS", ascending=False).reset_index(drop=True)
    ranking_df.insert(0, "Ranking", np.arange(1, len(ranking_df) + 1))

    return {
        "criteria": criteria,
        "matrix": matrix,
        "av": av_df,
        "pda": pda_df,
        "nda": nda_df,
        "sp_sn": sp_sn_df,
        "score": score_df,
        "ranking": ranking_df,
    }
