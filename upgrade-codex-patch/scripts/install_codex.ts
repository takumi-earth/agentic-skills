import { Database } from "bun:sqlite";
import {
	chmod,
	copyFile,
	lstat,
	mkdir,
	mkdtemp,
	readFile,
	realpath,
	rename,
	rm,
	stat,
	symlink,
	writeFile,
} from "node:fs/promises";
import { homedir } from "node:os";
import { basename, delimiter, dirname, join, resolve } from "node:path";
import { fileDigest, reusablePackage, sourceIdentity } from "./prepared_package.ts";

type Environment = Record<string, string | undefined>;
type Options = {
	plan: boolean;
	prepareV8: boolean;
	preparePackage: boolean;
	daemon: boolean;
	prebuilt: Record<string, string>;
};
type Command = {
	phase: string;
	argv: string[];
	cwd: string;
	capture?: "stdout";
};
type Result = { command: Command; exitCode: number; stdout: string };
type PythonRuntime = {
	version: [number, number, number];
	trust: {
		cafile: string | null;
		capath: string | null;
		openssl_cafile_env: string;
		openssl_cafile: string;
		openssl_capath_env: string;
		openssl_capath: string;
	};
};
type RuntimeProcess = { pid: number; parent: number; created: string; executable: string };
type DaemonState = {
	backend?: string;
	pid?: number;
	managedCodexPath: string;
	cliVersion?: string;
	managedCodexVersion?: string;
	appServerVersion?: string;
};
type RuntimeOutcome = {
	stopped: { status: string; processes: RuntimeProcess[]; remaining: RuntimeProcess[] };
	launched: DaemonState;
	state: DaemonState;
	processes: RuntimeProcess[];
	executables: { source: string; selected: string; sha256: string }[];
};
export type Context = {
	env: Environment;
	execute: (command: Command, env: Environment) => Promise<Result>;
	say: (message: string) => void;
};
type Plan = {
	repository_root: string;
	runtime_root: string;
	skill_root: string;
	v8_repository: string;
	cargo_bin: string;
	version: string;
	target: string;
	compiler: string;
	python: string;
	launcher: string;
	side_effects: string[];
};

const home = homedir();
const started = performance.now();
const display = (value: string) =>
	value.replaceAll(`${home}/`, "~/").replaceAll(`${home}\\`, "~/");
const expand = (value: string) =>
	resolve(value.startsWith("~/") ? join(home, value.slice(2)) : value);
const suffix = (target: string) => (target.includes("windows") ? ".exe" : "");
const elapsed = () => ((performance.now() - started) / 1000).toFixed(1);

export class InstallConditionError extends Error {
	constructor(
		readonly condition: string,
		readonly expected: unknown,
		readonly received: unknown,
	) {
		super(
			`${condition}: expected ${JSON.stringify(expected)}, received ${JSON.stringify(received)}`,
		);
	}
}

function required(
	condition: unknown,
	checked: string,
	expected: unknown,
	received: unknown,
): asserts condition {
	if (!condition) throw new InstallConditionError(checked, expected, received);
}

async function exists(path: string) {
	try {
		return await lstat(path);
	} catch (error) {
		if ((error as NodeJS.ErrnoException).code === "ENOENT") return undefined;
		throw error;
	}
}

async function executable(path: string) {
	const info = await stat(path).catch((error: NodeJS.ErrnoException) => {
		if (error.code === "ENOENT") return undefined;
		throw error;
	});
	required(
		info?.isFile() && (process.platform === "win32" || info.mode & 0o111),
		"executable file",
		display(path),
		info ? { file: info.isFile(), mode: info.mode } : "missing",
	);
}

function options(args: string[]): Options {
	const result: Options = {
		plan: false,
		prepareV8: false,
		preparePackage: false,
		daemon: true,
		prebuilt: {},
	};
	if (args[0] === "i") args = args.slice(1);
	for (let i = 0; i < args.length; i++) {
		const arg = args[i];
		if (arg === "--plan") result.plan = true;
		else if (arg === "--prepare-v8") result.prepareV8 = true;
		else if (arg === "--prepare-package") result.preparePackage = true;
		else if (arg === "--no-daemon") result.daemon = false;
		else if (
			[
				"--entrypoint-bin",
				"--code-mode-host-bin",
				"--logs-client-bin",
				"--bwrap-bin",
			].includes(arg)
		) {
			required(args[i + 1], `${arg} argument`, "executable path", "missing");
			result.prebuilt[arg] = expand(args[++i]);
		} else throw new Error(`Unknown argument: ${arg}`);
	}
	return result;
}

