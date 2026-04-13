"""Run @语言学之父 batch-2 test cases."""
import sys
sys.path.insert(0, "/home/babysor00/tts-normalizer")
from tts_normalizer import Normalizer

zh = Normalizer(lang="zh")

cases = [
    # 年份
    ("2026年",          "二零二六年"),
    ("1949年",          "一九四九年"),
    ("公元前100年",     "公元前一百年"),
    ("已过去2000年",    "已过去两千年"),
    ("1990年代",        "一九九零年代"),
    # 分数
    ("1/2",             "二分之一"),
    ("3/4",             "四分之三"),
    ("2/3",             "三分之二"),
    ("1/10",            "十分之一"),
    ("10/11",           "十一分之十"),
    ("4月10日",         "四月十日"),
    # 负数
    ("-5",              "负五"),
    ("-3.14",           "负三点一四"),
    ("-0.5",            "负零点五"),
    ("-100",            "负一百"),
    # 大数
    ("10000000",        "一千万"),
    ("100000000",       "一亿"),
    ("1200000000",      "十二亿"),
    ("12345678",        "一千两百三十四万五千六百七十八"),
    # 特殊编号
    ("192.168.1.1",     "一九二点一六八点一点一"),
    ("邮编100000",      "邮编一零零零零零"),
    ("房间号1023",      "房间号一零二三"),
    ("身份证末四位1234","身份证末四位一二三四"),
    # 范围
    ("10~20",           "十到二十"),
    ("5-10岁",          "五到十岁"),
    ("100-200元",       "一百到两百元"),
    # 比例/比分
    ("3:0",             "三比零"),
    ("1:100",           "一比一百"),
    ("比赛结果5:3",     "比赛结果五比三"),
    # 其他
    ("第一章·第二节",   "第一章第二节"),
    ("2026/04/13",      "二零二六年零四月十三日"),
    ("约100人",         "约一百人"),
    ("共计￥12,345.67", "共计一万两千三百四十五元六角七分"),
    # 减法（与范围/负数的区分）
    ("10-3=7",          "十减三等于七"),
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
