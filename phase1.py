#!/usr/bin/env python3
"""Read a signup CSV and print a basic data overview."""

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


def main() -> None:
    parser = argparse.ArgumentParser(description="概览协会招新报名 CSV")
    parser.add_argument("input_csv", type=Path)
    args = parser.parse_args()
    rows = read_csv(args.input_csv)
    blank_counts = {field: sum(not row[field].strip() for row in rows) for field in FIELDS}
    duplicates = len(rows) - len({tuple(row[field] for field in FIELDS) for row in rows})
    print(f"总行数：{len(rows)}")
    print("各列空值数：")
    for field, count in blank_counts.items():
        print(f"  {field}：{count}")
    print(f"完全重复行（重复的额外行数）：{duplicates}")


if __name__ == "__main__":
    main()
