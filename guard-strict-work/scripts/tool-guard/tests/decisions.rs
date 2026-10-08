use std::path::PathBuf;
use strict_test_support::{ComparisonFailure, ensure_eq as compare_native};
use strict_tool_guard::{
    Coverage, Decision, Denial, GitOperation, Invocation, NetworkScope, Policy, ToolRequest,
    evaluate,
};

type Outcome = Result<(), ComparisonFailure<Box<Decision>, Box<Decision>>>;
type DecisionComparison =
    Result<(Box<Decision>, Box<Decision>), ComparisonFailure<Box<Decision>, Box<Decision>>>;

fn ensure_eq(actual: Decision, expected: Decision, context: &'static str) -> DecisionComparison {
    compare_native(Box::new(actual), Box::new(expected), context)
}

fn policy() -> Policy {
    Policy {
        schema_version: 1,
        session_id: None,
        bun_executable: None,
        write_roots: None,
        repository_roots: None,
        allowed_git_operations: None,
        destructive_git_grants: Vec::new(),
        github_owners: None,
        network: NetworkScope::Unrestricted,
        network_tools: Vec::new(),
        require_literal_shell: false,
        require_normal_git_refresh: false,
        trace_path: None,
    }
}

fn run(script: &str, policy: &Policy) -> Decision {
    evaluate(
        &Invocation {
            session_id: "fixture-session".to_owned(),
            tool_use_id: "fixture-call".to_owned(),
            tool_name: "Bash".to_owned(),
            cwd: PathBuf::from(env!("CARGO_MANIFEST_DIR")),
            request: ToolRequest::Shell {
                script: script.to_owned(),
                directory: None,
            },
        },
        policy,
    )
}

fn allowed(commands: usize) -> Decision {
    Decision::Allow {
        coverage: Coverage::LiteralShell,
        inspected_commands: commands,
    }
}

fn denied(issue: Denial) -> Decision {
    Decision::Deny {
        coverage: Coverage::LiteralShell,
        issues: vec![issue],
    }
}

#[test]
fn documentation_and_package_labels_do_not_become_executable_invocations() -> Outcome {
    for script in [
        "echo 'brew install node'",
        "printf '%s' 'engines.node >=24'",
        "cat package.json",
        "bunx --bun tsc --noEmit",
    ] {
        ensure_eq(
            run(script, &policy()),
            allowed(1),
            "literal data and Bun workloads remain permitted",
        )?;
    }
    Ok(())
}

#[test]
fn actual_node_installations_are_refused_before_execution() -> Outcome {
    for (script, program, package) in [
        ("brew install node", "brew", "node"),
        ("apt-get install nodejs", "apt-get", "nodejs"),
        ("sudo brew install node@24", "brew", "node@24"),
    ] {
        ensure_eq(
            run(script, &policy()),
            denied(Denial::NodeInstallation {
                program: program.to_owned(),
                package: package.to_owned(),
            }),
            "separate runtime installation is refused",
        )?;
    }
    Ok(())
}

#[test]
fn ordinary_cache_refresh_and_authorized_git_workflow_remain_permitted() -> Outcome {
    for script in [
        "git status --short",
        "git diff --cached",
        "git update-index --refresh",
        "git pull --no-rebase --no-autostash --ff --no-commit",
        "git add .",
        "git commit -m 'fix(scope): preserve intent'",
        "git push --no-follow-tags origin HEAD:refs/heads/main",
    ] {
        ensure_eq(
            run(script, &policy()),
            allowed(1),
            "normal Git behavior needs no recurring approval",
        )?;
    }
    Ok(())
}

#[test]
fn destructive_operations_do_not_inherit_ordinary_git_grants() -> Outcome {
    for (script, operation) in [
        ("git reset --hard", GitOperation::Reset),
        ("git stash", GitOperation::Stash),
        ("git clean -fd", GitOperation::Clean),
        ("git push --force origin main", GitOperation::ForcePush),
        ("git commit --amend", GitOperation::Amend),
        ("git checkout -- private.txt", GitOperation::CheckoutPath),
        ("git branch -D old", GitOperation::DeleteBranch),
    ] {
        ensure_eq(
            run(script, &policy()),
            denied(Denial::GitOperation { operation }),
            "a destructive operation requires its own trusted grant",
        )?;
    }
    Ok(())
}

