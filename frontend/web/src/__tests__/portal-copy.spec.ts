import { readFileSync, readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function collectVueSources(directory: string): string[] {
  return readdirSync(directory).flatMap((entry) => {
    const path = resolve(directory, entry);
    return statSync(path).isDirectory()
      ? collectVueSources(path)
      : path.endsWith(".vue")
        ? [path]
        : [];
  });
}

describe("public portal copy", () => {
  it("does not expose prototype or upstream implementation labels", () => {
    const portalDirectory = resolve(__dirname, "../views/portal");
    const sources = collectVueSources(portalDirectory).map((path) => readFileSync(path, "utf8"));
    const portalStyles = readFileSync(resolve(__dirname, "../styles/portal.scss"), "utf8");

    expect([...sources, portalStyles].join("\n")).not.toMatch(
      /MinerU|DEMO|Demo|\u6f14示数据|\u6f14示原型|portal-demo-badge/,
    );
  });
});
