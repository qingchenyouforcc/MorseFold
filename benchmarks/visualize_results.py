from __future__ import annotations

import csv
from pathlib import Path
from xml.sax.saxutils import escape


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output"
GROUP_SUMMARY_CSV_PATH = OUTPUT_DIR / "experiment_group_summary.csv"
SAMPLE_DETAILS_CSV_PATH = OUTPUT_DIR / "experiment_sample_details.csv"
GROUP_COLOR_MAP = {
    "single_word": "#4C78A8",
    "multi_word_phrase": "#F58518",
    "number_heavy": "#E45756",
    "punctuation_heavy": "#72B7B2",
    "mixed_digits_punctuation": "#54A24B",
    "long_sentence_gt20_words": "#B279A2",
    "paragraph_samples": "#FF9DA6",
    "long_text_gt200_words": "#9D755D",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf6"/>',
    ]


def write_svg(path: Path, lines: list[str]) -> Path:
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def percentile(sorted_values: list[float], ratio: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * ratio
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    weight = position - lower_index
    return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight


def compute_box_stats(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    q1 = percentile(ordered, 0.25)
    median = percentile(ordered, 0.5)
    q3 = percentile(ordered, 0.75)
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    whisker_low = next((value for value in ordered if value >= lower_fence), ordered[0])
    whisker_high = next((value for value in reversed(ordered) if value <= upper_fence), ordered[-1])
    return {
        "min": ordered[0],
        "q1": q1,
        "median": median,
        "q3": q3,
        "max": ordered[-1],
        "whisker_low": whisker_low,
        "whisker_high": whisker_high,
    }


def format_axis_value(value: float, *, as_percent: bool) -> str:
    if as_percent:
        return f"{value:.1f}%"
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def sample_rows_for_points(
    rows: list[dict[str, str]],
    value_key: str,
    *,
    max_points: int = 800,
) -> list[tuple[int, dict[str, str]]]:
    indexed_rows = list(enumerate(rows))
    if len(indexed_rows) <= max_points:
        return indexed_rows

    ranked_rows = sorted(indexed_rows, key=lambda item: (float(item[1][value_key]), item[0]))
    step = (len(ranked_rows) - 1) / (max_points - 1)
    selection_indexes = sorted({round(position * step) for position in range(max_points)})
    return [ranked_rows[index] for index in selection_indexes]


def jitter_offset(seed_text: str, index: int, spread: float) -> float:
    seed = sum((char_index + 1) * ord(char) for char_index, char in enumerate(seed_text)) + index * 131
    normalized = ((seed % 997) / 996) * 2 - 1
    return normalized * spread


def plot_group_box_scatter(
    rows: list[dict[str, str]],
    group_order: list[str],
    value_key: str,
    title: str,
    y_axis_label: str,
    filename: str,
    *,
    as_percent: bool,
) -> Path:
    width = 1320
    height = 760
    margin_left = 95
    margin_right = 40
    margin_top = 80
    margin_bottom = 190
    chart_height = height - margin_top - margin_bottom
    chart_width = width - margin_left - margin_right

    grouped_rows: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped_rows.setdefault(row["group"], []).append(row)

    groups = [group for group in group_order if group in grouped_rows]
    all_values = [
        float(row[value_key]) * 100 if as_percent else float(row[value_key])
        for group in groups
        for row in grouped_rows[group]
    ]
    min_value = min(all_values) if all_values else 0.0
    max_value = max(all_values) if all_values else 1.0
    padding = max((max_value - min_value) * 0.08, 1.0 if as_percent else 0.5)
    axis_min = min_value - padding
    axis_max = max_value + padding
    axis_span = max(axis_max - axis_min, 1.0)
    gap = chart_width / max(len(groups), 1)
    box_width = gap * 0.34
    point_spread = gap * 0.18

    def to_y(value: float) -> float:
        return margin_top + chart_height - chart_height * (value - axis_min) / axis_span

    lines = svg_header(width, height)
    lines.append(f'<text x="{width / 2:.0f}" y="42" text-anchor="middle" font-size="28" fill="#1f2933">{escape(title)}</text>')
    lines.append(
        '<text x="{0}" y="66" text-anchor="middle" font-size="14" fill="#52606d">'
        "Box plot with sampled points overlay (distribution stats use all samples)"
        "</text>".format(width / 2)
    )
    lines.append(
        f'<line x1="{margin_left}" y1="{margin_top + chart_height}" x2="{margin_left + chart_width}" y2="{margin_top + chart_height}" stroke="#334e68" stroke-width="2"/>'
    )
    lines.append(
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + chart_height}" stroke="#334e68" stroke-width="2"/>'
    )

    for tick in range(6):
        value = axis_min + axis_span * tick / 5
        y = to_y(value)
        lines.append(
            f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + chart_width}" y2="{y:.2f}" stroke="#d9e2ec" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{margin_left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="14" fill="#486581">{format_axis_value(value, as_percent=as_percent)}</text>'
        )

    for index, group in enumerate(groups):
        center_x = margin_left + gap * index + gap / 2
        color = GROUP_COLOR_MAP.get(group, "#999999")
        group_values = [
            float(row[value_key]) * 100 if as_percent else float(row[value_key])
            for row in grouped_rows[group]
        ]
        stats = compute_box_stats(group_values)
        display_rows = sample_rows_for_points(grouped_rows[group], value_key)

        lines.append(
            f'<line x1="{center_x:.2f}" y1="{margin_top}" x2="{center_x:.2f}" y2="{margin_top + chart_height}" stroke="#f0f4f8" stroke-width="1"/>'
        )

        for original_index, row in display_rows:
            value = float(row[value_key]) * 100 if as_percent else float(row[value_key])
            cx = center_x + jitter_offset(row["text"], original_index, point_spread)
            cy = to_y(value)
            lines.append(
                f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="2.5" fill="{color}" fill-opacity="0.28" stroke="{color}" stroke-opacity="0.36" stroke-width="0.5"/>'
            )

        q1_y = to_y(stats["q1"])
        q3_y = to_y(stats["q3"])
        median_y = to_y(stats["median"])
        low_y = to_y(stats["whisker_low"])
        high_y = to_y(stats["whisker_high"])
        box_x = center_x - box_width / 2

        lines.append(
            f'<line x1="{center_x:.2f}" y1="{high_y:.2f}" x2="{center_x:.2f}" y2="{q3_y:.2f}" stroke="{color}" stroke-width="2.2"/>'
        )
        lines.append(
            f'<line x1="{center_x:.2f}" y1="{q1_y:.2f}" x2="{center_x:.2f}" y2="{low_y:.2f}" stroke="{color}" stroke-width="2.2"/>'
        )
        lines.append(
            f'<line x1="{center_x - box_width * 0.28:.2f}" y1="{high_y:.2f}" x2="{center_x + box_width * 0.28:.2f}" y2="{high_y:.2f}" stroke="{color}" stroke-width="2.2"/>'
        )
        lines.append(
            f'<line x1="{center_x - box_width * 0.28:.2f}" y1="{low_y:.2f}" x2="{center_x + box_width * 0.28:.2f}" y2="{low_y:.2f}" stroke="{color}" stroke-width="2.2"/>'
        )
        lines.append(
            f'<rect x="{box_x:.2f}" y="{q3_y:.2f}" width="{box_width:.2f}" height="{max(q1_y - q3_y, 1):.2f}" fill="{color}" fill-opacity="0.18" stroke="{color}" stroke-width="2.2" rx="5"/>'
        )
        lines.append(
            f'<line x1="{box_x:.2f}" y1="{median_y:.2f}" x2="{box_x + box_width:.2f}" y2="{median_y:.2f}" stroke="{color}" stroke-width="3"/>'
        )
        lines.append(
            f'<text x="{center_x:.2f}" y="{margin_top + chart_height + 26:.2f}" text-anchor="end" transform="rotate(-28 {center_x:.2f},{margin_top + chart_height + 26:.2f})" font-size="13" fill="#243b53">{escape(group)}</text>'
        )

    lines.append(
        f'<text x="{margin_left + chart_width / 2:.2f}" y="{height - 18}" text-anchor="middle" font-size="16" fill="#243b53">Experiment Group</text>'
    )
    lines.append(
        f'<text x="24" y="{margin_top + chart_height / 2:.2f}" text-anchor="middle" transform="rotate(-90 24,{margin_top + chart_height / 2:.2f})" font-size="16" fill="#243b53">{escape(y_axis_label)}</text>'
    )

    return write_svg(OUTPUT_DIR / filename, lines)


