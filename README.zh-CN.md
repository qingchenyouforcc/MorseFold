[![English](https://img.shields.io/badge/README-English-2f6b7c)](README.md)
[![简体中文](https://img.shields.io/badge/README-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-c46a2d)](README.zh-CN.md)

# Morse Code Simplify

**请注意，这是一个实验算法。不是算法的最终版本。**
**该算法用于AI迭代测试，存储库位于[MorseFold-AI](https://github.com/SwarmGKA/MorseFold-AI)**

一种面向摩斯码序列的可逆轻量压缩实验：先将文本映射为标准摩斯码，再基于“连续同长度分组 + 符号偏向 + 规则交替结构”生成更短的简化表示，并支持完整解码回原始文本。

## Abstract

本项目研究一个很具体的问题：标准摩斯码本身已经是离散符号序列，但在字符级仍存在明显结构冗余，例如相同长度的连续模式、点划比例偏向，以及严格交替的规则结构。基于这些特征，项目提出了一种可逆的组内简化编码方法。该方法不追求全局最优压缩，而是通过局部规则压缩和“收益不足即回退”的策略，在保证解码稳定性的前提下，尽量缩短编码长度。

从当前实现与仓库内实验结果看，该方法在单词、短语、长句、段落和长文本场景中都能稳定获得一定压缩收益，且无需第三方依赖，便于教学、演示和后续算法迭代。

## Problem Statement

标准摩斯码有两个直接问题：

- 它是为可传输性设计的，不是为文本压缩设计的
- 字符之间虽然短小，但长文本下总长度仍然显著增长

本项目尝试回答两个问题：

1. 是否能在不破坏可逆性的前提下，对标准摩斯码做结构化简化？
2. 这种简化在不同文本尺度下是否能稳定产生字符级收益？

## Method

核心实现位于 [`encoder.py`](encoder.py) 的 `text_to_morseSimplify()`，整体流程如下：

1. 使用 [`main.py`](main.py) 中的 `text_to_morse()` 将文本转为标准摩斯码
2. 在每个单词内部，按“连续且长度相同”的摩斯码序列分组
3. 对满足条件的组计算组级规则符号 `RS`
4. 将组内每个摩斯码转换为位置标识 `ID`
5. 若压缩后不比原始组更短，则回退为原始摩斯组
6. 输出可逆的简化编码串

### Grouping Rule

每个单词内部按连续同长度分组。例如：

```text
.... . .-.. .-.. ---
```

会被划分为：

```text
.... | . | .-.. .-.. | ---
```

只有“连续且长度一致”的码元才会进入同一组。

### RS Symbol

每个候选组先生成一个 `RS`，格式为：

```text
<length><tail>
```

例如 `4-`、`3.`。

其中：

- `length` 是组内每个摩斯码的长度
- `tail` 是组偏向符号

组偏向的计算方式：

- 若某个摩斯码中 `-` 数量大于等于 `.`，记为 `1`
- 若 `.` 数量大于 `-`，记为 `0`
- 若该码是严格交替结构，也按特殊规则参与判断
- 组内 `1` 多于 `0`，则 `tail = -`
- 否则 `tail = .`

### ID Encoding

组确定 `RS` 后，为每个摩斯码生成 `ID`：

- 若 `RS` 末尾为 `-`，记录 `.` 出现的位置
- 若 `RS` 末尾为 `.`，记录 `-` 出现的位置
- 位置从 `1` 开始编号
- 多个位置直接拼接成字符串

例如在 `4-` 组中：

- `--.- -> 3`
- `---- -> ""`

### Alternating Structure

若一个摩斯码从头到尾没有相邻重复字符，则记为规则交替码：

- 以 `-` 开头记为 `+`
- 以 `.` 开头记为 `-`

例如：

- `-.-. -> +`
- `.-.- -> -`

### Reversible Output Format

简化编码的逻辑结构为：

```text
ID\ID\...%RS|raw_group|ID\ID\...%RS/...
```

分隔符含义：

- `\`：组内多个 `ID`
- `%`：`ID` 与 `RS` 的分界
- `|`：单词内多个分组
- `/`：单词边界

该格式由 [`decoder.py`](decoder.py) 完整解码回标准摩斯码与普通文本。

### Fallback Strategy

这也是当前实现最重要的工程约束之一：

```text
if len(encoded_group) >= len(raw_group):
    keep raw_group
```

也就是说，算法不是“强制压缩”，而是“有收益才压缩”。这保证了输出不会因为附加元信息而整体变长。

## Example

### Example A

输入文本：

```text
QC
```

标准摩斯码：

```text
--.- -.-.
```

简化编码：

```text
3\+%4-
```

解释：

- 两个字符长度都为 `4`，因此可分为同一组
- 组偏向结果为 `4-`
- `--.-` 中 `.` 在第 `3` 位，编码为 `3`
- `-.-.` 为规则交替码，编码为 `+`

### Example B

输入文本：

```text
HELLO WORLD
```

标准摩斯码：

```text
.... . .-.. .-.. --- / .-- --- .-. .-.. -..
```

简化编码：

```text
....|.|2\2%4.|---/1\\-%3-|.-..|-..
```

这说明压缩并不是逐字符统一进行，而是对每个单词内部的候选组分别判断，部分组压缩，部分组保持原样。

## Demo

### 1. 文本编码演示

```powershell
python main.py
```

程序会输出：

- 标准摩斯码
- 简化编码
- 两者长度
- 字符减少量
- 压缩率

### 2. 简化编码解码演示

```powershell
python decoder.py
```

程序会输出：

- 解码后的标准摩斯码
- 解码后的文本

### 3. Python API 演示

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

实验脚本位于 [`benchmarks/`](benchmarks/)：

- [`benchmarks/benchmark_experiments.py`](benchmarks/benchmark_experiments.py)：统一实验入口，生成汇总 CSV
- [`benchmarks/visualize_results.py`](benchmarks/visualize_results.py)：将 CSV 生成 SVG 图表
- [`benchmarks/benchmark_dataset.py`](benchmarks/benchmark_dataset.py)：基础样本统计
- [`benchmarks/benchmark_long_sentences.py`](benchmarks/benchmark_long_sentences.py)：长句统计
- [`benchmarks/benchmark_paragraphs.py`](benchmarks/benchmark_paragraphs.py)：段落统计
- [`benchmarks/benchmark_long_texts.py`](benchmarks/benchmark_long_texts.py)：长文本统计

数据集位于 [`datasets/`](datasets/)：

- `base`：基础短样本
- `long`：长句样本
- `paragraph`：段落样本
- `long_text`：超长文本样本

运行方式：

```powershell
python benchmarks/benchmark_experiments.py
python benchmarks/visualize_results.py
```

输出文件位于 [`output/`](output/)。

## Results Overview

以下结果来自当前仓库内已有实验输出 [`output/experiment_group_summary.csv`](output/experiment_group_summary.csv)。

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

说明：

- `Compression Ratio` 越低越好，表示简化编码占原标准摩斯码的比例
- `Normalized Compression Ratio` 会扣除 `" / "` 与 `"/"` 的格式差异，更接近算法本身带来的收益

从当前结果可以看到：

- 短样本和结构化样本上，压缩收益比较明显
- 文本越长，归一化压缩率越接近 `1`，说明分隔符和控制信息的固定开销逐步被摊薄
- 项目在长句、段落、长文本场景下仍保持正收益，但收益低于“高重复、高局部规律”的短样本组

## Visualization

### Compression Ratio by Group

![Compression Ratio](output/group_normalized_compression_ratio.svg)

### Distribution by Group

![Box Scatter](output/group_normalized_compression_ratio_box_scatter.svg)

### Sample-Level Trend

![Sample Trend](output/sample_normalized_ratio_vs_word_count.svg)

这些图适合直接用于项目汇报、答辩展示或 README 首页演示。

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

模块职责：

- [`main.py`](main.py)：文本到标准摩斯码；命令行编码入口
- [`encoder.py`](encoder.py)：标准摩斯码到简化编码
- [`decoder.py`](decoder.py)：简化编码到摩斯码、文本
- [`benchmarks/`](benchmarks/)：实验统计与图表生成

## Engineering Rules Observed in Code

从当前仓库实现可以总结出以下编码约定：

- 只使用 Python 标准库，无第三方依赖
- 公开函数统一进行 `str` 类型校验
- 非法输入抛出 `TypeError` 或 `ValueError`
- 广泛使用类型标注
- 文件读取默认使用 `utf-8`
- 基准脚本统一使用 `pathlib.Path`
- 命令行和模块调用两种方式都可使用

## Limitations

当前方法仍有明确边界：

- 压缩单位是局部分组，不是全局最优编码
- 当前字符集主要面向英文、数字和常见英文标点
- 对结构不规律的摩斯序列，收益可能有限
- `ID` 采用直接位置拼接，在更长码长场景下仍可能有额外冗余
- 当前评估以字符长度为主，尚未引入更严格的信息论指标

## Future Work

后续可继续扩展的方向包括：

- 设计更强的组间复用机制，而不只是组内压缩
- 引入统计学习或词典机制，进一步压缩高频模式
- 对 `RS` 和 `ID` 设计更紧凑的元编码方案
- 引入更系统的实验对照，如与 RLE、Huffman 风格方案比较
- 增加论文式评估指标，如熵估计、解码复杂度、吞吐表现

## Environment

- Python 3.10+

## Reproducibility

当前仓库代码已经支持完整往返：

```text
text -> morse -> simplified -> morse -> text
```

在现有数据集上，可直接用脚本复现实验、生成 CSV，并导出 SVG 图表，适合作为：

- 算法课程作业
- 小型论文原型
- 编码规则展示 Demo
- GitHub 项目演示页
