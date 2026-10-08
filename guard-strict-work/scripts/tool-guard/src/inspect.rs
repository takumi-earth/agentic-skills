use crate::{
    Command, Coverage, Decision, Denial, FileIssue, FileOperation, GitOperation, Invocation,
    NetworkScope, Policy, RemoteIssue, ToolRequest, Word, inspect_script,
};
use std::path::{Path, PathBuf};
use url::Url;

/// Resolve an executable's actual identity without executing it.
pub fn resolve_executable(name: &str, cwd: &Path) -> Result<Option<PathBuf>, FileIssue> {
    if name.contains('/') || name.contains('\\') {
        return executable_candidate(&cwd.join(name));
    }
    if let Some(paths) = std::env::var_os("PATH") {
        for root in std::env::split_paths(&paths) {
            if let Some(candidate) = executable_candidate(&root.join(name))? {
                return Ok(Some(candidate));
            }
        }
    }
    Ok(None)
}

fn executable_candidate(path: &Path) -> Result<Option<PathBuf>, FileIssue> {
    match std::fs::metadata(path) {
        Ok(metadata) if metadata.is_file() && executable_permissions(&metadata) => {
            std::fs::canonicalize(path).map(Some).map_err(|source| {
                FileIssue::from_io(
                    path.to_owned(),
                    FileOperation::CanonicalizeExecutable,
                    &source,
                )
            })
        }
        Ok(_) => Ok(None),
        Err(source) if source.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(source) => Err(FileIssue::from_io(
            path.to_owned(),
            FileOperation::InspectExecutable,
            &source,
        )),
    }
}

#[cfg(unix)]
fn executable_permissions(metadata: &std::fs::Metadata) -> bool {
    use std::os::unix::fs::PermissionsExt;
    metadata.permissions().mode() & 0o111 != 0
}

#[cfg(not(unix))]
fn executable_permissions(_metadata: &std::fs::Metadata) -> bool {
    true
}

/// Evaluate the actual requested effects against trusted grants.
pub fn evaluate(invocation: &Invocation, policy: &Policy) -> Decision {
    let mut issues = Vec::new();
    if policy.schema_version != 1 {
        issues.push(Denial::PolicyVersion {
            received: policy.schema_version,
        });
    }
    if let Some(expected) = &policy.session_id
        && expected != &invocation.session_id
    {
        issues.push(Denial::SessionMismatch {
            expected: expected.clone(),
            received: invocation.session_id.clone(),
        });
    }
    let (coverage, count) = match &invocation.request {
        ToolRequest::Shell { script, directory } => {
            let cwd = directory
                .as_ref()
                .map_or_else(|| invocation.cwd.clone(), |path| invocation.cwd.join(path));
            match inspect_script(script) {
                Err(cause) => {
                    if policy.require_literal_shell {
                        issues.push(Denial::UnavailableShellInspection { cause });
                    }
                    (
                        Coverage::PartialShell {
                            constructs: vec!["unsupported_shell_syntax".to_owned()],
                        },
                        0,
                    )
                }
                Ok(inspection) => {
                    if policy.require_literal_shell && !inspection.opaque.is_empty() {
                        issues.push(Denial::UninspectedShell {
                            constructs: inspection.opaque.clone(),
                        });
                    }
                    for command in &inspection.commands {
                        inspect_command(command, &cwd, policy, &mut issues);
                    }
                    let coverage = if inspection.opaque.is_empty() {
                        Coverage::LiteralShell
                    } else {
                        Coverage::PartialShell {
                            constructs: inspection.opaque,
                        }
                    };
                    (coverage, inspection.commands.len())
                }
            }
        }
        ToolRequest::Write { paths } => {
            for path in paths {
                check_path(
                    &invocation.cwd.join(path),
                    &policy.write_roots,
                    false,
                    &mut issues,
                );
            }
            (Coverage::ExplicitPaths, 0)
        }
        ToolRequest::Network { urls } => {
            inspect_network(urls, &invocation.tool_name, policy, &mut issues);
            (Coverage::NetworkTargets, 0)
        }
        ToolRequest::Other => (
            Coverage::UnsupportedTool {
                name: invocation.tool_name.clone(),
            },
            0,
        ),
    };
    if issues.is_empty() {
        Decision::Allow {
            coverage,
            inspected_commands: count,
        }
    } else {
        Decision::Deny { coverage, issues }
    }
}

