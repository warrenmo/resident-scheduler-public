"""service_test.py
"""

import pytest
from resident_scheduler_public import Service

@pytest.fixture
def service_instances():
    service = Service(
        name="wards",
        priority=1,
        allows_vacations=False,
        is_core=True,
        min_interns_per_block=2,
        max_interns_per_block=2,
        min_seniors_per_block=1,
        max_seniors_per_block=1,
        min_blocks_per_intern=2,
        max_blocks_per_intern=3,
        min_blocks_per_senior=1,
        max_blocks_per_senior=2,
    )
    return service

def test_repr(service_instances):
    service = service_instances
    assert "name=wards" in repr(service)

def test_str(service_instances):
    service = service_instances
    assert "wards" == str(service)
