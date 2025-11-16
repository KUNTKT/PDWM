# engine/schemas.py
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any, Union

class LatentOp(BaseModel):
    op: Literal["add", "remove"]
    cue: str = Field(min_length=1, max_length=60)

class SpaceUpdate(BaseModel):
    type: Literal["space_update"] = "space_update"
    space_id: str
    visible_state_delta: str = Field(..., max_length=60)
    latent_state_ops: List[LatentOp] = []
    importance_delta: int = 0
    reasons: List[str] = []

class NpcUpdate(BaseModel):
    type: Literal["npc_update"] = "npc_update"
    npc_id: str
    state_delta: Dict[str, Any] = {}
    memory_write: List[str] = []
    importance_delta: int = 0
    reasons: List[str] = []

class EventProposal(BaseModel):
    type: Literal["event_proposal"] = "event_proposal"
    event_id: str
    scope_spaces: List[str] = []
    suggested_probability: float
    possible_outcomes: List[str] = []
    justification: str

Update = Union[SpaceUpdate, NpcUpdate, EventProposal]

class UpdateList(BaseModel):
    updates: List[Update]
