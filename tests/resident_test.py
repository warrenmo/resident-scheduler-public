"""resident_test.py
"""

import pytest
from resident_scheduler_public import Resident
from uuid import UUID

@pytest.fixture
def resident_instances():
    res1 = Resident(first_name="John", last_name="Doe", year=1)
    res2 = Resident(first_name="Jane", last_name="Doe", year=2)
    res3 = Resident(first_name="John", last_name="Doe", year=3)
    return res1, res2, res3

def test_id_is_generated(resident_instances):
    res1, res2, res3 = resident_instances
    assert isinstance(UUID(res1.id), UUID)
    assert isinstance(UUID(res2.id), UUID)
    assert isinstance(UUID(res3.id), UUID)

def test_id_is_readonly(resident_instances):
    res1, _, _ = resident_instances
    with pytest.raises(AttributeError):
        res1.id = "new_id"

def test_sorting(resident_instances):
    res1, res2, res3 = resident_instances
    residents = [res1, res2, res3]
    sorted_residents = sorted(residents)

    # Based on (last_name, first_name, -year, id)
    expected_order = [res2, res3, res1]
    assert sorted_residents == expected_order

def test_eq(resident_instances):
    res1, _, _ = resident_instances
    tmp_res = Resident(first_name=res1.first_name,
                       last_name=res1.last_name,
                       year=res1.year)
    assert res1 == res1
    assert res1 != tmp_res
    tmp_res._id = res1._id
    assert res1 == tmp_res

def test_repr(resident_instances):
    res1, _, _ = resident_instances
    repr_str = repr(res1)
    assert "first_name=John" in repr_str
    assert "last_name=Doe" in repr_str
    assert "year=1" in repr_str
    assert "id=" in repr_str

def test_str(resident_instances):
    res1, _, _ = resident_instances
    assert "Doe, John, year 1" == str(res1)
