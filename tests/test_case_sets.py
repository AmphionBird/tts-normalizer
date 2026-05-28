"""Run the shared iterable normalization test set."""

import pytest

from tests.case_sets import ALL_CASES, NormalizationCase
from tts_normalizer import Normalizer


@pytest.fixture(scope="module")
def normalizers():
    return {
        "en": Normalizer(lang="en"),
        "zh": Normalizer(lang="zh"),
    }


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda case: case.id)
def test_iterable_case_set(case: NormalizationCase, normalizers):
    assert normalizers[case.lang].normalize(case.text) == case.expected
