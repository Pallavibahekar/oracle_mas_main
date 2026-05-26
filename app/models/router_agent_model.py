from pydantic import BaseModel
from typing import Literal


class AgentNodeState(BaseModel):
    state: Literal["working", "input_required", "completed"] = "working"
