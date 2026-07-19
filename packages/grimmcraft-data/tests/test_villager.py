"""The villager profession and job-site registries, and the mapping between them.

The mapping is curated rather than read from a Mojang file (see
``_generate/advanced_villager.py`` for why), so these are the tests that keep it
honest — they check it against data that *is* Mojang's.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from grimmcraft_data import (
    VillagerProfession,
    VillagerWorkstation,
    profession_for_workstation,
    workstation_for_block,
    workstation_for_profession,
)
from grimmcraft_data.block import Block

VERSION = "1.21.11"
PACKAGE_DIRECTORY = Path(__file__).resolve().parents[1] / "srcs" / "grimmcraft_data"
GENERATOR = PACKAGE_DIRECTORY / "_generate" / "advanced_villager.py"

WITHOUT_A_JOB = {VillagerProfession.NONE, VillagerProfession.NITWIT}
EMPLOYED = [p for p in VillagerProfession if p not in WITHOUT_A_JOB]


# --- ids ---------------------------------------------------------------------


@pytest.mark.parametrize("profession", list(VillagerProfession))
def test_string_id_matches_the_house_convention(profession: VillagerProfession) -> None:
    """``string_id`` is what the compiler's validation and dialect rely on."""
    assert profession.string_id.startswith("minecraft:")
    assert profession.string_id == f"minecraft:{profession.name.lower()}"


@pytest.mark.parametrize("workstation", list(VillagerWorkstation))
def test_workstation_ids_match_too(workstation: VillagerWorkstation) -> None:
    assert workstation.string_id == f"minecraft:{workstation.name.lower()}"


def test_the_profession_list_is_mojangs(subtests) -> None:
    """Every profession in the shipped language.json, and no extras."""
    language = json.loads(
        (PACKAGE_DIRECTORY / "data" / VERSION / "language.json").read_text(encoding="utf-8")
    )
    prefix = "entity.minecraft.villager."
    from_mojang = {key[len(prefix) :] for key in language if key.startswith(prefix)}
    ours = {profession.name.lower() for profession in VillagerProfession}
    assert ours == from_mojang


# --- the mapping -------------------------------------------------------------


@pytest.mark.parametrize("profession", EMPLOYED)
def test_every_workstation_block_really_exists(profession: VillagerProfession) -> None:
    """A block id the registry does not have would only show up in game."""
    assert profession.workstation in {block.string_id for block in Block}


@pytest.mark.parametrize("profession", EMPLOYED)
def test_the_mapping_round_trips(profession: VillagerProfession) -> None:
    assert profession_for_workstation(workstation_for_profession(profession)) is profession


@pytest.mark.parametrize("workstation", list(VillagerWorkstation))
def test_the_mapping_round_trips_the_other_way(workstation: VillagerWorkstation) -> None:
    assert workstation_for_profession(workstation.profession) == workstation.string_id


def test_the_two_enums_agree() -> None:
    """A table that disagrees with itself is what this pair of tests exists for."""
    named_by_professions = {p.workstation for p in EMPLOYED}
    named_by_workstations = {w.string_id for w in VillagerWorkstation}
    assert named_by_professions == named_by_workstations

    professions_with_a_job = {p.string_id for p in EMPLOYED}
    professions_claimed = {w.profession for w in VillagerWorkstation}
    assert professions_with_a_job == professions_claimed


# --- the professions that have no job ----------------------------------------


@pytest.mark.parametrize("profession", sorted(WITHOUT_A_JOB, key=lambda p: p.name))
def test_jobless_professions_return_none_rather_than_raising(
    profession: VillagerProfession,
) -> None:
    """NONE and NITWIT are real professions with no block, not gaps in the data."""
    assert profession.workstation is None
    assert workstation_for_profession(profession) is None


def test_a_block_that_is_not_a_job_site_maps_to_nothing() -> None:
    assert profession_for_workstation("minecraft:crafting_table") is None
    assert workstation_for_block("minecraft:crafting_table") is None


def test_lookups_accept_an_id_or_an_enum_member() -> None:
    assert profession_for_workstation(Block.COMPOSTER) is VillagerProfession.FARMER
    assert profession_for_workstation("minecraft:composter") is VillagerProfession.FARMER


# --- the generator -----------------------------------------------------------


def test_the_generator_is_deterministic() -> None:
    """Checked-in output means drift shows up as a diff; this proves there is none."""
    before = {
        name: (PACKAGE_DIRECTORY / name).read_text(encoding="utf-8")
        for name in ("villager_profession.py", "villager_workstation.py")
    }
    subprocess.run([sys.executable, str(GENERATOR)], check=True, capture_output=True)
    for name, text in before.items():
        assert (PACKAGE_DIRECTORY / name).read_text(encoding="utf-8") == text


def test_the_curated_table_verifies_against_the_real_data() -> None:
    """``--check`` is what CI should call; it must pass on a clean tree."""
    finished = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"], capture_output=True, text=True
    )
    assert finished.returncode == 0, finished.stdout + finished.stderr
