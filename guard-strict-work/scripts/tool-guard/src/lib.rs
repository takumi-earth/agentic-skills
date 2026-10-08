//! Typed, scope-aware decisions at the native pre-execution boundary.

mod inspect;
mod policy;
mod shell;

pub use inspect::{evaluate, resolve_executable};
pub use policy::{
    Coverage, Decision, Denial, FileIssue, FileIssueKind, FileOperation, GitOperation, HookEvent,
    NetworkScope, Policy, RemoteIssue,
};
pub use shell::{Command, Inspection, ShellIssue, Word, inspect_script};

use serde::Deserialize;
use std::path::PathBuf;

/// A decoded tool request. Foreign JSON is contained at construction.
#[derive(Debug, Clone)]
pub enum ToolRequest {
    /// Shell execution whose syntax must be inspected.
    Shell {
        script: String,
        directory: Option<PathBuf>,
    },
    /// Explicit file writes, including native patch destinations.
    Write { paths: Vec<PathBuf> },
    /// A tool known to make outbound requests.
    Network { urls: Vec<String> },
    /// A tool without a supported effect decoder.
    Other,
}

/// A validated native event and its concrete request.
#[derive(Debug, Clone)]
pub struct Invocation {
    pub session_id: String,
    pub tool_use_id: String,
    pub tool_name: String,
    pub cwd: PathBuf,
    pub request: ToolRequest,
}

/// A concrete foreign-payload decode failure.
#[derive(Debug)]
pub enum DecodeIssue {
    Json(serde_json::Error),
    UnsupportedEvent { received: String },
    MissingPatchDestinations,
}

#[derive(Deserialize)]
struct BoundaryEvent {
    #[serde(default)]
    session_id: String,
    #[serde(default)]
    tool_use_id: String,
    tool_name: String,
    cwd: PathBuf,
    hook_event_name: String,
    tool_input: serde_json::Value,
}

#[derive(Deserialize)]
struct ShellInput {
    #[serde(alias = "cmd")]
    command: String,
    #[serde(default, alias = "cwd")]
    workdir: Option<PathBuf>,
}

#[derive(Deserialize)]
struct WriteInput {
    #[serde(alias = "path")]
    file_path: PathBuf,
}

#[derive(Deserialize)]
struct PatchInput {
    command: String,
}

#[derive(Deserialize, Default)]
struct NetworkInput {
    #[serde(default)]
    url: Option<String>,
    #[serde(default)]
    open: Vec<OpenInput>,
}

#[derive(Deserialize)]
struct OpenInput {
    ref_id: String,
}

/// Decode a native or compatible pre-tool event before policy evaluation.
///
/// # Errors
/// Returns the concrete JSON error, unsupported event, or invalid patch shape.
pub fn decode_event(bytes: &[u8], policy: &Policy) -> Result<Invocation, DecodeIssue> {
    let input: BoundaryEvent = serde_json::from_slice(bytes).map_err(DecodeIssue::Json)?;
    if input.hook_event_name != "PreToolUse" {
        return Err(DecodeIssue::UnsupportedEvent {
            received: input.hook_event_name,
        });
    }
    let request = match input.tool_name.as_str() {
        "Bash" | "exec_command" | "shell_command" => {
            let shell: ShellInput =
                serde_json::from_value(input.tool_input).map_err(DecodeIssue::Json)?;
            ToolRequest::Shell {
                script: shell.command,
                directory: shell.workdir,
            }
        }
        "Write" | "Edit" | "write_file" | "edit_file" => {
            let write: WriteInput =
                serde_json::from_value(input.tool_input).map_err(DecodeIssue::Json)?;
            ToolRequest::Write {
                paths: vec![write.file_path],
            }
        }
        "apply_patch" | "ApplyPatch" => {
            let patch: PatchInput =
                serde_json::from_value(input.tool_input).map_err(DecodeIssue::Json)?;
            let paths: Vec<PathBuf> = patch
                .command
                .lines()
                .filter_map(|line| {
                    [
                        "*** Add File: ",
                        "*** Update File: ",
                        "*** Delete File: ",
                        "*** Move to: ",
                    ]
                    .into_iter()
                    .find_map(|prefix| line.strip_prefix(prefix))
                    .map(PathBuf::from)
                })
                .collect();
            if paths.is_empty() {
                return Err(DecodeIssue::MissingPatchDestinations);
            }
            ToolRequest::Write { paths }
        }
        name if policy.network_tools.iter().any(|known| name == known) => {
            let network: NetworkInput =
                serde_json::from_value(input.tool_input).map_err(DecodeIssue::Json)?;
            let urls = network
                .url
                .into_iter()
                .chain(network.open.into_iter().map(|open| open.ref_id))
                .collect();
            ToolRequest::Network { urls }
        }
        _ => ToolRequest::Other,
    };
    Ok(Invocation {
        session_id: input.session_id,
        tool_use_id: input.tool_use_id,
        tool_name: input.tool_name,
        cwd: input.cwd,
        request,
    })
}
