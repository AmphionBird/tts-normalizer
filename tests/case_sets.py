"""Iterable normalization test cases shared by pytest and ad-hoc runners."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from tests import (
    run_linguist_batch1,
    run_linguist_batch2,
    run_linguist_batch3,
    run_linguist_batch4,
    run_linguist_limitations,
)


@dataclass(frozen=True)
class NormalizationCase:
    lang: str
    source: str
    name: str
    text: str
    expected: str

    @property
    def id(self) -> str:
        return f"{self.lang}:{self.source}:{self.name}"


EN_SMOKE_CASES = (
    NormalizationCase("en", "smoke", "integer", "There are 42 apples", "There are forty-two apples"),
    NormalizationCase("en", "smoke", "decimal", "Pi is 3.14", "Pi is three point one four"),
    NormalizationCase("en", "smoke", "ordinal", "He finished 1st", "He finished first"),
    NormalizationCase("en", "smoke", "percentage", "Success rate: 95%", "Success rate: ninety-five percent"),
    NormalizationCase("en", "smoke", "currency", "Price: $10.50", "Price: ten dollars and fifty cents"),
    NormalizationCase("en", "smoke", "date", "Date: 2026-04-13", "Date: April thirteenth, twenty twenty six"),
    NormalizationCase("en", "smoke", "time", "Meeting at 10:30", "Meeting at ten thirty"),
)

ZH_SMOKE_CASES = (
    NormalizationCase("zh", "smoke", "integer", "今天来了100人", "今天来了一百人"),
    NormalizationCase("zh", "smoke", "decimal", "气温10.5度", "气温十点五度"),
    NormalizationCase("zh", "smoke", "decimal_date_ambiguity", "版本号10.11", "版本号十点一一"),
    NormalizationCase("zh", "smoke", "date_iso", "2026-04-13", "二零二六年四月十三日"),
    NormalizationCase("zh", "smoke", "date_slash", "2026/04/13", "二零二六年四月十三日"),
    NormalizationCase("zh", "smoke", "time_hhmm", "10:30", "十点三十分"),
    NormalizationCase("zh", "smoke", "percentage", "完成率80%", "完成率百分之八十"),
    NormalizationCase("zh", "smoke", "currency_cny", "售价¥199", "售价一百九十九元"),
    NormalizationCase("zh", "smoke", "currency_usd", "售价$50", "售价五十美元"),
    NormalizationCase("zh", "smoke", "negative", "温度-10度", "温度负十度"),
    NormalizationCase("zh", "smoke", "negative_measure", "海拔-100米", "海拔负一百米"),
    NormalizationCase("zh", "smoke", "fraction", "3/4的概率", "四分之三的概率"),
    NormalizationCase("zh", "smoke", "unit_kg", "重量50kg", "重量五十千克"),
    NormalizationCase("zh", "smoke", "year_standalone", "2026年", "二零二六年"),
)

EN_DIGIT_SCENARIO_CASES = (
    NormalizationCase("en", "digit_scenarios", "ip_address", "IP 192.168.1.1", "IP one nine two dot one six eight dot one dot one"),
    NormalizationCase("en", "digit_scenarios", "verification_code", "Verification code 123456", "Verification code one two three four five six"),
    NormalizationCase("en", "digit_scenarios", "pin_leading_zero", "PIN 0429", "PIN zero four two nine"),
    NormalizationCase("en", "digit_scenarios", "room_leading_zero", "Room 007", "Room zero zero seven"),
    NormalizationCase("en", "digit_scenarios", "order_number_large", "Order number 1000000", "Order number one zero zero zero zero zero zero"),
    NormalizationCase("en", "digit_scenarios", "bare_long_digits", "Reference 13848396758", "Reference one three eight four eight three nine six seven five eight"),
)

ZH_DIGIT_SCENARIO_CASES = (
    NormalizationCase("zh", "digit_scenarios", "verification_code", "验证码0429", "验证码零四二九"),
    NormalizationCase("zh", "digit_scenarios", "serial_leading_zero", "编号007", "编号零零七"),
    NormalizationCase("zh", "digit_scenarios", "order_number_large", "订单号1000000", "订单号一零零零零零零"),
    NormalizationCase("zh", "digit_scenarios", "mobile_context", "手机号13800138000", "手机号一三八零零一三八零零零"),
    NormalizationCase("zh", "digit_scenarios", "mobile_hyphenated_context", "联系电话：138-0013-8000", "联系电话：一三八零零一三八零零零"),
    NormalizationCase("zh", "digit_scenarios", "bare_long_digits", "参考号13848396758", "参考号一三八四八三九六七五八"),
)


def _from_pairs(lang: str, source: str, pairs: Iterable[tuple[str, str]]) -> tuple[NormalizationCase, ...]:
    return tuple(
        NormalizationCase(lang, source, f"{index:03d}", text, expected)
        for index, (text, expected) in enumerate(pairs, start=1)
    )


def _extract_public_en_cases() -> tuple[NormalizationCase, ...]:
    """Keep the existing NeMo-sampled pytest file in the iterable registry."""
    path = Path(__file__).with_name("test_en_public.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cases = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        comparison = node.test
        if not (
            isinstance(comparison, ast.Compare)
            and len(comparison.ops) == 1
            and isinstance(comparison.ops[0], ast.Eq)
            and len(comparison.comparators) == 1
        ):
            continue

        call = comparison.left
        expected = comparison.comparators[0]
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "normalize"
            and len(call.args) == 1
            and isinstance(call.args[0], ast.Constant)
            and isinstance(call.args[0].value, str)
            and isinstance(expected, ast.Constant)
            and isinstance(expected.value, str)
        ):
            continue

        cases.append(
            NormalizationCase(
                "en",
                "nemo_public",
                f"line_{node.lineno}",
                call.args[0].value,
                expected.value,
            )
        )

    return tuple(sorted(cases, key=lambda case: int(case.name.removeprefix("line_"))))


EN_PUBLIC_CASES = _extract_public_en_cases()

EN_LINGUIST_CASES = (
    *_from_pairs("en", "linguist_batch3", run_linguist_batch3.cases_en),
    *_from_pairs("en", "linguist_batch4", run_linguist_batch4.cases_en),
)

ZH_LINGUIST_CASES = (
    *_from_pairs("zh", "linguist_batch1", run_linguist_batch1.cases),
    *_from_pairs("zh", "linguist_batch2", run_linguist_batch2.cases),
    *_from_pairs("zh", "linguist_batch3", run_linguist_batch3.cases_zh),
    *_from_pairs("zh", "linguist_batch4_mixed", run_linguist_batch4.cases_zh_mixed),
    *_from_pairs("zh", "linguist_limitations", run_linguist_limitations.cases),
)

EN_CASES = (
    *EN_SMOKE_CASES,
    *EN_DIGIT_SCENARIO_CASES,
    *EN_PUBLIC_CASES,
    *EN_LINGUIST_CASES,
)

ZH_CASES = (
    *ZH_SMOKE_CASES,
    *ZH_DIGIT_SCENARIO_CASES,
    *ZH_LINGUIST_CASES,
)

ALL_CASES = (
    *ZH_CASES,
    *EN_CASES,
)


def cases_for(lang: str) -> Sequence[NormalizationCase]:
    if lang == "en":
        return EN_CASES
    if lang == "zh":
        return ZH_CASES
    raise ValueError(f"Unsupported test case language: {lang}")
