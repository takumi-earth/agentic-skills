use serde::Serialize;
use std::io::{Read, Write};
use std::path::PathBuf;
use std::process::ExitCode;
use strict_tool_guard::{Decision, HookEvent, Policy, decode_event, evaluate};

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct HookOutput {
    #[serde(skip_serializing_if = "Option::is_none")]
    hook_specific_output: Option<HookSpecific>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct HookSpecific {
    hook_event_name: &'static str,
    permission_decision: &'static str,
    #[serde(skip_serializing_if = "Option::is_none")]
    permission_decision_reason: Option<String>,
}

#[derive(Debug)]
enum RunIssue {
    Arguments,
    ReadPolicy {
        path: PathBuf,
        source: std::io::Error,
    },
    Policy(serde_json::Error),
    Input(std::io::Error),
    Decode(strict_tool_guard::DecodeIssue),
    Trace(std::io::Error),
    Serialize(serde_json::Error),
    Output(std::io::Error),
}

impl std::fmt::Display for RunIssue {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Arguments => formatter.write_str("expected --policy PATH and optional --inspect"),
            Self::ReadPolicy { path, source } => {
                write!(formatter, "policy read at {}: {source}", path.display())
            }
            Self::Policy(source) => write!(formatter, "policy decoding: {source}"),
            Self::Input(source) => write!(formatter, "hook input read: {source}"),
            Self::Decode(source) => write!(formatter, "hook input decoding: {source:?}"),
            Self::Trace(source) => write!(formatter, "guard trace recording: {source}"),
            Self::Serialize(source) => write!(formatter, "guard response encoding: {source}"),
            Self::Output(source) => write!(formatter, "guard response writing: {source}"),
        }
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(issue) => {
            let rendered = format!("Tool guard refused execution: {issue}");
            let response = HookOutput {
                hook_specific_output: Some(HookSpecific {
                    hook_event_name: "PreToolUse",
                    permission_decision: "deny",
                    permission_decision_reason: Some(rendered),
                }),
            };
            match serde_json::to_vec(&response) {
                Ok(bytes) => match std::io::stdout().lock().write_all(&bytes) {
                    Ok(()) => ExitCode::SUCCESS,
                    Err(_) => ExitCode::from(2),
                },
                Err(_) => ExitCode::from(2),
            }
        }
    }
}

fn run() -> Result<(), RunIssue> {
    let mut arguments = std::env::args_os().skip(1);
    if arguments.next().as_deref() != Some(std::ffi::OsStr::new("--policy")) {
        return Err(RunIssue::Arguments);
    }
    let path = arguments
        .next()
        .map(PathBuf::from)
        .ok_or(RunIssue::Arguments)?;
    let inspect = arguments.next().as_deref() == Some(std::ffi::OsStr::new("--inspect"));
    let bytes = std::fs::read(&path).map_err(|source| RunIssue::ReadPolicy { path, source })?;
    let policy: Policy = serde_json::from_slice(&bytes).map_err(RunIssue::Policy)?;
    let mut input = Vec::new();
    std::io::stdin()
        .lock()
        .read_to_end(&mut input)
        .map_err(RunIssue::Input)?;
    let invocation = decode_event(&input, &policy).map_err(RunIssue::Decode)?;
    let decision = evaluate(&invocation, &policy);
    if let Some(path) = &policy.trace_path {
        let mut trace = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(path)
            .map_err(RunIssue::Trace)?;
        let event = HookEvent {
            session_id: &invocation.session_id,
            tool_use_id: &invocation.tool_use_id,
            tool_name: &invocation.tool_name,
            decision: &decision,
        };
        let mut bytes = serde_json::to_vec(&event).map_err(RunIssue::Serialize)?;
        bytes.push(b'\n');
        trace.write_all(&bytes).map_err(RunIssue::Trace)?;
    }
    let output = if inspect {
        serde_json::to_vec(&decision).map_err(RunIssue::Serialize)?
    } else {
        // An allowed guard inspection is not a new grant of tool authority.
        // Abstain so native approval and other handlers retain their decisions.
        let hook_specific_output = match &decision {
            Decision::Allow { .. } => None,
            Decision::Deny { issues, .. } => Some(HookSpecific {
                hook_event_name: "PreToolUse",
                permission_decision: "deny",
                permission_decision_reason: Some(format!(
                    "Pre-execution scope refusal: {}",
                    issues
                        .iter()
                        .map(strict_tool_guard::Denial::code)
                        .collect::<Vec<_>>()
                        .join(", ")
                )),
            }),
        };
        serde_json::to_vec(&HookOutput {
            hook_specific_output,
        })
        .map_err(RunIssue::Serialize)?
    };
    std::io::stdout()
        .lock()
        .write_all(&output)
        .map_err(RunIssue::Output)
}
