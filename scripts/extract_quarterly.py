#!/usr/bin/env python3
"""Extract the last 20 quarterly results for SBCL (consolidated)."""

import argparse
import csv
import html
import os
import re
import urllib.request
from html.parser import HTMLParser


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self._current_row = []
        self._current_cell = []
        self._in_cell = False
        self._skip_tag = None

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._skip_tag = tag
        if self._skip_tag:
            return
        if tag in {"td", "th"}:
            self._in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag):
        if self._skip_tag and tag == self._skip_tag:
            self._skip_tag = None
            return
        if self._skip_tag:
            return
        if tag in {"td", "th"}:
            cell_text = html.unescape("".join(self._current_cell)).strip()
            self._current_row.append(" ".join(cell_text.split()))
            self._in_cell = False
            self._current_cell = []
        elif tag == "tr":
            if self._current_row:
                self.rows.append(self._current_row)
            self._current_row = []

    def handle_data(self, data):
        if self._skip_tag:
            return
        if self._in_cell:
            self._current_cell.append(data)


def fetch_html(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def extract_quarters_table(html_text: str) -> list[list[str]]:
    section_match = re.search(r"<section[^>]+id=\"quarters\"[\s\S]*?</section>", html_text)
    if not section_match:
        raise ValueError("Could not find the quarterly results section in the HTML.")
    section_html = section_match.group(0)
    table_match = re.search(r"<table[\s\S]*?</table>", section_html)
    if not table_match:
        raise ValueError("Could not find the quarterly results table in the HTML section.")

    parser = TableParser()
    parser.feed(table_match.group(0))
    return parser.rows


def build_quarter_rows(rows: list[list[str]], limit: int) -> list[dict[str, str]]:
    if not rows:
        raise ValueError("Quarterly results table is empty.")
    headers = rows[0]
    if len(headers) < 2:
        raise ValueError("Unexpected header format in quarterly results table.")

    quarters = headers[1:]
    metrics = {}
    for row in rows[1:]:
        if not row:
            continue
        metric = row[0]
        if not metric:
            continue
        metrics[metric] = row[1:]

    count = min(limit, len(quarters))
    quarter_rows = []
    for idx in range(count):
        row_data = {"Quarter": quarters[idx]}
        for metric, values in metrics.items():
            row_data[metric] = values[idx] if idx < len(values) else ""
        quarter_rows.append(row_data)
    return quarter_rows


def write_csv(rows: list[dict[str, str]], output_path: str) -> None:
    if not rows:
        raise ValueError("No quarterly data extracted to write.")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default="https://www.screener.in/company/SBCL/consolidated/",
        help="Screener.in company consolidated URL.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of most-recent quarters to extract.",
    )
    parser.add_argument(
        "--output",
        default="data/sbcl_last_20_quarters.csv",
        help="Output CSV path.",
    )
    args = parser.parse_args()

    html_text = fetch_html(args.url)
    table_rows = extract_quarters_table(html_text)
    quarter_rows = build_quarter_rows(table_rows, args.limit)
    write_csv(quarter_rows, args.output)


if __name__ == "__main__":
    main()