#[test]
fn an_exact_trusted_grant_is_consumed_without_expanding_adjacent_authority() -> Outcome {
    let mut selected = policy();
    selected.destructive_git_grants = vec![GitOperation::Reset];
    ensure_eq(
        run("git reset --hard", &selected),
        allowed(1),
        "selected reset grant remains usable",
    )?;
    ensure_eq(
        run("git push --force", &selected),
        denied(Denial::GitOperation {
            operation: GitOperation::ForcePush,
        }),
        "reset grant cannot authorize force push",
    )
    .map(drop)
}

#[test]
fn repository_operation_scope_does_not_treat_configuration_writes_as_reads() -> Outcome {
    let mut selected = policy();
    selected.allowed_git_operations = Some(vec![GitOperation::Read]);
    ensure_eq(
        run("git config --get core.editor", &selected),
        allowed(1),
        "configuration reads remain permitted",
    )?;
    ensure_eq(
        run("git config core.editor changed", &selected),
        denied(Denial::GitOperation {
            operation: GitOperation::ConfigWrite,
        }),
        "configuration writes are a distinct effect",
    )
    .map(drop)
}

#[test]
fn metadata_overrides_are_scoped_to_the_selected_requirement() -> Outcome {
    ensure_eq(
        run("git -c diff.autoRefreshIndex=false diff", &policy()),
        allowed(1),
        "diagnostic overrides are not globally banned",
    )?;
    let mut selected = policy();
    selected.require_normal_git_refresh = true;
    ensure_eq(
        run("git -c diff.autoRefreshIndex=false diff", &selected),
        denied(Denial::GitRefreshOverride {
            setting: "diff.autoRefreshIndex=false".to_owned(),
        }),
        "selected normal-refresh requirement is preserved",
    )
    .map(drop)
}

#[test]
fn authorized_github_owner_does_not_authorize_unscoped_disclosure() -> Outcome {
    let mut selected = policy();
    selected.github_owners = Some(vec!["fixture-owner".to_owned()]);
    ensure_eq(
        run("gh repo view fixture-owner/project", &selected),
        allowed(1),
        "named owner grant remains usable",
    )?;
    ensure_eq(
        run("gh search code private-project", &selected),
        denied(Denial::GitHubScope {
            owner: None,
            allowed: vec!["fixture-owner".to_owned()],
        }),
        "unscoped private query is refused before request",
    )
    .map(drop)
}

#[test]
fn selected_network_hosts_are_checked_before_outbound_execution() -> Outcome {
    let mut selected = policy();
    selected.network = NetworkScope::Hosts {
        allowed: vec!["docs.example.test".to_owned()],
    };
    ensure_eq(
        run("curl https://docs.example.test/api", &selected),
        allowed(1),
        "selected documentation host is permitted",
    )?;
    ensure_eq(
        run("curl https://outside.example.test/api", &selected),
        denied(Denial::NetworkHost {
            host: "outside.example.test".to_owned(),
            allowed: vec!["docs.example.test".to_owned()],
        }),
        "outside host is refused before execution",
    )
    .map(drop)
}

#[test]
fn a_disabled_network_scope_rejects_reads_as_well_as_writes() -> Outcome {
    let mut selected = policy();
    selected.network = NetworkScope::Disabled;
    ensure_eq(
        run("cat local.txt", &selected),
        allowed(1),
        "local read stays local",
    )?;
    ensure_eq(
        run("gh repo view fixture-owner/project", &selected),
        denied(Denial::NetworkDisabled {
            program: "gh".to_owned(),
        }),
        "read-only network request still discloses information",
    )
    .map(drop)
}

#[test]
fn a_session_grant_is_not_reusable_by_a_different_session() -> Outcome {
    let mut selected = policy();
    selected.session_id = Some("fixture-session".to_owned());
    ensure_eq(
        run("git status", &selected),
        allowed(1),
        "matching session consumes retained authority",
    )?;
    selected.session_id = Some("another-session".to_owned());
    ensure_eq(
        run("git status", &selected),
        denied(Denial::SessionMismatch {
            expected: "another-session".to_owned(),
            received: "fixture-session".to_owned(),
        }),
        "other session cannot inherit the grant",
    )
    .map(drop)
}
