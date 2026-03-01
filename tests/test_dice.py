import pytest

from lib.dice import DiceRoller


def test_roll_rejects_trailing_garbage_after_standard_notation():
    roller = DiceRoller()

    with pytest.raises(ValueError):
        roller.roll("1d20oops")


def test_roll_rejects_trailing_garbage_after_keep_highest_notation():
    roller = DiceRoller()

    with pytest.raises(ValueError):
        roller.roll("2d20kh1extra")
