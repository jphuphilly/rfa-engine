"""
State tracking for the RFA Engine.
One JSON file per run, saved to ./output/{timestamp}.json.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_DIR = Path(__file__).parent.parent / "output"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


class RunState:
    """
    Tracks a single RFA debate run from start to finish.

    Structure:
    {
        "run_id": "20260319_143022",
        "created_at": "2026-03-19T14:30:22Z",
        "input": {
            "idea": "...",
            "mode": "idea",
            "max_rounds": 3
        },
        "rounds": [
            {
                "round_number": 1,
                "critiques": {
                    "customer": "...",
                    "hater": "...",
                    "builder": "...",
                    "vc": "...",
                    "growth": "...",
                    "indie": "..."
                },
                "scores": {
                    "customer": [7, 6],
                    "hater": [9, 7],
                    ...
                },
                "severities": {
                    "customer": ["MAJOR", "MAJOR"],
                    ...
                },
                "architect": "...",
                "revised_idea": "..."
            }
        ],
        "verdict": "PIVOT",
        "surviving_objections": "...",
        "assumption_test": "...",
        "total_api_calls": 7,
        "amplification_triggered": false
    }
    """

    def __init__(self, idea: str, mode: str = "idea", max_rounds: int = 3):
        self.run_id = _timestamp()
        self.file_path = OUTPUT_DIR / f"{self.run_id}.json"

        self._data: dict[str, Any] = {
            "run_id": self.run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "input": {
                "idea": idea,
                "mode": mode,
                "max_rounds": max_rounds,
            },
            "rounds": [],
            "verdict": None,
            "surviving_objections": None,
            "assumption_test": None,
            "total_api_calls": 0,
            "amplification_triggered": False,
        }

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self._save()

    # ------------------------------------------------------------------
    # Round management
    # ------------------------------------------------------------------

    def start_round(self, round_number: int) -> None:
        """Add a new round slot."""
        self._data["rounds"].append({
            "round_number": round_number,
            "critiques": {},
            "scores": {},
            "severities": {},
            "architect": None,
            "revised_idea": None,
        })
        self._save()

    def set_critique(
        self,
        persona: str,
        critique_text: str,
        scores: list[int],
        severities: list[str],
    ) -> None:
        """Record one critic's output for the current round."""
        round_ = self._current_round()
        round_["critiques"][persona] = critique_text
        round_["scores"][persona] = scores
        round_["severities"][persona] = severities
        self._data["total_api_calls"] += 1
        self._save()

    def set_architect(self, architect_text: str, revised_idea: str) -> None:
        """Record the Architect's output for the current round."""
        round_ = self._current_round()
        round_["architect"] = architect_text
        round_["revised_idea"] = revised_idea
        self._data["total_api_calls"] += 1
        self._save()

    # ------------------------------------------------------------------
    # Final outputs
    # ------------------------------------------------------------------

    def set_verdict(self, verdict: str, surviving_objections: str) -> None:
        self._data["verdict"] = verdict
        self._data["surviving_objections"] = surviving_objections
        self._save()

    def set_assumption_test(self, text: str) -> None:
        self._data["assumption_test"] = text
        self._data["total_api_calls"] += 1
        self._save()

    def set_amplification_triggered(self) -> None:
        self._data["amplification_triggered"] = True
        self._save()

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    @property
    def current_idea(self) -> str:
        """The most recent idea text (original or latest revision)."""
        for round_ in reversed(self._data["rounds"]):
            if round_["revised_idea"]:
                return round_["revised_idea"]
        return self._data["input"]["idea"]

    @property
    def round_number(self) -> int:
        return len(self._data["rounds"])

    @property
    def input_idea(self) -> str:
        return self._data["input"]["idea"]

    @property
    def max_rounds(self) -> int:
        return self._data["input"]["max_rounds"]

    def get_round(self, round_number: int) -> dict:
        return self._data["rounds"][round_number - 1]

    def get_all_scores(self) -> dict[str, list[int]]:
        """Flat map of persona → scores for the most recent round."""
        if not self._data["rounds"]:
            return {}
        return self._current_round().get("scores", {})

    def get_all_severities(self) -> dict[str, list[str]]:
        """Flat map of persona → severities for the most recent round."""
        if not self._data["rounds"]:
            return {}
        return self._current_round().get("severities", {})

    def count_fatals(self) -> int:
        """Count FATAL objections in the most recent round."""
        total = 0
        for sevs in self.get_all_severities().values():
            total += sum(1 for s in sevs if s == "FATAL")
        return total

    def count_majors(self) -> int:
        """Count MAJOR objections in the most recent round."""
        total = 0
        for sevs in self.get_all_severities().values():
            total += sum(1 for s in sevs if s == "MAJOR")
        return total

    def count_minors(self) -> int:
        """Count MINOR objections in the most recent round."""
        total = 0
        for sevs in self.get_all_severities().values():
            total += sum(1 for s in sevs if s == "MINOR")
        return total

    @property
    def to_dict(self) -> dict:
        return self._data

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _current_round(self) -> dict:
        if not self._data["rounds"]:
            raise RuntimeError("No rounds started. Call start_round() first.")
        return self._data["rounds"][-1]

    def _save(self) -> None:
        with open(self.file_path, "w") as f:
            json.dump(self._data, f, indent=2)

    @classmethod
    def load(cls, file_path: str) -> "RunState":
        """Load a previously saved run from disk."""
        instance = object.__new__(cls)
        with open(file_path) as f:
            instance._data = json.load(f)
        instance.run_id = instance._data["run_id"]
        instance.file_path = Path(file_path)
        return instance
