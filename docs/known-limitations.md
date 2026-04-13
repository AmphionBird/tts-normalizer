# Known Limitations

This document lists known limitations of the TTS Normalizer that do not block current delivery but are candidates for future iteration.

## 1. Deep Context Ambiguity

The normalizer operates on surface text without syntactic or semantic context. The same token can have multiple valid readings:

- A 4-digit number (e.g. `1234`) is always read as a year-style pair in English (`twelve thirty-four`). In non-year contexts (e.g. a PIN or model number) this may be undesirable. Resolving this requires upstream part-of-speech or entity tagging.
- Chinese `200` in "200m 跑道" (distance), "200 年前" (year count), and "200 元" (currency) all normalize to "两百", which is correct at the normalizer layer but acoustically identical — downstream TTS cannot distinguish stress patterns without further annotation.

## 2. Brand / Technical Terms Containing Digits

Letter-digit sequences where the digit is part of a product name or identifier (e.g. `A4`, `H100`, `GPT-4`) will have their numeric portion converted:

- `A4` → `A四` (Chinese), `A four` (English)
- `GPT-4` → `GPT负四` (Chinese, minus-sign misread) or similar

Mitigation: maintain an entity allowlist upstream and pass pre-tokenized text to the normalizer.

## 3. Phone Number "幺" (Chinese Dialectal Reading)

Colloquial Chinese reads the digit `1` in phone numbers as "幺" rather than "一". The normalizer outputs "一" uniformly, which is the written-standard and acoustically unambiguous form. Dialectal "幺" pronunciation is the responsibility of the acoustic/synthesis layer.

## 4. Punctuation Pause Semantics

The following punctuation marks are passed through unchanged:

| Symbol | Rationale |
|--------|-----------|
| `……` (ellipsis) | TTS engine handles pause duration |
| `——` (em-dash) | Preserved as punctuation |
| `《》` (title marks) | No spoken equivalent; TTS engine should suppress |

If the downstream TTS engine does not natively handle these symbols, a pre-processing step is needed to map them to SSML `<break>` tags or silence tokens.

## 5. URLs, Code Snippets, and Markup

The normalizer does not detect or skip URLs (`https://…`), inline code, HTML/Markdown tags, or file paths. Numbers and symbols within these constructs will be expanded, producing unnatural output. Recommended approach: strip or replace such spans before passing text to the normalizer.

## 6. Incomplete Measure-Word Coverage (Chinese)

The `2 + measure word → 两` rule covers the most common measure words (`个只位件杯碗张本台辆条块间套座名人份`). Less common or domain-specific measure words (e.g. `架`, `棵`, `幅`) are not included and will produce `二` instead of `两`. Extend `_mw` in `zh.py` as needed.

## 7. Currency Formatting Edge Cases

- Negative currency is supported for `$` in English (`-$50` → `negative fifty dollars`) but not yet for `¥`, `£`, `€`, `₩`.
- Very large CNY amounts with both 角 and 分 that round to edge values (e.g. `¥0.10`) are handled, but amounts with more than 2 decimal places are truncated without rounding notification.

## 8. Language Auto-Detection

The normalizer requires explicit `lang="zh"` or `lang="en"` selection. Mixed-language documents must be pre-segmented by language before normalization. There is no automatic language detection.

---

*Last updated: 2026-04-13. Verified against 200 test cases across 4 batches.*
