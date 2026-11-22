// Entry point for the news-image-20261122 make.fun entry.
//
// The front page itself is drawn by render_image.py (Python + PIL) and the
// rendered entry.png ships in this repository. This program's job is only
// to make sure /output/entry.png holds that image:
//
//   * if a rendered entry.png already sits beside this file, copy it;
//   * otherwise run the renderer once, writing straight to the output.
//
// Everything is local and deterministic: no network, no clock, no random.

import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const botDir: string =
  process.env.MAKEFUN_BOT_DIR ?? dirname(fileURLToPath(import.meta.url));
const outDir: string = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

mkdirSync(outDir, { recursive: true });

const shipped: string = join(botDir, "entry.png");
const dest: string = join(outDir, "entry.png");

if (existsSync(shipped)) {
  copyFileSync(shipped, dest);
} else {
  execFileSync("python3", [join(botDir, "render_image.py"), dest], {
    stdio: "inherit",
  });
}
