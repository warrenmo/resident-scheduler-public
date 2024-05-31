"""service.py

Contains the Service class.

Classes:
    Service

"""

class Service:
    """
    A class that represents a service (a.k.a. rotation).

    Attributes
    ----------
    name : str
        the name of the service (e.g., "MICU", "wards")
    priority : int
    allows_vacations : bool
    is_core : bool
    min_interns_per_block : int
        the minimum number of interns required for this service per block
    max_interns_per_block : int,
        the maximum number of interns required for this service per block
    min_seniors_per_block : int,
        the minimum number of seniors required for this service per block
    max_seniors_per_block : int,
        the maximum number of seniors required for this service per block
    min_blocks_per_intern : int,
        the minimum number of blocks an intern should be assigned this service
    max_blocks_per_intern : int,
        the maximum number of blocks an intern should be assigned this service
    min_blocks_per_senior : int,
        the minimum number of blocks a senior should be assigned this service
    max_blocks_per_senior : int,
        the maximum number of blocks a senior should be assigned this service
    earliest_pgy2_block : int,
        the earliest block a pgy2 (second-year) resident may be assigned this
        service; (context) some services are significantly more difficult to be
        the senior on, so pgy2 residents should ideally obtain more experience
        being a senior prior to being assigned this service as a senior
    is_difficult : bool
    """
    def __init__(self,
                 *,
                 name: str,
                 #block_or_week: str,
                 priority: int,
                 allows_vacations: bool,
                 is_core: bool,
                 min_interns_per_block: int,
                 max_interns_per_block: int,
                 min_seniors_per_block: int,
                 max_seniors_per_block: int,
                 min_blocks_per_intern: int,
                 max_blocks_per_intern: int,
                 # NOTE: seniors is hardcoded to be PGY2 & PGY3
                 #       => min/max_blocks_per_senior is hardcoded to be over two years
                 min_blocks_per_senior: int,
                 max_blocks_per_senior: int,
                 earliest_pgy2_block: int=0,
                 is_difficult: bool=False):
        self.name = name
        #self.block_or_week = block_or_week
        self.priority = priority
        self.allows_vacations = allows_vacations
        self.is_core = is_core
        self.min_interns_per_block = min_interns_per_block
        self.max_interns_per_block = max_interns_per_block
        self.min_seniors_per_block = min_seniors_per_block
        self.max_seniors_per_block = max_seniors_per_block
        self.min_blocks_per_intern = min_blocks_per_intern
        self.max_blocks_per_intern = max_blocks_per_intern
        self.min_blocks_per_senior = min_blocks_per_senior
        self.max_blocks_per_senior = max_blocks_per_senior
        self.earliest_pgy2_block = earliest_pgy2_block
        self.is_difficult = is_difficult

    def __repr__(self):
        return f"Service(name={self.name})"

    def __str__(self):
        return self.name