fn check_path(
    path: &Path,
    roots: &Option<Vec<PathBuf>>,
    repository: bool,
    issues: &mut Vec<Denial>,
) {
    let Some(allowed) = roots else {
        return;
    };
    match canonical_target(path) {
        Ok(requested) => {
            let mut matches = false;
            for root in allowed {
                match canonical_target(root) {
                    Ok(normalized) => matches |= requested.starts_with(normalized),
                    Err(source) => issues.push(Denial::PathInspection {
                        cause: FileIssue::from_io(
                            root.clone(),
                            FileOperation::ResolveScopeRoot,
                            &source,
                        ),
                    }),
                }
            }
            if !matches {
                if repository {
                    issues.push(Denial::RepositoryScope {
                        requested,
                        allowed: allowed.clone(),
                    });
                } else {
                    issues.push(Denial::WriteScope {
                        requested,
                        allowed: allowed.clone(),
                    });
                }
            }
        }
        Err(source) => issues.push(Denial::PathInspection {
            cause: FileIssue::from_io(
                path.to_owned(),
                FileOperation::ResolveRequestedPath,
                &source,
            ),
        }),
    }
}

fn canonical_target(path: &Path) -> Result<PathBuf, std::io::Error> {
    let mut resolved = PathBuf::new();
    for component in path.components() {
        match component {
            std::path::Component::CurDir => (),
            std::path::Component::ParentDir => {
                resolved.pop();
            }
            component => {
                resolved.push(component.as_os_str());
                match std::fs::canonicalize(&resolved) {
                    Ok(existing) => resolved = existing,
                    Err(issue) if issue.kind() == std::io::ErrorKind::NotFound => {
                        match std::fs::symlink_metadata(&resolved) {
                            Ok(metadata) if metadata.is_symlink() => {
                                let target = std::fs::read_link(&resolved)?;
                                let destination = if target.is_absolute() {
                                    target
                                } else {
                                    let parent = resolved.parent().ok_or_else(|| {
                                        std::io::Error::new(
                                            std::io::ErrorKind::InvalidInput,
                                            "symlink has no parent directory",
                                        )
                                    })?;
                                    parent.join(target)
                                };
                                resolved = canonical_target(&destination)?;
                            }
                            Ok(_) => (),
                            Err(issue) if issue.kind() == std::io::ErrorKind::NotFound => (),
                            Err(issue) => return Err(issue),
                        }
                    }
                    Err(issue) => return Err(issue),
                }
            }
        }
    }
    Ok(resolved)
}

fn inspect_words(words: &[String], cwd: &Path, policy: &Policy, issues: &mut Vec<Denial>) {
    let Some((first, arguments)) = words.split_first() else {
        return;
    };
    let filename = Path::new(first)
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or(first);
    let program = filename.strip_suffix(".exe").unwrap_or(filename);
    if matches!(program, "sudo" | "command" | "exec" | "env") {
        let rest = arguments
            .iter()
            .position(|word| !word.starts_with('-') && !word.contains('='));
        if let Some(start) = rest
            && let Some(rest) = arguments.get(start..)
        {
            inspect_words(rest, cwd, policy, issues);
        }
        return;
    }
    if matches!(program, "node" | "nodejs" | "npm" | "npx") {
        let resolved = resolve_executable(first, cwd);
        let bun = match &policy.bun_executable {
            Some(path) => executable_candidate(path),
            None => resolve_executable("bun", cwd),
        };
        match (resolved, bun) {
            (Ok(resolved), Ok(bun)) if resolved.is_some() && resolved == bun => (),
            (Ok(resolved), Ok(bun)) => issues.push(Denial::SeparateRuntime {
                requested: first.clone(),
                resolved,
                bun,
            }),
            (Err(cause), _) | (_, Err(cause)) => issues.push(Denial::RuntimeInspection {
                requested: first.clone(),
                cause,
            }),
        }
    }
    if matches!(
        program,
        "brew" | "apt" | "apt-get" | "dnf" | "yum" | "pacman" | "winget" | "choco"
    ) && arguments
        .iter()
        .any(|word| matches!(word.as_str(), "install" | "add" | "-S"))
    {
        for package in arguments {
            if matches!(
                package.as_str(),
                "node" | "nodejs" | "nodejs-lts" | "OpenJS.NodeJS" | "OpenJS.NodeJS.LTS"
            ) || package.starts_with("node@")
            {
                issues.push(Denial::NodeInstallation {
                    program: program.to_owned(),
                    package: package.clone(),
                });
            }
        }
    }
    if program == "git" {
        inspect_git(arguments, cwd, policy, issues);
    }
    if program == "gh" {
        inspect_github(arguments, policy, issues);
    }
    if matches!(program, "curl" | "wget" | "gh" | "ssh" | "scp") {
        let urls: Vec<String> = arguments
            .iter()
            .filter(|word| word.starts_with("https://") || word.starts_with("http://"))
            .cloned()
            .collect();
        inspect_network(&urls, program, policy, issues);
        for url in urls {
            if let Ok(parsed) = Url::parse(&url)
                && parsed.host_str() == Some("nodejs.org")
                && parsed.path().contains("/dist/")
                && [".tar.gz", ".tar.xz", ".zip", ".msi", ".pkg"]
                    .iter()
                    .any(|suffix| parsed.path().ends_with(suffix))
            {
                issues.push(Denial::NodeInstallation {
                    program: program.to_owned(),
                    package: "Node.js runtime archive".to_owned(),
                });
            }
        }
    }
    if matches!(program, "bash" | "sh" | "zsh")
        && let Some(index) = arguments
            .iter()
            .position(|word| matches!(word.as_str(), "-c" | "-lc"))
        && let Some(script) = arguments.get(index.saturating_add(1))
        && let Ok(inspection) = inspect_script(script)
    {
        for nested in inspection.commands {
            inspect_command(&nested, cwd, policy, issues);
        }
    }
}

