from dataclasses import dataclass, field


@dataclass
class CheckResult:
    """The outcome of comparing an env file against an example file."""

    missing: list[str] = field(default_factory=list)  # in example, not in env
    extra: list[str] = field(default_factory=list)  # in env, not in example
    empty: list[str] = field(default_factory=list)  # in both, but env value is ""
    invalid: dict[str, str] = field(
        default_factory=dict
    )  # name -> problem (never the value)

    @property
    def ok(self) -> bool:
        return not (self.missing or self.empty or self.invalid)
