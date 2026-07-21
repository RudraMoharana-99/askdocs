import logging
from dataclasses import dataclass
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)

CheckFn = Callable[[], Awaitable[None]]


@dataclass(frozen=True)
class DependencyCheck:
    name: str
    check: CheckFn


_checks: list[DependencyCheck] = []


def register_check(name: str, check: CheckFn) -> None:
    _checks.append(DependencyCheck(name=name, check=check))


async def run_checks() -> tuple[bool, dict[str, str]]:
    results: dict[str, str] = {}
    healthy = True

    for dependency in _checks:
        try:
            await dependency.check()
            results[dependency.name] = "ok"
        except Exception as exc:
            healthy = False
            results[dependency.name] = "unavailable"

            logger.warning(
                "readiness_check_failed",
                extra={"dependency": dependency.name, "error": str(exc)}
            )
    return healthy, results