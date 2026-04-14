"""Test cases for known-limitations fixes.

Covers:
- Limitation 2: entity allowlist (brand codes, URLs)
- Limitation 5: URL/code protection
- Limitation 6: expanded measure-word 两 substitution
- Limitation 7: negative currency
"""
import sys
sys.path.insert(0, "/home/babysor00/tts-normalizer")
from tts_normalizer import Normalizer

zh = Normalizer(lang="zh")

cases = [
    # --- Limitation 6: expanded measure words ---
    ("2架飞机",         "两架飞机"),
    ("2棵树",           "两棵树"),
    ("2幅画",           "两幅画"),
    ("2头牛",           "两头牛"),
    ("2匹马",           "两匹马"),
    ("2根柱子",         "两根柱子"),
    # Original measure words still work
    ("2个苹果",         "两个苹果"),
    ("2位老师",         "两位老师"),
    # 3 stays cardinal
    ("3架飞机",         "三架飞机"),

    # --- Limitation 7: negative currency ---
    ("-¥100",           "负一百元"),
    ("-￥50",           "负五十元"),
    ("-¥9.99",          "负九元九角九分"),
    ("-€20",            "负二十欧元"),
    ("-£15",            "负十五英镑"),
    ("-₩5000",          "负五千韩元"),
    ("-$30",            "负三十美元"),
    # Positive variants still work
    ("¥100",            "一百元"),
    ("¥9.99",           "九元九角九分"),
    ("€20",             "二十欧元"),

    # --- CNY decimal truncation fix ---
    ("¥1.234",          "一元二角三分"),   # truncates to 2dp → jiao=2, fen=3

    # --- Limitation 5: URL / code span protection (verbatim) ---
    ("请访问https://example.com了解更多",
     "请访问https://example.com了解更多"),
    # Code span protection
    ("执行`rm -rf /`命令",  "执行`rm -rf /`命令"),

    # --- Limitation 2: brand codes — digits converted, hyphens not mangled ---
    # Fixed integer pattern ((?<![a-zA-Z])) prevents "GPT-4" → "GPT负四"
    ("波音A380客机",    "波音A三百八十客机"),
    ("用USB3.0连接",    "用USB三点零连接"),
    ("GPT-4模型",       "GPT-四模型"),
    ("A4纸",            "A四纸"),
    ("Q1季度",          "Q一季度"),
]

passed = failed = 0
failures = []
for inp, expected in cases:
    got = zh.normalize(inp)
    if got == expected:
        passed += 1
    else:
        failed += 1
        failures.append((inp, expected, got))

print(f"\n{'='*65}")
print(f"PASSED: {passed}/{passed+failed}")
print(f"FAILED: {failed}/{passed+failed}")
if failures:
    print("\nFailed cases:")
    for inp, exp, got in failures:
        print(f"  Input:    {inp!r}")
        print(f"  Expected: {exp!r}")
        print(f"  Got:      {got!r}")
        print()
