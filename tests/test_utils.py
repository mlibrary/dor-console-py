import pytest

from dor.utils import Filter, FilterLabel, remove_parameter


@pytest.fixture
def parameters() -> dict[str, str]:
    return {
        "object_type": "types:monograph",
        "alt_identifier": "amjewess:",
        "collection_alt_identifier": "amjewess"
    }



def test_remove_parameter_returns_parameters_minus_key(parameters: dict[str, str]):
    new_params = remove_parameter(parameters, "alt_identifier")
    assert new_params == {
        "object_type": "types:monograph",
        "collection_alt_identifier": "amjewess"
    }


def test_filter_makes_label(parameters: dict[str, str]):
    filter = Filter(key="object_type", value="types:monograph", name="Object Type")
    expected_label = FilterLabel(
        title='Object Type: types:monograph',
        remove_url="?alt_identifier=amjewess%3A&collection_alt_identifier=amjewess"
    )
    assert expected_label == filter.make_label(parameters)
