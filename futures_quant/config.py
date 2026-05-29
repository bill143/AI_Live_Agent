"""Typed configuration loader.

Loads ``config/default.yaml`` into frozen dataclasses so the rest of the code
reads typed attributes instead of poking at raw dicts. The loader also enforces
the master safety invariant: **live execution stays off unless explicitly,
loudly enabled.**
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_CONFIG_PATH = Path(__file__).with_name("config") / "default.yaml"


@dataclass(frozen=True)
class RiskConfig:
    max_daily_loss_usd: float
    hard_stop_usd: float
    max_position_contracts: int


@dataclass(frozen=True)
class RollConfig:
    policy: str
    calendar_days_before_expiry: int


@dataclass(frozen=True)
class DataConfig:
    root: str
    bar_interval: str
    session: str
    timezone_canonical: str
    timestamp_edge: str


@dataclass(frozen=True)
class ExecutionConfig:
    venue: str
    enabled: bool


@dataclass(frozen=True)
class Config:
    mode: str
    live_enabled: bool
    instruments: tuple[str, ...]
    data: DataConfig
    roll: RollConfig
    risk: RiskConfig
    execution: ExecutionConfig

    def assert_safe_for_phase1(self) -> None:
        """Fail loudly if the config has been switched into a live state.

        Phase 1 is backtest-only. Live routing requires an explicit,
        human-approved change in a later phase, so we refuse to proceed if it
        has been turned on prematurely.
        """
        if self.live_enabled or self.execution.enabled or self.mode != "backtest":
            raise ValueError(
                "Live execution is not permitted in Phase 1. Found "
                f"mode={self.mode!r}, live_enabled={self.live_enabled}, "
                f"execution.enabled={self.execution.enabled}. "
                "Routing real orders is gated behind explicit per-phase approval."
            )


def load_config(path: str | Path | None = None) -> Config:
    """Load and type the configuration from YAML."""
    cfg_path = Path(path) if path is not None else _DEFAULT_CONFIG_PATH
    raw: dict[str, Any] = yaml.safe_load(cfg_path.read_text())

    return Config(
        mode=raw["mode"],
        live_enabled=bool(raw["live_enabled"]),
        instruments=tuple(raw["instruments"]),
        data=DataConfig(**raw["data"]),
        roll=RollConfig(**raw["roll"]),
        risk=RiskConfig(**raw["risk"]),
        execution=ExecutionConfig(**raw["execution"]),
    )
