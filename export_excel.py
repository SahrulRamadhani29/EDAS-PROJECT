from io import BytesIO

import pandas as pd


def create_excel_file(results: dict) -> bytes:
    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        results["criteria"].to_excel(writer, index=False, sheet_name="Kriteria")
        results["matrix"].to_excel(writer, index=False, sheet_name="Matriks_Keputusan")
        results["av"].to_excel(writer, index=False, sheet_name="AV")
        results["pda"].to_excel(writer, index=False, sheet_name="PDA")
        results["nda"].to_excel(writer, index=False, sheet_name="NDA")
        results["sp_sn"].to_excel(writer, index=False, sheet_name="SP_SN")
        results["score"].to_excel(writer, index=False, sheet_name="NSP_NSN_AS")
        results["ranking"].to_excel(writer, index=False, sheet_name="Ranking")

        workbook = writer.book
        number_format = workbook.add_format({"num_format": "0.0000"})

        numeric_sheets = ["AV", "PDA", "NDA", "SP_SN", "NSP_NSN_AS", "Ranking"]
        for sheet_name in numeric_sheets:
            worksheet = writer.sheets[sheet_name]
            data = results[
                {
                    "AV": "av",
                    "PDA": "pda",
                    "NDA": "nda",
                    "SP_SN": "sp_sn",
                    "NSP_NSN_AS": "score",
                    "Ranking": "ranking",
                }[sheet_name]
            ]
            for col_idx, col_name in enumerate(data.columns):
                if pd.api.types.is_numeric_dtype(data[col_name]):
                    worksheet.set_column(col_idx, col_idx, 15, number_format)
                else:
                    worksheet.set_column(col_idx, col_idx, 20)

    output.seek(0)
    return output.getvalue()