def plot_group_ratio(rows: list[dict[str, str]], ratio_key: str, title: str, filename: str) -> Path:
    width = 1200
    height = 720
    margin_left = 90
    margin_right = 40
    margin_top = 80
    margin_bottom = 170
    chart_height = height - margin_top - margin_bottom
    chart_width = width - margin_left - margin_right

    groups = [row["group"] for row in rows]
    ratios = [float(row[ratio_key]) * 100 for row in rows]
    max_ratio = max(ratios) if ratios else 1.0
    bar_width = chart_width / max(len(groups), 1) * 0.65
    gap = chart_width / max(len(groups), 1)

    lines = svg_header(width, height)
    lines.append(f'<text x="600" y="42" text-anchor="middle" font-size="28" fill="#1f2933">{escape(title)}</text>')
    lines.append(f'<line x1="{margin_left}" y1="{margin_top + chart_height}" x2="{margin_left + chart_width}" y2="{margin_top + chart_height}" stroke="#334e68" stroke-width="2"/>')

    for i in range(6):
        y = margin_top + chart_height - chart_height * i / 5
        value = max_ratio * i / 5
        lines.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + chart_width}" y2="{y:.2f}" stroke="#d9e2ec" stroke-width="1"/>')
        lines.append(f'<text x="{margin_left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="14" fill="#486581">{value:.1f}%</text>')

    for index, (group, ratio) in enumerate(zip(groups, ratios)):
        x = margin_left + gap * index + (gap - bar_width) / 2
        bar_height = chart_height * ratio / max_ratio if max_ratio else 0
        y = margin_top + chart_height - bar_height
        lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" fill="#2f6b7c" rx="4"/>')
        lines.append(f'<text x="{x + bar_width / 2:.2f}" y="{y - 8:.2f}" text-anchor="middle" font-size="13" fill="#102a43">{ratio:.2f}%</text>')
        lines.append(f'<text x="{x + bar_width / 2:.2f}" y="{margin_top + chart_height + 22:.2f}" text-anchor="end" transform="rotate(-28 {x + bar_width / 2:.2f},{margin_top + chart_height + 22:.2f})" font-size="13" fill="#243b53">{escape(group)}</text>')

    return write_svg(OUTPUT_DIR / filename, lines)