fn inspect_command(command: &Command, cwd: &Path, policy: &Policy, issues: &mut Vec<Denial>) {
    let words: Vec<String> = command
        .words
        .iter()
        .map_while(|word| match word {
            Word::Literal { value } => Some(value.clone()),
            Word::Dynamic { .. } => None,
        })
        .collect();
    if command.dynamic
        && policy.allowed_git_operations.is_some()
        && words.first().is_some_and(|word| {
            Path::new(word)
                .file_name()
                .is_some_and(|name| name == "git")
        })
    {
        issues.push(Denial::UninspectedShell {
            constructs: vec!["dynamic_git_arguments".to_owned()],
        });
    }
    inspect_words(&words, cwd, policy, issues);
}

fn inspect_git(arguments: &[String], cwd: &Path, policy: &Policy, issues: &mut Vec<Denial>) {
    let mut words = arguments.iter();
    let mut directory = cwd.to_owned();
    let mut subcommand = None;
    let mut configuration = Vec::new();
    while let Some(word) = words.next() {
        if word == "-C" {
            if let Some(path) = words.next() {
                directory = directory.join(path);
            }
        } else if word == "-c" {
            if let Some(setting) = words.next() {
                configuration.push(setting.clone());
                if policy.require_normal_git_refresh
                    && matches!(
                        setting.as_str(),
                        "diff.autoRefreshIndex=false" | "core.fsmonitor=false"
                    )
                {
                    issues.push(Denial::GitRefreshOverride {
                        setting: setting.clone(),
                    });
                }
            }
        } else if !word.starts_with('-') {
            subcommand = Some(word.as_str());
            break;
        }
    }
    check_path(&directory, &policy.repository_roots, true, issues);
    let rest: Vec<&str> = words.map(String::as_str).collect();
    let operation = match subcommand {
        Some("reset") => GitOperation::Reset,
        Some("restore") => GitOperation::Restore,
        Some("stash") => GitOperation::Stash,
        Some("clean") => GitOperation::Clean,
        Some("branch")
            if rest
                .iter()
                .any(|word| matches!(*word, "-d" | "-D" | "--delete" | "--force")) =>
        {
            GitOperation::DeleteBranch
        }
        Some("checkout") if rest.contains(&"--") => GitOperation::CheckoutPath,
        Some("push")
            if rest.iter().any(|word| {
                matches!(*word, "--force" | "--force-with-lease" | "-f")
                    || word.starts_with("--force-with-lease=")
                    || word.starts_with('+')
            }) =>
        {
            GitOperation::ForcePush
        }
        Some("commit") if rest.contains(&"--amend") => GitOperation::Amend,
        Some("commit") => GitOperation::Commit,
        Some("add") => GitOperation::Add,
        Some("pull") => GitOperation::Pull,
        Some("push") => GitOperation::Push,
        Some("init") => GitOperation::Init,
        Some("merge") => GitOperation::Merge,
        Some("rebase") => GitOperation::Rebase,
        Some("branch")
            if rest.is_empty()
                || rest
                    .iter()
                    .any(|word| matches!(*word, "--list" | "-l" | "--show-current")) =>
        {
            GitOperation::Read
        }
        Some("branch") => GitOperation::Branch,
        Some("tag")
            if rest.is_empty() || rest.iter().any(|word| matches!(*word, "--list" | "-l")) =>
        {
            GitOperation::Read
        }
        Some("tag") => GitOperation::Tag,
        Some("config")
            if rest.iter().any(|word| {
                matches!(
                    *word,
                    "--get" | "--get-all" | "--get-regexp" | "--list" | "-l"
                )
            }) =>
        {
            GitOperation::Read
        }
        Some("config") => GitOperation::ConfigWrite,
        Some("remote")
            if rest.is_empty()
                || rest
                    .first()
                    .is_some_and(|word| matches!(*word, "-v" | "get-url")) =>
        {
            GitOperation::Read
        }
        Some("remote") => GitOperation::RemoteWrite,
        Some("apply") if rest.contains(&"--check") => GitOperation::Read,
        Some("apply") => GitOperation::Apply,
        Some("update-index")
            if rest
                .iter()
                .all(|word| matches!(*word, "--refresh" | "--really-refresh")) =>
        {
            GitOperation::Read
        }
        Some("update-index") => GitOperation::UpdateIndex,
        Some(
            "status" | "diff" | "show" | "log" | "ls-files" | "rev-parse" | "rev-list" | "fetch"
            | "merge-base" | "describe" | "cat-file" | "ls-tree" | "check-ignore" | "check-attr",
        ) => GitOperation::Read,
        other => {
            if policy.allowed_git_operations.is_some() {
                issues.push(Denial::UnsupportedGitOperation {
                    received: other.map(str::to_owned),
                });
            }
            return;
        }
    };
    let destructive = matches!(
        operation,
        GitOperation::Reset
            | GitOperation::Restore
            | GitOperation::Stash
            | GitOperation::Clean
            | GitOperation::ForcePush
            | GitOperation::Amend
            | GitOperation::DeleteBranch
            | GitOperation::CheckoutPath
            | GitOperation::Rebase
    );
    if policy.require_normal_git_refresh
        && operation == GitOperation::ConfigWrite
        && rest
            .windows(2)
            .any(|pair| matches!(pair, ["diff.autoRefreshIndex" | "core.fsmonitor", "false"]))
    {
        issues.push(Denial::GitRefreshOverride {
            setting: rest.join(" "),
        });
    }
    if (destructive && !policy.destructive_git_grants.contains(&operation))
        || policy
            .allowed_git_operations
            .as_ref()
            .is_some_and(|allowed| !allowed.contains(&operation))
    {
        issues.push(Denial::GitOperation { operation });
    }
    if !matches!(policy.network, NetworkScope::Unrestricted)
        && matches!(subcommand, Some("pull" | "push" | "fetch"))
    {
        let remote = rest
            .iter()
            .find(|word| !word.starts_with('-'))
            .copied()
            .unwrap_or("origin");
        let target = if remote.contains("://")
            || remote.starts_with("git@")
            || remote.starts_with('/')
            || remote.starts_with('.')
        {
            Ok(remote.to_owned())
        } else {
            resolve_git_remote(
                &directory,
                remote,
                subcommand == Some("push"),
                &configuration,
            )
        };
        match target {
            Ok(target) => match endpoint_host(&target) {
                Ok(Some(host)) => match &policy.network {
                    NetworkScope::Disabled => issues.push(Denial::NetworkDisabled {
                        program: "git".to_owned(),
                    }),
                    NetworkScope::Hosts { allowed } if !allowed.contains(&host) => {
                        issues.push(Denial::NetworkHost {
                            host,
                            allowed: allowed.clone(),
                        })
                    }
                    _ => (),
                },
                Ok(None) => (),
                Err(cause) => issues.push(Denial::RemoteInspection {
                    repository: directory.clone(),
                    remote: remote.to_owned(),
                    cause,
                }),
            },
            Err(cause) => issues.push(Denial::RemoteInspection {
                repository: directory.clone(),
                remote: remote.to_owned(),
                cause,
            }),
        }
    }
}

