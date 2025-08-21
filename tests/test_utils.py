from dataclasses import dataclass

import pytest

from dor.utils import Filter, FilterLabel, Page, remove_parameter


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


# Page

@dataclass
class DummyItem:
    id: int
    name: str


@pytest.fixture
def dummy_items() -> list[DummyItem]:
    return [
        DummyItem(id=0, name="A"),
        DummyItem(id=1, name="B"),
        DummyItem(id=2, name="C"),
        DummyItem(id=3, name="D"),
        DummyItem(id=4, name="E"),
        DummyItem(id=5, name="F"),
        DummyItem(id=6, name="G"),
        DummyItem(id=7, name="H")
    ]


def test_page_sets_total_pages(dummy_items: list[DummyItem]):
    page = Page(total_items=len(dummy_items), offset=0, limit=2, items=dummy_items[0:2])

    assert page.total_pages == 4


def test_page_updates_offsets_in_middle_of_range(dummy_items: list[DummyItem]):
    page = Page(total_items=len(dummy_items), offset=4, limit=2, items=dummy_items[4:6])

    assert page.previous_offset == 2
    assert page.next_offset == 6


def test_page_updates_offsets_at_beginning_of_range(dummy_items: list[DummyItem]):
    page = Page(total_items=len(dummy_items), offset=0, limit=2, items=dummy_items[0:2])

    assert page.previous_offset == -1
    assert page.next_offset == 2


def test_page_updates_offsets_near_beginning_of_range(dummy_items: list[DummyItem]):
    page = Page(total_items=len(dummy_items), offset=1, limit=2, items=dummy_items[1:3])

    assert page.previous_offset == 0
    assert page.next_offset == 3


def test_page_updates_offsets_at_end_of_range(dummy_items: list[DummyItem]):
    page = Page(total_items=len(dummy_items), offset=7, limit=2, items=dummy_items[7:])

    assert page.previous_offset == 5
    assert page.next_offset == -1