async function execute(command: Command, env: Environment): Promise<Result> {
	console.error(
		`[just i +${elapsed()}s] ${command.phase}: ${command.argv.map(display).join(" ")}`,
	);
	const child = Bun.spawn(command.argv, {
		cwd: command.cwd,
		env,
		stdin: "inherit",
		stdout: command.capture ? "pipe" : "inherit",
		stderr: "inherit",
	});
	const timer = setInterval(
		() => console.error(`[just i +${elapsed()}s] waiting: ${command.phase}`),
		30_000,
	);
	const forward = (signal: NodeJS.Signals) => child.kill(signal);
	const onInterrupt = () => forward("SIGINT");
	process.on("SIGINT", onInterrupt);
	try {
		const stdout = command.capture
			? await new Response(child.stdout as ReadableStream).text()
			: "";
		const exitCode = await child.exited;
		console.error(`[just i +${elapsed()}s] ${command.phase}: exit ${exitCode}`);
		return { command, exitCode, stdout };
	} finally {
		clearInterval(timer);
		process.off("SIGINT", onInterrupt);
	}
}

async function run(
	ctx: Context,
	plan: Plan,
	phase: string,
	argv: string[],
	cwd = plan.repository_root,
	capture?: "stdout",
) {
	const result = await ctx.execute({ phase, argv, cwd, capture }, ctx.env);
	required(result.exitCode === 0, phase, "exit 0", result);
	return result.stdout.trim();
}

export async function resolvePlan(ctx: Context): Promise<Plan> {
	required(
		ctx.env.CODEX_REPO_ROOT,
		"Codex repository authority",
		"CODEX_REPO_ROOT from the importing justfile or environment",
		"missing",
	);
	const repository = expand(ctx.env.CODEX_REPO_ROOT);
	const workspace = join(repository, "codex-rs");
	const cargo = Bun.TOML.parse(
		await readFile(join(workspace, "Cargo.toml"), "utf8"),
	) as any;
	required(
		cargo.workspace?.package?.version,
		"Codex workspace version",
		"workspace.package.version",
		cargo.workspace,
	);
	required(
		await exists(join(repository, "scripts", "build_codex_package.py")),
		"package builder",
		"scripts/build_codex_package.py",
		"missing",
	);
	const configFile = join(workspace, ".cargo", "config.toml");
	const config = (await exists(configFile))
		? (Bun.TOML.parse(await readFile(configFile, "utf8")) as any)
		: {};
	const configuredWrapper = config.build?.["rustc-wrapper"];
	const wrapper = configuredWrapper
		? resolve(workspace, configuredWrapper)
		: undefined;
	const inferredV8 = wrapper
		? basename(dirname(wrapper)) === "bin"
			? dirname(dirname(wrapper))
			: dirname(wrapper)
		: undefined;
	const v8 = expand(
		ctx.env.CODEX_V8_REPO ||
			inferredV8 ||
			join(dirname(repository), "codex-v8"),
	);
	const manifest = JSON.parse(await readFile(join(v8, "package.json"), "utf8"));
	required(
		manifest.name === "codex-v8" && manifest.scripts?.setup,
		"V8 helper repository",
		"codex-v8 with a setup script",
		manifest,
	);
	const runtime = expand(ctx.env.CODEX_HOME || join(home, ".codex"));
	const cargoHome = expand(ctx.env.CARGO_HOME || join(home, ".cargo"));
	const python =
		ctx.env.CODEX_INSTALL_PYTHON ||
		(process.platform === "win32" ? "python" : "python3");
	const plan: Plan = {
		repository_root: repository,
		runtime_root: runtime,
		skill_root: dirname(dirname(import.meta.path)),
		v8_repository: v8,
		cargo_bin: join(cargoHome, "bin"),
		version: cargo.workspace.package.version,
		target: "",
		compiler: "",
		python,
		launcher: "",
		side_effects: [],
	};
	const compiler = await run(
		ctx,
		plan,
		"compiler host",
		["rustc", "-vV"],
		workspace,
		"stdout",
	);
	const target = compiler
		.split("\n")
		.find((line) => line.startsWith("host: "))
		?.slice(6)
		.trim();
	required(
		target &&
			/^(x86_64|aarch64)-(unknown-linux-(gnu|musl)|apple-darwin|pc-windows-msvc)$/.test(
				target,
			),
		"native package target",
		"supported Rust host triple",
		target,
	);
	plan.target = target;
	plan.compiler = compiler.trim();
	plan.launcher = join(v8, "bin", `rustc-wrapper${suffix(target)}`);
	return plan;
}

