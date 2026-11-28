from dataclasses import dataclass, field


@dataclass
class DiffResult:
    """Differences between two env files, A and B."""

    only_in_a: list[str] = field(default_factory=list)
    only_in_b: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)  # in both, different values

    @property
    def identical(self) -> bool:
        return not (self.only_in_a or self.only_in_b or self.changed)


def diff_envs(
    a: dict[str, str], b: dict[str, str], keys_only: bool = False
) -> DiffResult:
    """Compare two parsed env files. With keys_only, value differences are ignored."""
    keys_a, keys_b = set(a), set(b)
    changed = [] if keys_only else sorted(k for k in keys_a & keys_b if a[k] != b[k])
    return DiffResult(
        only_in_a=sorted(keys_a - keys_b),
        only_in_b=sorted(keys_b - keys_a),
        changed=changed,
    )
