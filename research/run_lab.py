"""
BO_AI_5M
AI研究所
run_lab.py

研究所単独テスト
"""

from confidence_lab import (
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
