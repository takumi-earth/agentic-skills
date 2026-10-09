import { lstat, readFile, readdir, realpath } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";

const expand = (value: string) => resolve(value.startsWith("~/") ? join(homedir(), value.slice(2)) : value);

export async function fileDigest(path: string) {
	const hash = new Bun.CryptoHasher("sha256");
	for await (const chunk of Bun.file(path).stream()) hash.update(chunk);
	return hash.digest("hex");
}

async function repositoryDigest(repository: string, env: Record<string, string | undefined>) {
	const git = async (args: string[]) => {
		const child = Bun.spawn(["git", "-C", repository, ...args], { env, stdout: "pipe", stderr: "pipe" });
		const [output] = await Promise.all([new Response(child.stdout).arrayBuffer(), new Response(child.stderr).text()]);
		return await child.exited === 0 ? new Uint8Array(output) : undefined;
	};
	const top = await git(["rev-parse", "--show-toplevel"]);
	if (!top || await realpath(new TextDecoder().decode(top).trim()) !== await realpath(repository)) return undefined;
	const head = await git(["rev-parse", "HEAD"]);
	const diff = await git(["diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD"]);
	const others = await git(["ls-files", "--others", "--exclude-standard", "-z"]);
	if (!head || !diff || !others) return undefined;
	const hash = new Bun.CryptoHasher("sha256").update(head).update(diff);
	for (const name of new TextDecoder().decode(others).split("\0").filter(Boolean).sort()) {
		const path = join(repository, name);
		hash.update(name + "\0");
		const info = await lstat(path);
		if (info.isFile() || info.isSymbolicLink()) hash.update(await fileDigest(path));
	}
	return hash.digest("hex");
}

export async function sourceIdentity(repository: string, launcher: string, compiler: string, env: Record<string, string | undefined>) {
	const sha256 = await repositoryDigest(repository, env);
	if (!sha256) return undefined;
	const launcherRepository = dirname(dirname(launcher));
	const launcherSource = await repositoryDigest(launcherRepository, env);
	return { repository: await realpath(repository), sha256,
		launcher_source: launcherSource || await fileDigest(launcher), compiler, rustflags: env.RUSTFLAGS || "", encoded_rustflags: env.CARGO_ENCODED_RUSTFLAGS || "" };
}

export async function reusablePackage(root: string, identity: Awaited<ReturnType<typeof sourceIdentity>>, target: string, version: string) {
	if (!identity) return undefined;
	let names: string[];
	try { names = await readdir(root); } catch (error) {
		if ((error as NodeJS.ErrnoException).code === "ENOENT") return undefined;
		throw error;
	}
	for (const name of names.filter(name => name.endsWith(".json")).sort().reverse()) {
		const record = JSON.parse(await readFile(join(root, name), "utf8"));
		if (record.status !== "prepared" || record.target !== target || record.version !== version || !record.source || !record.artifacts) continue;
		const recorded = { ...record.source, repository: expand(record.source.repository) };
		if (!Object.entries(identity).every(([key, value]) => recorded[key] === value)) continue;
		const packageDir = expand(record.package);
		const releases = resolve(root, "..", "releases");
		if (!packageDir.startsWith(releases + (process.platform === "win32" ? "\\" : "/"))) continue;
		const extension = target.includes("windows") ? ".exe" : "";
		const expected = ["codex", "codex-code-mode-host", "logs_client"].map(name => `bin/${name}${extension}`);
		if (target.includes("linux")) expected.push("codex-resources/bwrap");
		if (!expected.every(path => record.artifacts.some((item: { path: string }) => item.path === path))) continue;
		let matches = true;
		for (const artifact of record.artifacts.filter((item: { path: string }) => expected.includes(item.path))) {
			try {
				if (await fileDigest(join(packageDir, artifact.path)) !== artifact.sha256) matches = false;
			} catch (error) {
				if ((error as NodeJS.ErrnoException).code === "ENOENT") matches = false;
				else throw error;
			}
		}
		if (matches && record.artifacts.length >= 3) return packageDir;
	}
	return undefined;
}
