#!/usr/bin/env python3
"""Reference Streaming reducer: sorted city|day -> count, mean °C, rain mm."""
from itertools import groupby
import sys


def main():
    rows = (line.rstrip("\n").split("\t") for line in sys.stdin)
    for key, grouped in groupby(rows, key=lambda row: row[0]):
        count, total_temperature, total_rain = 0, 0.0, 0.0
        for row in grouped:
            count += int(row[1])
            total_temperature += float(row[2])
            total_rain += float(row[3])
        if count:
            print(f"{key}\t{count}\t{total_temperature/count:.6f}\t{total_rain:.6f}")


if __name__ == "__main__":
    main()
