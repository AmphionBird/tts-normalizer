"""Run @语言学之父 Japanese batch-2 test cases."""
import sys
sys.path.insert(0, "/home/babysor00/tts-normalizer")
from tts_normalizer import Normalizer

ja = Normalizer(lang="ja")

cases = [
    # 分数
    ("1/2",             "二分の一"),
    ("2/3",             "三分の二"),
    ("3/4",             "四分の三"),
    ("1/10",            "十分の一"),
    # 範囲・比率
    ("5〜10歳",         "五から十歳"),
    ("100〜200円",      "百から二百円"),
    ("3:0",             "三対零"),
    ("1:100",           "一対百"),
    # 大数エッジケース
    ("1000000000000",   "一兆"),
    ("10000000000000",  "十兆"),
    ("1001",            "千一"),
    ("1010",            "千十"),
    ("1100",            "千百"),
    # 科学計数法
    ("1.5×10^6",        "百五十万"),
    ("3×10^8",          "三億"),
    ("2.5e-3",          "千分の二・五"),
    # 負数・単位組み合わせ
    ("-10°C",           "マイナス十度"),
    ("-¥500",           "マイナス五百円"),
    ("-50kg",           "マイナス五十キログラム"),
]

passed = failed = 0
failures = []
for inp, expected in cases:
    got = ja.normalize(inp)
    if got == expected:
        passed += 1
    else:
        failed += 1
        failures.append((inp, expected, got))

print(f"\n{'='*60}")
print(f"PASSED: {passed}/{passed+failed}")
print(f"FAILED: {failed}/{passed+failed}")
if failures:
    print("\nFailed cases:")
    for inp, exp, got in failures:
        print(f"  Input:    {inp!r}")
        print(f"  Expected: {exp!r}")
        print(f"  Got:      {got!r}")
        print()
