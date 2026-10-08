#!/usr/bin/env python3
"""Reference Hadoop Streaming mapper; not run on Hadoop in this project."""
import csv
from datetime import datetime
import math
import sys


def main():
    for row in csv.reader(sys.stdin):
        if not row or row[0] == "city" or len(row) < 8:
            continue
        try:
            city, stamp = row[:2]
            day = datetime.fromisoformat(stamp).date().isoformat()
            temperature, rain = float(row[2]), float(row[4])
            if not city or "\t" in city or "|" in city or not all(map(math.isfinite, (temperature, rain))):
                continue
            if not -90 <= temperature <= 60 or not 0 <= rain <= 500:
                continue
            print(f"{city}|{day}\t1\t{temperature:.12g}\t{rain:.12g}")
        except (ValueError, IndexError):
            continue


if __name__ == "__main__":
    main()
