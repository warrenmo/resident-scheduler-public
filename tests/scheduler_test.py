"""scheduler_test.py

TODO: add more test cases
  - test each of the rules for the residency program
  - add heavier stress test
  - test randomization
"""

import pytest
from resident_scheduler_public import Resident, Scheduler, Service
from uuid import UUID

@pytest.fixture
def resident_service_instances():
    residents = (
        [
            Resident(
                first_name=f'{i:02} - PGY2',
                last_name=f'{i:02}',
                year=2,
                is_fellowship_applicant=False,
                is_rising_chief=False
            )
            for i in range(2)
        ] \
        + [
            Resident(
                first_name=f'{i:02} - chief',
                last_name=f'{i:02}',
                year=3,
                is_fellowship_applicant=False,
                is_rising_chief=True
            )
            for i in range(2, 4)
        ] \
        + [
            Resident(
                first_name=f'{i:02} - fell. app.',
                last_name=f'{i:02}',
                year=3,
                is_fellowship_applicant=True,
                is_rising_chief=False
            )
            for i in range(4, 6)
        ] \
        + [
            Resident(
                first_name=f'{i:02}',
                last_name=f'{i:02}',
                year=3,
                is_fellowship_applicant=False,
                is_rising_chief=False
            )
            for i in range(6, 8)
        ]
    )

    services = [
        Service(
            name="1-Firm",
            priority=1,
            allows_vacations=False,
            is_core=True,
            min_interns_per_block=2,
            max_interns_per_block=2,
            min_blocks_per_intern=1,
            max_blocks_per_intern=1,
            min_seniors_per_block=2,
            max_seniors_per_block=2,
            min_blocks_per_senior=2,
            max_blocks_per_senior=3,
        ),
        Service(
            name="2-Firm",
            priority=1,
            allows_vacations=True,
            is_core=True,
            min_interns_per_block=2,
            max_interns_per_block=2,
            min_blocks_per_intern=1,
            max_blocks_per_intern=1,
            min_seniors_per_block=1,
            max_seniors_per_block=1,
            min_blocks_per_senior=1,
            max_blocks_per_senior=2,
        ),
        Service(
            name="3-Firm",
            priority=1,
            allows_vacations=True,
            is_core=True,
            min_interns_per_block=2,
            max_interns_per_block=2,
            min_blocks_per_intern=1,
            max_blocks_per_intern=1,
            min_seniors_per_block=1,
            max_seniors_per_block=1,
            min_blocks_per_senior=1,
            max_blocks_per_senior=2,
        ),
    ]
    return residents, services

def test_init(resident_service_instances):
    residents, services = resident_service_instances
    s = Scheduler(
        num_blocks_per_year=4,
        residents=residents,
        services=services
    )
    # haven't called s.create() yet, so the schedules should be None
    assert s.schedule is None
    assert s.service_schedule is None

def test_valid_schedule_created(resident_service_instances):
    residents, services = resident_service_instances
    s = Scheduler(
        num_blocks_per_year=4,
        residents=residents,
        services=services
    )
    schedule = s.create()
    assert schedule is not None

def test_not_enough_residents_to_create_schedule(resident_service_instances):
    residents, services = resident_service_instances
    residents_shortened = residents[:2]
    s = Scheduler(
        num_blocks_per_year=4,
        residents=residents_shortened,
        services=services
    )
    schedule = s.create()
    assert schedule is None

def test_residents_maxed_out_on_all_services(resident_service_instances):
    residents, services = resident_service_instances
    s = Scheduler(
        num_blocks_per_year=4,
        residents=residents,
        services=services
    )
    maxed_count = {
        i: services[i].max_blocks_per_senior
        for i in range(len(services))
    }
    schedule = s.create(resident_service_count={
        i: maxed_count for i in range(len(residents))
    })
    assert schedule is None
