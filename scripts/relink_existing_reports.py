from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
import re


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.models.simulation_result import SimulationResult


PDF_PATTERN = re.compile(r"^rapport_recommandation_pv_(\d{8})_(\d{6})\.pdf$")
TOLERANCE = timedelta(minutes=10)


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is not None and value.tzinfo.utcoffset(value) is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _parse_pdf_timestamp(pdf_path: Path) -> datetime | None:
    match = PDF_PATTERN.match(pdf_path.name)
    if not match:
        return None
    try:
        return datetime.strptime(f"{match.group(1)}_{match.group(2)}", "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def _collect_pdf_files(root: Path) -> list[tuple[datetime, Path]]:
    pdfs: list[tuple[datetime, Path]] = []
    if not root.exists():
        return pdfs

    for pdf_path in root.rglob("rapport_recommandation_pv_*.pdf"):
        if not pdf_path.is_file():
            continue
        pdf_timestamp = _parse_pdf_timestamp(pdf_path)
        if pdf_timestamp is None:
            continue
        pdfs.append((pdf_timestamp, pdf_path))

    pdfs.sort(key=lambda item: (item[0], str(item[1])))
    return pdfs


def _find_pdf_by_filename(root: Path, filename: str | None) -> Path | None:
    if not filename:
        return None

    direct_path = root / filename
    if direct_path.exists():
        return direct_path

    matches = [path for path in root.rglob(filename) if path.is_file()]
    if not matches:
        return None

    return sorted(matches, key=lambda path: str(path))[0]


def _choose_pdf_for_report(
    report_created_at: datetime,
    available_pdfs: list[tuple[datetime, Path]],
    used_paths: set[Path],
) -> Path | None:
    candidates: list[tuple[int, float, datetime, Path]] = []
    for pdf_timestamp, pdf_path in available_pdfs:
        if pdf_path in used_paths:
            continue

        delta_seconds = (pdf_timestamp - report_created_at).total_seconds()
        abs_delta = abs(delta_seconds)
        if abs_delta > TOLERANCE.total_seconds():
            continue

        after_or_near_priority = 0 if delta_seconds >= 0 else 1
        candidates.append((after_or_near_priority, abs_delta, pdf_timestamp, pdf_path))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1], item[2], str(item[3])))
    return candidates[0][3]


def main() -> int:
    reports_root = BACKEND_ROOT / "generated_reports"
    available_pdfs = _collect_pdf_files(reports_root)
    if not available_pdfs:
        print(f"No matching PDFs found under {reports_root}")
        return 0

    db = SessionLocal()
    try:
        reports = (
            db.query(SimulationResult)
            .filter(
                SimulationResult.simulation_type == "dimensioning",
                (
                    SimulationResult.report_pdf_path.is_(None)
                    | SimulationResult.report_pdf_filename.is_(None)
                ),
            )
            .order_by(SimulationResult.created_at.asc(), SimulationResult.id.asc())
            .all()
        )

        used_paths: set[Path] = set()
        linked = 0
        skipped = 0

        for report in reports:
            if report.report_pdf_path:
                skipped += 1
                print("SKIPPED report", report.id, "already linked")
                continue

            created_at = _normalize_datetime(report.created_at)
            if created_at is None:
                skipped += 1
                print("SKIPPED report", report.id, "missing created_at")
                continue

            chosen_pdf = None
            if report.report_pdf_filename:
                direct_path = _find_pdf_by_filename(reports_root, report.report_pdf_filename)
                if direct_path is not None and direct_path not in used_paths:
                    chosen_pdf = direct_path

            if chosen_pdf is None:
                chosen_pdf = _choose_pdf_for_report(created_at, available_pdfs, used_paths)

            if chosen_pdf is None:
                skipped += 1
                print("SKIPPED report", report.id, "no matching PDF found")
                continue

            report.report_pdf_path = str(chosen_pdf)
            report.report_pdf_filename = chosen_pdf.name
            used_paths.add(chosen_pdf)
            linked += 1
            print("LINKED report", report.id, "=>", chosen_pdf.name)

        db.commit()
        print(f"Done. Linked {linked} report(s), skipped {skipped}.")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