async function lock(root: string, say: Context["say"]) {
	await mkdir(root, { recursive: true });
	const database = new Database(join(root, "source-install-lock.sqlite"), {
		create: true,
	});
	database.exec("PRAGMA busy_timeout=1000");
	while (true) {
		try {
			database.exec("BEGIN IMMEDIATE");
			break;
		} catch (error) {
			if ((error as any).code !== "SQLITE_BUSY") {
				database.close();
				throw error;
			}
			say("waiting for another source-package installation");
			await Bun.sleep(1000);
		}
	}
	return () => {
		database.exec("ROLLBACK");
		database.close();
	};
}

type LinkChange = {
	path: string;
	temporary: string;
	kind?: "directory";
	backup?: string;
	installed?: { ino: number; dev: number; size: number; mtimeMs: number };
};
async function publishLinks(changes: LinkChange[]) {
	const published: LinkChange[] = [];
	try {
		for (const change of changes) {
			const current = await exists(change.path);
			required(
				!current?.isDirectory() || change.kind === "directory",
				"installed executable alias path",
				"file, symlink, or absent",
				{ path: display(change.path), directory: current?.isDirectory() },
			);
		}
		for (const change of changes) {
			if (await exists(change.path)) {
				change.backup = `${change.path}.before-source-install-${crypto.randomUUID()}`;
				await rename(change.path, change.backup);
			}
			try {
				await rename(change.temporary, change.path);
			} catch (error) {
				if (change.backup) await rename(change.backup, change.path);
				throw error;
			}
			const installed = await lstat(change.path);
			change.installed = {
				ino: installed.ino,
				dev: installed.dev,
				size: installed.size,
				mtimeMs: installed.mtimeMs,
			};
			published.push(change);
		}
	} catch (error) {
		for (const change of published.reverse()) {
			const current = await lstat(change.path);
			const received = {
				ino: current.ino,
				dev: current.dev,
				size: current.size,
				mtimeMs: current.mtimeMs,
			};
			required(
				JSON.stringify(received) === JSON.stringify(change.installed),
				"CLI alias changed during rollback; backup retained",
				change.installed,
				received,
			);
			await rm(change.path, { force: true, recursive: true });
			if (change.backup) await rename(change.backup, change.path);
		}
		throw error;
	} finally {
		for (const change of changes)
			await rm(change.temporary, { force: true, recursive: true });
	}
}

async function installLinks(ctx: Context, plan: Plan, packageDir: string) {
	await mkdir(plan.cargo_bin, { recursive: true });
	const changes: LinkChange[] = [];
	const extension = suffix(plan.target);
	const names = ["codex", "codex-code-mode-host", "logs_client"];
	const windows = extension === ".exe";
	let proxy: string | undefined;
	try {
		if (windows) {
			proxy = join(plan.cargo_bin, `.codex-proxy-${crypto.randomUUID()}.exe`);
			const built = await Bun.build({
				entrypoints: [join(plan.skill_root, "scripts", "windows_bin_proxy.ts")],
				compile: {
					outfile: proxy,
					executablePath: process.execPath,
					autoloadDotenv: false,
					autoloadBunfig: false,
				},
				minify: true,
			});
			required(
				built.success,
				"Windows native launcher",
				"successful Bun compilation",
				built.logs,
			);
			const metadata = join(
				plan.cargo_bin,
				`.codex-meta-${crypto.randomUUID()}`,
			);
			await writeFile(
				metadata,
				JSON.stringify({ package: display(packageDir) }),
			);
			changes.push({
				path: join(plan.cargo_bin, ".codex-source-package.json"),
				temporary: metadata,
			});
		}
		for (const name of names) {
			const path = join(plan.cargo_bin, `${name}${extension}`);
			const temporary = `${path}.next-source-install-${crypto.randomUUID()}`;
			if (proxy) await copyFile(proxy, temporary);
			else await symlink(join(packageDir, "bin", name), temporary);
			changes.push({ path, temporary });
		}
		const standalone = join(plan.runtime_root, "packages", "standalone");
		const temporary = join(standalone, `.current-${crypto.randomUUID()}`);
		await symlink(packageDir, temporary, windows ? "junction" : "dir");
		changes.push({
			path: join(standalone, "current"),
			temporary,
			kind: "directory",
		});
		await publishLinks(changes);
		// A source package is pinned; preserve the old marker as a recoverable backup.
		const marker = join(standalone, "auto-update-version");
		if (await exists(marker))
			await rename(
				marker,
				`${marker}.before-source-install-${crypto.randomUUID()}`,
			);
		return changes;
	} finally {
		if (proxy) await rm(proxy, { force: true });
		for (const change of changes)
			await rm(change.temporary, { force: true, recursive: true });
	}
}

