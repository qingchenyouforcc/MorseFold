[![English](https://img.shields.io/badge/README-English-2f6b7c)](README.md)
[![简体中文](https://img.shields.io/badge/README-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-c46a2d)](README.zh-CN.md)

# Morse Code Simplify

**Please note, this is an experimental algorithm. Not the final version of the algorithm.**
**This algorithm is used for experimental AI iterative testing, and the repository is located at [MorseFold-AI](https://github.com/SwarmGKA/MorseFold-AI)**

A reversible lightweight compression experiment for Morse code sequences: text is first converted into standard Morse code, then transformed into a shorter simplified representation using consecutive equal-length grouping, symbol bias, and alternating-pattern detection, while still supporting full decoding back to the original text.

## Abstract

This project studies a narrow but practical question: although standard Morse code is already a discrete symbol sequence, it still contains visible structural redundancy at the character level, including repeated length patterns, dot-dash bias, and fully alternating structures. Based on these properties, the project implements a reversible intra-group simplification method. Rather than pursuing globally optimal compression, it applies local structural rules with a fallback policy that keeps the raw Morse group whenever simplification is not shorter.

From the current implementation and benchmark outputs in this repository, the method produces consistent character-level savings across single words, phrases, long sentences, paragraphs, and long texts. The implementation uses only the Python standard library, which makes it suitable for teaching demos, small research prototypes, and further algorithm iteration.

## Problem Statement

Standard Morse code has two direct limitations in this context:

- It was designed for transmission robustness, not text compression.
- Even though each symbol is small, total encoded length still grows quickly for long texts.

This project tries to answer two questions:

1. Can standard Morse code be structurally simplified without losing reversibility?
2. Can that simplification produce stable character-level gains across different text scales?

## Method

The core implementation is [`encoder.py`](encoder.py), specifically `text_to_morseSimplify()`. The overall pipeline is:

1. Convert plain text to standard Morse code with [`main.py`](main.py) and `text_to_morse()`.
2. Inside each word, split the Morse stream into groups of consecutive codes with the same length.
3. Compute a group-level rule symbol `RS` for each compressible group.
4. Convert each Morse code in that group into an identifier `ID`.
5. If the compressed group is not shorter than the raw group, keep the raw Morse group.
6. Emit a reversible simplified string.

### Grouping Rule

Inside each word, grouping is based on consecutive Morse codes with identical length. For example:

```text
.... . .-.. .-.. ---
```

is split into:

```text
.... | . | .-.. .-.. | ---
```

Only consecutive codes with the same length can belong to the same group.

### RS Symbol

Each candidate group first produces an `RS` value with the form:

```text
<length><tail>
```

For example: `4-`, `3.`.

Where:

- `length` is the Morse length shared by all codes in the group.
- `tail` is the group bias symbol.

The bias is computed as follows:

- If a Morse code has at least as many `-` as `.`, it is marked as `1`.
- If it has more `.` than `-`, it is marked as `0`.
- If the code is strictly alternating, it is handled as a special regular case.
- If the group has more `1` than `0`, then `tail = -`.
- Otherwise, `tail = .`.

### ID Encoding

After `RS` is determined, each Morse code in the group is converted into an `ID`:

- If `RS` ends with `-`, record the positions of `.`.
- If `RS` ends with `.`, record the positions of `-`.
- Positions are 1-based.
- Multiple positions are concatenated directly as a string.

For example, in a `4-` group:

- `--.- -> 3`
- `---- -> ""`

### Alternating Structure

If a Morse code contains no adjacent repeated symbol from start to end, it is treated as a regular alternating code:

- Codes starting with `-` are encoded as `+`
- Codes starting with `.` are encoded as `-`

For example:

- `-.-. -> +`
- `.-.- -> -`

### Reversible Output Format

The simplified output has the logical form:

```text
ID\ID\...%RS|raw_group|ID\ID\...%RS/...
```

Separators:

- `\`: separates multiple `ID` values inside one compressed group
- `%`: separates `ID` data from `RS`
- `|`: separates groups inside one word
- `/`: separates words

This format is fully decoded by [`decoder.py`](decoder.py) back into standard Morse code and then plain text.

### Fallback Strategy

This is one of the main engineering constraints in the current implementation:

```text
if len(encoded_group) >= len(raw_group):
    keep raw_group
```

So the algorithm is not a forced compression scheme. It only compresses when the result is actually shorter.

## Example

### Example A

Input text:

```text
QC
```

Standard Morse code:

```text
--.- -.-.
```

Simplified encoding:

```text
3\+%4-
```

Explanation:

- Both characters have length `4`, so they form one group.
- The group bias becomes `4-`.
- In `--.-`, the dot is at position `3`, so its identifier is `3`.
- `-.-.` is a regular alternating code, so it is encoded as `+`.

### Example B

Input text:

```text
HELLO WORLD
```

Standard Morse code:

```text
.... . .-.. .-.. --- / .-- --- .-. .-.. -..
```

Simplified encoding:

```text
....|.|2\2%4.|---/1\\-%3-|.-..|-..
```

This shows that simplification is not applied uniformly character by character. Each candidate group inside a word is evaluated independently, so some groups are compressed and others remain raw.

## Demo

### 1. Text Encoding Demo

```powershell
python main.py
```

The program prints:

- Standard Morse code
- Simplified encoding
- Both lengths
- Character reduction
- Compression ratio

### 2. Simplified-Code Decoding Demo

```powershell
python decoder.py
```

The program prints:

- Decoded standard Morse code
- Decoded plain text

### 3. Python API Demo

```python
from main import text_to_morse
from encoder import text_to_morseSimplify
from decoder import simplified_to_morse, simplified_to_text

text = "HELLO WORLD"
morse = text_to_morse(text)
simplified = text_to_morseSimplify(morse)

print(morse)
print(simplified)
print(simplified_to_morse(simplified))
print(simplified_to_text(simplified))
```

## Experimental Setup

Benchmark scripts are under [`benchmarks/`](benchmarks/):

- [`benchmarks/benchmark_experiments.py`](benchmarks/benchmark_experiments.py): unified experiment entry point, generates summary CSV files
- [`benchmarks/visualize_results.py`](benchmarks/visualize_results.py): converts CSV outputs into SVG charts
- [`benchmarks/benchmark_dataset.py`](benchmarks/benchmark_dataset.py): base-sample statistics
- [`benchmarks/benchmark_long_sentences.py`](benchmarks/benchmark_long_sentences.py): long-sentence statistics
- [`benchmarks/benchmark_paragraphs.py`](benchmarks/benchmark_paragraphs.py): paragraph statistics
- [`benchmarks/benchmark_long_texts.py`](benchmarks/benchmark_long_texts.py): long-text statistics

Datasets are stored under [`datasets/`](datasets/):

- `base`: short baseline samples
- `long`: long-sentence samples
- `paragraph`: paragraph samples
- `long_text`: extra-long text samples

Run:

```powershell
python benchmarks/benchmark_experiments.py
python benchmarks/visualize_results.py
```

Outputs are written to [`output/`](output/).

## Results Overview

The following numbers come from the current repository output file [`output/experiment_group_summary.csv`](output/experiment_group_summary.csv).

| Group | Samples | Compression Ratio | Normalized Compression Ratio | Total Reduction |
| --- | ---: | ---: | ---: | ---: |
| single_word | 10000 | 84.70% | 84.70% | 46614 |
| multi_word_phrase | 10000 | 77.95% | 83.00% | 214705 |
| number_heavy | 10000 | 77.86% | 82.90% | 216753 |
| punctuation_heavy | 10000 | 77.86% | 82.90% | 216823 |
| mixed_digits_punctuation | 10000 | 77.86% | 82.91% | 216826 |
| long_sentence_gt20_words | 1000 | 85.99% | 93.60% | 123325 |
| paragraph_samples | 200 | 85.45% | 94.14% | 58951 |
| long_text_gt200_words | 10 | 86.12% | 94.88% | 6626 |

Notes:

- Lower `Compression Ratio` is better; it means the simplified representation occupies a smaller fraction of the original Morse string.
- `Normalized Compression Ratio` removes the formatting advantage of replacing `" / "` with `"/"`, so it better isolates the algorithmic gain.

From the current results:

- Shorter and more structured samples show clearer gains.
- As texts grow longer, normalized compression ratios move closer to `1`, which suggests that fixed separator and control overhead is being amortized.
- The method still shows positive savings on long sentences, paragraphs, and long texts, but the gains are smaller than in highly repetitive short samples.

## Visualization

### Compression Ratio by Group

![Compression Ratio](output/group_normalized_compression_ratio.svg)

### Distribution by Group

![Box Scatter](output/group_normalized_compression_ratio_box_scatter.svg)

### Sample-Level Trend

![Sample Trend](output/sample_normalized_ratio_vs_word_count.svg)

These charts are suitable for reports, demos, presentations, or a repository landing page.

## Code Organization

```text
morsecode_simplify/
├─ main.py
├─ encoder.py
├─ decoder.py
├─ benchmarks/
├─ datasets/
└─ output/
```

Module roles:

- [`main.py`](main.py): plain text to standard Morse code; CLI encoding entry point
- [`encoder.py`](encoder.py): standard Morse code to simplified encoding
- [`decoder.py`](decoder.py): simplified encoding back to Morse code and plain text
- [`benchmarks/`](benchmarks/): experiment statistics and chart generation

## Engineering Rules Observed in Code

The current codebase follows these visible implementation conventions:

- Python standard library only, with no third-party dependencies
- Public functions validate `str` inputs
- Invalid inputs raise `TypeError` or `ValueError`
- Type annotations are used throughout
- Files are read with `utf-8`
- Benchmark scripts use `pathlib.Path`
- Both CLI usage and module import usage are supported

## Limitations

The current method still has clear boundaries:

- Compression is local to groups, not globally optimal
- The supported character set is mainly English letters, digits, and common English punctuation
- Gains can be limited for irregular Morse sequences
- `ID` values are direct position concatenations, which can still be redundant for longer code lengths
- Evaluation currently focuses on character length, not stricter information-theoretic metrics

## Future Work

Possible next steps include:

- stronger reuse across groups instead of only intra-group compression
- statistical or dictionary-based handling of high-frequency patterns
- a more compact meta-encoding for `RS` and `ID`
- systematic comparisons against alternatives such as RLE-style or Huffman-style approaches
- more formal metrics such as entropy estimates, decoding complexity, and throughput

## Environment

- Python 3.10+

## Reproducibility

The current repository supports the full round trip:

```text
text -> morse -> simplified -> morse -> text
```

Using the included datasets and scripts, the project can reproduce benchmark CSV files and SVG charts directly. That makes it suitable for:

- algorithm coursework
- small paper prototypes
- encoding-rule demos
- GitHub project showcases