def plot_group_reduction(rows: list[dict[str, str]], reduction_key: str, title: str, filename: str) -> Path:
    width = 1200
    height = 720
    margin_left = 90
    margin_right = 40
    margin_top = 80
    margin_bottom = 170
    chart_height = height - margin_top - margin_bottom
    chart_width = width - margin_left - margin_right

    groups = [row["group"] for row in rows]
    reductions = [int(float(row[reduction_key])) for row in rows]
    min_reduction = min(reductions) if reductions else 0
    max_reduction = max(reductions) if reductions else 1
    value_span = max(max_reduction - min_reduction, 1)
    baseline_value = min(0, min_reduction)
    baseline_y = margin_top + chart_height - chart_height * (0 - baseline_value) / value_span
    bar_width = chart_width / max(len(groups), 1) * 0.65
    gap = chart_width / max(len(groups), 1)

    lines = svg_header(width, height)
    lines.append(f'<text x="600" y="42" text-anchor="middle" font-size="28" fill="#1f2933">{escape(title)}</text>')
    lines.append(f'<line x1="{margin_left}" y1="{baseline_y:.2f}" x2="{margin_left + chart_width}" y2="{baseline_y:.2f}" stroke="#334e68" stroke-width="2"/>')

    for i in range(6):
        y = margin_top + chart_height - chart_height * i / 5
        value = baseline_value + value_span * i / 5
        lines.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + chart_width}" y2="{y:.2f}" stroke="#d9e2ec" stroke-width="1"/>')
        lines.append(f'<text x="{margin_left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="14" fill="#486581">{value:.0f}</text>')

    for index, (group, reduction) in enumerate(zip(groups, reductions)):
        x = margin_left + gap * index + (gap - bar_width) / 2
        scaled_height = chart_height * abs(reduction) / value_span if value_span else 0
        y = baseline_y - scaled_height if reduction >= 0 else baseline_y
        color = "#c46a2d" if reduction >= 0 else "#aa3a2a"
        lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{scaled_height:.2f}" fill="{color}" rx="4"/>')
        label_y = y - 8 if reduction >= 0 else y + scaled_height + 18
        lines.append(f'<text x="{x + bar_width / 2:.2f}" y="{label_y:.2f}" text-anchor="middle" font-size="13" fill="#102a43">{reduction}</text>')
        lines.append(f'<text x="{x + bar_width / 2:.2f}" y="{margin_top + chart_height + 22:.2f}" text-anchor="end" transform="rotate(-28 {x + bar_width / 2:.2f},{margin_top + chart_height + 22:.2f})" font-size="13" fill="#243b53">{escape(group)}</text>')

    return write_svg(OUTPUT_DIR / filename, lines)