export async function install(ctx: Context, args: string[] = []) {
	const selected = options(args);
	required(
		Bun.semver.satisfies(Bun.version, ">=1.4.1"),
		"Bun runtime",
		">=1.4.1",
		Bun.version,
	);
	const plan = await resolvePlan(ctx);
	const childEnv: Environment = {
		...ctx.env,
		PATH: [dirname(process.execPath), ctx.env.PATH]
			.filter(Boolean)
			.join(delimiter),
		CODEX_V8_BUN: process.execPath,
		CODEX_REPO_ROOT: plan.repository_root,
		CODEX_HOME: plan.runtime_root,
		CARGO_HOME: dirname(plan.cargo_bin),
		RUSTC_WRAPPER: plan.launcher,
	};
	ctx = { ...ctx, env: childEnv };
	for (const path of Object.values(selected.prebuilt)) await executable(path);
	if (selected.plan)
		return {
			...plan,
			mode: selected.prepareV8 ? "prepare-v8" : selected.preparePackage ? "prepare-package" : "install",
			daemon: selected.daemon && !selected.preparePackage,
			prebuilt: selected.prebuilt,
			operations: selected.prepareV8
				? ["prepare native V8 launcher"]
				: [
						"prepare native V8 launcher",
						"resolve package builder interpreter and TLS trust",
						"reuse a package for this exact checkout or refresh dependencies and build",
						"assemble and validate platform package",
						"include logs_client",
						"verify compiled CLI version",
						"retain immutable validated package",
						...(selected.preparePackage ? ["return user-run handoff command"] : [
							...(selected.daemon ? ["stop previous runtime and helpers"] : []),
							"publish recoverable CLI aliases",
						]),
						...(selected.daemon && !selected.preparePackage
							? [
									"select and pin source daemon package",
									"start selected app-server with saved settings",
									"verify process exit, executable provenance and runtime versions",
								]
							: []),
					],
		};
	await run(
		ctx,
		plan,
		"prepare V8 launcher",
		[process.execPath, "--no-env-file", "run", "setup"],
		plan.v8_repository,
	);
	await executable(plan.launcher);
	if (selected.prepareV8)
		return { ...plan, mode: "prepared-v8", side_effects: [plan.launcher] };

	const pythonInfo = await run(
		ctx,
		plan,
		"package builder interpreter",
		[
			plan.python,
			"-c",
			"import json, ssl, sys; print(json.dumps({'version': list(sys.version_info[:3]), 'trust': ssl.get_default_verify_paths()._asdict()}))",
		],
		plan.repository_root,
		"stdout",
	);
	const python = JSON.parse(pythonInfo) as PythonRuntime;
	const [major, minor] = python.version;
	required(
		major > 3 || (major === 3 && minor >= 11),
		"Python package builder runtime",
		">=3.11",
		python,
	);
	if (
		ctx.env.SSL_CERT_FILE === undefined &&
		ctx.env.SSL_CERT_DIR === undefined &&
		python.trust.cafile === null &&
		process.platform !== "win32"
	) {
		const candidates =
			process.platform === "darwin"
				? ["/etc/ssl/cert.pem"]
				: [
						"/etc/ssl/certs/ca-certificates.crt",
						"/etc/pki/tls/certs/ca-bundle.crt",
						"/etc/ssl/ca-bundle.pem",
						"/etc/ssl/cert.pem",
					];
		for (const bundle of candidates) {
			if (
				!(
					await stat(bundle).catch((error: NodeJS.ErrnoException) => {
						if (error.code === "ENOENT") return undefined;
						throw error;
					})
				)?.isFile()
			)
				continue;
			ctx = { ...ctx, env: { ...ctx.env, SSL_CERT_FILE: bundle } };
			ctx.say(
				`Python CA bundle missing at ${python.trust.openssl_cafile}; using system bundle ${bundle} with certificate verification enabled`,
			);
			break;
		}
	}
	const standalone = join(plan.runtime_root, "packages", "standalone");
	const releases = join(standalone, "releases");
	const unlock = await lock(standalone, ctx.say);
	let stage: string | undefined;
	let packageDir: string | undefined;
	let links: LinkChange[] = [];
	try {
		await mkdir(releases, { recursive: true });
		if (!Object.keys(selected.prebuilt).length) {
			const source = await sourceIdentity(plan.repository_root, plan.launcher, plan.compiler, ctx.env);
			const reused = await reusablePackage(join(standalone, "prepared"), source, plan.target, plan.version);
			if (reused) {
				ctx.say(`reusing prepared binaries for this checkout: ${display(reused)}`);
				const extension = suffix(plan.target);
				for (const [flag, name] of [["--entrypoint-bin", "codex"], ["--code-mode-host-bin", "codex-code-mode-host"], ["--logs-client-bin", "logs_client"]]) selected.prebuilt[flag] = join(reused, "bin", `${name}${extension}`);
				if (plan.target.includes("linux")) selected.prebuilt["--bwrap-bin"] = join(reused, "codex-resources", "bwrap");
			}
		}
		if (!selected.prebuilt["--entrypoint-bin"] || !selected.prebuilt["--code-mode-host-bin"]) {
			const workspace = join(plan.repository_root, "codex-rs");
			await run(ctx, plan, "upgrade source dependencies", ["cargo", "upgrade", "--recursive", "--verbose"], workspace);
			await run(ctx, plan, "resolve source dependencies", ["cargo", "update", "--recursive"], workspace);
		}
		stage = await mkdtemp(join(releases, ".source-build-"));
		const buildArgs = [
			plan.python,
			join(plan.repository_root, "scripts", "build_codex_package.py"),
			"--variant",
			"codex",
			"--target",
			plan.target,
			"--cargo-profile",
			"release",
			"--package-dir",
			stage,
		];
		for (const flag of ["--entrypoint-bin", "--code-mode-host-bin", "--bwrap-bin"])
			if (selected.prebuilt[flag])
				buildArgs.push(flag, selected.prebuilt[flag]);
		await run(ctx, plan, "build and validate complete package", buildArgs);
		const metadata = JSON.parse(
			await readFile(join(stage, "codex-package.json"), "utf8"),
		);
		required(
			metadata.target === plan.target && metadata.variant === "codex",
			"prepared package identity",
			{ target: plan.target, variant: "codex" },
			metadata,
		);
		const extension = suffix(plan.target);
		let logs = selected.prebuilt["--logs-client-bin"];
		if (!logs) {
			await run(
				ctx,
				plan,
				"build logs_client",
				[
					"cargo",
					"build",
					"--target",
					plan.target,
					"--profile",
					"release",
					"--bin",
					"logs_client",
				],
				join(plan.repository_root, "codex-rs"),
			);
			const target = childEnv.CARGO_TARGET_DIR
				? resolve(plan.repository_root, "codex-rs", childEnv.CARGO_TARGET_DIR)
				: join(plan.repository_root, "codex-rs", "target");
			logs = join(target, plan.target, "release", `logs_client${extension}`);
		}
		await executable(logs);
		await copyFile(logs, join(stage, "bin", `logs_client${extension}`));
		if (!extension) await chmod(join(stage, "bin", "logs_client"), 0o755);
		const reportedVersion = await run(
			ctx,
			plan,
			"verify package CLI version",
			[join(stage, metadata.entrypoint), "--version"],
			plan.repository_root,
			"stdout",
		);
		required(
			reportedVersion === `codex-cli ${metadata.version}`,
			"prepared package version",
			metadata.version,
			reportedVersion,
		);
		packageDir = join(
			releases,
			`local-${metadata.version}-${plan.target}-${crypto.randomUUID()}`,
		);
		await rename(stage, packageDir);
		stage = undefined;
		if (selected.preparePackage) {
			const handoff = ["just", "i"];
			const command = "just i";
			ctx.say(`package prepared; final handoff is reserved for the user: ${command}`);
			const record = join(standalone, "prepared", `${basename(packageDir)}.json`);
			const source = await sourceIdentity(plan.repository_root, plan.launcher, plan.compiler, ctx.env);
			const artifacts = [];
			for (const name of ["codex", "codex-code-mode-host", "logs_client"]) {
				const path = `bin/${name}${extension}`;
				artifacts.push({ path, sha256: await fileDigest(join(packageDir, path)) });
			}
			if (plan.target.includes("linux")) artifacts.push({ path: "codex-resources/bwrap", sha256: await fileDigest(join(packageDir, "codex-resources", "bwrap")) });
			const prepared = { ...plan, version: metadata.version, status: "prepared" as const, package: packageDir, daemon: "user-reserved" as const,
				handoff: { cwd: plan.repository_root, argv: handoff, command }, source, artifacts, record, side_effects: [releases, dirname(record)] };
			await mkdir(dirname(record), { recursive: true });
			await writeFile(record, JSON.stringify(prepared, (_key, value) => typeof value === "string" ? display(value) : value, 2) + "\n");
			ctx.say(`prepared package record: ${display(record)}`);
			return prepared;
		}
		ctx.say(`installing ${metadata.version} from ${display(packageDir)}`);
		const codex = join(packageDir, metadata.entrypoint);
		let runtime: RuntimeOutcome | undefined;
		const roots = [
			join(plan.runtime_root, "packages"), plan.cargo_bin,
			childEnv.CARGO_TARGET_DIR
				? resolve(plan.repository_root, "codex-rs", childEnv.CARGO_TARGET_DIR)
				: join(plan.repository_root, "codex-rs", "target"),
		];
		let stopped: RuntimeOutcome["stopped"] | undefined;
		if (selected.daemon) {
			for (const name of ["codex", "codex-code-mode-host", "logs_client"]) {
				const alias = join(plan.cargo_bin, `${name}${extension}`);
				required(!(await exists(alias))?.isDirectory(), "installed executable alias path", "file, symlink, or absent", alias);
			}
			stopped = JSON.parse(await run(ctx, plan, "stop previous runtime and helpers", [
				plan.python, join(plan.skill_root, "scripts", "source_install.py"), "stop", ...roots,
			], plan.repository_root, "stdout")) as RuntimeOutcome["stopped"];
			required(stopped.status === "stopped" && Array.isArray(stopped.remaining) && stopped.remaining.length === 0,
				"previous runtime exit", "no remaining processes", stopped);
		}
		// Running loose binaries must exit before their alias files are renamed.
		links = await installLinks(ctx, plan, packageDir);
		if (selected.daemon) {
			const stateDir = join(plan.runtime_root, "app-server-daemon");
			const legacy = await Promise.all(["app-server.pid", "app-server.stderr.log", "app-server-updater.pid", "app-server-updater.stderr.log"].map(name => exists(join(stateDir, name))));
			if (await exists(join(plan.runtime_root, "packages", "app-server-daemon", "current")) || legacy.some(Boolean)) {
				await run(ctx, plan, "select and pin source daemon package", [
					plan.python, join(plan.skill_root, "scripts", "source_install.py"), "select", plan.runtime_root, codex, ...roots,
				]);
			}
			// Restart also starts a stopped or fresh daemon, retaining saved settings.
			// On a fresh home its native preparation installs this complete package.
			const launched = JSON.parse(await run(ctx, plan, "start selected app-server with saved settings", [
				codex, "app-server", "daemon", "restart",
			], plan.repository_root, "stdout")) as DaemonState;
			const state = JSON.parse(
				await run(
					ctx,
					plan,
					"verify selected daemon",
					[codex, "app-server", "daemon", "version"],
					plan.repository_root,
					"stdout",
				),
			) as DaemonState;
			required(
				state.backend === "pid" && launched.backend === "pid" &&
					state.cliVersion === metadata.version &&
					state.managedCodexVersion === metadata.version &&
					state.appServerVersion === metadata.version,
				"installed runtime versions",
				metadata.version,
				state,
			);
			const managed = expand(state.managedCodexPath);
			const identities = [];
			for (const name of ["codex", "codex-code-mode-host", "logs_client"]) {
				const source = join(packageDir, "bin", `${name}${extension}`);
				const selectedPath = join(dirname(managed), `${name}${extension}`);
				const expected = await fileDigest(source);
				const received = await fileDigest(selectedPath);
				required(expected === received, "selected runtime executable", { source, sha256: expected }, { selected: selectedPath, sha256: received });
				identities.push({ source, selected: selectedPath, sha256: received });
			}
			const observed = JSON.parse(await run(ctx, plan, "verify running executable provenance", [
				plan.python, join(plan.skill_root, "scripts", "source_install.py"), "inspect", ...roots,
			], plan.repository_root, "stdout")) as { processes: RuntimeProcess[] };
			const allowed = await Promise.all(identities.flatMap(identity => [identity.source, identity.selected]).map(path => realpath(path)));
			const server = observed.processes.find(item => item.pid === launched.pid);
			required(server && await realpath(expand(server.executable)) === await realpath(managed),
				"running app-server executable", { pid: launched.pid, executable: managed }, server);
			for (const item of observed.processes) {
				if (["codex", "codex-code-mode-host", "logs_client"].map(name => `${name}${extension}`).includes(basename(item.executable))) {
					required(allowed.includes(await realpath(expand(item.executable))), "running runtime generation", allowed, item);
				}
			}
			required(stopped, "previous runtime handoff", "completed shutdown observation", stopped);
			runtime = { stopped, launched, state, processes: observed.processes, executables: identities };
		}
		const receipt = {
			...plan,
			version: metadata.version,
			status: "installed" as const,
			package: packageDir,
			daemon: selected.daemon ? "selected-and-verified" : "not-requested",
			runtime,
			links,
			side_effects: [standalone, plan.cargo_bin],
		};
		await writeFile(
			join(standalone, "source-install.json"),
			JSON.stringify(
				receipt,
				(_key, value) => (typeof value === "string" ? display(value) : value),
				2,
			) + "\n",
		);
		return receipt;
	} catch (error) {
		throw new Error(
			`${error instanceof Error ? error.message : error}${packageDir ? `; validated package retained at ${display(packageDir)}; ${links.length ? "CLI alias publication completed" : "CLI alias publication did not complete"}` : "; installed CLI aliases were not changed"}`,
			{ cause: error },
		);
	} finally {
		if (stage) await rm(stage, { recursive: true, force: true });
		unlock();
	}
}

