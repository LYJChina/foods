import { describe, expect, it } from "vitest";

import { scoreDiagnosis } from "@/views/portal/diagnosis/scoring";

describe("diagnosis scoring", () => {
  it.each([
    [{ digital_foundation: 0, data_readiness: 0, ai_experience: 0, governance_readiness: 0, export_need: 0 }, 0, "start"],
    [{ digital_foundation: 1, data_readiness: 1, ai_experience: 1, governance_readiness: 1, export_need: 1 }, 5, "prepare"],
    [{ digital_foundation: 2, data_readiness: 2, ai_experience: 2, governance_readiness: 2, export_need: 2 }, 10, "advance"],
  ] as const)("maps five answers to the expected maturity band", (answers, score, maturity) => {
    const result = scoreDiagnosis(answers);

    expect(result.score).toBe(score);
    expect(result.maturity).toBe(maturity);
    expect(Object.keys(result.recommendations)).toEqual([
      "public_platform",
      "light_poc",
      "enterprise_project",
    ]);
    expect(result.is_demo).toBe(true);
  });
});
