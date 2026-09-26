#!/usr/bin/env python3
"""Summarize, validate, and export association signup CSV files."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

FIELDS = ("姓名", "学号", "邮箱", "志愿1", "志愿2", "推荐人")


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = reader.fieldnames or []
            missing = [field for field in FIELDS if field not in headers]
            if missing:
                raise ValueError("CSV 缺少必需字段：" + "、".join(missing))
            rows = []
            for row in reader:
                rows.append({field: (row.get(field) or "") for field in FIELDS})
            return rows
    except UnicodeDecodeError as exc:
        raise ValueError("文件不是有效的 UTF-8 CSV（支持带 BOM 的 UTF-8）") from exc


def write_csv(path: Path, fields: tuple[str, ...] | list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def process(input_path: Path, output_dir: Path) -> tuple[str, str]:
    rows = read_csv(input_path)

    blank_counts = {
        field: sum(not (row[field] or "").strip() for row in rows)
        for field in FIELDS
    }
    duplicate_rows = len(rows) - len({tuple(row[field] for field in FIELDS) for row in rows})

    student_counts = Counter(row["学号"] for row in rows if row["学号"].strip())
    issues: list[dict[str, str]] = []
    clean: list[dict[str, str]] = []
    for source_row, row in enumerate(rows, start=2):
        reasons: list[str] = []
        student_id = row["学号"]
        email = row["邮箱"]
        if not (student_id.isascii() and student_id.isdigit()):
            reasons.append("学号必须为纯数字")
        if email != f"{student_id}@smbu.edu.cn":
            reasons.append("邮箱必须严格等于学号@smbu.edu.cn")
        if student_id.strip() and student_counts[student_id] > 1:
            reasons.append("学号重复报名")
        if reasons:
            issues.append({"CSV行号": str(source_row), **row, "问题原因": "；".join(reasons)})
        else:
            clean.append(row)

    preference_counts = Counter(row["志愿1"].strip() or "（未填写）" for row in clean)
    both = sum(bool(row["志愿1"].strip()) and bool(row["志愿2"].strip()) for row in clean)
    one = sum(bool(row["志愿1"].strip()) != bool(row["志愿2"].strip()) for row in clean)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "问题清单.csv", ["CSV行号", *FIELDS, "问题原因"], issues)
    write_csv(output_dir / "第一志愿统计.csv", ["第一志愿", "人数"], [
        {"第一志愿": name, "人数": str(count)}
        for name, count in sorted(preference_counts.items(), key=lambda item: (-item[1], item[0]))
    ])
    write_csv(output_dir / "干净数据.csv", list(FIELDS), clean)

    overview = [f"总行数：{len(rows)}", "各列空值数："]
    overview.extend(f"  {field}：{count}" for field, count in blank_counts.items())
    overview.append(f"完全重复行（重复的额外行数）：{duplicate_rows}")
    overview.extend([
        f"问题行数：{len(issues)}",
        f"干净数据行数：{len(clean)}",
        f"两个志愿都填写：{both} 人",
        f"只填写一个志愿：{one} 人",
        f"输出目录：{output_dir}",
    ])
    return "\n".join(overview), "\n".join([
        "第一志愿人数（仅统计干净数据）：",
        *(f"  {name}：{count}" for name, count in sorted(preference_counts.items(), key=lambda item: (-item[1], item[0]))),
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="清洗并统计协会招新报名 CSV")
    parser.add_argument("input_csv", type=Path, help="报名 CSV 文件路径")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("output"), help="输出目录（默认：output）")
    args = parser.parse_args(argv)
    try:
        if args.input_csv.resolve() == args.output_dir.resolve():
            raise ValueError("输出目录不能是输入 CSV 文件")
        overview, statistics = process(args.input_csv, args.output_dir)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    print(overview)
    print(statistics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
