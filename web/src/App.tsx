import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from "react";
import {
  getInitialCodexEndpoint,
  getInitialCodexBridgeNonce,
  hasExplicitCodexEndpoint,
  isDefaultCodexEndpoint,
  isGithubPagesRuntime,
  logoutCodex,
  probeCodexBridge,
  readCodexAccount,
  rememberCodexBridgeNonce,
  rememberCodexEndpoint,
  startCodexLogin,
  validateCodexEndpoint,
  type CodexLoginFlow,
} from "./codexAuth";
import { allInstitutionCatalogues, groups, programFromCatalogueOption } from "./data/catalogues";
import { programs, sourcePages } from "./data/programs";
import type { InstitutionCatalogue, InstitutionGroup, MaterialItem, NarrativeOption, Program, ProgramLevel } from "./types";

type CodexOAuthStatus = "unchecked" | "static_blocked" | "needs_sign_in" | "opening_oauth" | "pending_verification" | "connected" | "error";
type CodexOAuthAction = "idle" | "checking_status" | "starting_oauth" | "refreshing_status" | "resetting";
type BridgeHealthStatus = "unknown" | "checking" | "ready" | "blocked";

interface CodexOAuthPanelState {
  status: CodexOAuthStatus;
  action: CodexOAuthAction;
  lastCheckedAt?: string;
  message: string;
  events: string[];
  accountLabel?: string;
  authUrl?: string;
  verificationUrl?: string;
  userCode?: string;
  endpointKind?: string;
  endpointMessage?: string;
}

