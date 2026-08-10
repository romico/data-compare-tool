"""외부 CSV를 업로드해 컬럼 합계를 비교하는 Streamlit 앱."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from compare import (
    format_number,
    read_columns,
    save_upload,
    sum_column,
)

UPLOAD_DIR = Path(tempfile.gettempdir()) / "data-compare-tool-uploads"

st.set_page_config(page_title="CSV 컬럼 합계 비교", layout="wide")
st.title("CSV 컬럼 합계 비교")
st.caption("외부 CSV 파일을 업로드한 뒤, 각 파일의 컬럼을 선택해 전체 합계를 비교합니다.")


def persist_uploaded(uploaded, side: str) -> Path | None:
    if uploaded is None:
        return None
    dest = UPLOAD_DIR / side / uploaded.name
    # 동일 파일명·크기가 있으면 재사용
    if dest.exists() and dest.stat().st_size == uploaded.size:
        return dest
    return save_upload(uploaded, dest)


@st.cache_data(show_spinner=False)
def cached_columns(path_str: str, mtime: float, encoding: str) -> list[str]:
    return read_columns(Path(path_str), encoding=encoding)


encoding = st.selectbox(
    "인코딩",
    ["utf-8-sig", "utf-8", "cp949", "euc-kr"],
    index=0,
    help="한글이 깨지면 cp949 또는 euc-kr을 선택하세요.",
)

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("파일 A")
    upload_a = st.file_uploader("CSV 업로드 (A)", type=["csv"], key="upload_a")
    path_a = persist_uploaded(upload_a, "a")
    column_a = None
    if path_a is not None:
        st.caption(f"선택됨: `{upload_a.name}` ({upload_a.size:,} bytes)")
        try:
            columns_a = cached_columns(str(path_a), path_a.stat().st_mtime, encoding)
            column_a = st.selectbox("컬럼 선택 (A)", columns_a, key="column_a")
        except Exception as exc:
            st.error(f"파일 A 헤더를 읽지 못했습니다: {exc}")

with col_b:
    st.subheader("파일 B")
    upload_b = st.file_uploader("CSV 업로드 (B)", type=["csv"], key="upload_b")
    path_b = persist_uploaded(upload_b, "b")
    column_b = None
    if path_b is not None:
        st.caption(f"선택됨: `{upload_b.name}` ({upload_b.size:,} bytes)")
        try:
            columns_b = cached_columns(str(path_b), path_b.stat().st_mtime, encoding)
            preferred_b = (
                column_a if column_a is not None and column_a in columns_b else columns_b[0]
            )
            if "column_b" not in st.session_state or st.session_state.column_b not in columns_b:
                st.session_state.column_b = preferred_b
            column_b = st.selectbox("컬럼 선택 (B)", columns_b, key="column_b")
        except Exception as exc:
            st.error(f"파일 B 헤더를 읽지 못했습니다: {exc}")

run = st.button(
    "합계 비교 실행",
    type="primary",
    disabled=path_a is None or path_b is None or column_a is None or column_b is None,
)

if run:
    assert path_a is not None and path_b is not None
    assert column_a is not None and column_b is not None
    assert upload_a is not None and upload_b is not None

    if upload_a.name == upload_b.name and column_a == column_b:
        st.warning("같은 파일명의 같은 컬럼을 비교하고 있습니다.")

    progress = st.progress(0, text="파일 A 합계 계산 중...")
    try:
        sum_a, valid_a, rows_a = sum_column(path_a, column_a, encoding=encoding)
        progress.progress(50, text="파일 B 합계 계산 중...")
        sum_b, valid_b, rows_b = sum_column(path_b, column_b, encoding=encoding)
        progress.progress(100, text="완료")
    except ValueError as exc:
        progress.empty()
        st.error(str(exc))
        st.stop()
    except UnicodeDecodeError:
        progress.empty()
        st.error("인코딩이 맞지 않습니다. 상단에서 cp949 또는 euc-kr을 선택해 보세요.")
        st.stop()

    diff = sum_a - sum_b
    if sum_b != 0:
        diff_pct = diff / sum_b * 100
        diff_pct_text = f"{diff_pct:.6f}%"
    elif sum_a == 0:
        diff_pct_text = "0%"
    else:
        diff_pct_text = "N/A (B 합계 0)"

    if abs(diff) < 1e-9:
        st.success("합계가 일치합니다.")
    else:
        st.error("합계가 일치하지 않습니다.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("A 합계", format_number(sum_a))
    m2.metric("B 합계", format_number(sum_b))
    m3.metric("차이 (A − B)", format_number(diff))
    m4.metric("차이율 (대비 B)", diff_pct_text)

    st.dataframe(
        {
            "항목": ["파일", "컬럼", "전체 행 수", "숫자 행 수", "합계"],
            "A": [upload_a.name, column_a, f"{rows_a:,}", f"{valid_a:,}", format_number(sum_a)],
            "B": [upload_b.name, column_b, f"{rows_b:,}", f"{valid_b:,}", format_number(sum_b)],
        },
        hide_index=True,
        use_container_width=True,
    )