fn resolve_git_remote(
    repository: &Path,
    remote: &str,
    push: bool,
    configuration: &[String],
) -> Result<String, RemoteIssue> {
    let mut command = std::process::Command::new("git");
    command.arg("-C").arg(repository);
    for setting in configuration {
        command.arg("-c").arg(setting);
    }
    command.args(["remote", "get-url"]);
    if push {
        command.arg("--push");
    }
    let output = command
        .arg(remote)
        .output()
        .map_err(|source| RemoteIssue::Spawn {
            cause: FileIssue::from_io(
                repository.to_owned(),
                FileOperation::InspectGitRemote,
                &source,
            ),
        })?;
    if !output.status.success() {
        return Err(RemoteIssue::Process {
            code: output.status.code(),
            stdout: output.stdout,
            stderr: output.stderr,
        });
    }
    String::from_utf8(output.stdout)
        .map(|target| target.trim().to_owned())
        .map_err(|source| {
            let cause = source.utf8_error();
            RemoteIssue::Encoding {
                valid_up_to: cause.valid_up_to(),
                error_len: cause.error_len(),
            }
        })
}

fn endpoint_host(target: &str) -> Result<Option<String>, RemoteIssue> {
    if let Ok(url) = Url::parse(target) {
        if url.scheme() == "file" {
            return Ok(None);
        }
        return url
            .host_str()
            .map(|host| Some(host.to_owned()))
            .ok_or_else(|| RemoteIssue::UnsupportedEndpoint {
                received: target.to_owned(),
            });
    }
    if let Some((authority, _path)) = target.split_once(':')
        && let Some(host) = authority
            .rsplit('@')
            .next()
            .filter(|host| !host.contains('/'))
    {
        return Ok(Some(host.to_owned()));
    }
    if !target.contains("::") {
        return Ok(None);
    }
    Err(RemoteIssue::UnsupportedEndpoint {
        received: target.to_owned(),
    })
}

