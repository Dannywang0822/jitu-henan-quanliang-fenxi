"""裁定记录。中枢无执行动作。"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict


class HubHasNoExecution(RuntimeError):
    """决策中枢无执行动作。"""


SHANGHAI = timezone(timedelta(hours=8))


class RulingRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    ruling_id: str
    裁定人: str
    方案: str
    依据: str
    生效时间: str
    recorded_at: str


class Hub:
    """收题、选项、裁定记录。不发薪、不调度、不签加盟政策。"""

    def __init__(self) -> None:
        self.questions: list[dict[str, Any]] = []
        self.options: list[dict[str, Any]] = []
        self.rulings: list[RulingRecord] = []

    def collect_question(self, question: str, *, source: str) -> None:
        self.questions.append({"question": question, "source": source})

    def add_option(self, option: dict[str, Any]) -> None:
        self.options.append(option)

    def record_ruling(self, record: dict[str, Any]) -> RulingRecord:
        ruling = RulingRecord(
            ruling_id=record.get("ruling_id", f"r{len(self.rulings)+1}"),
            裁定人=record["裁定人"],
            方案=record["方案"],
            依据=record["依据"],
            生效时间=record["生效时间"],
            recorded_at=datetime.now(SHANGHAI).isoformat(),
        )
        self.rulings.append(ruling)
        return ruling

    def execute(self, *_args, **_kwargs) -> None:
        raise HubHasNoExecution("决策中枢无执行动作")

    def 发薪(self, *_args, **_kwargs) -> None:
        raise HubHasNoExecution("决策中枢无执行动作：不发薪")

    def 调度(self, *_args, **_kwargs) -> None:
        raise HubHasNoExecution("决策中枢无执行动作：不调度")

    def 签加盟商政策(self, *_args, **_kwargs) -> None:
        raise HubHasNoExecution("决策中枢无执行动作：不签加盟商政策")