const baseMaterials: MaterialItem[] = [
  { id: "transcript", name: "Academic transcript", scope: "All post-16 or degree study", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "List transcript evidence in this session before checking it against the academic route." },
  { id: "english", name: "English language test", scope: "IELTS or TOEFL if required", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Add test-result evidence in this session, then check exact component scores on the source page." },
  { id: "statement", name: "Personal statement", scope: "Programme-specific writing", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Needs evidence-backed narrative and programme fit before any draft is treated as ready." },
  { id: "reference", name: "Reference", scope: "Academic referee", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Confirm referee identity and submission route in this session." },
  { id: "passport", name: "Passport or ID", scope: "Identity document", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Add identity-document evidence in this session before marking it ready." },
  { id: "funding", name: "Fee / funding note", scope: "Tuition funding plan", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Add funding evidence in this session if the programme or portal asks for it." },
  { id: "course-code", name: "Course code", scope: "UCAS or direct application", status: "Unresolved", evidence: "Not confirmed in portal", check: "Unresolved", note: "Confirm exact code in the official application route before submission." },
  { id: "extra", name: "Additional documents", scope: "Portfolio, CV, research proposal if required", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Check the selected programme page before deciding whether extra documents are required." },
];

const freshMaterials = () => baseMaterials.map((item) => ({ ...item }));

const narrativeOptions: NarrativeOption[] = [
  {
    id: "research-curiosity",
    title: "Research Curiosity in Genetics",
    body: "A curiosity-driven story that connects gene-expression exposure, independent reading, and lab methods to a commitment to genetic mechanisms.",
    evidence: ["Research project on gene expression", "Independent reading: Watson, Epigenetics; Pierce, Genetics", "Lab skills: PCR and gel electrophoresis"],
    gaps: ["Quantitative analysis example", "Reflection on ethical or societal implications"],
  },
  {
    id: "problem-solving",
    title: "Problem-Solving in Biology",
    body: "A problem-led story about using biological reasoning, lab work, and interdisciplinary learning to answer real questions.",
    evidence: ["Biology coursework project", "Wet-lab practical record", "Data interpretation exercise"],
    gaps: ["Clear programme-specific module link"],
  },
  {
    id: "impact",
    title: "Impact Through Biosciences",
    body: "A motivation-led story about using bioscience responsibly for human or environmental benefit.",
    evidence: ["Volunteering or outreach example", "Coursework on genetics or molecular biology"],
    gaps: ["Concrete research or lab evidence", "Specific Manchester programme fit"],
  },
];

function Logo() {
  return (
    <div className="brand">
      <span className="brand-mark" aria-hidden="true" />
      <span>Soleil Admissions</span>
    </div>
  );
}

function Header({ activeView, setActiveView }: { activeView: string; setActiveView: (view: string) => void }) {
  return (
    <header className="topbar">
      <Logo />
      <nav className="nav-tabs" aria-label="Primary">
        {["Programs", "Materials", "Writing Studio", "Sources", "Codex OAuth"].map((item) => (
          <button className={activeView === item ? "active" : ""} key={item} onClick={() => setActiveView(item)}>
            {item}
          </button>
        ))}
      </nav>
    </header>
  );
}

function FilterRail({
  level,
  setLevel,
  group,
  setGroup,
  catalogueId,
  setCatalogueId,
  catalogues,
  resetFilters,
}: {
  level: ProgramLevel;
  setLevel: (level: ProgramLevel) => void;
  group: InstitutionGroup;
  setGroup: (group: InstitutionGroup) => void;
  catalogueId: string;
  setCatalogueId: (id: string) => void;
  catalogues: InstitutionCatalogue[];
  resetFilters: () => void;
}) {
  const groupCatalogues = catalogues.filter((item) => item.group === group);
  return (
    <aside className="filter-rail">
      <div className="rail-title"><span>Filters</span><button onClick={resetFilters}>Reset all</button></div>
      <section>
        <h3>Institution set</h3>
        <div className="segment stack">
          {groups.map((item) => (
            <button key={item} className={group === item ? "selected" : ""} onClick={() => { setGroup(item); setCatalogueId(catalogues.find((catalogue) => catalogue.group === item)?.id ?? catalogueId); }}>{item}</button>
          ))}
        </div>
      </section>
      <section>
        <h3>Institution</h3>
        <select className="select-input" value={catalogueId} onChange={(event) => setCatalogueId(event.target.value)}>
          {groupCatalogues.map((item) => <option key={item.id} value={item.id}>{item.shortName}</option>)}
        </select>
      </section>
      <section>
        <h3>Degree level</h3>
        <div className="segment">
          {(["Undergraduate", "Postgraduate"] as ProgramLevel[]).map((item) => (
            <button key={item} className={level === item ? "selected" : ""} onClick={() => setLevel(item)}>{item}</button>
          ))}
        </div>
      </section>
      <section>
        <h3>Qualification route</h3>
        {["A-level / IB", "US high school", "Bachelor degree", "Other"].map((item, index) => (
          <label className="check-row" key={item}>
            <input type="checkbox" defaultChecked={index < 2} />
            <span>{item}</span>
          </label>
        ))}
      </section>
      <section>
        <h3>English language</h3>
        {["IELTS Academic", "TOEFL iBT", "PTE Academic"].map((item, index) => (
          <label className="check-row" key={item}>
            <input type="checkbox" defaultChecked={index < 2} />
            <span>{item}</span>
          </label>
        ))}
      </section>
      <section>
        <h3>Budget per year</h3>
        {["Any", "Under GBP 15,000", "GBP 15,000-25,000", "GBP 25,000+"].map((item, index) => (
          <label className="radio-row" key={item}>
            <input type="radio" name="budget" defaultChecked={index === 0} />
            <span>{item}</span>
          </label>
        ))}
      </section>
    </aside>
  );
}

function RequirementChips({ program }: { program: Program }) {
  return (
    <div className="chips">
      {program.hardRequirements.slice(0, 3).map((req) => (
        <span className="chip" key={`${program.id}-${req.label}`}>{req.label}: {req.value}</span>
      ))}
    </div>
  );
}

function ProgramMeta({ program }: { program: Program }) {
  const flags = [
    program.sourceTitle.includes("Closed this cycle") ? "Closed this cycle" : "",
    program.sourceTitle.includes("EPSRC CDT") ? "EPSRC CDT" : "",
  ];
  const meta = Array.from(new Set(
    [program.award, program.mode, ...flags].filter((item) => item && item !== "See official programme page" && item !== "Open in official directory"),
  ));
  return (
    <div className="program-meta">
      {meta.map((item) => <span key={`${program.id}-${item}`}>{item}</span>)}
    </div>
  );
}

function SourceCell({ program }: { program: Program }) {
  const label = program.sourceUrl.includes("postgraduate.study.cam.ac.uk/courses/directory")
    ? "Official directory row"
    : "Official programme page";
  return (
    <span className="code-cell">
      <span>
        <strong>{label}</strong>
        <small>{program.sourceStatus}</small>
      </span>
      <svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6" /></svg>
    </span>
  );
}

function ProgramTable({
  level,
  rows,
  selected,
  setSelected,
  catalogue,
}: {
  level: ProgramLevel;
  rows: Program[];
  selected: Program;
  setSelected: (program: Program) => void;
  catalogue: InstitutionCatalogue;
}) {
  return (
    <main className="program-panel">
      <div className="panel-heading">
        <div>
          <h1>Programme Catalogue Coverage</h1>
          <p>{catalogue.name} / {level}. <a href={(catalogue.sources.find((source) => source.level === level) ?? catalogue.sources[0]).url} target="_blank" rel="noreferrer">Open source</a></p>
        </div>
        <div className="sort-tools">
          <span>{rows.length} programs</span>
        </div>
      </div>
      <div className="program-table" role="table">
        <div className="table-head" role="row">
          <span>Program</span>
          <span>Route</span>
          <span>Duration</span>
          <span>Source</span>
        </div>
        {!rows.length && (
          <div className="empty-state">
            <strong>No programme rows for this level.</strong>
            <span>{catalogue.caveat}</span>
          </div>
        )}
        {rows.map((program, index) => (
          <button className={`program-row ${selected.id === program.id ? "selected" : ""}`} key={`${program.id}-${index}`} onClick={() => setSelected(program)} role="row">
            <span className="program-name-cell">
              <strong>{program.name}</strong>
              <small>{program.institution} / {program.level}</small>
            </span>
            <ProgramMeta program={program} />
            <span className="duration-cell">{program.duration}</span>
            <SourceCell program={program} />
          </button>
        ))}
      </div>
      <div className="table-footer">
        <span>{catalogue.extractionNote}</span>
      </div>
    </main>
  );
}

function Inspector({ program, openChecklist }: { program: Program; openChecklist: () => void }) {
  return (
    <aside className="inspector">
      <div className="inspector-title">
        <div>
          <h2>{program.name}</h2>
          <p>{program.institution ?? "Institution"} / {program.level} / {program.award}</p>
          <a href={program.sourceUrl} target="_blank" rel="noreferrer">View official page</a>
        </div>
      </div>
      <section>
        <h3>Overview</h3>
        <p>{program.summary}</p>
      </section>
      <section>
        <h3>Hard Requirements</h3>
        {program.hardRequirements.map((req) => (
          <div className="info-row" key={req.label}><span>{req.label}</span><strong>{req.value}</strong></div>
        ))}
      </section>
      <section>
        <h3>Fees</h3>
        <div className="info-row"><span>Tuition</span><strong>{program.fees}</strong></div>
        <div className="info-row"><span>Duration</span><strong>{program.duration}</strong></div>
      </section>
      <section>
        <h3>Documents</h3>
        <ul className="plain-list">{program.documents.map((doc) => <li key={doc}>{doc}</li>)}</ul>
      </section>
      <section>
        <h3>Source Status</h3>
        <p className={`status-line ${program.sourceStatus === "Source gap" ? "warn" : "pass"}`}>{program.sourceStatus} / last checked {program.sourceChecked}</p>
      </section>
      <button className="primary-button wide" onClick={openChecklist}>Open Application Checklist</button>
    </aside>
  );
}

function CatalogueInspector({ catalogue }: { catalogue: InstitutionCatalogue }) {
  return (
    <aside className="inspector">
      <div className="inspector-title">
        <div>
          <h2>{catalogue.name}</h2>
          <p>{catalogue.group} / {catalogue.region}</p>
        </div>
      </div>
      <section>
        <h3>Coverage</h3>
        <p>{catalogue.extractionNote}</p>
      </section>
      <section>
        <h3>Official Sources</h3>
        <ul className="plain-list">
          {catalogue.sources.map((source) => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.label}</a></li>)}
        </ul>
      </section>
      <section>
        <h3>Caveat</h3>
        <p>{catalogue.caveat}</p>
      </section>
      <section>
        <h3>Source Status</h3>
        <p className="status-line warn">Catalogue-level source only / last checked {catalogue.checked}</p>
      </section>
    </aside>
  );
}

function MaterialsView({
  program,
  openWriting,
  backToPrograms,
}: {
  program: Program;
  openWriting: () => void;
  backToPrograms: () => void;
}) {
  const [materials, setMaterials] = useState(freshMaterials);
  const complete = materials.filter((item) => item.check === "Pass").length;
  useEffect(() => {
    setMaterials(freshMaterials());
  }, [program.id]);
  const markProvided = (id: string) => {
    setMaterials((items) => items.map((item) => item.id === id ? { ...item, status: "Complete", evidence: "Provided in session", check: "Pass", note: "Marked as provided in this browser session. Verify the content against the official requirement before submission." } : item));
  };
  const markNotRequired = (id: string) => {
    setMaterials((items) => items.map((item) => item.id === id ? { ...item, status: "Not Required", evidence: "Not applicable", check: "N/A", note: "Marked not applicable in this browser session. Keep this only if the official programme page does not request it." } : item));
  };
  const clearMaterial = (id: string) => {
    const original = baseMaterials.find((item) => item.id === id);
    if (!original) return;
    setMaterials((items) => items.map((item) => item.id === id ? { ...original } : item));
  };
  return (
    <section className="workspace split">
      <aside className="context-rail">
        <button className="back-button" onClick={backToPrograms}>Back to Programs</button>
        <h2>{program.name}</h2>
        <p>{program.institution ?? "Institution"} / {program.award} / {program.duration}</p>
        <p className="status-pill">{program.sourceStatus}</p>
        <h3>Hard Requirements Summary</h3>
        <RequirementChips program={program} />
      </aside>
      <main className="checklist-panel">
        <div className="panel-heading compact">
          <h1>Application Checklist</h1>
          <div className="progress"><span style={{ width: `${(complete / materials.length) * 100}%` }} /> </div>
          <p>{complete} of {materials.length} complete</p>
        </div>
        <div className="material-table">
          {materials.map((item, index) => (
            <div className={`material-row ${item.check === "Unresolved" ? "attention" : ""}`} key={item.id}>
              <span className="row-number">{index + 1}</span>
              <div><strong>{item.name}</strong><small>{item.scope}</small></div>
              <span className={`status-dot ${item.check.toLowerCase().replace("/", "-")}`}>{item.check}</span>
              <span className="evidence">{item.evidence}</span>
              <p>{item.note}</p>
              <div className="material-actions">
                {item.id === "statement" && <button className="primary-outline" onClick={openWriting}>Plan writing</button>}
                <button className="ghost-button" onClick={() => markProvided(item.id)}>Mark provided</button>
                <button className="ghost-button" onClick={() => markNotRequired(item.id)}>N/A</button>
                {item.check !== "Unresolved" && <button className="ghost-button" onClick={() => clearMaterial(item.id)}>Clear</button>}
              </div>
            </div>
          ))}
        </div>
        <div className="table-footer">
          <span>Selected programme: {program.name}</span>
        </div>
      </main>
    </section>
  );
}

function WritingView({ program, backToChecklist }: { program: Program; backToChecklist: () => void }) {
  const [selected, setSelected] = useState(narrativeOptions[0]);
  const [resolved, setResolved] = useState<string[]>([]);
  const [approval, setApproval] = useState("");
  const gaps = selected.gaps.filter((gap) => !resolved.includes(gap));
  const approveEnabled = gaps.length === 0;
  return (
    <section className="workspace writing-layout">
      <aside className="context-rail">
        <button className="back-button" onClick={backToChecklist}>Back to Checklist</button>
        <h2>{program.name}</h2>
        <p>{program.institution ?? "Institution"} / {program.level} / {program.duration}</p>
        <h3>Verified Sources</h3>
        <a href={program.sourceUrl} target="_blank" rel="noreferrer">Programme page</a>
        <h3>Writing Brief</h3>
        <p>Personal statement must connect applicant evidence to programme fit. Unsupported claims remain blocked.</p>
      </aside>
      <main className="checklist-panel">
        <div className="writing-steps">
          {["Brief Lock", "Evidence Inventory", "Narrative Options", "Programme Fit Paragraph", "Critical Review", "Draft Gate"].map((step, index) => (
            <span className={index < 2 ? "done" : index === 2 ? "current" : ""} key={step}>{index + 1}. {step}</span>
          ))}
        </div>
        <div className="panel-heading compact">
          <h1>Step 3 of 6 / Narrative Options</h1>
          <p>Select the thesis direction that best reflects real evidence. The structure is blocked until gaps are resolved.</p>
        </div>
        <div className="writing-grid">
          <div className="option-stack">
            <h3>Narrative Options</h3>
            {narrativeOptions.map((optionItem) => (
              <button className={`narrative-option ${selected.id === optionItem.id ? "selected" : ""}`} key={optionItem.id} onClick={() => { setSelected(optionItem); setResolved([]); }}>
                <strong>{optionItem.title}</strong>
                <span>{optionItem.body}</span>
              </button>
            ))}
          </div>
          <div className="evidence-map">
            <h3>Evidence Map</h3>
            {selected.evidence.map((item) => <p className="evidence-pass" key={item}>{item}</p>)}
            {selected.gaps.map((gap) => (
              <button className={`gap-item ${resolved.includes(gap) ? "resolved" : ""}`} key={gap} onClick={() => setResolved((items) => items.includes(gap) ? items.filter((item) => item !== gap) : [...items, gap])}>
                {gap}
              </button>
            ))}
          </div>
        </div>
        <div className="composer">
          <p>{gaps.length ? `${gaps.length} evidence gap${gaps.length > 1 ? "s" : ""} left. Add missing evidence or choose a different narrative.` : "Evidence gaps resolved. Structure approval is available."}</p>
          <textarea placeholder="Tell the Writing Studio what evidence you can add, or choose a different narrative option." />
          <button className="primary-button" disabled={!approveEnabled} onClick={() => setApproval("Structure approved for this browser session.")}>Approve Structure</button>
          {approval && <p className="status-line pass">{approval}</p>}
        </div>
      </main>
    </section>
  );
}

function SourceView({ program, catalogue }: { program: Program; catalogue: InstitutionCatalogue }) {
  return (
    <section className="source-page">
      <div className="panel-heading">
        <div>
          <h1>Source Drawer</h1>
          <p>Every hard requirement in this prototype is tied to an official page or marked for official-page review.</p>
        </div>
      </div>
      <div className="source-grid">
        {catalogue.sources.map((source) => (
          <a className="source-card" key={source.url} href={source.url} target="_blank" rel="noreferrer">
            <strong>{catalogue.shortName}: {source.label}</strong>
            <span>{source.url}</span>
            <small>{source.coverage} / {source.note}</small>
          </a>
        ))}
        {catalogue.id === "manchester" && sourcePages.map((source) => (
          <a className="source-card" key={source.url} href={source.url} target="_blank" rel="noreferrer">
            <strong>{source.label}</strong>
            <span>{source.url}</span>
            <small>Last checked {source.checked}</small>
          </a>
        ))}
        {program.hardRequirements.map((req) => (
          <a className="source-card" key={`${req.label}-${req.value}`} href={req.sourceUrl} target="_blank" rel="noreferrer">
            <strong>{req.category}: {req.label}</strong>
            <span>{req.value}</span>
            <small>{req.sourceTitle}</small>
          </a>
        ))}
      </div>
    </section>
  );
}

function CodexOAuthView({
  state,
  setState,
}: {
  state: CodexOAuthPanelState;
  setState: Dispatch<SetStateAction<CodexOAuthPanelState>>;
}) {
  const [endpoint, setEndpoint] = useState(getInitialCodexEndpoint);
  const [bridgeNonce, setBridgeNonce] = useState(getInitialCodexBridgeNonce);
  const [bridgeHealth, setBridgeHealth] = useState<{ status: BridgeHealthStatus; message: string; nonceRequired?: boolean }>({
    status: "unknown",
    message: "Bridge health has not been checked.",
  });
  const validation = validateCodexEndpoint(endpoint);
  const busy = state.action !== "idle" && state.action !== "resetting";
  const now = () => new Date().toLocaleString();
  const defaultStaticBridgeBlocked = validation.kind === "bridge-http" && isGithubPagesRuntime() && isDefaultCodexEndpoint(endpoint) && !hasExplicitCodexEndpoint() && bridgeHealth.status !== "ready";
  const nonceBlocked = validation.kind === "bridge-http" && bridgeHealth.nonceRequired === true && !bridgeNonce.trim();
  const oauthControlsDisabled = !validation.valid || busy || defaultStaticBridgeBlocked || nonceBlocked;

  useEffect(() => {
    setBridgeHealth({ status: "unknown", message: "Bridge health has not been checked." });
  }, [endpoint]);

  const append = (
    message: string,
    status: CodexOAuthStatus,
    action: CodexOAuthAction = "idle",
    extra: Partial<CodexOAuthPanelState> = {},
  ) => {
    const timestamp = now();
    setState((previous) => ({
      ...previous,
      ...extra,
      status,
      action,
      lastCheckedAt: timestamp,
      message,
      endpointKind: validation.kind,
      endpointMessage: validation.message,
      events: [`${timestamp} / ${message}`, ...previous.events].slice(0, 8),
    }));
  };

  const run = async (action: CodexOAuthAction, task: () => Promise<void>) => {
    append(`Running ${action.replace("_", " ")}.`, state.status, action);
    try {
      rememberCodexEndpoint(endpoint);
      rememberCodexBridgeNonce(bridgeNonce);
      await task();
    } catch (error) {
      append(error instanceof Error ? error.message : "Codex OAuth action failed.", "error", "idle");
    }
  };

  const checkBridgeHealth = async () => {
    await run("checking_status", async () => {
      setBridgeHealth({ status: "checking", message: "Checking local bridge health." });
      const health = await probeCodexBridge(endpoint, bridgeNonce);
      const message = health.nonceRequired && !bridgeNonce.trim()
        ? "Bridge is reachable but requires the nonce printed by scripts/codex_oauth_bridge.mjs."
        : "Bridge health check passed.";
      setBridgeHealth({ status: "ready", message, nonceRequired: health.nonceRequired });
      append(message, health.nonceRequired && !bridgeNonce.trim() ? "static_blocked" : "unchecked", "idle");
    });
  };

  const checkStatus = async (refreshToken: boolean) => {
    await run(refreshToken ? "refreshing_status" : "checking_status", async () => {
      const account = await readCodexAccount(endpoint, refreshToken, bridgeNonce);
      const accountLabel = account.account
        ? `${account.account.type}${account.account.email ? ` / ${account.account.email}` : ""}${account.account.planType ? ` / ${account.account.planType}` : ""}`
        : undefined;
      append(account.connected ? "Codex OAuth account is connected." : "No Codex OAuth account is connected.", account.connected ? "connected" : "needs_sign_in", "idle", {
        accountLabel,
        authUrl: undefined,
        verificationUrl: undefined,
        userCode: undefined,
      });
    });
  };

  const startLogin = async (flow: CodexLoginFlow) => {
    const popup = flow === "browser" ? window.open("about:blank", "_blank") : null;
    let popupNavigated = false;
    if (popup) {
      popup.opener = null;
    }

    await run("starting_oauth", async () => {
      const login = await startCodexLogin(endpoint, flow, bridgeNonce);
      if (login.type === "chatgpt") {
        if (popup) {
          popup.location.href = login.authUrl;
          popupNavigated = true;
        } else {
          window.open(login.authUrl, "_blank", "noopener,noreferrer");
        }
        append("Codex browser OAuth opened. Complete sign-in, then refresh status.", "opening_oauth", "idle", {
          authUrl: login.authUrl,
          verificationUrl: undefined,
          userCode: undefined,
        });
        return;
      }

      if (login.type === "chatgptDeviceCode") {
        popup?.close();
        append("Codex device-code OAuth started. Enter the code, then refresh status.", "pending_verification", "idle", {
          authUrl: undefined,
          verificationUrl: login.verificationUrl,
          userCode: login.userCode,
        });
        return;
      }

      if (login.authUrl) {
        if (popup) {
          popup.location.href = login.authUrl;
          popupNavigated = true;
        } else {
          window.open(login.authUrl, "_blank", "noopener,noreferrer");
        }
      } else {
        popup?.close();
      }
      append(login.message ?? "Bridge started Codex OAuth. Complete sign-in, then refresh status.", "pending_verification", "idle", {
        authUrl: login.authUrl,
        verificationUrl: login.verificationUrl,
        userCode: login.userCode,
      });
    });
    if (popup && !popupNavigated) {
      popup.close();
    }
  };

  const disconnect = async () => {
    await run("resetting", async () => {
      await logoutCodex(endpoint, bridgeNonce);
      append("Codex OAuth account was logged out through the configured endpoint.", "needs_sign_in", "idle", {
        accountLabel: undefined,
        authUrl: undefined,
        verificationUrl: undefined,
        userCode: undefined,
      });
    });
  };

  const resetPanel = () => {
    setBridgeHealth({ status: "unknown", message: "Bridge health has not been checked." });
    setState({
      status: "unchecked",
      action: "resetting",
      message: "Panel reset. No token data was read or stored.",
      events: [],
      endpointKind: validation.kind,
      endpointMessage: validation.message,
    });
  };

  return (
    <section className="source-page">
      <div className="panel-heading">
        <div>
          <h1>Codex OAuth Runtime</h1>
          <p>Hermes-style integration: Codex owns OAuth; this website calls Codex app-server or a trusted bridge and never stores bearer tokens.</p>
        </div>
        <span className={`oauth-state ${state.status}`}>{state.status.replace("_", " ")}</span>
      </div>
      <div className="oauth-grid">
        <div className="oauth-panel oauth-panel-wide">
          <h3>Endpoint</h3>
          <label className="field-label" htmlFor="codex-endpoint">Codex HTTP bridge or app-server WebSocket</label>
          <div className="endpoint-row">
            <input
              id="codex-endpoint"
              className="text-input"
              value={endpoint}
              onChange={(event) => setEndpoint(event.target.value)}
              spellCheck={false}
            />
            <button className="ghost-button" onClick={() => { rememberCodexEndpoint(endpoint); rememberCodexBridgeNonce(bridgeNonce); append("Endpoint saved locally.", validation.valid ? "unchecked" : "error"); }}>Save</button>
          </div>
          <label className="field-label" htmlFor="codex-bridge-nonce">Local bridge nonce</label>
          <input
            id="codex-bridge-nonce"
            className="text-input"
            value={bridgeNonce}
            onChange={(event) => setBridgeNonce(event.target.value)}
            placeholder="Paste codex_bridge_nonce printed by the bridge"
            spellCheck={false}
          />
          <p className={validation.valid ? "status-line pass" : "status-line error"}>{validation.message}</p>
          <p className={bridgeHealth.status === "ready" && !nonceBlocked ? "status-line pass" : "status-line error"}>{defaultStaticBridgeBlocked ? "Static Pages default bridge is blocked until /health succeeds." : bridgeHealth.message}</p>
          <pre>{`node scripts/codex_oauth_bridge.mjs --port 8787\n\n# Then open with the printed nonce:\n?codex_bridge=http://127.0.0.1:8787&codex_bridge_nonce=PASTE_PRINTED_NONCE\n\n# Origin-free clients can also use:\ncodex app-server --listen ws://127.0.0.1:4500`}</pre>
        </div>
        <div className="oauth-panel">
          <h3>OAuth Controls</h3>
          <p>{state.message}</p>
          <div className="button-row">
            <button className="primary-button" disabled={!validation.valid || busy || validation.kind !== "bridge-http"} onClick={checkBridgeHealth}>Probe Bridge</button>
            <button className="primary-button" disabled={oauthControlsDisabled} onClick={() => checkStatus(false)}>Check Status</button>
            <button className="ghost-button" disabled={oauthControlsDisabled} onClick={() => startLogin("browser")}>Browser OAuth</button>
            <button className="ghost-button" disabled={oauthControlsDisabled} onClick={() => startLogin("device")}>Device Code</button>
            <button className="ghost-button" disabled={oauthControlsDisabled} onClick={() => checkStatus(true)}>Refresh Auth</button>
            <button className="ghost-button" disabled={oauthControlsDisabled} onClick={disconnect}>Logout</button>
            <button className="ghost-button" onClick={resetPanel}>Reset Panel</button>
          </div>
        </div>
        <div className="oauth-panel">
          <h3>Account Snapshot</h3>
          <div className="info-row"><span>Runtime</span><strong>{validation.kind ?? "Unconfigured"}</strong></div>
          <div className="info-row"><span>Last check</span><strong>{state.lastCheckedAt ?? "Not checked"}</strong></div>
          <div className="info-row"><span>Account</span><strong>{state.accountLabel ?? "Not connected"}</strong></div>
          {state.authUrl && <a className="source-card compact-link" href={state.authUrl} target="_blank" rel="noreferrer">Open browser OAuth URL</a>}
          {state.verificationUrl && <a className="source-card compact-link" href={state.verificationUrl} target="_blank" rel="noreferrer">Open device verification URL</a>}
          {state.userCode && <p className="device-code">{state.userCode}</p>}
        </div>
        <div className="oauth-panel">
          <h3>Bridge Contract</h3>
          <pre>{`GET /codex/status\nPOST /codex/start-oauth { "flow": "browser" | "device" }\nPOST /codex/refresh\nPOST /codex/logout`}</pre>
          <p>Public Pages deployments must call a localhost or HTTPS bridge when they cannot reach Codex app-server directly.</p>
        </div>
        <div className="oauth-panel">
          <h3>Event Log</h3>
          <div className="event-log">
            {(state.events.length ? state.events : ["No status action yet."]).map((item) => <span key={item}>{item}</span>)}
          </div>
        </div>
      </div>
    </section>
  );
}

export default function App() {
  const [activeView, setActiveView] = useState("Programs");
  const [level, setLevel] = useState<ProgramLevel>("Undergraduate");
  const [group, setGroup] = useState<InstitutionGroup>("UK Core");
  const [catalogueId, setCatalogueId] = useState("cambridge");
  const [selected, setSelected] = useState<Program>(programs.find((program) => program.id === "bsc-genetics") ?? programs[0]);
  const [oauthState, setOauthState] = useState<CodexOAuthPanelState>({
    status: "unchecked",
    action: "idle",
    message: "No status check has run. Use explicit controls before connecting a local Codex bridge.",
    events: [],
  });
  const selectedCatalogue = allInstitutionCatalogues.find((catalogue) => catalogue.id === catalogueId) ?? allInstitutionCatalogues[0];
  const rows = useMemo(() => {
    const catalogueOptions = selectedCatalogue.programs ?? selectedCatalogue.examples;
    const catalogueRows = catalogueOptions
      .filter((item) => item.level === level)
      .map((item) => programFromCatalogueOption(selectedCatalogue, item));
    const detailRows = selectedCatalogue.id === "manchester"
      ? programs.filter((program) => program.level === level)
      : [];
    return [...detailRows, ...catalogueRows];
  }, [level, selectedCatalogue]);
  const activeProgram = rows.find((row) => row.id === selected.id) ?? rows[0] ?? selected;
  useEffect(() => {
    if (rows.length && !rows.some((row) => row.id === selected.id)) {
      setSelected(rows[0]);
    }
  }, [rows, selected.id]);
  const openChecklist = () => setActiveView("Materials");
  const openWriting = () => setActiveView("Writing Studio");
  const resetFilters = () => {
    const defaultCatalogue = allInstitutionCatalogues.find((catalogue) => catalogue.group === "UK Core");
    setGroup("UK Core");
    setLevel("Undergraduate");
    setCatalogueId(defaultCatalogue?.id ?? allInstitutionCatalogues[0].id);
  };

  return (
    <div className="app-shell">
      <Header activeView={activeView} setActiveView={setActiveView} />
      {activeView === "Programs" && (
        <div className="program-layout">
          <FilterRail level={level} setLevel={setLevel} group={group} setGroup={setGroup} catalogueId={catalogueId} setCatalogueId={setCatalogueId} catalogues={allInstitutionCatalogues} resetFilters={resetFilters} />
          <ProgramTable level={level} rows={rows} selected={activeProgram} setSelected={setSelected} catalogue={selectedCatalogue} />
          {rows.length ? <Inspector program={activeProgram} openChecklist={openChecklist} /> : <CatalogueInspector catalogue={selectedCatalogue} />}
        </div>
      )}
      {activeView === "Materials" && <MaterialsView program={activeProgram} openWriting={openWriting} backToPrograms={() => setActiveView("Programs")} />}
      {activeView === "Writing Studio" && <WritingView program={activeProgram} backToChecklist={() => setActiveView("Materials")} />}
      {activeView === "Sources" && <SourceView program={activeProgram} catalogue={selectedCatalogue} />}
      {activeView === "Codex OAuth" && <CodexOAuthView state={oauthState} setState={setOauthState} />}
    </div>
  );
}