fn inspect_github(arguments: &[String], policy: &Policy, issues: &mut Vec<Denial>) {
    let Some(allowed) = &policy.github_owners else {
        return;
    };
    let owner = arguments
        .windows(2)
        .find_map(|pair| match pair {
            [flag, value] if matches!(flag.as_str(), "--owner" | "-R" | "--repo") => {
                value.split('/').next().map(str::to_owned)
            }
            _ => None,
        })
        .or_else(|| {
            arguments.iter().find_map(|word| {
                word.strip_prefix("repos/")
                    .or_else(|| word.strip_prefix("/repos/"))
                    .and_then(|path| path.split('/').next())
                    .map(str::to_owned)
            })
        })
        .or_else(|| {
            arguments.windows(3).find_map(|triple| match triple {
                [subcommand, action, target]
                    if subcommand == "repo" && matches!(action.as_str(), "view" | "clone") =>
                {
                    target.split_once('/').map(|(owner, _)| owner.to_owned())
                }
                _ => None,
            })
        });
    if !owner.as_ref().is_some_and(|owner| allowed.contains(owner)) {
        issues.push(Denial::GitHubScope {
            owner,
            allowed: allowed.clone(),
        });
    }
}

fn inspect_network(urls: &[String], program: &str, policy: &Policy, issues: &mut Vec<Denial>) {
    match &policy.network {
        NetworkScope::Unrestricted => (),
        NetworkScope::Disabled => issues.push(Denial::NetworkDisabled {
            program: program.to_owned(),
        }),
        NetworkScope::Hosts { allowed } => {
            if urls.is_empty() {
                issues.push(Denial::MissingNetworkTarget {
                    program: program.to_owned(),
                });
            }
            for address in urls {
                match Url::parse(address)
                    .ok()
                    .and_then(|url| url.host_str().map(str::to_owned))
                {
                    Some(host) if allowed.contains(&host) => (),
                    Some(host) => issues.push(Denial::NetworkHost {
                        host,
                        allowed: allowed.clone(),
                    }),
                    None => issues.push(Denial::MissingNetworkTarget {
                        program: program.to_owned(),
                    }),
                }
            }
        }
    }
}
