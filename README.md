# Resident Scheduler

This project aims to programmatically generate year-long, rotation/service
schedules for medical residents. This program does not determine
which days of the week a specific resident is off, but rather to which
rotation/service a given resident will be assigned for a given month/block.

This is a public-facing version of a private project. The private repo will
most likely not be made public in the near future.


## Features
 - Automated schedule creation for block-based residency programs
 - Constraint handling (e.g., rotation/service limits, resident service histories, etc.)
 - Optimization for "resident-friendly" schedules (e.g., bias against back-to-back difficult services)


## Limitations
 - Currently only works for non-intern residents (i.e., non-first-year residents)
 - Certain configurations of residents, services, and previous resident histories (services that residents performed in previous years) may result in long schedule-generation times
 - Certain constraints yet to be added (e.g., currently, residents may end up working with the same other residents repeatedly)


## Installation
Clone the repository and install the required dependencies.

```bash
git clone https://github.com/warrenmo/resident-scheduler-public.git
cd resident-scheduler-public
pip install -r requirements.txt
```


## Usage
The three main classes from this module are `Resident`, `Service`, and `Scheduler`.

```python
from resident_scheduler_public import Resident, Scheduler, Service

resident1 = Resident(
    first_name="John",
    last_name="Doe",
    year=2,
    is_fellowship_applicant=False,
    is_rising_chief=False
)
resident2 = Resident(
    first_name="Jane",
    last_name="Smith",
    year=3,
    is_fellowship_applicant=False,
    is_rising_chief=True
)
...
service1 = Service(
    name="Wards",
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
)
...
scheduler = Scheduler(
    residents = [resident1, resident2, ...],
    services = [service1, ...]
)
scheduler.create()
print(s)
```


## Testing
The unit tests all rely on the `pytest` library. To run the tests, navigate to the top-level of the project directory and run the following:

```bash
pytest
```


## Contributing

This is a public-facing copy of a private project. As such, pull requests and
issues are welcome, but I make no promises as to whether I'll read or respond
to them.


## License
This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
