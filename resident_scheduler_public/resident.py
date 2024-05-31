"""resident.py

Contains the Resident class.

Classes:
    Resident

"""

import uuid

class Resident:
    """
    A class that represents a resident.

    Attributes
    ----------
    id : str
        a unique ID to identify each resident; used as a tiebreaker for sorting
        when two residents have the same first and last names and are in the
        same year
    first_name : str
    last_name : str
    year : int
        the year of the residency program this resident is in
    is_fellowship_applicant : bool
        true if the resident is applying for a fellowship program after
        completing the residency program; reserved for residents in the last
        year of the program
    is_rising_chief : bool
        true if the resident will be a "chief resident" the next year; reserved
        for residents in the last year of the program; typcially only a small
        percentage of residents will be rising chiefs
    specialty : str
        a.k.a. the type of the residency program the resident is a part of;
        examples of specialties include "internal medicine" and "dermatology";
        note that this is distinct from "sub-specialties" like "cardiology" and
        "gastroenterology" (which are types of fellowship programs)

    """
    def __init__(
        self,
        *,
        first_name: str,
        last_name: str,
        year: int,
        is_fellowship_applicant: bool=False,
        is_rising_chief: bool=False,
        specialty: str='',
        # TODO: add vacation_requests, elective_requests, schedule
    ):
        self._id = self._generate_id()
        self.first_name = first_name
        self.last_name = last_name
        self.year = year
        self.is_fellowship_applicant = is_fellowship_applicant
        self.is_rising_chief = is_rising_chief
        self.specialty = specialty

    def _generate_id(self):
        return str(uuid.uuid4())

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        raise AttributeError("Cannot manually set the 'id' attribute")

    def __repr__(self):
        return f"Resident(first_name={self.first_name}" \
               f", last_name={self.last_name}, year={self.year}" \
               + f", id={self.id})"

    def __str__(self):
        return f"{self.last_name}, {self.first_name}, year {self.year}"

    def __lt__(self, other):
        return (self.last_name, self.first_name, -self.year, self._id) \
               < (other.last_name, other.first_name, -other.year, other._id)

    def __eq__(self, other):
        return self._id == other._id
