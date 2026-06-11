from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ModelVia(str, Enum):
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    MLX = "mlx"
    LLAMACPP = "llamacpp"
    LMSTUDIO = "lmstudio"


class ScopeKind(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"
    CUSTOM = "custom"


class HarnessCapabilities(BaseModel):
    supports_subagent_model: bool = False
    supports_tool_permissions: str = "none"  # e.g. "full", "partial", "none"
    supports_mcp: bool = False


class HarnessScope(BaseModel):
    name: str
    kind: ScopeKind
    path: str
    launch_env: Optional[Dict[str, str]] = None
    enabled: bool = True


class HarnessTarget(BaseModel):
    capabilities: HarnessCapabilities
    scopes: List[HarnessScope] = Field(default_factory=list)


class Profile(BaseModel):
    preferred_tier: Optional[str] = None
    budget_limit: Optional[float] = None


class MCPServer(BaseModel):
    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    disabled: bool = False


class ModelSource(BaseModel):
    via: ModelVia
    id: str
    cost: Optional[Dict[str, float]] = None
    base_url: Optional[str] = None
    key_ref: Optional[str] = None


class Model(BaseModel):
    sources: List[ModelSource] = Field(default_factory=list)


class Tier(BaseModel):
    primary: str
    fallback: Optional[str] = None


class AgentRole(str, Enum):
    HUB = "hub"
    WORKER = "worker"


class Agent(BaseModel):
    tier: str
    role: AgentRole
    can_delegate: List[str] = Field(default_factory=list)
    escalates_to: Optional[str] = None
    delegate_via: Optional[str] = None  # e.g., "cli"


class Spec(BaseModel):
    version: str = "1.0"
    harness: Dict[str, HarnessTarget] = Field(default_factory=dict)
    tiers: Dict[str, Tier] = Field(default_factory=dict)
    models: Dict[str, Model] = Field(default_factory=dict)
    mcp: Dict[str, MCPServer] = Field(default_factory=dict)
    agents: Dict[str, Agent] = Field(default_factory=dict)
    profiles: Dict[str, Profile] = Field(default_factory=dict)