def plot_sample_scatter(rows: list[dict[str, str]], ratio_key: str, title: str, filename: str) -> Path:
    width = 1200
    height = 720
    margin_left = 90
    margin_right = 230
    margin_top = 80
    margin_bottom = 80
    chart_height = height - margin_top - margin_bottom
    chart_width = width - margin_left - margin_right

    word_counts = [int(row["word_count"]) for row in rows]
    ratios = [float(row[ratio_key]) * 100 for row in rows]
    max_words = max(word_counts) if word_counts else 1
    min_ratio = min(ratios) if ratios else 0.0
    max_ratio = max(ratios) if ratios else 100.0
    ratio_span = max(max_ratio - min_ratio, 1.0)

    lines = svg_header(width, height)
    lines.append(f'<text x="600" y="42" text-anchor="middle" font-size="28" fill="#1f2933">{escape(title)}</text>')
    lines.append(f'<line x1="{margin_left}" y1="{margin_top + chart_height}" x2="{margin_left + chart_width}" y2="{margin_top + chart_height}" stroke="#334e68" stroke-width="2"/>')
    lines.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + chart_height}" stroke="#334e68" stroke-width="2"/>')

    for i in range(6):
        x = margin_left + chart_width * i / 5
        value = max_words * i / 5
        lines.append(f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{margin_top + chart_height}" stroke="#d9e2ec" stroke-width="1"/>')
        lines.append(f'<text x="{x:.2f}" y="{margin_top + chart_height + 24:.2f}" text-anchor="middle" font-size="14" fill="#486581">{value:.0f}</text>')

    for i in range(6):
        y = margin_top + chart_height - chart_height * i / 5
        value = min_ratio + ratio_span * i / 5
        lines.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + chart_width}" y2="{y:.2f}" stroke="#d9e2ec" stroke-width="1"/>')
        lines.append(f'<text x="{margin_left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="14" fill="#486581">{value:.1f}%</text>')

    for row in rows:
        words = int(row["word_count"])
        ratio = float(row[ratio_key]) * 100
        x = margin_left + chart_width * words / max_words if max_words else margin_left
        y = margin_top + chart_height - chart_height * (ratio - min_ratio) / ratio_span
        color = GROUP_COLOR_MAP.get(row["group"], "#999999")
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="{color}" fill-opacity="0.72"/>')

    lines.append(f'<text x="{margin_left + chart_width / 2:.2f}" y="{height - 18}" text-anchor="middle" font-size="16" fill="#243b53">Word Count</text>')
    lines.append(f'<text x="22" y="{margin_top + chart_height / 2:.2f}" text-anchor="middle" transform="rotate(-90 22,{margin_top + chart_height / 2:.2f})" font-size="16" fill="#243b53">Compression Ratio (%)</text>')

    legend_x = margin_left + chart_width + 24
    legend_y = margin_top + 10
    lines.append(f'<text x="{legend_x}" y="{legend_y}" font-size="16" fill="#243b53">Groups</text>')
    for index, (group, color) in enumerate(GROUP_COLOR_MAP.items()):
        if any(row["group"] == group for row in rows):
            y = legend_y + 30 + index * 24
            lines.append(f'<rect x="{legend_x}" y="{y - 10}" width="14" height="14" fill="{color}" rx="3"/>')
            lines.append(f'<text x="{legend_x + 22}" y="{y + 2}" font-size="13" fill="#243b53">{escape(group)}</text>')

    return write_svg(OUTPUT_DIR / filename, lines)


