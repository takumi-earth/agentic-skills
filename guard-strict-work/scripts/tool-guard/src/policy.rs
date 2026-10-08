use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Trusted policy supplied by the operator, never by model tool arguments.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Policy {
    pub schema_version: u8,
    #[serde(default)]
    pub session_id: Option<String>,
    #[serde(default)]
    pub bun_executable: Option<PathBuf>,
    #[serde(default)]
    pub write_roots: Option<Vec<PathBuf>>,
    #[serde(default)]
    pub repository_roots: Option<Vec<PathBuf>>,
    #[serde(default)]
    pub allowed_git_operations: Option<Vec<GitOperation>>,
    #[serde(default)]
    pub destructive_git_grants: Vec<GitOperation>,
    #[serde(default)]
    pub github_owners: Option<Vec<String>>,
    #[serde(default)]
    pub network: NetworkScope,
    #[serde(default)]
    pub network_tools: Vec<String>,
    #[serde(default)]
    pub require_literal_shell: bool,
    #[serde(default)]
    pub require_normal_git_refresh: bool,
    #[serde(default)]
    pub trace_path: Option<PathBuf>,
}

/// A repository operation, distinct from cache serialization.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum GitOperation {
    Read,
    Add,
    Commit,
    Pull,
    Push,
    Init,
    Merge,
    Branch,
    Tag,
    ConfigWrite,
    RemoteWrite,
    Apply,
    UpdateIndex,
    Reset,
    Restore,
    Stash,
    Clean,
    ForcePush,
    Amend,
    DeleteBranch,
    CheckoutPath,
    Rebase,
}

/// The selected network scope.
#[derive(Debug, Clone, Default, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum NetworkScope {
    #[default]
    Unrestricted,
    Disabled,
    Hosts {
        allowed: Vec<String>,
    },
}

/// Exact inspection reach. Partial inspection is never claimed as containment.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Coverage {
    LiteralShell,
    ExplicitPaths,
    NetworkTargets,
    PartialShell { constructs: Vec<String> },
    UnsupportedTool { name: String },
}

/// A concrete refused effect or failed prerequisite.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Denial {
    PolicyVersion {
        received: u8,
    },
    SessionMismatch {
        expected: String,
        received: String,
    },
    UnavailableShellInspection {
        cause: crate::ShellIssue,
    },
    UnsupportedGitOperation {
        received: Option<String>,
    },
    UninspectedShell {
        constructs: Vec<String>,
    },
    NodeInstallation {
        program: String,
        package: String,
    },
    SeparateRuntime {
        requested: String,
        resolved: Option<PathBuf>,
        bun: Option<PathBuf>,
    },
    RuntimeInspection {
        requested: String,
        cause: FileIssue,
    },
    GitOperation {
        operation: GitOperation,
    },
    RepositoryScope {
        requested: PathBuf,
        allowed: Vec<PathBuf>,
    },
    WriteScope {
        requested: PathBuf,
        allowed: Vec<PathBuf>,
    },
    NetworkDisabled {
        program: String,
    },
    NetworkHost {
        host: String,
        allowed: Vec<String>,
    },
    MissingNetworkTarget {
        program: String,
    },
    GitHubScope {
        owner: Option<String>,
        allowed: Vec<String>,
    },
    GitRefreshOverride {
        setting: String,
    },
    PathInspection {
        cause: FileIssue,
    },
    RemoteInspection {
        repository: PathBuf,
        remote: String,
        cause: RemoteIssue,
    },
}

impl Denial {
    /// Stable presentation codes avoid exposing tool argument or process bytes.
    pub fn code(&self) -> &'static str {
        match self {
            Self::PolicyVersion { .. } => "policy_version",
            Self::SessionMismatch { .. } => "session_mismatch",
            Self::UnavailableShellInspection { .. } => "shell_inspection_failed",
            Self::UnsupportedGitOperation { .. } => "unsupported_git_operation",
            Self::UninspectedShell { .. } => "uninspected_shell",
            Self::NodeInstallation { .. } => "separate_node_installation",
            Self::SeparateRuntime { .. } => "separate_runtime",
            Self::RuntimeInspection { .. } => "runtime_inspection_failed",
            Self::GitOperation { .. } => "git_operation_outside_grant",
            Self::RepositoryScope { .. } => "repository_outside_scope",
            Self::WriteScope { .. } => "write_outside_scope",
            Self::NetworkDisabled { .. } => "network_disabled",
            Self::NetworkHost { .. } => "network_host_outside_scope",
            Self::MissingNetworkTarget { .. } => "network_target_unresolved",
            Self::GitHubScope { .. } => "github_owner_outside_scope",
            Self::GitRefreshOverride { .. } => "normal_git_refresh_required",
            Self::PathInspection { .. } => "path_inspection_failed",
            Self::RemoteInspection { .. } => "remote_inspection_failed",
        }
    }
}

/// Structured filesystem failure at the immediate effect boundary.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub struct FileIssue {
    pub path: PathBuf,
    pub operation: FileOperation,
    pub kind: FileIssueKind,
    pub os_code: Option<i32>,
    pub detail: String,
}

/// A native failure category, distinct from an absent executable.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FileIssueKind {
    Missing,
    PermissionDenied,
    InvalidInput,
    Other,
}

/// Concrete effect that produced the native filesystem failure.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FileOperation {
    CanonicalizeExecutable,
    InspectExecutable,
    ResolveScopeRoot,
    ResolveRequestedPath,
    InspectGitRemote,
}

impl FileIssue {
    pub fn from_io(path: PathBuf, operation: FileOperation, source: &std::io::Error) -> Self {
        let kind = match source.kind() {
            std::io::ErrorKind::NotFound => FileIssueKind::Missing,
            std::io::ErrorKind::PermissionDenied => FileIssueKind::PermissionDenied,
            std::io::ErrorKind::InvalidInput => FileIssueKind::InvalidInput,
            _ => FileIssueKind::Other,
        };
        Self {
            path,
            operation,
            kind,
            os_code: source.raw_os_error(),
            detail: source.to_string(),
        }
    }
}

/// Original process or decoding failure while resolving a named Git remote.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum RemoteIssue {
    Spawn {
        cause: FileIssue,
    },
    Process {
        code: Option<i32>,
        stdout: Vec<u8>,
        stderr: Vec<u8>,
    },
    Encoding {
        valid_up_to: usize,
        error_len: Option<usize>,
    },
    UnsupportedEndpoint {
        received: String,
    },
}

/// Complete decision, preserving every identified refusal.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Decision {
    Allow {
        coverage: Coverage,
        inspected_commands: usize,
    },
    Deny {
        coverage: Coverage,
        issues: Vec<Denial>,
    },
}

/// A correlated guard observation, written only when a trusted trace path exists.
#[derive(Debug, Serialize)]
pub struct HookEvent<'a> {
    pub session_id: &'a str,
    pub tool_use_id: &'a str,
    pub tool_name: &'a str,
    pub decision: &'a Decision,
}
