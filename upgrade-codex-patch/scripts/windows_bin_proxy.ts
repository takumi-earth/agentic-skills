import { readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { basename, dirname, join } from "node:path";

// A native proxy avoids Windows symlink privileges. The real executable stays
// inside its complete package, where InstallContext can discover its resources.
try {
	const metadata = JSON.parse(
		await readFile(
			join(dirname(process.execPath), ".codex-source-package.json"),
			"utf8",
		),
	) as { package: string };
	const root = metadata.package.startsWith("~/")
		? join(homedir(), metadata.package.slice(2))
		: metadata.package;
	const program = join(root, "bin", basename(process.execPath));
	const child = Bun.spawn([program, ...process.argv.slice(2)], {
		stdin: "inherit",
		stdout: "inherit",
		stderr: "inherit",
	});
	process.exitCode = await child.exited;
} catch (error) {
	console.error(
		`codex source package: ${error instanceof Error ? error.message : error}`,
	);
	process.exitCode = 1;
}
