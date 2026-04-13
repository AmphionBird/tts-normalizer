"""Run @语言学之父 batch-3 test cases."""
import sys
sys.path.insert(0, "/home/babysor00/tts-normalizer")
from tts_normalizer import Normalizer

zh = Normalizer(lang="zh")
en = Normalizer(lang="en")

cases_zh = [
    # 科学计数法
    ("1.5×10^6",    "一百五十万"),
    ("3×10^8",      "三亿"),
    ("1e6",         "一百万"),
    ("2.5e-3",      "千分之二点五"),
    # 罗马数字
    ("第Ⅰ卷",      "第一卷"),
    ("第Ⅱ章",      "第二章"),
    ("Ⅲ级",        "三级"),
    # 电话（普通逐位）
    ("电话：13812345678", "电话：一三八一二三四五六七八"),
    # 其他货币
    ("€50",         "五十欧元"),
    ("£100",        "一百英镑"),
    ("₩5000",       "五千韩元"),
    ("¥0.01",       "一分"),
    # 特殊标点保留
    ("他说……然后走了",   "他说……然后走了"),
    ("这是——关键点",     "这是——关键点"),
    ("《三体》是好书",   "《三体》是好书"),
    ("10月后出发",        "十月后出发"),
    ("3天前",             "三天前"),
    # 两 vs 二 边界
    ("2个",         "两个"),
    ("2只",         "两只"),
    ("2位",         "两位"),
    ("第2名",       "第二名"),
    ("第22名",      "第二十二名"),
    ("12",          "十二"),
    ("22",          "二十二"),
    # 减法（回归）
    ("10-3=7",      "十减三等于七"),
]

cases_en = [
    # 基础数字
    ("0",           "zero"),
    ("1",           "one"),
    ("13",          "thirteen"),
    ("21",          "twenty-one"),
    ("100",         "one hundred"),
    ("1000",        "one thousand"),
    ("1000000",     "one million"),
    ("1234567",     "one million two hundred thirty-four thousand five hundred sixty-seven"),
    # 小数
    ("3.14",        "three point one four"),
    ("0.5",         "zero point five"),
    ("10.5",        "ten point five"),
    # 百分比
    ("50%",         "fifty percent"),
    ("3.5%",        "three point five percent"),
    ("100%",        "one hundred percent"),
    # 货币
    ("$100",        "one hundred dollars"),
    ("$99.99",      "ninety-nine dollars and ninety-nine cents"),
    ("$0.50",       "fifty cents"),
    ("£50",         "fifty pounds"),
    # 序数
    ("1st",         "first"),
    ("2nd",         "second"),
    ("3rd",         "third"),
    ("4th",         "fourth"),
    ("21st",        "twenty-first"),
    ("100th",       "one hundredth"),
    # 日期时间
    ("April 13, 2026",  "April thirteenth, twenty twenty-six"),
    ("10:30 AM",        "ten thirty AM"),
    ("3:05 PM",         "three oh five PM"),
    # 单位
    ("50kg",            "fifty kilograms"),
    ("10cm",            "ten centimeters"),
    ("100km/h",         "one hundred kilometers per hour"),
    ("-5°C",            "negative five degrees Celsius"),
    # 电话
    ("1-800-555-1234",  "one eight hundred five five five one two three four"),
]

passed = failed = 0
failures = []

for inp, expected in cases_zh:
    got = zh.normalize(inp)
    if got == expected:
        passed += 1
    else:
        failed += 1
        failures.append(("ZH", inp, expected, got))

for inp, expected in cases_en:
    got = en.normalize(inp)
    if got == expected:
        passed += 1
    else:
        failed += 1
        failures.append(("EN", inp, expected, got))

print(f"\n{'='*65}")
print(f"PASSED: {passed}/{passed+failed}  (ZH={len(cases_zh)}, EN={len(cases_en)})")
print(f"FAILED: {failed}/{passed+failed}")
if failures:
    print("\nFailed cases:")
    for lang, inp, exp, got in failures:
        print(f"  [{lang}] Input:    {inp!r}")
        print(f"       Expected: {exp!r}")
        print(f"       Got:      {got!r}")
        print()
