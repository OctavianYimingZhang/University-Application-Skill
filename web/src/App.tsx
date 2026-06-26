import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from "react";
import {
  getInitialCodexEndpoint,
  logoutCodex,
  readCodexAccount,
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
  { id: "transcript", name: "Academic transcript", scope: "All post-16 or degree study", status: "Complete", evidence: "Transcript.pdf", check: "Pass", note: "Must match academic requirement route." },
  { id: "english", name: "English language test", scope: "IELTS or TOEFL if required", status: "Complete", evidence: "IELTS_Report.pdf", check: "Pass", note: "Check exact component scores on source page." },
  { id: "statement", name: "Personal statement", scope: "Programme-specific writing", status: "In Progress", evidence: "PS_Draft_v1.md", check: "Unresolved", note: "Needs evidence-backed narrative and programme fit." },
  { id: "reference", name: "Reference", scope: "Academic referee", status: "Complete", evidence: "Reference_Letter.pdf", check: "Pass", note: "Referee identity and submission route must match portal." },
  { id: "passport", name: "Passport or ID", scope: "Identity document", status: "Complete", evidence: "Passport.pdf", check: "Pass", note: "Valid ID for application account." },
  { id: "funding", name: "Fee / funding note", scope: "Tuition funding plan", status: "Complete", evidence: "Funding_Plan.pdf", check: "Pass", note: "Shows ability to pay tuition if requested." },
  { id: "course-code", name: "Course code", scope: "UCAS or direct application", status: "Complete", evidence: "Selected in case", check: "Pass", note: "Confirm exact code before submission." },
  { id: "extra", name: "Additional documents", scope: "Portfolio, CV, research proposal if required", status: "Not Required", evidence: "-", check: "N/A", note: "No extra document requirement in the current seed." },
];

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
      <div className="topbar-actions">
        <button className="icon-button" aria-label="Notifications">
          <svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" /><path d="M10 21h4" /></svg>
        </button>
        <button className="primary-button">Start Case</button>
      </div>
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
}: {
  level: ProgramLevel;
  setLevel: (level: ProgramLevel) => void;
  group: InstitutionGroup;
  setGroup: (group: InstitutionGroup) => void;
  catalogueId: string;
  setCatalogueId: (id: string) => void;
  catalogues: InstitutionCatalogue[];
}) {
  const groupCatalogues = catalogues.filter((item) => item.group === group);
  return (
    <aside className="filter-rail">
      <div className="rail-title"><span>Filters</span><button>Reset all</button></div>
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
      <button className="ghost-button wide">More filters</button>
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

function ProgramTable({
  level,
  rows,
  selected,
  setSelected,
  openChecklist,
  catalogue,
}: {
  level: ProgramLevel;
  rows: Program[];
  selected: Program;
  setSelected: (program: Program) => void;
  openChecklist: () => void;
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
          <button className="icon-button active" aria-label="Table view">
            <svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16" /></svg>
          </button>
        </div>
      </div>
      <div className="program-table" role="table">
        <div className="table-head" role="row">
          <span>Program</span>
          <span>Requirements (typical minimum)</span>
          <span>Duration</span>
          <span>Fees</span>
          <span>Code</span>
        </div>
        {!rows.length && (
          <div className="empty-state">
            <strong>No programme rows for this level.</strong>
            <span>{catalogue.caveat}</span>
          </div>
        )}
        {rows.map((program) => (
          <button className={`program-row ${selected.id === program.id ? "selected" : ""}`} key={program.id} onClick={() => setSelected(program)} role="row">
            <span>
              <strong>{program.name}</strong>
              <small>{program.level}</small>
            </span>
            <RequirementChips program={program} />
            <span>{program.duration}</span>
            <span>{program.fees}</span>
            <span className="code-cell">{program.code}<svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6" /></svg></span>
          </button>
        ))}
      </div>
      <div className="table-footer">
        <span>{catalogue.extractionNote}</span>
        <button className="primary-button" onClick={openChecklist} disabled={!rows.length}>Open Application Checklist</button>
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
        <button className="icon-button" aria-label="Bookmark programme">
          <svg viewBox="0 0 24 24"><path d="M6 3h12v18l-6-4-6 4z" /></svg>
        </button>
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
      <button className="ghost-button wide">Add to Case</button>
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

function MaterialsView({ program, openWriting }: { program: Program; openWriting: () => void }) {
  const [materials, setMaterials] = useState(baseMaterials);
  const complete = materials.filter((item) => item.check === "Pass").length;
  const toggleStatement = () => {
    setMaterials((items) => items.map((item) => item.id === "statement" ? { ...item, status: "Complete", check: "Pass", note: "Writing structure approved and evidence gaps resolved." } : item));
  };
  return (
    <section className="workspace split">
      <aside className="context-rail">
        <button className="back-button">Back to Programs</button>
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
              <button className={item.id === "statement" ? "primary-outline" : "ghost-button"} onClick={item.id === "statement" ? openWriting : undefined}>Review</button>
            </div>
          ))}
        </div>
        <div className="table-footer">
          <span>Selected programme: {program.name}</span>
          <button className="primary-button" onClick={toggleStatement}>Simulate Statement Approved</button>
        </div>
      </main>
    </section>
  );
}

function WritingView({ program }: { program: Program }) {
  const [selected, setSelected] = useState(narrativeOptions[0]);
  const [resolved, setResolved] = useState<string[]>([]);
  const gaps = selected.gaps.filter((gap) => !resolved.includes(gap));
  const approveEnabled = gaps.length === 0;
  return (
    <section className="workspace writing-layout">
      <aside className="context-rail">
        <button className="back-button">Back to Checklist</button>
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
          <button className="primary-button" disabled={!approveEnabled}>Approve Structure</button>
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
  const validation = validateCodexEndpoint(endpoint);
  const busy = state.action !== "idle" && state.action !== "resetting";
  const now = () => new Date().toLocaleString();

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
      await task();
    } catch (error) {
      append(error instanceof Error ? error.message : "Codex OAuth action failed.", "error", "idle");
    }
  };

  const checkStatus = async (refreshToken: boolean) => {
    await run(refreshToken ? "refreshing_status" : "checking_status", async () => {
      const account = await readCodexAccount(endpoint, refreshToken);
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
    await run("starting_oauth", async () => {
      const login = await startCodexLogin(endpoint, flow);
      if (login.type === "chatgpt") {
        window.open(login.authUrl, "_blank", "noopener,noreferrer");
        append("Codex browser OAuth opened. Complete sign-in, then refresh status.", "opening_oauth", "idle", {
          authUrl: login.authUrl,
          verificationUrl: undefined,
          userCode: undefined,
        });
        return;
      }

      if (login.type === "chatgptDeviceCode") {
        append("Codex device-code OAuth started. Enter the code, then refresh status.", "pending_verification", "idle", {
          authUrl: undefined,
          verificationUrl: login.verificationUrl,
          userCode: login.userCode,
        });
        return;
      }

      if (login.authUrl) {
        window.open(login.authUrl, "_blank", "noopener,noreferrer");
      }
      append(login.message ?? "Bridge started Codex OAuth. Complete sign-in, then refresh status.", "pending_verification", "idle", {
        authUrl: login.authUrl,
        verificationUrl: login.verificationUrl,
        userCode: login.userCode,
      });
    });
  };

  const disconnect = async () => {
    await run("resetting", async () => {
      await logoutCodex(endpoint);
      append("Codex OAuth account was logged out through the configured endpoint.", "needs_sign_in", "idle", {
        accountLabel: undefined,
        authUrl: undefined,
        verificationUrl: undefined,
        userCode: undefined,
      });
    });
  };

  const resetPanel = () => {
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
            <button className="ghost-button" onClick={() => { rememberCodexEndpoint(endpoint); append("Endpoint saved locally.", validation.valid ? "unchecked" : "error"); }}>Save</button>
          </div>
          <p className={validation.valid ? "status-line pass" : "status-line error"}>{validation.message}</p>
          <pre>{`node scripts/codex_oauth_bridge.mjs --port 8787\n\n# Then open:\n?codex_bridge=http://127.0.0.1:8787\n\n# Origin-free clients can also use:\ncodex app-server --listen ws://127.0.0.1:4500`}</pre>
        </div>
        <div className="oauth-panel">
          <h3>OAuth Controls</h3>
          <p>{state.message}</p>
          <div className="button-row">
            <button className="primary-button" disabled={!validation.valid || busy} onClick={() => checkStatus(false)}>Check Status</button>
            <button className="ghost-button" disabled={!validation.valid || busy} onClick={() => startLogin("browser")}>Browser OAuth</button>
            <button className="ghost-button" disabled={!validation.valid || busy} onClick={() => startLogin("device")}>Device Code</button>
            <button className="ghost-button" disabled={!validation.valid || busy} onClick={() => checkStatus(true)}>Refresh Auth</button>
            <button className="ghost-button" disabled={!validation.valid || busy} onClick={disconnect}>Logout</button>
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
  const [catalogueId, setCatalogueId] = useState("manchester");
  const [selected, setSelected] = useState<Program>(programs.find((program) => program.id === "bsc-genetics") ?? programs[0]);
  const [oauthState, setOauthState] = useState<CodexOAuthPanelState>({
    status: "unchecked",
    action: "idle",
    message: "No status check has run. Use explicit controls before connecting a local Codex bridge.",
    events: [],
  });
  const selectedCatalogue = allInstitutionCatalogues.find((catalogue) => catalogue.id === catalogueId) ?? allInstitutionCatalogues[0];
  const rows = useMemo(() => {
    const catalogueRows = selectedCatalogue.examples
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

  return (
    <div className="app-shell">
      <Header activeView={activeView} setActiveView={setActiveView} />
      {activeView === "Programs" && (
        <div className="program-layout">
          <FilterRail level={level} setLevel={setLevel} group={group} setGroup={setGroup} catalogueId={catalogueId} setCatalogueId={setCatalogueId} catalogues={allInstitutionCatalogues} />
          <ProgramTable level={level} rows={rows} selected={activeProgram} setSelected={setSelected} openChecklist={openChecklist} catalogue={selectedCatalogue} />
          {rows.length ? <Inspector program={activeProgram} openChecklist={openChecklist} /> : <CatalogueInspector catalogue={selectedCatalogue} />}
        </div>
      )}
      {activeView === "Materials" && <MaterialsView program={activeProgram} openWriting={openWriting} />}
      {activeView === "Writing Studio" && <WritingView program={activeProgram} />}
      {activeView === "Sources" && <SourceView program={activeProgram} catalogue={selectedCatalogue} />}
      {activeView === "Codex OAuth" && <CodexOAuthView state={oauthState} setState={setOauthState} />}
    </div>
  );
}