def main() -> None:
    group_rows = read_csv(GROUP_SUMMARY_CSV_PATH)
    sample_rows = read_csv(SAMPLE_DETAILS_CSV_PATH)
    group_order = [row["group"] for row in group_rows]

    outputs = [
        plot_group_ratio(
            group_rows,
            "overall_compression_ratio",
            "Compression Ratio by Experiment Group",
            "group_compression_ratio.svg",
        ),
        plot_group_ratio(
            group_rows,
            "normalized_compression_ratio",
            "Normalized Compression Ratio by Experiment Group",
            "group_normalized_compression_ratio.svg",
        ),
        plot_group_reduction(
            group_rows,
            "total_character_reduction",
            "Total Character Reduction by Experiment Group",
            "group_character_reduction.svg",
        ),
        plot_group_reduction(
            group_rows,
            "total_normalized_reduction",
            "Total Normalized Reduction by Experiment Group",
            "group_normalized_character_reduction.svg",
        ),
        plot_group_box_scatter(
            sample_rows,
            group_order,
            "compression_ratio",
            "Compression Ratio Distribution by Experiment Group",
            "Compression Ratio (%)",
            "group_compression_ratio_box_scatter.svg",
            as_percent=True,
        ),
        plot_group_box_scatter(
            sample_rows,
            group_order,
            "normalized_compression_ratio",
            "Normalized Compression Ratio Distribution by Experiment Group",
            "Normalized Compression Ratio (%)",
            "group_normalized_compression_ratio_box_scatter.svg",
            as_percent=True,
        ),
        plot_group_box_scatter(
            sample_rows,
            group_order,
            "character_reduction",
            "Character Reduction Distribution by Experiment Group",
            "Character Reduction",
            "group_character_reduction_box_scatter.svg",
            as_percent=False,
        ),
        plot_group_box_scatter(
            sample_rows,
            group_order,
            "normalized_reduction",
            "Normalized Character Reduction Distribution by Experiment Group",
            "Normalized Character Reduction",
            "group_normalized_character_reduction_box_scatter.svg",
            as_percent=False,
        ),
        plot_sample_scatter(
            sample_rows,
            "compression_ratio",
            "Sample Compression Ratio vs Word Count",
            "sample_ratio_vs_word_count.svg",
        ),
        plot_sample_scatter(
            sample_rows,
            "normalized_compression_ratio",
            "Sample Normalized Compression Ratio vs Word Count",
            "sample_normalized_ratio_vs_word_count.svg",
        ),
    ]

    for path in outputs:
        print(f"Chart written: {path}")


if __name__ == "__main__":
    main()
