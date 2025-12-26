"""Planning domain enumerations."""

from enum import StrEnum


class Day(StrEnum):
    """Days of the week for meal scheduling."""

    MON = "Mon"
    TUE = "Tue"
    WED = "Wed"
    THU = "Thu"
    FRI = "Fri"
    SAT = "Sat"
    SUN = "Sun"

    @classmethod
    def weekdays(cls) -> tuple["Day", ...]:
        """Return tuple of weekdays (Mon-Fri)."""
        return (cls.MON, cls.TUE, cls.WED, cls.THU, cls.FRI)

    @classmethod
    def weekend(cls) -> tuple["Day", ...]:
        """Return tuple of weekend days (Sat-Sun)."""
        return (cls.SAT, cls.SUN)
