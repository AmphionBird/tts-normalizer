"""Run @语言学之父 batch-4 test cases."""
import sys
sys.path.insert(0, "/home/babysor00/tts-normalizer")
from tts_normalizer import Normalizer

zh = Normalizer(lang="zh")
en = Normalizer(lang="en")

cases_en = [
    # 年份读法
    ("2026",        "twenty twenty-six"),
    ("1999",        "nineteen ninety-nine"),
    ("2000",        "two thousand"),
    ("2001",        "two thousand one"),
    ("2010",        "twenty ten"),
    ("1900",        "nineteen hundred"),
    ("1800",        "eighteen hundred"),
    ("100 AD",      "one hundred AD"),
    # 英文分数
    ("1/2",         "one half"),
    ("1/3",         "one third"),
    ("2/3",         "two thirds"),
    ("1/4",         "one quarter"),
    ("3/4",         "three quarters"),
    ("1/5",         "one fifth"),
    ("2/5",         "two fifths"),
    # 英文负数
    ("-5",          "negative five"),
    ("-3.14",       "negative three point one four"),
    ("-$50",        "negative fifty dollars"),
    # 英文缩写展开
    ("Dr. Smith",   "Doctor Smith"),
    ("Mr. Lee",     "Mister Lee"),
    ("vs.",         "versus"),
    ("etc.",        "et cetera"),
    ("No. 1",       "Number one"),
    # 英文大数（带千位逗号）
    ("1,000",       "one thousand"),
    ("12,345",      "twelve thousand three hundred forty-five"),
    ("1,000,000",   "one million"),
]

cases_zh_mixed = [
    # 中英混排
    ("5G网络覆盖率达99%",           "五G网络覆盖率达百分之九十九"),
    ("WiFi 6已普及",                "WiFi 六已普及"),
    ("USB 3.0接口",                 "USB 三点零接口"),
    ("iPhone 15 Pro售价¥9999",      "iPhone 十五 Pro售价九千九百九十九元"),
    ("API调用次数：1,234次",        "API调用次数：一千两百三十四次"),
    ("共2个bug待修复",              "共两个bug待修复"),
    ("延迟从200ms降至50ms",         "延迟从两百ms降至五十ms"),
    ("完成度80% done",              "完成度百分之八十 done"),
    ("v2.3.1正式发布",              "v二点三点一正式发布"),
    ("第2季第3集",                  "第二季第三集"),
    ("排名Top 3",                   "排名Top 三"),
    ("2026年Q1目标",                "二零二六年Q一目标"),
    ("B2B客户增长30%",              "B二B客户增长百分之三十"),
    ("存储空间还剩1.5GB",           "存储空间还剩一点五GB"),
]

passed = failed = 0
failures = []

for inp, expected in cases_en:
    got = en.normalize(inp)
    if got == expected:
        passed += 1
    else:
        failed += 1
        failures.append(("EN", inp, expected, got))

for inp, expected in cases_zh_mixed:
    got = zh.normalize(inp)
    if got == expected:
        passed += 1
    else:
        failed += 1
        failures.append(("ZH", inp, expected, got))

print(f"\n{'='*65}")
print(f"PASSED: {passed}/{passed+failed}  (EN={len(cases_en)}, ZH_mixed={len(cases_zh_mixed)})")
print(f"FAILED: {failed}/{passed+failed}")
if failures:
    print("\nFailed cases:")
    for lang, inp, exp, got in failures:
        print(f"  [{lang}] Input:    {inp!r}")
        print(f"         Expected: {exp!r}")
        print(f"         Got:      {got!r}")
        print()
