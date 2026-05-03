import numpy as np
import pandas as pd
import streamlit as st
import re

from edas import calculate_edas
from export_excel import create_excel_file


st.set_page_config(page_title="SPK EDAS", layout="wide")


def build_default_criteria(n_criteria: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Kode": [f"K{i}" for i in range(1, n_criteria + 1)],
            "Nama Kriteria": ["" for _ in range(n_criteria)],
            "Jenis": ["Benefit" for _ in range(n_criteria)],
            "Bobot": [0.0 for _ in range(n_criteria)],
        }
    )


def build_default_matrix(n_alternatives: int, criteria_codes: list[str]) -> pd.DataFrame:
    base = {"Alternatif": [f"A{i}" for i in range(1, n_alternatives + 1)]}
    for code in criteria_codes:
        base[code] = ["" for _ in range(n_alternatives)]
    return pd.DataFrame(base)


def get_rank_description(rank: int) -> str:
    if rank == 1:
        return "Alternatif terbaik"
    if 2 <= rank <= 3:
        return "Sangat direkomendasikan"
    if 4 <= rank <= 10:
        return "Direkomendasikan"
    return "Alternatif pembanding"


def validate_inputs(criteria_df: pd.DataFrame, matrix_df: pd.DataFrame) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    work_criteria = criteria_df.copy()
    work_matrix = matrix_df.copy()

    work_criteria["Kode"] = work_criteria["Kode"].astype(str).str.strip()
    work_criteria["Nama Kriteria"] = work_criteria["Nama Kriteria"].astype(str).str.strip()
    work_criteria["Jenis"] = work_criteria["Jenis"].astype(str).str.strip()
    work_criteria["Bobot"] = pd.to_numeric(work_criteria["Bobot"], errors="coerce")

    if (work_criteria["Kode"] == "").any():
        errors.append("Kode kriteria tidak boleh kosong.")
    if work_criteria["Kode"].duplicated().any():
        errors.append("Terdapat duplikasi kode kriteria.")
    if (work_criteria["Nama Kriteria"] == "").any() or work_criteria["Nama Kriteria"].isna().any():
        errors.append("Nama kriteria tidak boleh kosong.")
    if (work_criteria["Jenis"] == "").any() or work_criteria["Jenis"].isna().any():
        errors.append("Jenis kriteria tidak boleh kosong.")
    if ~work_criteria["Jenis"].isin(["Benefit", "Cost"]).all():
        errors.append("Jenis kriteria hanya boleh Benefit atau Cost.")
    if work_criteria["Bobot"].isna().any():
        errors.append("Bobot kriteria tidak boleh kosong dan harus angka.")

    total_weight = work_criteria["Bobot"].sum()
    if np.isclose(total_weight, 0.0):
        errors.append("Total bobot bernilai 0. Perhitungan tidak dapat dilakukan.")
    elif not np.isclose(total_weight, 1.0):
        warnings.append(f"Total bobot saat ini = {total_weight:.4f}, idealnya 1.00.")

    criteria_codes = work_criteria["Kode"].tolist()
    expected_cols = ["Alternatif"] + criteria_codes
    missing_cols = [c for c in expected_cols if c not in work_matrix.columns]
    if missing_cols:
        errors.append("Kolom matriks keputusan belum sinkron dengan tabel kriteria.")
        return False, errors, warnings

    work_matrix["Alternatif"] = work_matrix["Alternatif"].astype(str).str.strip()
    if (work_matrix["Alternatif"] == "").any():
        errors.append("Nama alternatif tidak boleh kosong.")
    if work_matrix["Alternatif"].duplicated().any():
        warnings.append("Terdapat duplikasi nama alternatif.")

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

    numeric_block = work_matrix[criteria_codes].applymap(_extract_numeric)
    if numeric_block.isna().any().any():
        errors.append("Semua nilai matriks keputusan harus terisi dan bernilai numerik.")

    return len(errors) == 0, errors, warnings


st.title("Sistem Pendukung Keputusan Metode EDAS")
st.subheader("Nama: SAHRUL RAMADHANI | NIM: 244107020058")
st.info("Seluruh data bersifat dinamis dan wajib diinput oleh pengguna. Aplikasi tidak menggunakan data contoh bawaan.")

