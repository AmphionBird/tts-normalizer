# tts-normalizer

Converts written text (numbers, symbols, dates) to spoken form for TTS pipelines.

Supports **Chinese (zh)**, **English (en)**, **Japanese (ja)**, and **Spanish (es)**.

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
ja = Normalizer(lang="ja")
es = Normalizer(lang="es")

zh.normalize("2026年4月13日气温-5°C")
# → "二零二六年四月十三日气温负五摄氏度"

en.normalize("The temperature is -5°C on April 13, 2026.")
# → "The temperature is negative five degrees Celsius on April thirteenth, twenty twenty-six."

ja.normalize("2026年4月13日、気温-5°C、湿度50%です。")
# → "二〇二六年四月十三日、気温マイナス五度、五十パーセントです。"

es.normalize("El 2026-04-13, la temperatura fue de -5°C y la humedad del 80%.")
# → "El trece de abril de dos mil veintiséis, la temperatura fue de menos cinco grados Celsius y la humedad del ochenta por ciento."
```

### Normalize a single token

```python
zh.normalize_token("3.14")   # → "三点一四"
en.normalize_token("$99.99") # → "ninety-nine dollars and ninety-nine cents"
ja.normalize_token("¥1500")  # → "千五百円"
es.normalize_token("€1.50")  # → "un euro y cincuenta céntimos"
```

## What gets converted

| Category | zh | en | ja | es |
|----------|----|----|----|----|
| Cardinals | `1200` → 一千两百 | `1,200` → one thousand two hundred | `1200` → 千二百 | `1200` → mil doscientos |
| Decimals | `3.14` → 三点一四 | `3.14` → three point one four | `3.14` → 三点一四 | `3.14` → tres coma uno cuatro |
| Negatives | `-5` → 负五 | `-5` → negative five | `-5` → マイナス五 | `-5` → menos cinco |
| Fractions | `3/4` → 四分之三 | `3/4` → three quarters | `3/4` → 四分の三 | `3/4` → tres cuartos |
| Percentages | `50%` → 百分之五十 | `50%` → fifty percent | `50%` → 五十パーセント | `50%` → cincuenta por ciento |
| Currency | `¥12.50` → 十二元五角 | `$9.99` → nine dollars and ninety-nine cents | `¥1500` → 千五百円 | `€1.50` → un euro y cincuenta céntimos |
| Dates | `2026-04-13` → 二零二六年零四月十三日 | `April 13, 2026` → April thirteenth, twenty twenty-six | `2026-04-13` → 二〇二六年四月十三日 | `2026-04-13` → trece de abril de dos mil veintiséis |
| Times | `10:05` → 十点零五分 | `10:05` → ten oh five | `10:30` → 十時三十分 | `3:15` → las tres y cuarto |
| Years | `1999年` → 一九九九年 | `1999` → nineteen ninety-nine | `2026年` → 二〇二六年 | `1999` → mil novecientos noventa y nueve |
| Units | `50kg` → 五十千克 | `10cm` → ten centimeters | `50kg` → 五十キログラム | `50kg` → cincuenta kilogramos |
| Ordinals | `第3名` → 第三名 | `21st` → twenty-first | `第3章` → 第三章 | `3º` → tercero |
| Scientific | `1.5×10^6` → 一百五十万 | — | `1.5×10^6` → 百五十万 | `1.5×10^6` → un millón quinientos mil |
| Abbreviations | — | `Dr.` → Doctor, `vs.` → versus | — | `Dr.` → doctor, `Sr.` → señor |

## Extending to a new language

Add `tts_normalizer/languages/xx.py` subclassing `BaseNormalizer`, then register it in `tts_normalizer/normalizer.py`.

## Known limitations

See [`docs/known-limitations.md`](docs/known-limitations.md).