async function independentInstall(args: string[]) {
	required(process.env.CODEX_REPO_ROOT, "Codex repository authority", "CODEX_REPO_ROOT", "missing");
	const runtime = expand(process.env.CODEX_HOME || join(home, ".codex"));
	const attempts = join(runtime, "packages", "standalone", "source-install-attempts");
	await mkdir(attempts, { recursive: true });
	const attempt = await mkdtemp(join(attempts, "install-"));
	const manifest = join(attempt, "invocation.json");
	await writeFile(manifest, JSON.stringify({
		nonce: crypto.randomUUID(), command: [process.execPath, "--no-env-file", import.meta.path, ...args],
		cwd: process.cwd(),
	}, (_key, value) => typeof value === "string" ? display(value) : value, 2) + "\n");
	const python = process.env.CODEX_INSTALL_PYTHON || (process.platform === "win32" ? "python" : "python3");
	const launcher = Bun.spawn([python, join(dirname(import.meta.path), "source_install.py"), "launch", manifest], {
		stdin: "ignore", stdout: "pipe", stderr: "pipe",
	});
	const [stdout, stderr] = await Promise.all([
		new Response(launcher.stdout).text(), new Response(launcher.stderr).text(),
	]);
	required(await launcher.exited === 0, "independent installation lifetime", "detached supervisor", { stdout, stderr });
	const supervisor = JSON.parse(stdout);
	console.error(`[just i +${elapsed()}s] independent installation: PID ${supervisor.supervisor_pid}; outcome ${display(join(attempt, "result.json"))}`);
	const offsets = new Map<string, number>();
	const decoders = new Map<string, TextDecoder>();
	const relay = async (name: string, output: NodeJS.WriteStream) => {
		const file = Bun.file(join(attempt, name));
		if (!await file.exists()) return;
		const offset = offsets.get(name) || 0;
		const bytes = await file.slice(offset).arrayBuffer();
		if (!bytes.byteLength) return;
		offsets.set(name, offset + bytes.byteLength);
		const decoder = decoders.get(name) || new TextDecoder();
		decoders.set(name, decoder);
		output.write(decoder.decode(bytes, { stream: true }));
	};
	const cancel = () => { void writeFile(join(attempt, "cancel"), "cancel\n"); };
	process.on("SIGINT", cancel);
	try {
		while (!await Bun.file(join(attempt, "result.json")).exists()) {
			await relay("stdout.log", process.stdout);
			await relay("stderr.log", process.stderr);
			await Bun.sleep(200);
		}
		await relay("stdout.log", process.stdout);
		await relay("stderr.log", process.stderr);
		for (const [name, decoder] of decoders) (name === "stdout.log" ? process.stdout : process.stderr).write(decoder.decode());
		const result = await Bun.file(join(attempt, "result.json")).json();
		process.exitCode = result.exit_status;
		console.error(`[just i +${elapsed()}s] independent installation: exit ${result.exit_status}; ${display(join(attempt, "result.json"))}`);
		if (result.error) console.error(display(result.error));
	} finally {
		process.off("SIGINT", cancel);
	}
}

