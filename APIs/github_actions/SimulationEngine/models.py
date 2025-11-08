from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

# Enums for controlled vocabularies

class ActorType(str, Enum):
    USER = "User"
    BOT = "Bot"
    ORGANIZATION = "Organization"

class WorkflowState(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"
    DISABLED_FORK = "disabled_fork"
    DISABLED_INACTIVITY = "disabled_inactivity"
    DISABLED_MANUALLY = "disabled_manually"

class WorkflowRunStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ACTION_REQUIRED = "action_required"
    CANCELLED = "cancelled"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    SKIPPED = "skipped"
    STALE = "stale"
    SUCCESS = "success"
    TIMED_OUT = "timed_out"
    WAITING = "waiting"
    REQUESTED = "requested"
    PENDING = "pending"

class WorkflowRunConclusion(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"

class JobStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class JobConclusion(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral" # GitHub jobs can also have neutral conclusion
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out" # GitHub jobs can also have timed_out conclusion

class StepStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PENDING = "pending" # Steps can be pending
    SKIPPED = "skipped" # Steps can be skipped

class StepConclusion(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    NEUTRAL = "neutral"


# Common/Shared Models

class GithubUser(BaseModel):
    login: str
    id: int
    node_id: str
    type: ActorType
    site_admin: bool

class CommitPerson(BaseModel):
    name: str
    email: str

class HeadCommit(BaseModel):
    id: str  # SHA
    tree_id: str
    message: str
    timestamp: datetime
    author: Optional[CommitPerson] = None
    committer: Optional[CommitPerson] = None

class RepositoryBrief(BaseModel):
    id: int
    node_id: str
    name: str
    full_name: str # owner/repo
    private: bool
    owner: GithubUser

# Workflow Usage Models

class BillableOSEntry(BaseModel):
    total_ms: int
    jobs: int

class WorkflowUsageStats(BaseModel):
    billable: Dict[str, BillableOSEntry] = Field(default_factory=dict) # Keys: 'UBUNTU', 'MACOS', 'WINDOWS' etc.

# Workflow Model

class Workflow(BaseModel):
    id: int
    node_id: str
    name: str
    path: str  # Relative path to workflow file
    state: WorkflowState
    created_at: datetime
    updated_at: datetime
    # For internal linking/simulation convenience, not directly part of GitHub API response for this object
    # but helps in organizing data by repository.
    repo_owner_login: str
    repo_name: str
    # For storing usage stats directly with the workflow if desired, or can be separate
    usage: Optional[WorkflowUsageStats] = None

# Step and Job Models (part of WorkflowRun)

class Step(BaseModel):
    name: str
    status: StepStatus
    conclusion: Optional[StepConclusion] = None
    number: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class Job(BaseModel):
    id: int
    run_id: int # ID of the workflow run this job belongs to
    node_id: str
    head_sha: str # SHA of the commit
    name: str
    status: JobStatus
    conclusion: Optional[JobConclusion] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps: Optional[List[Step]] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    runner_id: Optional[int] = None
    runner_name: Optional[str] = None
    runner_group_id: Optional[int] = None
    runner_group_name: Optional[str] = None
    # run_attempt: int # The prompt says "latest job for each job name", implying re-runs of jobs within a run attempt.
                       # However, the job object itself doesn't list 'run_attempt' in the provided spec.
                       # It's usually associated with the WorkflowRun.

# Workflow Run Model

class WorkflowRun(BaseModel):
    id: int
    name: Optional[str] = None # Name of the workflow run (often same as workflow name or commit message)
    node_id: str
    head_branch: Optional[str] = None
    head_sha: str
    path: str # Path of the workflow file
    run_number: int
    event: str
    status: Optional[WorkflowRunStatus] = None
    conclusion: Optional[WorkflowRunConclusion] = None
    workflow_id: int # ID of the parent workflow
    check_suite_id: Optional[int] = None
    check_suite_node_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    run_attempt: int
    run_started_at: Optional[datetime] = None
    actor: Optional[GithubUser] = None
    triggering_actor: Optional[GithubUser] = None # If different from actor
    head_commit: Optional[HeadCommit] = None
    repository: RepositoryBrief
    # For internal linking/simulation convenience
    repo_owner_login: str
    repo_name: str
    # Jobs associated with this run
    jobs: List[Job] = Field(default_factory=list)

# Main Repository DB Structure
# This model represents a single repository in our in-memory database
class RepositoryModel(BaseModel):
    id: int # Unique ID for the repository in our simulation
    node_id: str # GitHub's node_id for the repository
    name: str # Repository name
    owner: GithubUser # Repository owner information
    private: bool = False

    workflows: Dict[int, Workflow] = Field(default_factory=dict) # Keyed by Workflow.id
    workflow_runs: Dict[int, WorkflowRun] = Field(default_factory=dict) # Keyed by WorkflowRun.id
    # WorkflowUsageStats are stored within each Workflow model in this design

# Top-level DB Model
class GithubActionAPIDB(BaseModel):
    # Stores repositories keyed by "owner_login/repo_name" for easy lookup
    repositories: Dict[str, RepositoryModel] = Field(default_factory=dict)

    # Global counters for unique IDs, if not derived from elsewhere
    _next_workflow_id: int = 1
    _next_run_id: int = 1
    _next_job_id: int = 1
    _next_repo_id: int = 1
    _next_user_id: int = 1 # For actors, owners etc.

class WorkflowDetail(BaseModel):
    """
    Represents the detailed structure of a workflow as returned by the API.
    """
    id: int
    node_id: str
    name: str
    path: str
    state: WorkflowState
    created_at: str
    updated_at: str
    

class WorkflowListItem(BaseModel):
    """
    Represents a single workflow item as returned by the list_workflows function.
    """
    id: int
    node_id: str
    name: str
    path: str
    state: str
    created_at: str
    updated_at: Optional[str]

class ListWorkflowsResponse(BaseModel):
    """
    Represents the overall structure returned by the list_workflows function.
    """
    total_count: int
    workflows: List[WorkflowListItem]
