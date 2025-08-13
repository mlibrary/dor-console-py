from dor.utils import remove_parameter


def test_remove_parameter_returns_parameters_minus_key():
    current_params = {
        "object_type": "types:monograph",
        "alt_identifier": "amjewess",
        "collection_title": "American Jewess"
    }

    new_params = remove_parameter(current_params, "alt_identifier")
    assert new_params == {
        "object_type": "types:monograph",
        "collection_title": "American Jewess"
    }
