from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from encoder import text_to_morseSimplify
from main import text_to_morse

DATASETS_DIR = ROOT_DIR / "datasets"
OUTPUT_DIR = ROOT_DIR / "output"
BASE_DATASET_PATH = DATASETS_DIR / "base" / "standard_samples.txt"
LONG_DATASET_PATH = DATASETS_DIR / "long" / "long_sentence_samples.txt"
PARAGRAPH_DATASET_PATH = DATASETS_DIR / "paragraph" / "paragraph_samples.txt"
LONG_TEXT_DATASET_PATH = DATASETS_DIR / "long_text" / "long_text_samples.txt"
GROUP_SUMMARY_CSV_PATH = OUTPUT_DIR / "experiment_group_summary.csv"
SAMPLE_DETAILS_CSV_PATH = OUTPUT_DIR / "experiment_sample_details.csv"


def load_dataset(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def format_ratio(value: float) -> str:
    return f"{value:.2%}"


def normalized_morse_length(text: str, morse: str) -> int:
    # Treat each word boundary as a single logical separator so the encoder
    # is not credited for only changing " / " into "/".
    word_count = len(text.split())
    boundary_count = max(word_count - 1, 0)
    return len(morse) - (2 * boundary_count)


def sample_metrics(text: str) -> dict[str, object]:
    morse = text_to_morse(text, word_sep=" / ")
    simplified = text_to_morseSimplify(morse)
    morse_len = len(morse)
    simplified_len = len(simplified)
    reduction = morse_len - simplified_len
    ratio = simplified_len / morse_len if morse_len else 0.0
    word_count = len(text.split())
    normalized_morse_len = normalized_morse_length(text, morse)
    normalized_reduction = normalized_morse_len - simplified_len
    normalized_ratio = simplified_len / normalized_morse_len if normalized_morse_len else 0.0
    return {
        "text": text,
        "word_count": word_count,
        "morse_len": morse_len,
        "simplified_len": simplified_len,
        "reduction": reduction,
        "ratio": ratio,
        "normalized_morse_len": normalized_morse_len,
        "normalized_reduction": normalized_reduction,
        "normalized_ratio": normalized_ratio,
    }


def contains_digit(text: str) -> bool:
    return any(ch.isdigit() for ch in text)


def contains_punctuation(text: str) -> bool:
    return any(not ch.isalnum() and not ch.isspace() for ch in text)


def select_samples(samples: list[str], predicate) -> list[str]:
    return [sample for sample in samples if predicate(sample)]


def limit_samples(samples: list[str], limit: int | None = None) -> list[str]:
    if limit is None:
        return list(samples)
    return list(samples[:limit])


def print_group_report(name: str, samples: list[str]) -> None:
    print(f"[{name}]")
    if not samples:
        print("Samples: 0")
        print()
        return

    metrics = [sample_metrics(sample) for sample in samples]
    total_morse_len = sum(item["morse_len"] for item in metrics)
    total_simplified_len = sum(item["simplified_len"] for item in metrics)
    total_reduction = total_morse_len - total_simplified_len
    total_ratio = total_simplified_len / total_morse_len if total_morse_len else 0.0
    total_normalized_morse_len = sum(item["normalized_morse_len"] for item in metrics)
    total_normalized_reduction = total_normalized_morse_len - total_simplified_len
    total_normalized_ratio = (
        total_simplified_len / total_normalized_morse_len if total_normalized_morse_len else 0.0
    )
    avg_reduction = total_reduction / len(metrics)
    avg_normalized_reduction = total_normalized_reduction / len(metrics)

    best = max(metrics, key=lambda item: item["normalized_reduction"])
    worst = min(metrics, key=lambda item: item["normalized_reduction"])

    print(f"Samples: {len(metrics)}")
    print(f"Total Morse Length: {total_morse_len}")
    print(f"Total Normalized Morse Length: {total_normalized_morse_len}")
    print(f"Total Simplified Length: {total_simplified_len}")
    print(f"Total Character Reduction: {total_reduction}")
    print(f"Total Normalized Reduction: {total_normalized_reduction}")
    print(f"Average Character Reduction: {avg_reduction:.2f}")
    print(f"Average Normalized Reduction: {avg_normalized_reduction:.2f}")
    print(f"Overall Compression Ratio: {format_ratio(total_ratio)}")
    print(f"Normalized Compression Ratio: {format_ratio(total_normalized_ratio)}")
    print(
        f"Best Sample: {best['text']} | normalized_reduction={best['normalized_reduction']} | "
        f"normalized_ratio={format_ratio(best['normalized_ratio'])}"
    )
    print(
        f"Worst Sample: {worst['text']} | normalized_reduction={worst['normalized_reduction']} | "
        f"normalized_ratio={format_ratio(worst['normalized_ratio'])}"
    )
    print()


def build_group_summary(name: str, samples: list[str]) -> dict[str, object]:
    if not samples:
        return {
            "group": name,
            "samples": 0,
            "total_morse_length": 0,
            "total_normalized_morse_length": 0,
            "total_simplified_length": 0,
            "total_character_reduction": 0,
            "total_normalized_reduction": 0,
            "average_character_reduction": 0.0,
            "average_normalized_reduction": 0.0,
            "overall_compression_ratio": 0.0,
            "normalized_compression_ratio": 0.0,
            "best_sample": "",
            "best_reduction": 0,
            "best_ratio": 0.0,
            "worst_sample": "",
            "worst_reduction": 0,
            "worst_ratio": 0.0,
            "best_normalized_reduction": 0,
            "best_normalized_ratio": 0.0,
            "worst_normalized_reduction": 0,
            "worst_normalized_ratio": 0.0,
        }

    metrics = [sample_metrics(sample) for sample in samples]
    total_morse_len = sum(item["morse_len"] for item in metrics)
    total_simplified_len = sum(item["simplified_len"] for item in metrics)
    total_reduction = total_morse_len - total_simplified_len
    total_ratio = total_simplified_len / total_morse_len if total_morse_len else 0.0
    total_normalized_morse_len = sum(item["normalized_morse_len"] for item in metrics)
    total_normalized_reduction = total_normalized_morse_len - total_simplified_len
    total_normalized_ratio = (
        total_simplified_len / total_normalized_morse_len if total_normalized_morse_len else 0.0
    )
    avg_reduction = total_reduction / len(metrics)
    avg_normalized_reduction = total_normalized_reduction / len(metrics)
    best = max(metrics, key=lambda item: item["reduction"])
    worst = min(metrics, key=lambda item: item["reduction"])
    best_normalized = max(metrics, key=lambda item: item["normalized_reduction"])
    worst_normalized = min(metrics, key=lambda item: item["normalized_reduction"])

    return {
        "group": name,
        "samples": len(metrics),
        "total_morse_length": total_morse_len,
        "total_normalized_morse_length": total_normalized_morse_len,
        "total_simplified_length": total_simplified_len,
        "total_character_reduction": total_reduction,
        "total_normalized_reduction": total_normalized_reduction,
        "average_character_reduction": avg_reduction,
        "average_normalized_reduction": avg_normalized_reduction,
        "overall_compression_ratio": total_ratio,
        "normalized_compression_ratio": total_normalized_ratio,
        "best_sample": best["text"],
        "best_reduction": best["reduction"],
        "best_ratio": best["ratio"],
        "worst_sample": worst["text"],
        "worst_reduction": worst["reduction"],
        "worst_ratio": worst["ratio"],
        "best_normalized_reduction": best_normalized["normalized_reduction"],
        "best_normalized_ratio": best_normalized["normalized_ratio"],
        "worst_normalized_reduction": worst_normalized["normalized_reduction"],
        "worst_normalized_ratio": worst_normalized["normalized_ratio"],
    }


def write_group_summary_csv(rows: list[dict[str, object]]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with GROUP_SUMMARY_CSV_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "group",
                "samples",
                "total_morse_length",
                "total_normalized_morse_length",
                "total_simplified_length",
                "total_character_reduction",
                "total_normalized_reduction",
                "average_character_reduction",
                "average_normalized_reduction",
                "overall_compression_ratio",
                "normalized_compression_ratio",
                "best_sample",
                "best_reduction",
                "best_ratio",
                "worst_sample",
                "worst_reduction",
                "worst_ratio",
                "best_normalized_reduction",
                "best_normalized_ratio",
                "worst_normalized_reduction",
                "worst_normalized_ratio",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_sample_details_csv(groups: list[tuple[str, list[str]]]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with SAMPLE_DETAILS_CSV_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "group",
                "text",
                "word_count",
                "morse_length",
                "normalized_morse_length",
                "simplified_length",
                "character_reduction",
                "normalized_reduction",
                "compression_ratio",
                "normalized_compression_ratio",
            ],
        )
        writer.writeheader()
        for group_name, samples in groups:
            for sample in samples:
                metrics = sample_metrics(sample)
                writer.writerow(
                    {
                        "group": group_name,
                        "text": metrics["text"],
                        "word_count": metrics["word_count"],
                        "morse_length": metrics["morse_len"],
                        "normalized_morse_length": metrics["normalized_morse_len"],
                        "simplified_length": metrics["simplified_len"],
                        "character_reduction": metrics["reduction"],
                        "normalized_reduction": metrics["normalized_reduction"],
                        "compression_ratio": metrics["ratio"],
                        "normalized_compression_ratio": metrics["normalized_ratio"],
                    }
                )


def main() -> None:
    base_samples = load_dataset(BASE_DATASET_PATH)
    long_samples = load_dataset(LONG_DATASET_PATH)
    paragraph_samples = load_dataset(PARAGRAPH_DATASET_PATH)
    long_text_samples = load_dataset(LONG_TEXT_DATASET_PATH)
    group_limits = {
        "single_word": 10000,
        "multi_word_phrase": 10000,
        "number_heavy": 10000,
        "punctuation_heavy": 10000,
        "mixed_digits_punctuation": 10000,
        "long_sentence_gt20_words": 1000,
        "paragraph_samples": 200,
    }

    experiment_groups = [
        (
            "single_word",
            limit_samples(
                select_samples(base_samples, lambda s: len(s.split()) == 1),
                group_limits["single_word"],
            ),
        ),
        (
            "multi_word_phrase",
            limit_samples(
                select_samples(base_samples, lambda s: 2 <= len(s.split()) <= 5),
                group_limits["multi_word_phrase"],
            ),
        ),
        (
            "number_heavy",
            limit_samples(select_samples(base_samples, contains_digit), group_limits["number_heavy"]),
        ),
        (
            "punctuation_heavy",
            limit_samples(
                select_samples(base_samples, contains_punctuation),
                group_limits["punctuation_heavy"],
            ),
        ),
        (
            "mixed_digits_punctuation",
            limit_samples(
                select_samples(
                    base_samples,
                    lambda s: contains_digit(s) and contains_punctuation(s),
                ),
                group_limits["mixed_digits_punctuation"],
            ),
        ),
        (
            "long_sentence_gt20_words",
            limit_samples(long_samples, group_limits["long_sentence_gt20_words"]),
        ),
        ("paragraph_samples", limit_samples(paragraph_samples, group_limits["paragraph_samples"])),
        ("long_text_gt200_words", long_text_samples),
    ]

    group_rows: list[dict[str, object]] = []
    for name, samples in experiment_groups:
        print_group_report(name, samples)
        group_rows.append(build_group_summary(name, samples))

    write_group_summary_csv(group_rows)
    write_sample_details_csv(experiment_groups)
    print(f"CSV written: {GROUP_SUMMARY_CSV_PATH}")
    print(f"CSV written: {SAMPLE_DETAILS_CSV_PATH}")


if __name__ == "__main__":
    main()

