"""
BO_AI_5M
AI研究所
run_lab.py

研究所単独テスト
"""

import os
import sys


# BO_AI_5M のルートフォルダを
# Pythonの読み込み対象に追加
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


def main():

    print(
        "===== AI LAB START ====="
    )

    report = (
        make_confidence_report()
    )

    print(report)

    print(
        "===== AI LAB END ====="
    )


if __name__ == "__main__":
    main()
