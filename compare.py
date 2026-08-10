"""CSV 컬럼 합계 비교 유틸."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import BinaryIO, TextIO


def detect_open(path: Path, encoding: str = "utf-8-sig") -> TextIO:
    return open(path, "r", encoding=encoding, newline="")


def read_columns_from_text(fh: TextIO) -> list[str]:
    reader = csv.reader(fh)
    header = next(reader)
    return [c.strip() for c in header]


def read_columns(path: Path, encoding: str = "utf-8-sig") -> list[str]:
    with detect_open(path, encoding) as fh:
        return read_columns_from_text(fh)


def read_columns_bytes(data: bytes, encoding: str = "utf-8-sig") -> list[str]:
    with io.TextIOWrapper(io.BytesIO(data), encoding=encoding, newline="") as fh:
        return read_columns_from_text(fh)


def sum_column_from_text(fh: TextIO, column: str, source_name: str = "file") -> tuple[float, int, int]:
    """컬럼 합계를 계산한다.

    Returns:
        (합계, 유효 숫자 행 수, 전체 데이터 행 수)
    """
    reader = csv.DictReader(fh)
    if reader.fieldnames is None or column not in reader.fieldnames:
        raise ValueError(f"컬럼 '{column}'을(를) 찾을 수 없습니다: {source_name}")

    total = 0.0
    valid = 0
    rows = 0

    for row in reader:
        rows += 1
        raw = row.get(column)
        if raw is None:
            continue
        value = raw.strip().replace(",", "")
        if value == "":
            continue
        try:
            total += float(value)
            valid += 1
        except ValueError:
            continue

    return total, valid, rows


def sum_column(path: Path, column: str, encoding: str = "utf-8-sig") -> tuple[float, int, int]:
    with detect_open(path, encoding) as fh:
        return sum_column_from_text(fh, column, path.name)


def sum_column_bytes(
    data: bytes, column: str, source_name: str = "upload", encoding: str = "utf-8-sig"
) -> tuple[float, int, int]:
    with io.TextIOWrapper(io.BytesIO(data), encoding=encoding, newline="") as fh:
        return sum_column_from_text(fh, column, source_name)


def format_number(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.6f}".rstrip("0").rstrip(".")


def save_upload(file_obj: BinaryIO, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    file_obj.seek(0)
    with open(dest, "wb") as out:
        while True:
            chunk = file_obj.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    return dest
