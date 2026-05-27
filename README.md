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
| Units | `50kg` → 五十千克 | `10cm` → ten centimeters, `60 mph` → sixty miles per hour, `2.4 GHz` → two point four gigahertz | `50kg` → 五十キログラム | `50kg` → cincuenta kilogramos |
| Ordinals | `第3名` → 第三名 | `21st` → twenty-first | `第3章` → 第三章 | `3º` → tercero |
| Scientific | `1.5×10^6` → 一百五十万 | — | `1.5×10^6` → 百五十万 | `1.5×10^6` → un millón quinientos mil |
| Abbreviations | — | `Dr.` → Doctor, `vs.` → versus | — | `Dr.` → doctor, `Sr.` → señor |

## English normalizer details

### Supported patterns

| Pattern | Example input | Output |
|---------|--------------|--------|
| Cardinals | `1,234,567` | one million two hundred thirty-four thousand five hundred sixty-seven |
| Ordinals | `23rd` | twenty-third |
| Decimals | `3.14` | three point one four |
| Negatives | `-2` | negative two |
| Percentages | `2.5%` | two point five percent |
| Fractions | `3/4`, `2 1/2` | three quarters, two and a half |
| **Dates** | | |
| ISO date | `2026-04-13` | April thirteenth, twenty twenty-six |
| American | `April 13, 2026` / `apr. 13, 2026` | April thirteenth, twenty twenty-six |
| European | `25 July 2012` / `25th july 2012` | the twenty-fifth of July twenty twelve |
| **Times** | | |
| 24h clock | `23:00` | twenty-three o'clock |
| 12h with AM/PM | `1:59 p.m.` / `1:59 pm` | one fifty-nine PM |
| With timezone | `1:59 pm EST` / `1:59 p.m.est` | one fifty-nine PM EST |
| Dot separator | `1.59 p.m.` | one fifty-nine PM |
| Seconds | `1:01:01` | one hours one minutes and one seconds |
| AM/PM range | `2pm-5pm` | two PM to five PM |
| **Currency** | | |
| USD | `$10.50`, `-$50`, `$0.50` | ten dollars and fifty cents, negative fifty dollars, fifty cents |
| USD scale | `$45 billion` | forty-five billion dollars |
| GBP | `£10`, `£1.20` | ten pounds, one pound twenty pennies |
| JPY | `¥30`, `¥30b`, `¥30 billion` | thirty yen, thirty billion yen, thirty billion yen |
| KRW | `₩460b` | four hundred sixty billion won |
| Per-period | `$20/mo`, `£10/wk` | twenty dollars per month, ten pounds per week |
| **Phone numbers** | | |
| US with country code | `1-800-555-1234` | one eight hundred five five five one two three four |
| International +1 | `+1 (650) 555-1234` | plus one, six five zero, five five five, one two three four |
| Parenthesized | `(212) 867-5309` | two one two eight six seven five three zero nine |
| Bare local | `650-451-1234` | six five zero four five one one two three four |
| SSN | `123-45-6789` | one two three, four five, six seven eight nine |
| **Units** | | |
| Metric length/weight | `5cm`, `12kg`, `50ml` | five centimeters, twelve kilograms, fifty milliliters |
| Imperial length/weight | `6ft`, `6 ft`, `12in`, `3lbs`, `10oz` | six feet, six feet, twelve inches, three pounds, ten ounces |
| Distance | `5mi`, `10yd` | five miles, ten yards |
| Speed | `100km/h`, `50mph`, `60 mph` | one hundred kilometers per hour, fifty miles per hour, sixty miles per hour |
| Temperature | `2°C`, `37°F`, `-10°C` | two degrees Celsius, thirty-seven degrees Fahrenheit, negative ten degrees Celsius |
| Frequency | `100Hz`, `5kHz`, `2.4 GHz` | one hundred hertz, five kilohertz, two point four gigahertz |
| Data size | `512MB`, `2GB`, `1TB` | five hundred twelve megabytes, two gigabytes, one terabytes |
| Power | `100W`, `5kW` | one hundred watts, five kilowatts |
| Time (duration) | `10ms`, `5μs` | ten milliseconds, five microseconds |
| Pressure | `100psi`, `2atm` | one hundred pounds per square inch, two atmospheres |
| Voltage/current | `5V`, `100mA` | five volts, one hundred milliamperes |
| **Decades** | `1980s`, `'80s`, `2010s` | nineteen eighties, eighties, twenty tens |
| **Abbreviations** | `Dr.`, `No. 42`, `vs.` | Doctor, Number forty-two, versus |

### Style choices (vs. NeMo TN)

| Feature | NeMo default | Our style |
|---------|-------------|-----------|
| Negatives | "minus two" | "negative two" |
| Compounds | "twenty three" | "twenty-three" |
| Cardinals with "and" | "one hundred and twenty" | "one hundred twenty" |
| Money with "and" | "twenty dollars fifty cents" | "twenty dollars and fifty cents" |

### Preprocessing

Dotted abbreviations are normalised before pattern matching:
- `a.m.` / `p.m.` → `am` / `pm`
- `e.s.t.` / `p.s.t.` → `EST` / `PST`
- `pmest` / `amEST` (no space) → `pm EST`

### Entity protection

Brand codes, model names (`GPT-4o`, `H100`), URLs, and backtick-wrapped spans are shielded from pattern matching and restored verbatim afterwards.

## Digit-free output guarantee

All four languages guarantee **no Arabic digits (0-9) in the output**, making it safe to pass directly to any TTS model.

Brand codes, model names, and version numbers are handled without structural mangling:

```python
zh.normalize("今天用GPT-4写了10篇文章，效率提升了50%")
# → "今天用GPT-四写了十篇文章，效率提升了百分之五十"

en.normalize("GPT-4o is available on H100 GPUs")
# → "GPT-four o is available on H one hundred GPUs"

zh.normalize("A4纸和USB3.0接口")
# → "A四纸和USB三点零接口"
```

> **Note:** URLs containing digits (e.g. `/v1/`) will have their digits converted. Strip URLs before passing to the normalizer if verbatim URL preservation is required.

### Custom entity allowlist (zh)

Tokens that must be preserved verbatim can be passed via `context`:

```python
zh = Normalizer(lang="zh", context={"entity_allowlist": ["GPT-4o", "v1"]})
zh.normalize("调用GPT-4o的v1接口")
# → "调用GPT-四o的v一接口"  (digits still converted by cleanup pass)
```

## Extending to a new language

Add `tts_normalizer/languages/xx.py` subclassing `BaseNormalizer`, then register it in `tts_normalizer/normalizer.py`.

## Known limitations

See [`docs/known-limitations.md`](docs/known-limitations.md).
