#!/usr/bin/env python3
"""Read a signup CSV, print an overview, and export invalid applications."""

import argparse
import csv
from collections import Counter
from pathlib import Path

FIELDS = ("姓名", "学号", "邮箱", "志愿1", "志愿2", "推荐人")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = [field for field in FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("CSV 缺少必需字段：" + "、".join(missing))
        return [{field: row.get(field) or "" for field in FIELDS} for row in reader]


def write_issues(path: Path, issues: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["CSV行号", *FIELDS, "问题原因"])
        writer.writeheader()
        writer.writerows(issues)


def main() -> None:
    parser = argparse.ArgumentParser(description="校验协会招新报名 CSV")
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("问题清单.csv"))
    args = parser.parse_args()
    rows = read_csv(args.input_csv)
    blanks = {field: sum(not row[field].strip() for row in rows) for field in FIELDS}
    duplicates = len(rows) - len({tuple(row[field] for field in FIELDS) for row in rows})
    print(f"总行数：{len(rows)}；完全重复行（额外行数）：{duplicates}")
    print("各列空值数：" + "；".join(f"{key} {value}" for key, value in blanks.items()))

    id_counts = Counter(row["学号"] for row in rows if row["学号"])
    issues = []
    for line, row in enumerate(rows, start=2):
        student_id = row["学号"]
        reasons = []
        if not (student_id.isascii() and student_id.isdigit()):
            reasons.append("学号必须为纯数字")
        if row["邮箱"] != f"{student_id}@smbu.edu.cn":
            reasons.append("邮箱必须严格等于学号@smbu.edu.cn")
        if student_id and id_counts[student_id] > 1:
            reasons.append("学号重复报名")
        if reasons:
            issues.append({"CSV行号": str(line), **row, "问题原因": "；".join(reasons)})
    write_issues(args.output, issues)
    print(f"问题行数：{len(issues)}；问题清单：{args.output}")


if __name__ == "__main__":
    main()
