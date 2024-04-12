# pyre-ignore-all-errors
# flake8: noqa

type FancyTuple[T1, T2] = tuple[T1, T2]  # type: ignore[valid-type, name-defined]  # mypy
fancy_tuple1: FancyTuple[int, float] = (1, 2.0)  # type: ignore[valid-type]  # mypy
fancy_tuple2: FancyTuple = ("hello", "world")  # type: ignore[valid-type]  # mypy
