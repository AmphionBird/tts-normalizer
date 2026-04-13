# tts-normalizer

Converts written text (numbers, symbols, dates) to spoken form for TTS pipelines.

Supports **Chinese (zh)** and **English (en)**.

## Installation

```bash
pip install .
```

Requires Python 3.9+, no external dependencies.

## Usage

```python
from tts_normalizer import Normalizer

zh = Normalizer(lang="zh")
en = Normalizer(lang="en")

zh.normalize("2026年4月13日气温-5°C")
# → "二零二六年四月十三日气温负五摄氏度"

en.normalize("The temperature is -5°C on April 13, 2026.")
# → "The temperature is negative five degrees Celsius on April thirteenth, twenty twenty-six."
```

### Normalize a single token

```python
zh.normalize_token("3.14")   # → "三点一四"
en.normalize_token("$99.99") # → "ninety-nine dollars and ninety-nine cents"
```

## What gets converted

| Category | zh example | en example |
|----------|-----------|-----------|
| Cardinals | `1200` → 一千两百 | `1,200` → one thousand two hundred |
| Decimals | `3.14` → 三点一四 | `3.14` → three point one four |
| Negatives | `-5` → 负五 | `-5` → negative five |
| Fractions | `3/4` → 四分之三 | `3/4` → three quarters |
| Percentages | `50%` → 百分之五十 | `50%` → fifty percent |
| Currency | `¥12.50` → 十二元五角 | `$9.99` → nine dollars and ninety-nine cents |
| Dates | `2026-04-13` → 二零二六年零四月十三日 | `April 13, 2026` → April thirteenth, twenty twenty-six |
| Times | `10:05` → 十点零五分 | `10:05` → ten oh five |
| Years | `1999年` → 一九九九年 | `1999` → nineteen ninety-nine |
| Units | `50kg` → 五十千克 | `10cm` → ten centimeters |
| Ordinals | `第3名` → 第三名 | `21st` → twenty-first |
| Scientific | `1.5×10^6` → 一百五十万 | — |
| Abbreviations | — | `Dr.` → Doctor, `vs.` → versus |

## Extending to a new language

Add `tts_normalizer/languages/ja.py` subclassing `BaseNormalizer`, then register it in `tts_normalizer/__init__.py`.

## Known limitations

See [`docs/known-limitations.md`](docs/known-limitations.md).
