import { afterEach, expect, test } from "bun:test";
import {
	copyFile,
	cp,
	lstat,
	mkdir,
	mkdtemp,
	readFile,
	readlink,
	realpath,
	rm,
	symlink,
	writeFile,
} from "node:fs/promises";
import { delimiter, dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";
import { rootCertificates } from "node:tls";
import {
	install,
	InstallConditionError,
	type Context,
} from "./install_codex.ts";

const skill = dirname(dirname(fileURLToPath(import.meta.url)));
const scratch = join(dirname(skill), ".scratchpad", "upgrade-codex-patch");
const temporary: string[] = [];
afterEach(async () => {
	for (const root of temporary.splice(0))
		await rm(root, { recursive: true, force: true });
});

function installed(result: Awaited<ReturnType<typeof install>>) {
	if (!("status" in result) || result.status !== "installed") {
		throw new Error(
			`Expected an installed outcome, received ${JSON.stringify(result)}`,
		);
	}
	return result;
}

async function program(path: string, body: string) {
	await mkdir(dirname(path), { recursive: true });
	await writeFile(path, `#!/usr/bin/env bun\n${body}\n`, { mode: 0o755 });
}

async function fixture() {
	await mkdir(scratch, { recursive: true });
	const root = await mkdtemp(join(scratch, "installer fixture "));
	temporary.push(root);
	const repository = join(root, "source checkout");
	const v8 = join(root, "V8 helper");
	const runtime = join(root, "runtime state");
	const cargoHome = join(root, "cargo state");
	const pythonCertFile = join(root, "native Python CA bundle.pem");
	await writeFile(pythonCertFile, rootCertificates.join("\n"));
	await mkdir(join(repository, "codex-rs", ".cargo"), { recursive: true });
	await mkdir(join(repository, "scripts"), { recursive: true });
	await mkdir(v8, { recursive: true });
	await mkdir(join(cargoHome, "bin"), { recursive: true });
	await writeFile(
		join(repository, "codex-rs", "Cargo.toml"),
		'[workspace]\nmembers=[]\n[workspace.package]\nversion="1.2.3"\n',
	);
	await writeFile(
		join(repository, "codex-rs", ".cargo", "config.toml"),
		`[build]\nrustc-wrapper=${JSON.stringify(join(v8, "bin", "rustc-wrapper"))}\n`,
	);
	// A valid Python entrypoint occupies the production builder role; tests use
	// an injected process adapter and never run a Python interpreter.
	await writeFile(
		join(repository, "scripts", "build_codex_package.py"),
		'raise RuntimeError("fixture builder requires the process adapter")\n',
	);
	await writeFile(
		join(v8, "package.json"),
		JSON.stringify({
			name: "codex-v8",
			scripts: { setup: "bun scripts/setup.ts" },
		}),
	);
	const commands: Parameters<Context["execute"]>[0][] = [];
	const env = {
		...process.env,
		CODEX_REPO_ROOT: repository,
		CODEX_V8_REPO: v8,
		CODEX_HOME: runtime,
		CARGO_HOME: cargoHome,
	};
	const behavior = {
		target: "x86_64-unknown-linux-gnu",
		builderVersion: "1.2.3",
		pythonCertFile: pythonCertFile as string | null,
		failBuilder: false,
		badTarget: false,
		daemonVersion: "1.2.3",
		backend: "pid" as string | undefined,
		remaining: [] as number[],
		corruptHost: false,
		hold: undefined as Promise<void> | undefined,
	};
	await mkdir(join(runtime, "packages", "app-server-daemon", "current"), { recursive: true });
	const ctx: Context = {
		env,
		say: () => {},
		execute: async (command) => {
			commands.push(command);
			let stdout = "";
			const extension = behavior.target.includes("windows") ? ".exe" : "";
			if (command.phase === "compiler host")
				stdout = `rustc fixture\nhost: ${behavior.target}\n`;
			else if (command.phase === "package builder interpreter")
				stdout = JSON.stringify({
					version: [3, 14, 0],
					trust: {
						cafile: behavior.pythonCertFile,
						capath: null,
						openssl_cafile_env: "SSL_CERT_FILE",
						openssl_cafile: pythonCertFile,
						openssl_capath_env: "SSL_CERT_DIR",
						openssl_capath: join(root, "native Python certificate directory"),
					},
				});
			else if (command.phase === "prepare V8 launcher")
				await program(
					join(v8, "bin", `rustc-wrapper${extension}`),
					'console.log("fixture launcher");',
				);
			else if (command.phase === "build and validate complete package") {
				if (behavior.failBuilder)
					return {
						command,
						exitCode: 7,
						stdout: "builder failed before publication",
					};
				if (behavior.hold) await behavior.hold;
				const destination =
					command.argv[command.argv.indexOf("--package-dir") + 1];
				await mkdir(join(destination, "bin"));
				await mkdir(join(destination, "codex-path"));
				await mkdir(join(destination, "codex-resources"));
				await program(
					join(destination, "bin", `codex${extension}`),
					`console.log("codex-cli ${behavior.builderVersion}");`,
				);
				await program(
					join(destination, "bin", `codex-code-mode-host${extension}`),
					'console.log("fixture code mode");',
				);
				await program(
					join(destination, "codex-path", `rg${extension}`),
					'console.log("fixture rg");',
				);
				if (behavior.target.includes("linux"))
					await program(
						join(destination, "codex-resources", "bwrap"),
						'console.log("fixture bwrap");',
					);
				if (extension)
					for (const name of [
						"codex-command-runner.exe",
						"codex-windows-sandbox-setup.exe",
					])
						await program(
							join(destination, "codex-resources", name),
							'console.log("fixture Windows helper");',
						);
				await writeFile(
					join(destination, "codex-package.json"),
					JSON.stringify({
						layoutVersion: 1,
						version: behavior.builderVersion,
						target: behavior.badTarget
							? "aarch64-apple-darwin"
							: behavior.target,
						variant: "codex",
						entrypoint: `bin/codex${extension}`,
						resourcesDir: "codex-resources",
						pathDir: "codex-path",
					}),
				);
			} else if (command.phase === "build logs_client") {
				await program(
					join(
						repository,
						"codex-rs",
						"target",
						behavior.target,
						"release",
						`logs_client${extension}`,
					),
					'console.log("fixture logs");',
				);
			} else if (command.phase === "verify package CLI version")
				stdout = `codex-cli ${behavior.builderVersion}\n`;
		else if (command.phase === "stop previous runtime and helpers")
			stdout = JSON.stringify({ status: "stopped", processes: [{ pid: 10 }], remaining: behavior.remaining });
		else if (command.phase === "start selected app-server with saved settings") {
			const packageDir = dirname(dirname(command.argv[0]));
			const selected = join(runtime, "packages", "app-server-daemon", "current");
			await cp(packageDir, selected, { recursive: true });
			if (behavior.corruptHost) await writeFile(join(selected, "bin", `codex-code-mode-host${extension}`), "stale host");
			stdout = JSON.stringify({ backend: behavior.backend, pid: 11 });
		} else if (command.phase === "verify selected daemon")
				stdout = JSON.stringify({
					backend: behavior.backend,
					managedCodexPath: join(runtime, "packages", "app-server-daemon", "current", "bin", `codex${extension}`),
					cliVersion: behavior.builderVersion,
					managedCodexVersion: behavior.daemonVersion,
					appServerVersion: behavior.daemonVersion,
				});
		else if (command.phase === "verify running executable provenance")
			stdout = JSON.stringify({ processes: [{ pid: 11, executable: join(runtime, "packages", "app-server-daemon", "current", "bin", `codex${extension}`) }] });
			return { command, exitCode: 0, stdout };
		},
	};
	return { root, repository, v8, runtime, cargoHome, commands, behavior, ctx };
}

test("installs the complete prepared package, retains old binaries, and pins matching daemon", async () => {
	const f = await fixture();
	const old = join(f.cargoHome, "bin", "codex");
	await program(old, 'console.log("old source CLI");');
	const sourceBefore = await readFile(
		join(f.repository, "codex-rs", ".cargo", "config.toml"),
	);
	const execute = f.ctx.execute;
	f.ctx.execute = async (command, env) => {
		if (command.phase === "stop previous runtime and helpers") {
			expect((await lstat(old)).isSymbolicLink()).toBe(false);
			expect(await readFile(old, "utf8")).toBe('#!/usr/bin/env bun\nconsole.log("old source CLI");\n');
		}
		return execute(command, env);
	};
	const result = installed(await install(f.ctx));
	expect(result.status).toBe("installed");
	expect(result.daemon).toBe("selected-and-verified");
	const published = result.package!;
	expect(
		JSON.parse(await readFile(join(published, "codex-package.json"), "utf8")),
	).toEqual({
		layoutVersion: 1,
		version: "1.2.3",
		target: "x86_64-unknown-linux-gnu",
		variant: "codex",
		entrypoint: "bin/codex",
		resourcesDir: "codex-resources",
		pathDir: "codex-path",
	});
	for (const name of ["codex", "codex-code-mode-host", "logs_client"]) {
		expect(await readlink(join(f.cargoHome, "bin", name))).toBe(
			join(published, "bin", name),
		);
		expect((await lstat(join(published, "bin", name))).mode & 0o111).not.toBe(
			0,
		);
	}
	expect(
		await realpath(join(f.runtime, "packages", "standalone", "current")),
	).toBe(published);
	const backup = result.links!.find((link) => link.path === old)!.backup!;
	expect(await readFile(backup, "utf8")).toBe(
		'#!/usr/bin/env bun\nconsole.log("old source CLI");\n',
	);
	expect(
		await readFile(join(f.repository, "codex-rs", ".cargo", "config.toml")),
	).toEqual(sourceBefore);
	expect(f.commands.map((command) => command.phase)).toEqual([
		"compiler host",
		"prepare V8 launcher",
		"package builder interpreter",
		"build and validate complete package",
		"build logs_client",
		"verify package CLI version",
		"stop previous runtime and helpers",
		"select and pin source daemon package",
		"start selected app-server with saved settings",
		"verify selected daemon",
		"verify running executable provenance",
	]);
	expect(
		f.commands.find(
			(command) => command.phase === "select and pin source daemon package",
		)!.argv,
	).toEqual([
		process.platform === "win32" ? "python" : "python3",
		join(skill, "scripts", "source_install.py"),
		"select", f.runtime, join(published, "bin", "codex"),
		join(f.runtime, "packages"), join(f.cargoHome, "bin"), join(f.repository, "codex-rs", "target"),
	]);
});

test("package preparation returns the handoff without changing aliases or controlling services", async () => {
	const f = await fixture();
	const old = join(f.cargoHome, "bin", "codex");
	await program(old, 'console.log("keep running source");');
	const before = await readFile(old);
	const result = await install(f.ctx, ["--prepare-package"]);
	if (!("status" in result) || result.status !== "prepared") throw new Error("Expected a prepared package");
	expect(result.daemon).toBe("user-reserved");
	expect(await readFile(old)).toEqual(before);
	expect(await Bun.file(join(f.runtime, "packages", "standalone", "source-install.json")).exists()).toBe(false);
	expect(f.commands.some(command => command.phase.includes("runtime") || command.argv.includes("daemon"))).toBe(false);
	expect({ cwd: result.handoff.cwd, argv: result.handoff.argv }).toEqual({ cwd: f.repository, argv: ["just", "i",
		"--entrypoint-bin", join(result.package, "bin", "codex"),
		"--code-mode-host-bin", join(result.package, "bin", "codex-code-mode-host"),
		"--logs-client-bin", join(result.package, "bin", "logs_client"),
		"--bwrap-bin", join(result.package, "codex-resources", "bwrap")] });
	await writeFile(join(f.repository, "justfile"), "import x'${AGENTIC_SKILLS_REPO}/upgrade-codex-patch/justfile'\nexport CODEX_REPO_ROOT := justfile_directory()\n");
	const command = result.handoff.command + " --plan";
	const child = Bun.spawn(process.platform === "win32"
		? ["powershell.exe", "-NoProfile", "-Command", command]
		: ["/bin/sh", "-c", command], {
		cwd: f.repository, env: { ...f.ctx.env, AGENTIC_SKILLS_REPO: dirname(skill) }, stdout: "pipe", stderr: "pipe",
	});
	const [stdout, stderr] = await Promise.all([new Response(child.stdout).text(), new Response(child.stderr).text()]);
	expect({ exit: await child.exited, stderr }).toEqual({ exit: 0, stderr: "" });
	const plan = JSON.parse(stdout);
	const executable = plan.prebuilt["--entrypoint-bin"].replace(/^~\//, homedir() + "/");
	expect(executable).toBe(join(result.package, "bin", "codex"));
	expect(await readFile(old)).toEqual(before);
});

test("expanded location authorities govern the native setup, build and daemon commands", async () => {
	const f = await fixture();
	const homePath = (path: string) =>
		`~/${relative(homedir(), path).replaceAll("\\", "/")}`;
	f.ctx.env = {
		PATH: process.env.PATH,
		CODEX_REPO_ROOT: homePath(f.repository),
		CODEX_HOME: homePath(f.runtime),
		CARGO_HOME: homePath(f.cargoHome),
		CODEX_V8_REPO: homePath(f.v8),
	};
	const observed: {
		command: Parameters<Context["execute"]>[0];
		env: Context["env"];
	}[] = [];
	const execute = f.ctx.execute;
	f.ctx.execute = async (command, env) => {
		observed.push({ command, env });
		return execute(command, env);
	};
	installed(await install(f.ctx));
	const childEnv = {
		...f.ctx.env,
		PATH: [dirname(process.execPath), f.ctx.env.PATH]
			.filter(Boolean)
			.join(delimiter),
		CODEX_V8_BUN: process.execPath,
		CODEX_REPO_ROOT: f.repository,
		CODEX_HOME: f.runtime,
		CARGO_HOME: f.cargoHome,
		RUSTC_WRAPPER: join(f.v8, "bin", "rustc-wrapper"),
	};
	expect(observed).toEqual(
		f.commands.map((command) => ({
			command,
			env: command.phase === "compiler host" ? f.ctx.env : childEnv,
		})),
	);
});

test("invalid selected Bun fails at the real entrypoint without publication or unnormalized paths", async () => {
	const f = await fixture();
	const missing = join(f.root, "missing Bun runtime");
	const child = Bun.spawn(
		[
			process.execPath,
			"--no-env-file",
			join(skill, "scripts", "install_codex.ts"),
			"--plan",
		],
		{
			cwd: f.repository,
			env: { ...f.ctx.env, CODEX_V8_BUN: missing },
			stdout: "pipe",
			stderr: "pipe",
		},
	);
	const [stdout, stderr] = await Promise.all([
		new Response(child.stdout).text(),
		new Response(child.stderr).text(),
	]);
	expect({ exitCode: await child.exited, stdout }).toEqual({
		exitCode: 1,
		stdout: "",
	});
	expect(stderr).toContain("selected Bun executable");
	expect(stderr).toContain(`~/${relative(homedir(), missing)}`);
	expect(stderr).not.toContain(homedir());
	expect(
		await Bun.file(
			join(f.runtime, "packages", "standalone", "source-install.json"),
		).exists(),
	).toBe(false);
	expect(await Bun.file(join(f.cargoHome, "bin", "codex")).exists()).toBe(
		false,
	);
});

test.skipIf(process.platform === "win32")(
	"a missing native Python CA bundle uses system trust for package children and preserves verification",
	async () => {
		const f = await fixture();
		f.ctx.env = {
			...f.ctx.env,
			SSL_CERT_FILE: undefined,
			SSL_CERT_DIR: undefined,
		};
		f.behavior.pythonCertFile = null;
		const observed: {
			command: Parameters<Context["execute"]>[0];
			env: Context["env"];
		}[] = [];
		const execute = f.ctx.execute;
		f.ctx.execute = async (command, env) => {
			observed.push({ command, env });
			return execute(command, env);
		};
		const result = installed(await install(f.ctx, ["--no-daemon"]));
		const builder = observed.find(
			({ command }) => command.phase === "build and validate complete package",
		)!;
		const bundle = builder.env.SSL_CERT_FILE;
		if (!bundle)
			throw new Error("Expected the platform's existing system CA bundle");
		const probe = Bun.spawn(
			[
				result.python,
				"-c",
				"import json, ssl; context = ssl.create_default_context(); print(json.dumps({'cafile': ssl.get_default_verify_paths().cafile, 'check_hostname': context.check_hostname, 'verify_mode': context.verify_mode.name, 'certificates': context.cert_store_stats()}))",
			],
			{ env: builder.env, stdout: "pipe", stderr: "pipe" },
		);
		const [stdout, stderr] = await Promise.all([
			new Response(probe.stdout).text(),
			new Response(probe.stderr).text(),
		]);
		expect({ exitCode: await probe.exited, stderr }).toEqual({
			exitCode: 0,
			stderr: "",
		});
		const native = JSON.parse(stdout);
		const { certificates, ...configuration } = native;
		expect(configuration).toEqual({
			cafile: bundle,
			check_hostname: true,
			verify_mode: "CERT_REQUIRED",
		});
		expect(certificates.x509_ca).toBeGreaterThan(0);
		expect(builder.env).toEqual({
			...f.ctx.env,
			PATH: [dirname(process.execPath), f.ctx.env.PATH]
				.filter(Boolean)
				.join(delimiter),
			CODEX_V8_BUN: process.execPath,
			CODEX_REPO_ROOT: f.repository,
			CODEX_HOME: f.runtime,
			CARGO_HOME: f.cargoHome,
			RUSTC_WRAPPER: join(f.v8, "bin", "rustc-wrapper"),
			SSL_CERT_FILE: bundle,
		});
		expect(
			observed.find(({ command }) => command.phase === "prepare V8 launcher")!
				.env.SSL_CERT_FILE,
		).toBeUndefined();
		expect(f.ctx.env.SSL_CERT_FILE).toBeUndefined();
	},
);

for (const name of ["SSL_CERT_FILE", "SSL_CERT_DIR"] as const) {
	test(`an explicit ${name} survives a missing native bundle and a package failure`, async () => {
		const f = await fixture();
		f.behavior.pythonCertFile = null;
		f.behavior.failBuilder = true;
		const selected = join(f.root, `user-selected ${name}`);
		f.ctx.env = {
			...f.ctx.env,
			SSL_CERT_FILE: undefined,
			SSL_CERT_DIR: undefined,
			[name]: selected,
		};
		const old = join(f.cargoHome, "bin", "codex");
		await program(old, 'console.log("retain previous installation");');
		const before = await readFile(old);
		let builderEnv: Context["env"] | undefined;
		const execute = f.ctx.execute;
		f.ctx.execute = async (command, env) => {
			if (command.phase === "build and validate complete package")
				builderEnv = env;
			return execute(command, env);
		};
		await expect(install(f.ctx)).rejects.toThrow(
			"builder failed before publication",
		);
		expect(builderEnv).toEqual({
			...f.ctx.env,
			PATH: [dirname(process.execPath), f.ctx.env.PATH]
				.filter(Boolean)
				.join(delimiter),
			CODEX_V8_BUN: process.execPath,
			CODEX_REPO_ROOT: f.repository,
			CODEX_HOME: f.runtime,
			CARGO_HOME: f.cargoHome,
			RUSTC_WRAPPER: join(f.v8, "bin", "rustc-wrapper"),
		});
		expect(await readFile(old)).toEqual(before);
	});
}

test("builder failure leaves the existing CLI intact and removes only its staging directory", async () => {
	const f = await fixture();
	const old = join(f.cargoHome, "bin", "codex");
	await program(old, 'console.log("preserve this binary");');
	const before = await readFile(old);
	f.behavior.failBuilder = true;
	const failure: unknown = await install(f.ctx).catch(
		(error: unknown) => error,
	);
	if (
		!(failure instanceof Error) ||
		!(failure.cause instanceof InstallConditionError)
	)
		throw new Error("Expected the complete failed builder outcome", {
			cause: failure,
		});
	expect({
		condition: failure.cause.condition,
		expected: failure.cause.expected,
		received: failure.cause.received,
	}).toEqual({
		condition: "build and validate complete package",
		expected: "exit 0",
		received: {
			command: f.commands.find(
				(command) => command.phase === "build and validate complete package",
			),
			exitCode: 7,
			stdout: "builder failed before publication",
		},
	});
	expect(await readFile(old)).toEqual(before);
	expect((await lstat(old)).isFile()).toBe(true);
	expect(
		f.commands.some((command) => command.phase === "stop previous runtime and helpers"),
	).toBe(false);
	expect([
		...new Bun.Glob(".source-build-*").scanSync({
			cwd: join(f.runtime, "packages", "standalone", "releases"),
			onlyFiles: false,
		}),
	]).toEqual([]);
});

test("wrong prepared target fails before exposing any new executable", async () => {
	const f = await fixture();
	f.behavior.badTarget = true;
	await expect(install(f.ctx)).rejects.toThrow("prepared package identity");
	expect(await Bun.file(join(f.cargoHome, "bin", "codex")).exists()).toBe(
		false,
	);
	expect(f.commands.map((command) => command.phase)).toEqual([
		"compiler host",
		"prepare V8 launcher",
		"package builder interpreter",
		"build and validate complete package",
	]);
});

test("prepared metadata owns the installed version after the builder changes it", async () => {
	const f = await fixture();
	f.behavior.builderVersion = "1.2.4";
	f.behavior.daemonVersion = "1.2.4";
	const result = installed(await install(f.ctx));
	expect({
		version: result.version,
		daemon: result.daemon,
		metadata: JSON.parse(
			await readFile(join(result.package!, "codex-package.json"), "utf8"),
		).version,
	}).toEqual({
		version: "1.2.4",
		daemon: "selected-and-verified",
		metadata: "1.2.4",
	});
});

test("daemon mismatch reports the retained package and does not claim installation verified", async () => {
	const f = await fixture();
	f.behavior.daemonVersion = "0.9.0";
	await expect(install(f.ctx)).rejects.toThrow("installed runtime versions");
	const packageDir = await realpath(join(f.cargoHome, "bin", "codex"));
	expect(packageDir).toContain("local-1.2.3-x86_64-unknown-linux-gnu-");
	expect(
		await Bun.file(
			join(f.runtime, "packages", "standalone", "source-install.json"),
		).exists(),
	).toBe(false);
});

test("fresh installation starts the new package without first launching an old selection", async () => {
	const f = await fixture();
	await rm(join(f.runtime, "packages", "app-server-daemon", "current"), { recursive: true });
	installed(await install(f.ctx));
	expect(f.commands.filter(command => command.argv.includes("daemon")).map(command => command.argv.slice(3))).toEqual([
		["restart"], ["version"],
	]);
});

test("surviving old processes block package selection and restart", async () => {
	const f = await fixture();
	f.behavior.remaining = [10];
	await expect(install(f.ctx)).rejects.toThrow("previous runtime exit");
	expect(f.commands.some(command => command.argv.includes("daemon"))).toBe(false);
});

test("matching versions without managed ownership cannot complete installation", async () => {
	const f = await fixture();
	f.behavior.backend = undefined;
	await expect(install(f.ctx)).rejects.toThrow("installed runtime versions");
});

test("a stale selected code-mode host fails executable provenance despite matching versions", async () => {
	const f = await fixture();
	f.behavior.corruptHost = true;
	await expect(install(f.ctx)).rejects.toThrow("selected runtime executable");
	expect(await Bun.file(join(f.runtime, "packages", "standalone", "source-install.json")).exists()).toBe(false);
});

test("the official builder receives the previously built Linux sandbox helper", async () => {
	const f = await fixture();
	const bwrap = join(f.root, "prebuilt bwrap");
	await program(bwrap, 'console.log("prebuilt sandbox");');
	installed(await install(f.ctx, ["--no-daemon", "--bwrap-bin", bwrap]));
	expect(f.commands.find(command => command.phase === "build and validate complete package")!.argv.slice(-2)).toEqual(["--bwrap-bin", bwrap]);
});

test("prebuilt symlinks avoid rebuilding logs and no-daemon leaves service controls unused", async () => {
	const f = await fixture();
	const prebuilt = join(f.root, "already built logs");
	await program(prebuilt, 'console.log("existing logs client");');
	const alias = join(f.root, "logs alias");
	await symlink(prebuilt, alias);
	const result = installed(
		await install(f.ctx, ["--no-daemon", "--logs-client-bin", alias]),
	);
	expect(result.daemon).toBe("not-requested");
	expect(await readFile(join(result.package!, "bin", "logs_client"))).toEqual(
		await readFile(prebuilt),
	);
	expect(f.commands.map((command) => command.phase)).toEqual([
		"compiler host",
		"prepare V8 launcher",
		"package builder interpreter",
		"build and validate complete package",
		"verify package CLI version",
	]);
});

test("explicit V8 location wins over an obsolete Cargo hint", async () => {
	const f = await fixture();
	await writeFile(
		join(f.repository, "codex-rs", ".cargo", "config.toml"),
		'[build]\nrustc-wrapper="../../obsolete/bin/rustc-wrapper"\n',
	);
	f.ctx.env.CODEX_V8_REPO = f.v8;
	const result = await install(f.ctx, ["--prepare-v8"]);
	expect({
		root: result.v8_repository,
		launcher: result.launcher,
		effects: result.side_effects,
	}).toEqual({
		root: f.v8,
		launcher: join(f.v8, "bin", "rustc-wrapper"),
		effects: [join(f.v8, "bin", "rustc-wrapper")],
	});
	expect(await Bun.file(join(f.cargoHome, "bin", "codex")).exists()).toBe(
		false,
	);
});

test("missing Codex authority stops before any command or directory mutation", async () => {
	const f = await fixture();
	delete f.ctx.env.CODEX_REPO_ROOT;
	await expect(install(f.ctx, ["--plan"])).rejects.toThrow(
		"Codex repository authority",
	);
	expect(f.commands).toEqual([]);
	expect(await Bun.file(join(f.v8, "bin", "rustc-wrapper")).exists()).toBe(
		false,
	);
});

test("a directory occupying an executable alias is preserved and blocks all alias replacement", async () => {
	const f = await fixture();
	const original = join(f.cargoHome, "bin", "codex");
	await program(original, 'console.log("preserve original");');
	const directory = join(f.cargoHome, "bin", "logs_client");
	await mkdir(directory);
	await writeFile(join(directory, "user data"), "preserve this directory");
	await expect(install(f.ctx, ["--no-daemon"])).rejects.toThrow(
		"installed executable alias path",
	);
	expect(await readFile(original, "utf8")).toBe(
		'#!/usr/bin/env bun\nconsole.log("preserve original");\n',
	);
	expect(await readFile(join(directory, "user data"), "utf8")).toBe(
		"preserve this directory",
	);
	expect([
		...new Bun.Glob("*.next-source-install-*").scanSync({
			cwd: join(f.cargoHome, "bin"),
			onlyFiles: false,
		}),
	]).toEqual([]);
});

test("source installation removes the production update marker while retaining a backup", async () => {
	const f = await fixture();
	const standalone = join(f.runtime, "packages", "standalone");
	await mkdir(standalone, { recursive: true });
	await writeFile(
		join(standalone, "auto-update-version"),
		"previous-production-release",
	);
	await install(f.ctx, ["--no-daemon"]);
	expect(await Bun.file(join(standalone, "auto-update-version")).exists()).toBe(
		false,
	);
	const backups = [
		...new Bun.Glob("auto-update-version.before-source-install-*").scanSync({
			cwd: standalone,
		}),
	];
	expect(backups.length).toBe(1);
	expect(await readFile(join(standalone, backups[0]), "utf8")).toBe(
		"previous-production-release",
	);
});

test("concurrent installs serialize publication with native SQLite locks", async () => {
	const f = await fixture();
	let release!: () => void;
	f.behavior.hold = new Promise<void>((done) => {
		release = done;
	});
	const waits: string[] = [];
	f.ctx.say = (message) => {
		waits.push(message);
	};
	const first = install(f.ctx, ["--no-daemon"]);
	while (
		!f.commands.some(
			(command) => command.phase === "build and validate complete package",
		)
	)
		await Bun.sleep(1);
	const second = install(f.ctx, ["--no-daemon"]);
	while (!waits.includes("waiting for another source-package installation"))
		await Bun.sleep(1);
	release();
	const results = (await Promise.all([first, second])).map(installed);
	expect(results.map((result) => result.status)).toEqual([
		"installed",
		"installed",
	]);
	expect(results[0].package).not.toBe(results[1].package);
	expect(await readlink(join(f.cargoHome, "bin", "codex"))).toBe(
		join(results[1].package!, "bin", "codex"),
	);
});

test("Mac package installation uses its compiler target without Linux-only resources", async () => {
	const f = await fixture();
	f.behavior.target = "aarch64-apple-darwin";
	const result = installed(await install(f.ctx, ["--no-daemon"]));
	const invocation = f.commands.find(
		(command) => command.phase === "build and validate complete package",
	)!;
	expect(invocation.argv[invocation.argv.indexOf("--target") + 1]).toBe(
		"aarch64-apple-darwin",
	);
	expect(
		await Bun.file(join(result.package!, "codex-resources", "bwrap")).exists(),
	).toBe(false);
	expect(await readlink(join(f.cargoHome, "bin", "codex"))).toBe(
		join(result.package!, "bin", "codex"),
	);
});

test("native Windows proxy preserves arguments and runs the binary inside its package", async () => {
	const f = await fixture();
	f.behavior.target = "x86_64-pc-windows-msvc";
	const result = installed(await install(f.ctx, ["--no-daemon"]));
	const proxy = join(f.cargoHome, "bin", "codex.exe");
	expect((await lstat(proxy)).isSymbolicLink()).toBe(false);
	await program(
		join(result.package!, "bin", "codex.exe"),
		"console.log(JSON.stringify({path:process.argv[1],args:process.argv.slice(2)})); process.exitCode=37;",
	);
	const child = Bun.spawn([proxy, "argument with spaces", "--flag=value"], {
		stdout: "pipe",
		stderr: "pipe",
	});
	const [stdout, stderr] = await Promise.all([
		new Response(child.stdout).text(),
		new Response(child.stderr).text(),
	]);
	expect({
		exitCode: await child.exited,
		stderr,
		response: JSON.parse(stdout),
	}).toEqual({
		exitCode: 37,
		stderr: "",
		response: {
			path: join(result.package!, "bin", "codex.exe"),
			args: ["argument with spaces", "--flag=value"],
		},
	});
	expect(
		await Bun.file(
			join(result.package!, "codex-resources", "codex-command-runner.exe"),
		).exists(),
	).toBe(true);
});

test("real just entrypoint preserves authorities under canonical, copied and symlinked packages", async () => {
	const f = await fixture();
	const tools = join(f.root, "tools");
	await program(
		join(tools, "rustc"),
		'console.log("rustc fixture\\nhost: x86_64-unknown-linux-gnu");',
	);
	const canonical = join(f.root, "canonical skills");
	await mkdir(canonical);
	await cp(skill, join(canonical, "upgrade-codex-patch"), {
		recursive: true,
		filter: (source) => !source.includes("assets/patches"),
	});
	const copied = join(f.root, "copied skills");
	await mkdir(copied);
	await cp(
		join(canonical, "upgrade-codex-patch"),
		join(copied, "upgrade-codex-patch"),
		{ recursive: true },
	);
	const relativeRoot = join(f.root, "relative skills");
	const absoluteRoot = join(f.root, "absolute skills");
	await mkdir(relativeRoot);
	await mkdir(absoluteRoot);
	await symlink(
		relative(relativeRoot, join(canonical, "upgrade-codex-patch")),
		join(relativeRoot, "upgrade-codex-patch"),
		"dir",
	);
	await symlink(
		join(canonical, "upgrade-codex-patch"),
		join(absoluteRoot, "upgrade-codex-patch"),
		"dir",
	);
	const justfile = join(f.repository, "justfile");
	await writeFile(
		justfile,
		"import x'${AGENTIC_SKILLS_REPO}/upgrade-codex-patch/justfile'\nexport CODEX_REPO_ROOT := justfile_directory()\n",
	);
	const unchanged = await readFile(
		join(f.repository, "codex-rs", "Cargo.toml"),
	);
	const rows: any[] = [];
	for (const selected of [canonical, copied, relativeRoot, absoluteRoot]) {
		const child = Bun.spawn(["just", "--justfile", justfile, "i", "--plan"], {
			cwd: f.repository,
			env: {
				...f.ctx.env,
				AGENTIC_SKILLS_REPO: selected,
				CODEX_V8_REPO: f.v8,
				CODEX_V8_BUN: process.execPath,
				PATH: [tools, process.env.PATH].join(delimiter),
			},
			stdout: "pipe",
			stderr: "pipe",
		});
		const [stdout, stderr] = await Promise.all([
			new Response(child.stdout).text(),
			new Response(child.stderr).text(),
		]);
		expect({ exit: await child.exited, stderr }).toEqual({
			exit: 0,
			stderr: "",
		});
		const row = JSON.parse(stdout);
		expect(row.side_effects).toEqual([]);
		const reported = row.skill_root.startsWith("~/")
			? join(homedir(), row.skill_root.slice(2))
			: row.skill_root;
		expect(await realpath(reported)).toBe(
			await realpath(join(selected, "upgrade-codex-patch")),
		);
		delete row.skill_root;
		rows.push(row);
	}
	expect(rows).toEqual([rows[0], rows[0], rows[0], rows[0]]);
	expect(await readFile(join(f.repository, "codex-rs", "Cargo.toml"))).toEqual(
		unchanged,
	);
	expect(await Bun.file(join(f.cargoHome, "bin", "codex")).exists()).toBe(
		false,
	);
});
