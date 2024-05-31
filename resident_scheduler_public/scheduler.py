"""scheduler.py

Contains the Scheduler class.

Classes:
    Scheduler

"""

import itertools
import random

import pandas as pd
from scipy.special import comb

from .constants import NUM_BLOCKS_PER_YEAR, NUM_YEARS, WEEKS_PER_BLOCK
from .resident import Resident
from .service import Service

class Scheduler:
    """
    A class that creates the year-long schedule for medical residents.

    The (private) functions in this class frequently take as parameters or make
    use of `(b_idx, r_idx, s_idx)`, which are short for block index, resident
    index, and service index, respectively:
        - b_idx
            - represents the current block of the current year
            - 0 <= b_idx < self.num_blocks_per_year
        - r_idx
            - indexes into self.residents
        - s_idx
            - indexes into self.services

    Attributes
    ----------
    services : list[Service]
        list of all possible services that a resident can be assigned
    residents : list[Resident]
        list of all residents
    weeks_per_block : int
        number of weeks per block
    num_blocks_per_year : int
        number of blocks for the year; e.g., if each block is 4 weeks, then
        this should be 13
    num_years : int
        number of years that someone entering the residency program will take
        to complete the program
    random_seed : int
        currently, the random seed will only be used for sorting purposes; see
        the `self._block_resident_order` method for more details
    _schedule : list[list[int]]
        the year-long schedule from each resident's perspective;
        dimensions will be `R` by `B` where `R` is the number of residents and
        `B` the number of blocks per year; the value `v` at position `(i, j)`
        is an index into `self.services` representing the service resident `i`
        will be assigned to for block `j`
    _service_schedule : list[list[set[int]]]
        the year-long schedule from each service's perspective;
        dimensions will be `S` by `B` where `S` is the number of services and
        `B` the number of blocks per year; the value `v` at position `(i, j)`
        is a set of indices into `self.residents` representing the residents
        that will be assigned to service `i` for block `j`
    expected_rate_per_service : list[float]
        represents the approximate rate at which each service should be
        completed over the course of the residency program
    resident_service_count : list[list[int]]
        an `R`-by-`S`-dimensional grid where the value `v` at position `(i, j)`
        represents the number of times resident `i` has been assigned to
        service `j`
    remaining_residents_per_block : list[int]
        a `B`-length list where `B` is `self.num_blocks_per_year` and the value
        `v` at position `i` represents the number of residents yet to be
        assigned a service for block `i`
    remaining_blocks_per_resident : list[int]
        an `R`-length list where `R` is the number of residents and the value
        `v` at position `i` represents the number of blocks yet to be assigned
        a service for resident `i`
    remaining_service_spots_per_service_per_block : list[list[int]]
        an `S`-by-`B`-dimensional grid where the value `v` at position `(i, j)`
        represents the number of remaining unassigned spots for service `i` for
        block `j`
    remaining_spots_per_block : list[int]
        a `B`-length list where `B` is `self.num_blocks_per_year` and the value
        `v` at position `i` represents the number of unassigned spots for all
        services for block `i`

    Methods
    -------
    create(resident_service_count, randomize, verbose)
        creates and returns a valid schedule, if one can be created

    """
    def __init__(
            self,
            *,
            services: list[Service],
            residents: list[Resident],
            weeks_per_block: int=WEEKS_PER_BLOCK,
            num_blocks_per_year: int=NUM_BLOCKS_PER_YEAR,
            num_years: int=NUM_YEARS,
            random_seed: int=0,
    ):
        self.services = services
        # NOTE: bias may occur for or against names earlier in the alphabet;
        #       set `randomize=True` in `self.create` to prevent this
        self.residents = sorted(residents)
        self.weeks_per_block = weeks_per_block
        self.num_blocks_per_year = num_blocks_per_year
        self.num_years = num_years
        self.random_seed = random_seed
        self._schedule = [
            [-1] * self.num_blocks_per_year
            for _ in self.residents
        ]
        self._service_schedule = [
            [set() for _ in range(self.num_blocks_per_year)]
            for _ in range(len(self.services))
        ]
        # NOTE: uses min_blocks_per_senior
        self.expected_rate_per_service = [
            self.services[s_idx].min_blocks_per_senior \
            / ((self.num_years - 1) * self.num_blocks_per_year)
            for s_idx in range(len(self.services))
        ]
        self._reset_resident_service_count()
        self._get_remaining()

    @property
    def schedule(self):
        return self._schedule if self._is_valid_schedule() else None

    @schedule.setter
    def schedule(self, value):
        raise AttributeError("Cannot manually set the 'schedule' attribute")

    @property
    def service_schedule(self):
        return self._service_schedule if self._is_valid_schedule() else None

    @service_schedule.setter
    def service_scheduleschedule(self, value):
        raise AttributeError("Cannot manually set the 'schedule' attribute")

    def _reset_resident_service_count(self):
        self.resident_service_count = [
            [0] * len(self.services) for _ in range(len(self.residents))
        ]

    def _get_remaining(self):
        """
        Establish the remaining* attributes.
        """
        # how many residents have yet to be assigned a service for this block
        self.remaining_residents_per_block = [
            sum(
                self._schedule[r_idx][b_idx] == -1
                for r_idx in range(len(self.residents))
            )
            for b_idx in range(self.num_blocks_per_year)
        ]
        # how many blocks have yet to be assigned a service for this resident
        self.remaining_blocks_per_resident = [
            sum(s_idx == -1 for s_idx in resident_schedule) \
            + (self.num_years - self.residents[r_idx].year + 1) \
            * self.num_blocks_per_year
            for r_idx, resident_schedule in enumerate(self._schedule)
        ]
        # how many more residents need to be assigned to this service for this
        #   block
        self.remaining_spots_per_service_per_block = [
            [s.min_seniors_per_block for _ in range(self.num_blocks_per_year)]
            for s in self.services
        ]
        # how many more residents need to be assigned to any service for this
        # block
        _spots = sum(remaining_spots[0] for remaining_spots in self.remaining_spots_per_service_per_block)
        self.remaining_spots_per_block = [_spots] * self.num_blocks_per_year

    def _get_rules(self):
        """
        Returns a list of predicate functions, where each function models a rule
        specific to this residency program and evaluates to True if the rule has
        been violated.
        All functions are of the form f(b_idx, r_idx, s_idx).
        """
        # resident has already been assigned this service the maximum # of times
        def max_service_count_reached(b_idx, r_idx, s_idx):
            return self.resident_service_count[r_idx][s_idx] \
                   == self.services[s_idx].max_blocks_per_senior

        # 2nd-year resident cannot senior this service yet
        def too_early_for_second_year(b_idx, r_idx, s_idx):
            return self.residents[r_idx].year == 2 \
                   and b_idx + 1 < self.services[s_idx].earliest_pgy2_block

        # fellowship applicants can't be on core services on blocks 3 or 4
        def fellowship_applicant_block_three_or_four(b_idx, r_idx, s_idx):
            return (b_idx == 3 or b_idx == 4) \
                   and self.residents[r_idx].is_fellowship_applicant \
                   and self.services[s_idx].is_core

        # rising chiefs shouldn't be assigned to a service on last block
        def rising_chief_last_block(b_idx, r_idx, s_idx):
            return b_idx == self.num_blocks_per_year - 1 \
                   and self.residents[r_idx].is_rising_chief

        # 3rd-year residents shouldn't be on core services on last block
        def third_year_last_block(b_idx, r_idx, s_idx):
            return b_idx == 12 \
                   and self.residents[r_idx].year == 3 \
                   and self.services[s_idx].is_core

        return [
            max_service_count_reached,
            too_early_for_second_year,
            fellowship_applicant_block_three_or_four,
            rising_chief_last_block,
            third_year_last_block
        ]

    def _any_rule_violated(self, b_idx, r_idx, s_idx):
        """
        Run all rules on a given block-resident-service combination.
        Returns True if any of the rules were violated.
        """
        return any(pred(b_idx, r_idx, s_idx)
                   for pred in self._get_rules())

    def _block_resident_order(self, randomize=True):
        """
        Establishes the order of resident-block pairs we'll assign services to
        in `self.create`.
        """
        # `restrictions` represents the number of disallowed services per
        #   resident-block pair
        restrictions = {
            (b_idx, r_idx): 0
            for b_idx, r_idx in itertools.product(
                range(self.num_blocks_per_year),
                range(len(self.residents))
            )
        }
        # `restrictions_by_block` represents the number of disallowed services
        #   across all residents for a given block
        restrictions_by_block = [0] * self.num_blocks_per_year
        for b_idx, r_idx in restrictions.keys():
            r = sum(
                self.services[s_idx].min_seniors_per_block \
                / self.services[s_idx].max_blocks_per_senior
                for s_idx in range(len(self.services))
                if self._any_rule_violated(b_idx, r_idx, s_idx)
            )
            restrictions[(b_idx, r_idx)] = r
            restrictions_by_block[b_idx] += r

        def block_resident_sort_key(block_resident_pair):
            b_idx, r_idx = block_resident_pair
            return (
                # prioritize blocks that have a lot of restrictions
                -restrictions_by_block[b_idx],
                # prioritize earlier blocks
                b_idx,
                # prioritize individual resident-block pairs w/ restrictions
                -restrictions[block_resident_pair],
                # prioritize more senior residents first
                -self.residents[r_idx].year,
                # randomize the rest
                random.random() if randomize else r_idx
            )

        random.seed(self.random_seed)
        return [
            (b_idx, r_idx)
            for b_idx, r_idx in sorted(
                restrictions.keys(),
                key=block_resident_sort_key
                #key=lambda x: (
                #    -restrictions_by_block[x[0]],
                #    x[0],
                #    -restrictions[(x[0], x[1])],
                #    -self.residents[x[1]].year,
                #    x[1]
                #)
            )
        ]

    def _initialize_service_count(
        self,
        resident_service_count: dict[int, dict[int,int]]=None):
        """
        Non-first-year residents will have already completed some services in
        their previous year(s). So, we'll need to factor in their histories.

        Parameters
        ----------
        resident_service_count : dict[int, dict[int, int]]
            represents the number of times each resident has performed a
            particular service; the top-level keys represent residents
            (`r_idx`), the second-level keys services (`s_idx`), and the values
            the count; if there are any residents that aren't first-years, then
            you'll almost certainly need to supply this argument
        """
        if resident_service_count is None:
            self._reset_resident_service_count()
        else:
            for r_idx, service_count in resident_service_count.items():
                for s_idx, count in service_count.items():
                    self.resident_service_count[r_idx][s_idx] = count

    def _service_cooldown(self, b_idx, r_idx, s_idx):
        """
        Service sorting criteria.
        Add 2 to your score for each time you're assigned that service in block
            b_idx - 1 or b_idx + 1
        Add 1 to your score for each time you're assigned that service in block
            b_idx - 2 or b_idx + 2
        """
        score = 0
        for i in range(1, 3):
            if (b_idx >= i and self._schedule[r_idx][b_idx - i] == s_idx):
                score += 3 - i
            if (
                    b_idx + i < self.num_blocks_per_year
                    and self._schedule[r_idx][b_idx + i] == s_idx
            ):
                score += 3 - i
        return score

    def _consecutive_difficult_services(self, b_idx, r_idx, s_idx):
        """
        Service sorting criteria.
        For the given resident, returns True if both this current service is
        difficult and either the previous or next block's service for the given
        resident is difficult.
        """
        return (
            self.services[s_idx].is_difficult \
            and any (
                # neighboring block idx is valid
                0 <= nei_b_idx < self.num_blocks_per_year \
                # the assigned service idx of the neighboring block is valid
                and 0 <= self._schedule[r_idx][nei_b_idx] < len(self.services) \
                # the assigned service is difficult
                and self.services[self._schedule[r_idx][nei_b_idx]].is_difficult
                for nei_b_idx in (b_idx-1, b_idx+1)
            )
        )

    def _service_sort_key(self, b_idx, r_idx, s_idx):
        """
        When choosing a service for a given resident and block, this function
        returns the key by which we'll sort the services from which we'll
        choose.
        TODO: factor in resident's history (difficulty of previous rotation,
              who they've worked with already, and perhaps more) along with
              what rotations haven't met their minimum staffing quota
        """
        return (
            # try not to immediately repeat the same service
            self._service_cooldown(b_idx, r_idx, s_idx),
            # try not to have two consecutive difficult services
            self._consecutive_difficult_services(b_idx, r_idx, s_idx),
            # prioritize services with the most spots to be filled for the
            #   block, esp those where the max blocks per senior is low
            (
                self.remaining_spots_per_service_per_block[s_idx][b_idx] \
                - self.services[s_idx].max_blocks_per_senior
            ),
            # complete services at an even rate
            (
                self.expected_rate_per_service[s_idx] \
                - (self.resident_service_count[r_idx][s_idx] \
                   / self.remaining_blocks_per_resident[r_idx])
            ),
        )

    def _assign(self, b_idx, r_idx, s_idx):
        """
        Assigns a resident to a service for a particular block.
        """
        self._schedule[r_idx][b_idx] = s_idx
        self._service_schedule[s_idx][b_idx].add(r_idx)
        self.resident_service_count[r_idx][s_idx] += 1
        self.remaining_spots_per_service_per_block[s_idx][b_idx] -= 1
        self.remaining_spots_per_block[b_idx] -= 1
        self.remaining_residents_per_block[b_idx] -= 1
        self.remaining_blocks_per_resident[r_idx] -= 1

    def _assign_free_block(self, b_idx, r_idx):
        """
        Explicitly assigns a resident a "free" block (i.e., no service).
        Notes:
            - we use len(self.services) to denote the "free" block.
            - this is different from a resident having not yet been
              assigned a service for a particular block, which is denoted with
              -1.
        """
        # len(self.services) means explicitly no service
        self._schedule[r_idx][b_idx] = len(self.services)
        self.remaining_residents_per_block[b_idx] -= 1
        self.remaining_blocks_per_resident[r_idx] -= 1

    def _unassign(self, b_idx, r_idx, s_idx):
        """
        Unassigns a resident from a service for a particular block.
        """
        self._schedule[r_idx][b_idx] = -1
        self._service_schedule[s_idx][b_idx].remove(r_idx)
        self.resident_service_count[r_idx][s_idx] -= 1
        self.remaining_spots_per_service_per_block[s_idx][b_idx] += 1
        self.remaining_spots_per_block[b_idx] += 1
        self.remaining_residents_per_block[b_idx] += 1
        self.remaining_blocks_per_resident[r_idx] += 1

    def _put_rising_chiefs_on_pseudo_elective(self):
        """
        Rising chiefs should be assigned a "free" block in the last block of
        the year.
        """
        for r_idx in range(len(self.residents)):
            if self.residents[r_idx].is_rising_chief:
                self._assign_free_block(self.num_blocks_per_year - 1, r_idx)

    def _is_valid_schedule(self):
        return all(
            self.services[s_idx].min_seniors_per_block <= len(assigned_set) \
            <= self.services[s_idx].max_seniors_per_block
            for s_idx, service_year in enumerate(self._service_schedule)
            for assigned_set in service_year
        )

    def create(
            self,
            *,
            resident_service_count: dict[int, dict[int, int]]=None,
            randomize: bool=True,
            verbose: bool=False,
    ):
        """
        Creates the year-long schedule. This is the primary function of the
        class.

        First, we establish the `order` of resident-block pairs over which
        we'll backtrack. The order should give us resident-block pairs from
        most restrictive (fewest possible services to choose from) to least.
        See `self._block_resident_order` for more details.

        Then, for each pair, we'll sort the possible services that we can
        assign in order from highest priority to lowest. See
        `self._service_sort_key` for more details.

        Parameters
        ----------
        resident_service_count : dict[int, dict[int, int]]
            represents the number of times each resident has performed a
            particular service; the top-level keys represent residents
            (`r_idx`), the second-level keys services (`s_idx`), and the values
            the count; if there are any residents that aren't first-years, then
            you'll almost certainly need to supply this argument
        randomize : bool
            when we sort the block-resident pairs, there may be groups of pairs
            that have the same priority; in this case, if `randomize` is True,
            then we'll randomize the order of the pairs within each group; this
            should help prevent bias for or against residents with names
            earlier in the alphabet
        verbose : bool
            primarily for testing purposes
        """
        # setup
        self._put_rising_chiefs_on_pseudo_elective()
        self._initialize_service_count(resident_service_count)
        self._get_remaining()

        # get the block-resident pair order, over which `backtrack` will
        #   recurse
        order = self._block_resident_order(randomize=randomize)

        def backtrack(idx):
            if idx == len(order):
                return self._is_valid_schedule()

            b_idx, r_idx = order[idx]
            if self._schedule[r_idx][b_idx] != -1:
                return backtrack(idx + 1)

            s_idxs = sorted(
                range(len(self.services)),
                key=lambda s_idx: self._service_sort_key(b_idx, r_idx, s_idx)
            )
            for s_idx in s_idxs:
                # if the service is at max capacity or any of the rules have
                # been violated, continue
                if self.remaining_spots_per_service_per_block[s_idx][b_idx] == 0 \
                   or self._any_rule_violated(b_idx, r_idx, s_idx):
                    continue
                else:
                    self._assign(b_idx, r_idx, s_idx)
                    res = backtrack(idx + 1)
                    if res:
                        return res
                    else:
                        self._unassign(b_idx, r_idx, s_idx)

            # there are more remaining seniors this block than remaining
            #   service spots so this senior can take a break
            if (
                    self.remaining_residents_per_block[b_idx] \
                    > self.remaining_spots_per_block[b_idx]
            ):
                self._assign_free_block(b_idx, r_idx)
                if backtrack(idx + 1):
                    return True

            # failed to create a valid schedule
            if verbose:
                print(
                    f"Failed to find valid service in block {b_idx + 1}"
                    + f" for resident {self.residents[r_idx]}"
                    + f" ({self.remaining_residents_per_block[b_idx]}"
                    + f" remaining residents)"
                )
            return False

        res = backtrack(0)
        if verbose and not res:
            print("Failed to create a valid schedule.")
            return None
        else:
            return self.schedule

    def _pretty_resident_service_count(self):
        """
        Returns a pandas DataFrame that shows the number of service completions
        for each resident at year-end after using the created `self._schedule`.
        """
        # TODO: include "Elective" count
        return pd.DataFrame(self.resident_service_count,
                            index=self.residents,
                            columns=self.services)

    def _pretty_schedule(self):
        """
        Returns a pandas DataFrame that represents self._schedule using the
        service names (rather than something like `s_idx`).
        """
        def name(s_idx):
            if s_idx == -1:
                return "n/a"
            elif s_idx == len(self.services):
                return "Elective"
            else:
                return self.services[s_idx].name

        return pd.DataFrame(
            [[name(val) for val in row] for row in self._schedule],
            index=self.residents,
            columns=range(1, self.num_blocks_per_year + 1)
        )

    def _service_schedule_stats(self):
        """
        Returns a pandas DataFrame that shows the minimum and maximum number of
        residents covering a service over the year.
        """
        service_schedule = pd.DataFrame(
            [
                [len(residents) for residents in row]
                for row in self._service_schedule
            ],
            index=self.services,
            columns=range(1, self.num_blocks_per_year + 1)
        )
        min_ = pd.DataFrame(service_schedule.min(axis=1), columns=["min"])
        max_ = pd.DataFrame(service_schedule.max(axis=1), columns=["max"])
        service_schedule = pd.concat([service_schedule, min_, max_], axis=1)
        return service_schedule

    def __str__(self):
        return f"Resident Schedule:\n{self._pretty_schedule()}\n" \
               + f"\n\n# of Seniors per Service per Block:" \
               + f"\n{self._service_schedule_stats()}" \
               + f"\n\nResident Service Count:" \
               + f"\n{self._pretty_resident_service_count()}"
