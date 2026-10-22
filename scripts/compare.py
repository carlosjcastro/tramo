import sys
from pathlib import Path

from app.container import get_service


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def main(source_path: str, target_path: str) -> None:
    report = get_service().analyze(read(source_path), read(target_path))
    for match in report.matches:
        print(f"{match.status.value:<14} {match.score:.2f}  {match.target.text}")
    print(f"\nCobertura {report.coverage:.0%}  {report.verdict.value}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
