#!/usr/bin/env -S rote play run
/**
 * Clone Trap
 *
 * Find hidden local dependencies and assumptions that may prevent a repository
 * from working after a clean clone. The Play reads the working tree only and
 * presents evidence. It does not claim the clone will fail or succeed.
 *
 * Safety: reads Git metadata and repository files only. Does not modify the
 * target repository, create commits, run repository code, install
 * dependencies, make network calls, or push to remotes.
 *
 * @rote-frontmatter
 * ---
 * name: clone-trap
 * source: https://github.com/maannaan/clone-trap
 * description: Find hidden local dependencies and assumptions that prevent a repository from working on another machine. Clone Trap compares what a repository claims you need with what it appears to require, and returns evidence-backed portability findings for a coding agent or reviewer. It does not run install, Docker, or application commands.
 * metadata:
 *   rote_version: 0.80.0
 *   version: 0.1.0
 *   status: released
 *   kind: atomic
 *   flow_type: sequential
 *   execution_model: steps_with_presentation
 *   format: typescript
 *   requires_endpoints: []
 *   requires_sessions: false
 *   contract:
 *     atomic: true
 *     input:
 *       type: none
 *     output:
 *       format: json
 *       destination: stdout
 *     composable: true
 *   discoverability:
 *     tags:
 *     - git
 *     - developer-tools
 *     - repository-analysis
 *     - onboarding
 *     - software-engineering
 *     - effect-read-only
 * tags:
 * - git
 * - developer-tools
 * - repository-analysis
 * - onboarding
 * - software-engineering
 * - effect-read-only
 * parameters:
 * - name: repo_path
 *   param_type: string
 *   required: true
 *   description: Absolute path to the Git repository to analyze.
 * - name: max_findings
 *   param_type: integer
 *   required: false
 *   default: 20
 *   description: Maximum findings to display after ranking.
 * steps:
 *   analyze:
 *     type: process.exec
 *     timeout_ms: 120000
 *     argv:
 *     - python3
 *     - '@resource{run_clone_trap.py}'
 *     - --repo
 *     - $repo_path
 *     - --max-findings
 *     - $max_findings
 * presentation_fixtures:
 *   analyze: resources/presentation-fixtures/analyze/fixture.yaml
 * ---
 */

const presentationSdk = await import("__ROTE_PRESENTATION_SDK__").catch((cause) => {
  throw new Error(
    "This is a rote steps presentation program. Run it with `rote play run play/main.ts`.",
    { cause },
  );
});

const { FlowOutput, isProcessExecBody, loadPresentationContext, stepName } =
  presentationSdk;

const out = new FlowOutput();
const ctx = await loadPresentationContext();

type Evidence = {
  source?: string;
  path?: string;
  detail?: string;
};

type Finding = {
  id?: string;
  category?: string;
  verdict?: string;
  severity?: string;
  confidence?: number;
  title?: string;
  evidence?: Evidence[];
  why_it_matters?: string;
  verification?: string;
  remediation?: string;
  clone_stage?: string;
};

type EngineReport = {
  schema_version?: number;
  repository?: string;
  readiness?: string;
  readiness_reason?: string;
  summary?: Record<string, number>;
  documentation_drift?: {
    documented_setup?: string[];
    undocumented_requirements?: string[];
    documented_but_unused?: string[];
  };
  clone_path?: Array<{
    stage?: string;
    documented?: boolean;
    finding_ids?: string[];
  }>;
  bootstrap_actions?: Array<{
    action?: string;
    requirement?: string;
    confidence?: number;
  }>;
  findings?: Finding[];
  truncated?: boolean;
};

const READINESS_LABELS: Record<string, string> = {
  ready: "READY",
  mostly_portable: "MOSTLY PORTABLE",
  hidden_assumptions: "HAS HIDDEN ASSUMPTIONS",
  high_risk: "HIGH RISK TO CLONE",
};

const FOOTER =
  "Portability evidence only — not a guarantee the clone will fail or succeed.";

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function formatConfidence(value: number): string {
  if (value >= 0.85) return "Very high";
  if (value >= 0.7) return "High";
  if (value >= 0.55) return "Moderate";
  return "Limited";
}

function emitFailure(message: string, extra?: Record<string, unknown>): void {
  out.human(
    [
      "Clone Trap",
      "",
      "Analysis could not finish.",
      message,
      "",
      FOOTER,
    ].join("\n"),
  );
  out.summary(`Clone Trap could not analyze the repository: ${message}`);
  out.result({
    ok: false,
    error: message,
    ...(extra ?? {}),
  });
}