if "results" not in st.session_state:
    st.session_state["results"] = None

tab1, tab2, tab3, tab4 = st.tabs(["Input Data", "Matriks Keputusan", "Perhitungan EDAS", "Ranking Akhir"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        n_criteria = st.number_input("Jumlah Kriteria", min_value=1, step=1, value=3)
    with col_b:
        n_alternatives = st.number_input("Jumlah Alternatif", min_value=1, step=1, value=5)

    n_criteria = int(n_criteria)
    n_alternatives = int(n_alternatives)

    criteria_default = build_default_criteria(n_criteria)
    criteria_df = st.data_editor(
        criteria_default,
        use_container_width=True,
        num_rows="fixed",
        key="criteria_editor",
        column_config={
            "Kode": st.column_config.TextColumn("Kode"),
            "Nama Kriteria": st.column_config.TextColumn("Nama Kriteria"),
            "Jenis": st.column_config.SelectboxColumn("Jenis", options=["Benefit", "Cost"]),
            "Bobot": st.column_config.NumberColumn("Bobot"),
        },
    )

    criteria_codes = criteria_df["Kode"].astype(str).str.strip().tolist()
    matrix_default = build_default_matrix(n_alternatives, criteria_codes)
    matrix_df = st.data_editor(
        matrix_default,
        use_container_width=True,
        num_rows="fixed",
        key="matrix_editor",
        column_config={
            "Alternatif": st.column_config.TextColumn("Alternatif"),
            **{code: st.column_config.TextColumn(code) for code in criteria_codes},
        },
    )

    can_calculate, errors, warnings = validate_inputs(criteria_df, matrix_df)
    for warning_msg in warnings:
        st.warning(warning_msg)
    for error_msg in errors:
        st.error(error_msg)

    if st.button("Hitung EDAS", type="primary"):
        if not can_calculate:
            st.error("Perhitungan dibatalkan karena masih ada kesalahan input.")
        else:
            try:
                results = calculate_edas(criteria_df, matrix_df)
                ranking_df = results["ranking"].copy()
                ranking_df["Keterangan"] = ranking_df["Ranking"].apply(get_rank_description)
                results["ranking"] = ranking_df
                st.session_state["results"] = results
                st.success("Perhitungan EDAS berhasil dilakukan.")
            except Exception as exc:
                st.session_state["results"] = None
                st.error(f"Terjadi kesalahan saat menghitung EDAS: {exc}")

if st.session_state["results"] is not None:
    results_data = st.session_state["results"]
    best = results_data["ranking"].iloc[0]
    met1, met2, met3, met4 = st.columns(4)
    met1.metric("Alternatif Terbaik", str(best["Alternatif"]))
    met2.metric("Nilai AS Tertinggi", f"{best['AS']:.4f}")
    met3.metric("Jumlah Alternatif", str(len(results_data["matrix"])))
    met4.metric("Jumlah Kriteria", str(len(results_data["criteria"])))

with tab2:
    if st.session_state["results"] is None:
        st.info("Belum ada hasil. Silakan isi data dan klik Hitung EDAS di tab Input Data.")
    else:
        st.dataframe(st.session_state["results"]["matrix"], use_container_width=True)

with tab3:
    if st.session_state["results"] is None:
        st.info("Belum ada hasil perhitungan EDAS.")
    else:
        st.markdown("**Average Solution (AV)**")
        st.dataframe(st.session_state["results"]["av"], use_container_width=True)

        st.markdown("**PDA**")
        st.dataframe(st.session_state["results"]["pda"], use_container_width=True)

        st.markdown("**NDA**")
        st.dataframe(st.session_state["results"]["nda"], use_container_width=True)

        st.markdown("**SP dan SN**")
        st.dataframe(st.session_state["results"]["sp_sn"], use_container_width=True)

        st.markdown("**NSP, NSN, dan AS**")
        st.dataframe(st.session_state["results"]["score"], use_container_width=True)

with tab4:
    if st.session_state["results"] is None:
        st.info("Belum ada ranking akhir.")
    else:
        st.dataframe(st.session_state["results"]["ranking"], use_container_width=True)

        excel_bytes = create_excel_file(st.session_state["results"])
        st.download_button(
            label="Download Hasil Excel",
            data=excel_bytes,
            file_name="hasil_edas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
