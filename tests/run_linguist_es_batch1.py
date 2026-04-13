"""Run @语言学之父 Spanish batch-1 test cases."""
import sys
sys.path.insert(0, "/home/babysor00/tts-normalizer")
from tts_normalizer import Normalizer

es = Normalizer(lang="es")

cases = [
    # 整数
    ("1",           "uno"),
    ("10",          "diez"),
    ("16",          "dieciséis"),
    ("21",          "veintiuno"),
    ("22",          "veintidós"),
    ("30",          "treinta"),
    ("31",          "treinta y uno"),
    ("100",         "cien"),
    ("101",         "ciento uno"),
    ("200",         "doscientos"),
    ("500",         "quinientos"),
    ("700",         "setecientos"),
    ("900",         "novecientos"),
    ("1000",        "mil"),
    ("2000",        "dos mil"),
    ("1000000",     "un millón"),
    ("2000000",     "dos millones"),
    ("1234",        "mil doscientos treinta y cuatro"),
    # 小数
    ("3.14",        "tres coma uno cuatro"),
    ("0.5",         "cero coma cinco"),
    ("10.5",        "diez coma cinco"),
    ("-3.14",       "menos tres coma uno cuatro"),
    # 百分比
    ("50%",         "cincuenta por ciento"),
    ("100%",        "cien por ciento"),
    ("3.5%",        "tres coma cinco por ciento"),
    # 货币
    ("€100",        "cien euros"),
    ("€1.50",       "un euro y cincuenta céntimos"),
    ("$99",         "noventa y nueve dólares"),
    ("£50",         "cincuenta libras"),
    # 日期
    ("2026-04-13",  "trece de abril de dos mil veintiséis"),
    ("1999-12-31",  "treinta y uno de diciembre de mil novecientos noventa y nueve"),
    ("2000-01-01",  "uno de enero de dos mil"),
    # 时刻 — 10:30 expected: las diez y media (linguist test had typo)
    ("1:00",        "la una"),
    ("2:00",        "las dos"),
    ("10:30",       "las diez y media"),
    ("3:15",        "las tres y cuarto"),
    ("3:30",        "las tres y media"),
    # 温度与单位
    ("-5°C",        "menos cinco grados Celsius"),
    ("37°F",        "treinta y siete grados Fahrenheit"),
    ("50kg",        "cincuenta kilogramos"),
    ("100km",       "cien kilómetros"),
    ("10cm",        "diez centímetros"),
    # 分数
    ("1/2",         "un medio"),
    ("1/3",         "un tercio"),
    ("2/3",         "dos tercios"),
    ("3/4",         "tres cuartos"),
    ("1/5",         "un quinto"),
    # 缩写
    ("Dr. García",  "doctor García"),
    ("Sr. López",   "señor López"),
    ("Sra. Pérez",  "señora Pérez"),
]

passed = failed = 0
failures = []
for inp, expected in cases:
    got = es.normalize(inp)
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