function present(): void {
  const analyzeStep = ctx.step(stepName("analyze"));
  const outcome = analyzeStep.outcome;
  if (outcome.status === "blocked") {
    emitFailure("Analyze was blocked by an upstream step and did not run.");
    return;
  }
  if (outcome.status === "skipped") {
    emitFailure("Analyze did not run (skipped).");
    return;
  }
  if (outcome.status === "failed") {
    emitFailure(`Analyze failed: ${outcome.output.message}`);
    return;
  }

  const analyze = outcome.output;
  if (!isProcessExecBody(analyze.body)) {
    emitFailure("The analyze step did not record a process.exec observation.");
    return;
  }

  const exit = analyze.body.status.exit;
  if (exit.kind !== "code") {
    emitFailure("The analyze process did not exit with a status code.");
    return;
  }
  if (exit.code !== 0) {
    const stderr = analyze.body.stderr?.text?.trim() || "no stderr captured";
    emitFailure(stderr, { exit_code: exit.code });
    return;
  }

  const stdout = analyze.body.stdout?.text;
  const stdoutTruncated = analyze.body.stdout?.truncated === true;
  if (typeof stdout !== "string" || !stdout.trim()) {
    emitFailure("The analyze step captured no JSON stdout.");
    return;
  }
  if (stdoutTruncated) {
    emitFailure(
      "Analyze stdout was truncated; the report is partial and was not scored.",
      { truncated: true },
    );
    return;
  }

  let report: EngineReport;
  try {
    const parsed = JSON.parse(stdout) as unknown;
    if (!asRecord(parsed)) {
      throw new Error("stdout was not a JSON object");
    }
    report = parsed as EngineReport;
  } catch (error) {
    emitFailure(
      `Analyze output was not valid JSON: ${error instanceof Error ? error.message : String(error)}`,
    );
    return;
  }

  const findings = Array.isArray(report.findings) ? report.findings : [];
  const drift = report.documentation_drift ?? {};
  const bootstrap = Array.isArray(report.bootstrap_actions) ? report.bootstrap_actions : [];
  const displayedRepo = String(report.repository ?? ctx.params.repo_path ?? "provided path");
  const readiness = String(report.readiness ?? "ready");

  const lines: string[] = [
    "Clone Trap",
    "If a clean machine clones this repository, what hidden assumptions could prevent it from working?",
    "",
    `Repository: ${displayedRepo}`,
    "",
    `Readiness: ${READINESS_LABELS[readiness] ?? readiness.toUpperCase()}`,
    String(report.readiness_reason ?? ""),
    "",
    "Documentation drift",
  ];

  const setup = Array.isArray(drift.documented_setup) ? drift.documented_setup : [];
  if (setup.length) {
    lines.push("  Documented setup:");
    for (const command of setup) {
      lines.push(`    ${command}`);
    }
  } else {
    lines.push("  No setup commands were extracted from documentation.");
  }
  const undocumented = Array.isArray(drift.undocumented_requirements)
    ? drift.undocumented_requirements
    : [];
  if (undocumented.length) {
    lines.push("  Appears required but not documented:");
    for (const item of undocumented) {
      lines.push(`    ${item}`);
    }
  } else {
    lines.push("  No undocumented requirements were confirmed.");
  }

  const groups: Record<string, Finding[]> = {
    confirmed_trap: [],
    likely_trap: [],
    environment_assumption: [],
    informational: [],
  };
  for (const finding of findings) {
    const key = String(finding.verdict ?? "");
    if (groups[key]) {
      groups[key].push(finding);
    }
  }

  const headings: Array<[string, string]> = [
    ["confirmed_trap", "Confirmed traps"],
    ["likely_trap", "Likely traps"],
    ["environment_assumption", "Environment assumptions"],
    ["informational", "Informational findings"],
  ];
  for (const [key, heading] of headings) {
    const items = groups[key];
    if (!items.length) continue;
    lines.push("", heading);
    for (const finding of items) {
      lines.push("");
      lines.push(String(finding.title ?? "Finding"));
      const confidence = typeof finding.confidence === "number"
        ? formatConfidence(finding.confidence)
        : "unknown";
      lines.push(
        `  ${finding.verdict ?? "unknown"} · ${finding.severity ?? "unknown"} · confidence ${confidence}`,
      );
      for (const evidence of (finding.evidence ?? []).slice(0, 4)) {
        const location = evidence.path ? `${evidence.path}: ` : "";
        lines.push(`  ${location}${evidence.detail ?? ""}`);
      }
      if (finding.why_it_matters) {
        lines.push(`  Why this matters: ${finding.why_it_matters}`);
      }
    }
  }

  if (bootstrap.length) {
    lines.push("", "Suggested setup actions");
    for (const action of bootstrap) {
      const confidence = typeof action.confidence === "number"
        ? action.confidence.toFixed(2)
        : "?";
      lines.push(`  ${action.action}: ${action.requirement} (confidence ${confidence})`);
    }
  }

  if (!findings.length) {
    lines.push(
      "",
      "No high-confidence portability gaps were found.",
      "This is evidence from the working tree, not a safety guarantee.",
    );
  }

  if (report.truncated) {
    lines.push("", "Output was capped; more candidates were scored than shown.");
  }

  lines.push("", FOOTER);
  out.human(lines.join("\n"));

  const confirmed = Number(report.summary?.confirmed_traps ?? groups.confirmed_trap.length);
  const likely = Number(report.summary?.likely_traps ?? groups.likely_trap.length);
  out.summary(
    `${READINESS_LABELS[readiness] ?? readiness}: ${confirmed} confirmed trap(s), ${likely} likely trap(s).`,
  );
  out.result({
    ok: true,
    repo_path: ctx.params.repo_path,
    readiness,
    readiness_reason: report.readiness_reason,
    summary: report.summary ?? {},
    documentation_drift: drift,
    bootstrap_actions: bootstrap,
    findings,
  });
}

present();
