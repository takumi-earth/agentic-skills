use serde::{Deserialize, Serialize};
use tree_sitter::{Node, Parser};

/// A statically decoded executable invocation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Command {
    pub words: Vec<Word>,
    pub dynamic: bool,
}

/// Preserve unresolved argument positions instead of fabricating empty values.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Word {
    Literal { value: String },
    Dynamic { start_byte: usize, end_byte: usize },
}

/// Parsed commands and syntax whose effects are not fully determined.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Inspection {
    pub commands: Vec<Command>,
    pub opaque: Vec<String>,
}

/// Structured parser failures with their actual grammar or encoding evidence.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ShellIssue {
    Grammar {
        minimum_abi: usize,
        maximum_abi: usize,
        received_abi: usize,
    },
    NoTree,
    Syntax {
        start_byte: usize,
        end_byte: usize,
    },
    Encoding {
        valid_up_to: usize,
        error_len: Option<usize>,
    },
}

/// Inspect invocation nodes rather than matching arbitrary source text.
///
/// # Errors
/// Returns the parser's rejected grammar or syntax detail before execution.
pub fn inspect_script(script: &str) -> Result<Inspection, ShellIssue> {
    let mut parser = Parser::new();
    let language = tree_sitter_bash::LANGUAGE.into();
    parser
        .set_language(&language)
        .map_err(|_| ShellIssue::Grammar {
            minimum_abi: tree_sitter::MIN_COMPATIBLE_LANGUAGE_VERSION,
            maximum_abi: tree_sitter::LANGUAGE_VERSION,
            received_abi: language.abi_version(),
        })?;
    let tree = parser.parse(script, None).ok_or(ShellIssue::NoTree)?;
    if tree.root_node().has_error() {
        return Err(ShellIssue::Syntax {
            start_byte: tree.root_node().start_byte(),
            end_byte: tree.root_node().end_byte(),
        });
    }
    let mut pending = vec![tree.root_node()];
    let mut nodes = Vec::new();
    let mut opaque = Vec::new();
    while let Some(node) = pending.pop() {
        if node.kind() == "command" {
            nodes.push(node);
        }
        if matches!(
            node.kind(),
            "expansion"
                | "simple_expansion"
                | "command_substitution"
                | "process_substitution"
                | "variable_assignment"
                | "file_redirect"
                | "function_definition"
                | "heredoc_body"
        ) {
            opaque.push(node.kind().to_owned());
        }
        let mut cursor = node.walk();
        pending.extend(node.named_children(&mut cursor));
    }
    nodes.sort_by_key(Node::start_byte);
    opaque.sort();
    opaque.dedup();
    let mut commands = Vec::new();
    for node in nodes {
        let mut cursor = node.walk();
        let mut words = Vec::new();
        let mut dynamic = false;
        for child in node.named_children(&mut cursor) {
            if child.kind() == "variable_assignment" {
                dynamic = true;
                continue;
            }
            let text =
                child
                    .utf8_text(script.as_bytes())
                    .map_err(|issue| ShellIssue::Encoding {
                        valid_up_to: issue.valid_up_to(),
                        error_len: issue.error_len(),
                    })?;
            let expanded = contains_expansion(child);
            dynamic |= expanded;
            if !expanded {
                match shlex::split(text) {
                    Some(decoded) if decoded.len() == 1 => {
                        words.extend(decoded.into_iter().map(|value| Word::Literal { value }))
                    }
                    _ => {
                        dynamic = true;
                        words.push(Word::Dynamic {
                            start_byte: child.start_byte(),
                            end_byte: child.end_byte(),
                        });
                    }
                }
            } else {
                words.push(Word::Dynamic {
                    start_byte: child.start_byte(),
                    end_byte: child.end_byte(),
                });
            }
        }
        commands.push(Command { words, dynamic });
    }
    Ok(Inspection { commands, opaque })
}

fn contains_expansion(node: Node<'_>) -> bool {
    let mut pending = vec![node];
    while let Some(current) = pending.pop() {
        if matches!(
            current.kind(),
            "expansion" | "simple_expansion" | "command_substitution" | "process_substitution"
        ) {
            return true;
        }
        let mut cursor = current.walk();
        pending.extend(current.named_children(&mut cursor));
    }
    false
}
