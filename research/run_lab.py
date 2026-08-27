"""
BO_AI_5M
AI研究所
run_lab.py

研究所単独テスト
"""

import os
import sys


ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if ROOT_DIR not in sys.path:
    sys.path.insert(
        0,
        ROOT_DIR,
    )


from research.confidence_lab import (
    make_confidence_report,
)

from research.confidence_deep_lab import (
    make_report as make_deep_report,
)

from research.validation_lab import (
    make_report as make_validation_report,
)

from research.walkforward_lab import (
    make_report as make_walkforward_report,
)


def print_separator():

    print()
    print(
        "=============================="
    )
    print()


def main():

    print(
        "===== AI LAB START ====="
    )

    print()
    print(
        make_confidence_report()
    )

    print_separator()

    print(
        make_deep_report()
    )

    print_separator()

    print(
        make_validation_report()
    )

    print_separator()

    print(
        make_walkforward_report()
    )

    print()
    print(
        "===== AI LAB END ====="
    )


if __name__ == "__main__":
    main()