export async function main(args = process.argv.slice(2)) {
	if (args[0] === "i") args = args.slice(1);
	if (args.includes("--help")) {
		console.log(
			"just i [--plan] [--prepare-v8] [--prepare-package] [--no-daemon] [--entrypoint-bin PATH] [--code-mode-host-bin PATH] [--logs-client-bin PATH] [--bwrap-bin PATH]\nLocations: AGENTIC_SKILLS_REPO (import), CODEX_REPO_ROOT, CODEX_V8_REPO, CODEX_HOME, CARGO_HOME. Optional interpreter: CODEX_INSTALL_PYTHON.",
		);
		return;
	}
	try {
		if (process.env.CODEX_V8_BUN) {
			const configured = process.env.CODEX_V8_BUN.startsWith("~/")
				? expand(process.env.CODEX_V8_BUN)
				: process.env.CODEX_V8_BUN;
			const selected = Bun.which(configured);
			required(selected, "selected Bun executable", configured, "not found");
			if ((await realpath(selected)) !== (await realpath(process.execPath))) {
				const child = Bun.spawn(
					[selected, "--no-env-file", import.meta.path, ...args],
					{ stdin: "inherit", stdout: "inherit", stderr: "inherit" },
				);
				process.exitCode = await child.exited;
				return;
			}
		}
		const selectedOptions = options(args);
		if (process.env.CODEX_SOURCE_INSTALL_WORKER) {
			delete process.env.CODEX_SOURCE_INSTALL_WORKER;
		} else if (selectedOptions.daemon && !selectedOptions.plan && !selectedOptions.prepareV8 && !selectedOptions.preparePackage) {
			await independentInstall(args);
			return;
		}
		const quiet = args.includes("--plan");
		const ctx: Context = {
			env: process.env,
			execute: quiet
				? async (command, env) => {
						const child = Bun.spawn(command.argv, {
							cwd: command.cwd,
							env,
							stdout: "pipe",
							stderr: "pipe",
						});
						const [stdout, stderr] = await Promise.all([
							new Response(child.stdout).text(),
							new Response(child.stderr).text(),
						]);
						const exitCode = await child.exited;
						required(exitCode === 0, command.phase, "exit 0", {
							exitCode,
							stdout,
							stderr,
						});
						return { command, exitCode, stdout };
					}
				: execute,
			say: (message) =>
				console.error(`[just i +${elapsed()}s] ${display(message)}`),
		};
		const result = await install(ctx, args);
		console.log(
			JSON.stringify(
				result,
				(_key, value) => (typeof value === "string" ? display(value) : value),
				2,
			),
		);
	} catch (error) {
		console.error(
			`[just i +${elapsed()}s] ${display(error instanceof Error ? error.message : String(error))}`,
		);
		process.exitCode = 1;
	}
}

if (import.meta.main) await main();
