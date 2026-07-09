import { useEffect, useMemo, useRef, useState, type ChangeEvent, type Dispatch, type DragEvent, type MutableRefObject, type SetStateAction } from "react";
import {
  AI_PROVIDER_PROFILES,
  applyAIProviderDefaults,
  buildAIConfigPreview,
  extractInspirationFile,
  getAIProviderProfile,
  getInitialAIConfig,
  hasExplicitCodexEndpoint,
  isDefaultCodexEndpoint,
  isGithubPagesRuntime,
  logoutCodex,
  probeCodexBridge,
  readCodexAccount,
  rememberAIConfig,
  startCodexLogin,
  validateAIConfig,
  validateCodexEndpoint,
  type AIConfig,
  type AIConfigFormat,
  type AIProviderId,
  type CodexLoginFlow,
  type ExtractedInspirationBlock,
} from "./codexAuth";
import { allInstitutionCatalogues, groups, programFromCatalogueOption } from "./data/catalogues";
import { programs } from "./data/programs";
import type { InstitutionCatalogue, InstitutionGroup, MaterialItem, NarrativeOption, Program, ProgramLevel } from "./types";

type AIConfigStatus = "unchecked" | "static_blocked" | "needs_sign_in" | "opening_oauth" | "pending_verification" | "connected" | "configured" | "error";
type AIConfigAction = "idle" | "checking_status" | "starting_oauth" | "refreshing_status" | "saving_config" | "resetting";
type BridgeHealthStatus = "unknown" | "checking" | "ready" | "blocked";

interface AIConfigPanelState {
  status: AIConfigStatus;
  action: AIConfigAction;
  lastCheckedAt?: string;
  message: string;
  events: string[];
  accountLabel?: string;
  authUrl?: string;
  verificationUrl?: string;
  userCode?: string;
  runtime?: string;
  endpointKind?: string;
  configMessage?: string;
}

interface WritingRequirement {
  id: string;
  title: string;
  prompt: string;
  wordLimit: string;
  sourceUrl: string;
  sourceStatus: "Official prompt loaded" | "Source-backed document requirement" | "Needs official prompt verification";
  sourceTitle: string;
  required: string;
  sourceChecked: string;
}

interface ProgramRequirementGroup {
  program: Program;
  requirements: WritingRequirement[];
}

type InspirationFileStatus = "reading" | "ready" | "needs_bridge" | "needs_annotation" | "analyzing" | "analyzed" | "error";
type InspirationSourceKind = "text" | "pdf" | "docx" | "pptx" | "xlsx" | "spreadsheet" | "image" | "unsupported";
type InspirationCategory = "Interest Signals" | "Knowledge Evidence" | "Methods / Concepts" | "Possible Essay Angles" | "Unsupported Claims";

interface InspirationFile {
  id: string;
  name: string;
  size: number;
  mimeType: string;
  sourceKind: InspirationSourceKind;
  status: InspirationFileStatus;
  extractedTextPreview: string;
  extractionWarnings: string[];
  blocks: ExtractedInspirationBlock[];
  manualNote: string;
}

interface InspirationInsight {
  id: string;
  fileId: string;
  category: InspirationCategory;
  claim: string;
  evidenceExcerpt: string;
  pageOrSlide: string;
  essayUse: string;
  needsUserConfirmation: boolean;
}

const maxInspirationFileBytes = 25 * 1024 * 1024;
const textFileExtensions = new Set([".txt", ".md", ".markdown", ".csv", ".tsv", ".html", ".htm", ".json"]);
const bridgeFileExtensions = new Set([".pdf", ".docx", ".pptx", ".xlsx"]);
const imageFileExtensions = new Set([".png", ".jpg", ".jpeg", ".webp"]);
const sourceKindLabels: Record<InspirationSourceKind, string> = {
  text: "Text",
  pdf: "PDF",
  docx: "DOCX",
  pptx: "PPTX",
  xlsx: "XLSX",
  spreadsheet: "Spreadsheet",
  image: "Image",
  unsupported: "Manual note",
};
const inspirationStatusLabels: Record<InspirationFileStatus, string> = {
  reading: "Reading",
  ready: "Ready",
  needs_bridge: "Bridge needed",
  needs_annotation: "Manual note needed",
  analyzing: "Analyzing",
  analyzed: "Analyzed",
  error: "Error",
};

const globalMaterialTemplates: MaterialItem[] = [
  { id: "academic-record", name: "GPA / academic record", scope: "Reusable academic evidence", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Record the grade scale, transcript status, and any conversion notes in this session before checking programme thresholds." },
  { id: "language-test", name: "English language result", scope: "Reusable IELTS / TOEFL / PTE evidence", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Record test type, date, overall score, and component scores before matching programme language rules." },
  { id: "identity", name: "Passport or ID evidence", scope: "Reusable identity evidence", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Record only that valid identity evidence exists. Keep identity documents separate from Writing Studio inspiration files." },
  { id: "reference-contact", name: "Reference readiness", scope: "Reusable referee plan", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Record referee name/category and submission route only after the applicant has confirmed it." },
  { id: "funding-plan", name: "Funding plan", scope: "Reusable fee / scholarship evidence", status: "Unresolved", evidence: "Not provided", check: "Unresolved", note: "Record funding status when a programme, portal, or visa route requires it." },
];

const freshMaterials = (items: MaterialItem[]) => items.map((item) => ({ ...item }));

const writingDocPattern = /statement|essay|personal|purpose|writing|proposal|cv|resume|portfolio/i;

function institutionKey(program: Program) {
  return `${program.id} ${program.institution ?? ""} ${program.sourceUrl}`.toLowerCase();
}

function getWritingRequirements(program: Program): WritingRequirement[] {
  const key = institutionKey(program);

  if (key.includes("umich") || key.includes("michigan")) {
    const sourceUrl = "https://admissions.umich.edu/apply/first-year-applicants/essay-questions";
    return [
      {
        id: "umich-common-app-personal-essay",
        title: "Common Application personal essay",
        prompt: "Common Application personal essay slot. Verify the current official prompt list before drafting.",
        wordLimit: "250-650 words",
        sourceUrl,
        sourceStatus: "Needs official prompt verification",
        sourceTitle: "University of Michigan Essay Questions",
        required: "Expected through the Common Application route; verify in the official portal",
        sourceChecked: "2026-06-26",
      },
      {
        id: "umich-leadership-contribution",
        title: "Leadership and future contribution essay",
        prompt: "University of Michigan supplemental essay slot about leadership and future contribution. Verify current official wording before drafting.",
        wordLimit: "100-300 words",
        sourceUrl,
        sourceStatus: "Needs official prompt verification",
        sourceTitle: "University of Michigan Questions",
        required: "Expected for first-year applicants; verify in the official portal",
        sourceChecked: "2026-06-26",
      },
      {
        id: "umich-college-school-fit",
        title: "College or school fit essay",
        prompt: "University of Michigan supplemental essay slot about the selected undergraduate college or school. Verify current official wording before drafting.",
        wordLimit: "100-550 words",
        sourceUrl,
        sourceStatus: "Needs official prompt verification",
        sourceTitle: "University of Michigan Questions",
        required: "Expected for first-year applicants; verify in the official portal",
        sourceChecked: "2026-06-26",
      },
    ];
  }

  if (key.includes("cambridge")) {
    return [{
      id: "cambridge-additional-personal-statement",
      title: "Cambridge-specific additional personal statement",
      prompt: "Use the optional statement for Cambridge/course-specific reasons or subject exploration not fully covered in the UCAS personal statement.",
      wordLimit: "1200 characters",
      sourceUrl: "https://www.undergraduate.study.cam.ac.uk/apply/how/cambridge-application",
      sourceStatus: "Official prompt loaded",
      sourceTitle: "Completing My Cambridge Application",
      required: "Optional; recommended if the Cambridge course differs significantly from other UCAS choices",
      sourceChecked: "2026-06-26",
    }];
  }

  const writingDocuments = program.documents.filter((document) => writingDocPattern.test(document));
  if (writingDocuments.length) {
    return writingDocuments.map((document, index) => ({
      id: `source-doc-${index + 1}`,
      title: document,
      prompt: "Document requirement appears in the loaded programme material list. Exact prompt, audience, and word limit still need official page or portal verification.",
      wordLimit: "Needs official prompt verification",
      sourceUrl: program.sourceUrl,
      sourceStatus: program.sourceStatus === "Verified" ? "Source-backed document requirement" : "Needs official prompt verification",
      sourceTitle: program.sourceTitle,
      required: "Programme document list includes this writing-related item",
      sourceChecked: program.sourceChecked,
    }));
  }

  return [{
    id: "writing-verification-needed",
    title: "Writing requirement verification",
    prompt: "No source-backed writing prompt is loaded for this programme. Verify the official page or portal before treating any essay as required.",
    wordLimit: "Needs official prompt verification",
    sourceUrl: program.sourceUrl,
    sourceStatus: "Needs official prompt verification",
    sourceTitle: program.sourceTitle,
    required: "Not verified",
    sourceChecked: program.sourceChecked,
  }];
}

function createProgramMaterials(program: Program): MaterialItem[] {
  const writingRequirements = getWritingRequirements(program);
  const documentMaterials = program.documents
    .filter((document) => !writingDocPattern.test(document))
    .map((document, index) => ({
      id: `${program.id}-document-${index + 1}`,
      name: document,
      scope: `${program.name} / ${program.level}`,
      status: "Unresolved" as const,
      evidence: "Not provided",
      check: "Unresolved" as const,
      note: "Programme-specific requirement from the loaded source list. Record evidence in this session only after checking the official route.",
    }));

  return [
    {
      id: `${program.id}-route-code`,
      name: "Application route and programme code",
      scope: program.code || "Official programme route",
      status: "Unresolved",
      evidence: "Not confirmed in portal",
      check: "Unresolved",
      note: "Confirm exact programme title, code, cycle, and application route on the official source before submission.",
    },
    ...writingRequirements.map((requirement) => ({
      id: `${program.id}-writing-${requirement.id}`,
      name: requirement.title,
      scope: requirement.wordLimit,
      status: "Unresolved" as const,
      evidence: "Not provided",
      check: "Unresolved" as const,
      note: `${requirement.prompt} Source status: ${requirement.sourceStatus}.`,
    })),
    ...documentMaterials,
  ];
}

const narrativeOptions: NarrativeOption[] = [
  {
    id: "research-curiosity",
    title: "Research Curiosity",
    body: "Use a curiosity-driven structure only after the applicant confirms a specific question, its source, and the work or reading that developed it.",
    evidence: [],
    gaps: ["Confirmed question or experience", "Verified source and evidence date", "Explicit confirmation record"],
  },
  {
    id: "problem-solving",
    title: "Problem-Solving",
    body: "Use a problem-led structure only after a concrete applicant action, method, result, and reflection are explicitly confirmed.",
    evidence: [],
    gaps: ["Confirmed problem and applicant action", "Confirmed method and outcome", "Verified programme-specific fit"],
  },
  {
    id: "impact",
    title: "Purpose and Impact",
    body: "Use an impact-led structure only when the applicant has confirmed the relevant experience, contribution, limits, and future goal.",
    evidence: [],
    gaps: ["Confirmed experience and contribution", "Confirmed reflection and limits", "Verified programme-specific fit"],
  },
];

function fileExtension(name: string) {
  const index = name.lastIndexOf(".");
  return index >= 0 ? name.slice(index).toLowerCase() : "";
}

function makeClientId(prefix: string) {
  if (globalThis.crypto?.randomUUID) {
    return `${prefix}-${globalThis.crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function getInspirationSourceKind(file: File): InspirationSourceKind {
  const ext = fileExtension(file.name);
  if (textFileExtensions.has(ext) || file.type.startsWith("text/")) return ext === ".csv" || ext === ".tsv" ? "spreadsheet" : "text";
  if (ext === ".pdf" || file.type === "application/pdf") return "pdf";
  if (ext === ".docx") return "docx";
  if (ext === ".pptx") return "pptx";
  if (ext === ".xlsx") return "xlsx";
  if (imageFileExtensions.has(ext) || file.type.startsWith("image/")) return "image";
  return "unsupported";
}

function isBrowserReadableTextFile(file: File) {
  const ext = fileExtension(file.name);
  return textFileExtensions.has(ext) || file.type.startsWith("text/") || file.type === "application/json";
}

function needsBridgeExtraction(file: InspirationFile) {
  return bridgeFileExtensions.has(fileExtension(file.name)) || ["pdf", "docx", "pptx", "xlsx"].includes(file.sourceKind);
}

function compactPreview(text: string, limit = 1200) {
  const compact = text.replace(/\s+/g, " ").trim();
  return compact.length > limit ? `${compact.slice(0, limit).trim()}...` : compact;
}

function splitInsightSentences(text: string) {
  return text
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+|[\n;]+/)
    .map((item) => item.trim())
    .filter((item) => item.length > 28);
}

function findSentence(blocks: ExtractedInspirationBlock[], pattern: RegExp) {
  for (const block of blocks) {
    const match = splitInsightSentences(block.text).find((sentence) => pattern.test(sentence));
    if (match) {
      return { sentence: match, label: block.label };
    }
  }
  return undefined;
}

function firstSentence(blocks: ExtractedInspirationBlock[]) {
  for (const block of blocks) {
    const sentence = splitInsightSentences(block.text)[0];
    if (sentence) {
      return { sentence, label: block.label };
    }
  }
  return undefined;
}

function buildInsightsFromText(file: InspirationFile, blocks: ExtractedInspirationBlock[], writingContext: string): InspirationInsight[] {
  const insights: InspirationInsight[] = [];
  const addInsight = (
    category: InspirationCategory,
    match: { sentence: string; label: string } | undefined,
    claim: string,
    essayUse: string,
  ) => {
    if (!match || insights.some((item) => item.category === category)) return;
    insights.push({
      id: `${file.id}-${category.toLowerCase().replace(/[^a-z]+/g, "-")}-${insights.length + 1}`,
      fileId: file.id,
      category,
      claim,
      evidenceExcerpt: compactPreview(match.sentence, 280),
      pageOrSlide: match.label,
      essayUse,
      needsUserConfirmation: true,
    });
  };

  addInsight(
    "Interest Signals",
    findSentence(blocks, /interest|curious|curiosity|motivat|fascinat|question|explor|investigat|why|goal|aim|intend|hope/i),
    `Possible interest signal from ${file.name}.`,
    `Use only after the user confirms this reflects their real curiosity for ${writingContext}.`,
  );
  addInsight(
    "Knowledge Evidence",
    findSentence(blocks, /lecture|module|course|seminar|reading|paper|article|chapter|theory|concept|framework|case study|assessment/i),
    `Possible source-backed knowledge evidence from ${file.name}.`,
    "Use to make academic interest concrete without claiming personal achievement.",
  );
  addInsight(
    "Methods / Concepts",
    findSentence(blocks, /method|assay|protocol|dataset|analysis|experiment|lab|fieldwork|survey|interview|model|regression|statistics|python|matlab|spss|stata|pcr|gel electrophoresis/i),
    `Method or concept that may support a technical writing angle.`,
    "Use to show discipline knowledge; confirm whether the user used it or only learned it.",
  );
  addInsight(
    "Unsupported Claims",
    findSentence(blocks, /passion|passionate|excellent|exceptional|outstanding|strong|lifelong|always loved|dream|unique/i),
    "Potential unsupported wording that needs evidence before it can appear in an essay.",
    "Convert broad passion language into source-backed curiosity, or remove it.",
  );

  const fallback = firstSentence(blocks);
  addInsight(
    "Possible Essay Angles",
    fallback,
    `Discussion seed for ${writingContext}.`,
    "Use as a planning angle only after confirming the user's ownership and relevance.",
  );

  return insights.slice(0, 6);
}

function fileToBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Could not read file."));
    reader.onload = () => {
      const value = typeof reader.result === "string" ? reader.result : "";
      resolve(value.includes(",") ? value.split(",", 2)[1] : value);
    };
    reader.readAsDataURL(file);
  });
}

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
        {["Programs", "Materials", "Writing Studio", "AI Config"].map((item) => (
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

function cleanDegreeLabel(program: Program) {
  const award = program.award.trim();
  const awardText = `${award} ${program.name} ${program.id}`;
  const slashDegree = awardText.match(/\b(MPhil\/PhD|MSc\/PGDip\/PGCert\/PGA|PGA\/PGCert\/PGDip\/MSc|PGCert\/PGDip\/MSc)\b/i)?.[0];
  if (slashDegree) return slashDegree;

  const degree = awardText.match(/\b(PhD|MPhil|MSc|MA|MBA|MRes|MSt|MFA|MPH|MEd|LLM|PGDip|PGCert|PGCE|BA|BSc|BEng|MEng|MBBS)\b/i)?.[0];
  if (degree) return degree;
  if (/master'?s by coursework/i.test(award)) return "Master's";
  if (/master'?s degree/i.test(award)) return "Master's";
  if (/doctor/i.test(award)) return "PhD";
  return award.length <= 20 ? award : "Degree";
}

function getTeachingRoute(program: Program) {
  const text = `${program.award} ${program.mode} ${program.name} ${program.id}`.toLowerCase();
  if (/\b(by research|research|phd|mphil|mres)\b/.test(text)) return "Research";
  if (/\b(taught|coursework)\b/.test(text)) return "Taught";
  if (program.level === "Postgraduate" && /\b(msc|ma|mba|mst|mfa|mph|med|llm|pgdip|pgcert|pgce)\b/i.test(cleanDegreeLabel(program))) {
    return "Taught";
  }
  return "";
}

function getStudyModeLabels(program: Program) {
  const labels: string[] = [];
  const mode = program.mode.toLowerCase();
  if (/full[\s-]?time/.test(mode)) labels.push("Full-Time");
  if (/part[\s-]?time/.test(mode)) labels.push("Part-Time");
  if (/\bonline\b/.test(mode)) labels.push("Online");
  return Array.from(new Set(labels));
}

function ProgramMeta({ program }: { program: Program }) {
  const meta = Array.from(new Set([cleanDegreeLabel(program), getTeachingRoute(program)].filter(Boolean)));
  return (
    <div className="program-meta">
      {meta.map((item) => <span key={`${program.id}-${item}`}>{item}</span>)}
    </div>
  );
}

function DurationMeta({ program }: { program: Program }) {
  const modes = getStudyModeLabels(program);
  return (
    <div className="duration-cell">
      <span>{program.duration || "See official programme page"}</span>
      {modes.length > 0 && (
        <div className="duration-modes">
          {modes.map((mode) => <span key={`${program.id}-${mode}`}>{mode}</span>)}
        </div>
      )}
    </div>
  );
}

function SourceCell({ program }: { program: Program }) {
  const label = program.sourceUrl.includes("postgraduate.study.cam.ac.uk/courses/directory")
    ? "Official directory row"
    : "Official programme page";
  return (
    <a className="code-cell source-link-cell" href={program.sourceUrl} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()}>
      <span>
        <strong>{label}</strong>
        <small>{program.sourceStatus}</small>
      </span>
      <svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6" /></svg>
    </a>
  );
}

function ProgramTable({
  level,
  rows,
  selected,
  setSelected,
  catalogue,
  casePrograms,
  toggleCaseProgram,
}: {
  level: ProgramLevel;
  rows: Program[];
  selected: Program;
  setSelected: (program: Program) => void;
  catalogue: InstitutionCatalogue;
  casePrograms: Program[];
  toggleCaseProgram: (program: Program) => void;
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
          <span>Case</span>
        </div>
        {!rows.length && (
          <div className="empty-state">
            <strong>No programme rows for this level.</strong>
            <span>{catalogue.caveat}</span>
          </div>
        )}
        {rows.map((program, index) => (
          <div className={`program-row ${selected.id === program.id ? "selected" : ""}`} key={`${program.id}-${index}`} onClick={() => setSelected(program)} role="row">
            <button className="program-name-cell program-select-cell" onClick={(event) => { event.stopPropagation(); setSelected(program); }}>
              <strong>{program.name}</strong>
              <small>{program.institution} / {program.level}</small>
            </button>
            <ProgramMeta program={program} />
            <DurationMeta program={program} />
            <SourceCell program={program} />
            <button className={casePrograms.some((item) => item.id === program.id) ? "case-toggle active" : "case-toggle"} onClick={(event) => { event.stopPropagation(); toggleCaseProgram(program); }}>
              {casePrograms.some((item) => item.id === program.id) ? "In case" : "Add"}
            </button>
          </div>
        ))}
      </div>
      <div className="table-footer">
        <span>{catalogue.extractionNote}</span>
      </div>
    </main>
  );
}

function Inspector({
  program,
  openChecklist,
  inCase,
  toggleCaseProgram,
}: {
  program: Program;
  openChecklist: () => void;
  inCase: boolean;
  toggleCaseProgram: (program: Program) => void;
}) {
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
      <button className="ghost-button wide" onClick={() => toggleCaseProgram(program)}>{inCase ? "Remove from Writing Case" : "Add to Writing Case"}</button>
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
  casePrograms,
  toggleCaseProgram,
  openWriting,
  backToPrograms,
}: {
  program: Program;
  casePrograms: Program[];
  toggleCaseProgram: (program: Program) => void;
  openWriting: () => void;
  backToPrograms: () => void;
}) {
  const [globalMaterials, setGlobalMaterials] = useState(() => freshMaterials(globalMaterialTemplates));
  const [caseMaterials, setCaseMaterials] = useState<Record<string, MaterialItem[]>>({});
  const selectedPrograms = casePrograms;
  const caseKey = selectedPrograms.map((item) => item.id).join("|");

  useEffect(() => {
    setCaseMaterials((previous) => {
      const next = { ...previous };
      selectedPrograms.forEach((item) => {
        if (!next[item.id]) {
          next[item.id] = createProgramMaterials(item);
        }
      });
      return next;
    });
  }, [caseKey, selectedPrograms]);

  const programRows = selectedPrograms.map((item) => ({
    program: item,
    materials: caseMaterials[item.id] ?? createProgramMaterials(item),
  }));
  const totalMaterials = globalMaterials.length + programRows.reduce((sum, row) => sum + row.materials.length, 0);
  const complete = globalMaterials.filter((item) => item.check === "Pass").length
    + programRows.reduce((sum, row) => sum + row.materials.filter((item) => item.check === "Pass").length, 0);

  const recordGlobal = (id: string) => {
    setGlobalMaterials((items) => items.map((item) => item.id === id ? { ...item, status: "In Progress", evidence: "Structured evidence required", check: "Unresolved", note: "Add a substantive value, source URL/title/publisher, evidence date, explicit confirmation, verification, completeness, cycle, access date, and staleness before this item can pass." } : item));
  };
  const markGlobalNotRequired = (id: string) => {
    setGlobalMaterials((items) => items.map((item) => item.id === id ? { ...item, status: "In Progress", evidence: "N/A requires verification", check: "Unresolved", note: "Verify from the official route that this item is not required before marking it not applicable." } : item));
  };
  const clearGlobal = (id: string) => {
    const original = globalMaterialTemplates.find((item) => item.id === id);
    if (!original) return;
    setGlobalMaterials((items) => items.map((item) => item.id === id ? { ...original } : item));
  };
  const recordProgramMaterial = (programId: string, id: string) => {
    setCaseMaterials((lists) => ({
      ...lists,
      [programId]: (lists[programId] ?? []).map((item) => item.id === id ? { ...item, status: "In Progress", evidence: "Structured evidence required", check: "Unresolved", note: "Add the full normalized evidence record and verify it against the official programme requirement before this item can pass." } : item),
    }));
  };
  const markProgramNotRequired = (programId: string, id: string) => {
    setCaseMaterials((lists) => ({
      ...lists,
      [programId]: (lists[programId] ?? []).map((item) => item.id === id ? { ...item, status: "In Progress", evidence: "N/A requires verification", check: "Unresolved", note: "Verify from the official programme route that this item is not required before marking it not applicable." } : item),
    }));
  };
  const clearProgramMaterial = (targetProgram: Program, id: string) => {
    const original = createProgramMaterials(targetProgram).find((item) => item.id === id);
    if (!original) return;
    setCaseMaterials((lists) => ({
      ...lists,
      [targetProgram.id]: (lists[targetProgram.id] ?? []).map((item) => item.id === id ? { ...original } : item),
    }));
  };
  return (
    <section className="workspace split">
      <aside className="context-rail">
        <button className="back-button" onClick={backToPrograms}>Back to Programs</button>
        <h2>Application Case</h2>
        <p>Common evidence is recorded once. Programme-specific documents stay inside each selected case.</p>
        <button className="ghost-button wide" onClick={() => toggleCaseProgram(program)}>{casePrograms.some((item) => item.id === program.id) ? "Remove Current Program" : "Add Current Program"}</button>
        <h3>Selected Programs</h3>
        <div className="case-list">
          {selectedPrograms.length ? selectedPrograms.map((item) => (
            <button key={item.id} className="case-program-pill" onClick={() => toggleCaseProgram(item)}>
              <strong>{item.name}</strong>
              <span>{item.institution ?? "Institution"}</span>
            </button>
          )) : <p>No programs added yet.</p>}
        </div>
        <h3>Current Program Requirements</h3>
        <RequirementChips program={program} />
      </aside>
      <main className="checklist-panel">
        <div className="panel-heading compact">
          <h1>Application Checklist</h1>
          <div className="progress"><span style={{ width: `${totalMaterials ? (complete / totalMaterials) * 100 : 0}%` }} /> </div>
          <p>{complete} of {totalMaterials} complete</p>
        </div>
        <section className="material-section">
          <div className="section-heading">
            <div>
              <h2>Common Material Vault</h2>
              <p>Records reusable evidence only. Writing Studio inspiration files do not pre-mark checklist items as ready.</p>
            </div>
          </div>
          <div className="material-table">
            {globalMaterials.map((item, index) => (
              <div className={`material-row ${item.check === "Unresolved" ? "attention" : ""}`} key={item.id}>
                <span className="row-number">{index + 1}</span>
                <div><strong>{item.name}</strong><small>{item.scope}</small></div>
                <span className={`status-dot ${item.check.toLowerCase().replace("/", "-")}`}>{item.check}</span>
                <span className="evidence">{item.evidence}</span>
                <p>{item.note}</p>
                <div className="material-actions">
                  <button className="ghost-button" onClick={() => recordGlobal(item.id)}>Start evidence record</button>
                  <button className="ghost-button" onClick={() => markGlobalNotRequired(item.id)}>Review N/A</button>
                  {item.check !== "Unresolved" && <button className="ghost-button" onClick={() => clearGlobal(item.id)}>Clear</button>}
                </div>
              </div>
            ))}
          </div>
        </section>
        <section className="material-section">
          <div className="section-heading">
            <div>
              <h2>Programme-Specific Materials</h2>
              <p>Each selected programme keeps its own route, writing, and document checks.</p>
            </div>
            <button className="primary-outline" onClick={openWriting} disabled={!selectedPrograms.length}>Open Writing Studio</button>
          </div>
          {!programRows.length && (
            <div className="empty-state">
              <strong>No programme case selected.</strong>
              <span>Add the current programme or go back to Programs and add more options.</span>
            </div>
          )}
          {programRows.map((row) => (
            <div className="case-program-card" key={row.program.id}>
              <div className="case-program-heading">
                <div>
                  <h3>{row.program.institution ?? "Institution"}</h3>
                  <h2>{row.program.name}</h2>
                  <p>{row.program.level} / {row.program.award} / {row.program.duration}</p>
                </div>
                <button className="ghost-button" onClick={() => toggleCaseProgram(row.program)}>Remove</button>
              </div>
              <div className="material-table">
                {row.materials.map((item, index) => (
                  <div className={`material-row ${item.check === "Unresolved" ? "attention" : ""}`} key={item.id}>
                    <span className="row-number">{index + 1}</span>
                    <div><strong>{item.name}</strong><small>{item.scope}</small></div>
                    <span className={`status-dot ${item.check.toLowerCase().replace("/", "-")}`}>{item.check}</span>
                    <span className="evidence">{item.evidence}</span>
                    <p>{item.note}</p>
                    <div className="material-actions">
                      {item.id.includes("-writing-") && <button className="primary-outline" onClick={openWriting}>Plan writing</button>}
                      <button className="ghost-button" onClick={() => recordProgramMaterial(row.program.id, item.id)}>Start evidence record</button>
                      <button className="ghost-button" onClick={() => markProgramNotRequired(row.program.id, item.id)}>Review N/A</button>
                      {item.check !== "Unresolved" && <button className="ghost-button" onClick={() => clearProgramMaterial(row.program, item.id)}>Clear</button>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </section>
        <div className="table-footer">
          <span>Current programme: {program.name}</span>
        </div>
      </main>
    </section>
  );
}

function requirementKey(program: Program, requirement: WritingRequirement) {
  return `${program.id}:${requirement.id}`;
}

function buildWritingGroups(casePrograms: Program[]): ProgramRequirementGroup[] {
  return casePrograms.map((program) => ({ program, requirements: getWritingRequirements(program) }));
}

function WritingView({
  casePrograms,
  backToChecklist,
  openPrograms,
  inspirationFileRefs,
  inspirationFiles,
  setInspirationFiles,
  inspirationInsights,
  setInspirationInsights,
  approvedInsights,
  setApprovedInsights,
}: {
  casePrograms: Program[];
  backToChecklist: () => void;
  openPrograms: () => void;
  inspirationFileRefs: MutableRefObject<Map<string, File>>;
  inspirationFiles: InspirationFile[];
  setInspirationFiles: Dispatch<SetStateAction<InspirationFile[]>>;
  inspirationInsights: InspirationInsight[];
  setInspirationInsights: Dispatch<SetStateAction<InspirationInsight[]>>;
  approvedInsights: string[];
  setApprovedInsights: Dispatch<SetStateAction<string[]>>;
}) {
  const inspirationInputRef = useRef<HTMLInputElement>(null);
  const [selected, setSelected] = useState(narrativeOptions[0]);
  const [approval, setApproval] = useState("");
  const [activeProgramId, setActiveProgramId] = useState("");
  const [activeRequirementId, setActiveRequirementId] = useState("");
  const [draggingInspiration, setDraggingInspiration] = useState(false);
  const [inspirationNotice, setInspirationNotice] = useState("");
  const writingGroups = useMemo(() => buildWritingGroups(casePrograms), [casePrograms]);
  const requirementRows = useMemo(() => writingGroups.flatMap((group) => group.requirements.map((requirement) => ({
    key: requirementKey(group.program, requirement),
    program: group.program,
    requirement,
  }))), [writingGroups]);
  const requirementKeys = requirementRows.map((item) => item.key).join("|");
  const activeGroup = writingGroups.find((group) => group.program.id === activeProgramId) ?? writingGroups[0];

  useEffect(() => {
    if (writingGroups.length && !writingGroups.some((group) => group.program.id === activeProgramId)) {
      setActiveProgramId(writingGroups[0].program.id);
      setApproval("");
    }
    if (!writingGroups.length && activeProgramId) {
      setActiveProgramId("");
    }
  }, [activeProgramId, writingGroups]);

  useEffect(() => {
    const activeKeys = activeGroup?.requirements.map((requirement) => requirementKey(activeGroup.program, requirement)) ?? [];
    if (activeKeys.length && !activeKeys.includes(activeRequirementId)) {
      setActiveRequirementId(activeKeys[0]);
      setApproval("");
    }
    if (!requirementRows.length && activeRequirementId) {
      setActiveRequirementId("");
    }
  }, [activeGroup, activeRequirementId, requirementKeys, requirementRows.length]);

  const activeRequirement = requirementRows.find((item) => item.key === activeRequirementId) ?? requirementRows[0];
  const gaps = selected.gaps;
  const approveEnabled = Boolean(activeRequirement) && gaps.length === 0;
  const activeWritingContext = activeRequirement ? `${activeRequirement.program.name} / ${activeRequirement.requirement.title}` : "selected writing item";
  const approvedInsightRows = inspirationInsights.filter((insight) => approvedInsights.includes(insight.id));
  const approvedInsightSet = new Set(approvedInsights);
  const updateInspirationFile = (id: string, patch: Partial<InspirationFile>) => {
    setInspirationFiles((files) => files.map((file) => file.id === id ? { ...file, ...patch } : file));
  };
  const storeInsightsForFile = (fileId: string, insights: InspirationInsight[]) => {
    setInspirationInsights((items) => [...items.filter((item) => item.fileId !== fileId), ...insights]);
    setApprovedInsights((items) => items.filter((item) => !item.startsWith(`${fileId}-`)));
  };
  const focusProgram = (group: ProgramRequirementGroup) => {
    const firstRequirement = group.requirements[0];
    if (!firstRequirement) return;
    setActiveProgramId(group.program.id);
    setActiveRequirementId(requirementKey(group.program, firstRequirement));
    setApproval("");
  };
  const approveStructure = () => {
    if (!activeRequirement) return;
    const sourceVerified = activeRequirement.requirement.sourceStatus !== "Needs official prompt verification";
    setApproval(sourceVerified
      ? "Structure approved for this browser session. Drafting can proceed from this source-backed prompt."
      : "Structure recorded as a planning draft. Verify the official prompt before drafting.");
  };
  const handleInspirationFiles = async (fileList: FileList | File[]) => {
    const files = Array.from(fileList);
    if (!files.length) return;
    const accepted = files.slice(0, 5);
    setInspirationNotice(files.length > 5 ? "Only the first 5 files from this batch were added." : "");

    for (const file of accepted) {
      const id = makeClientId("inspiration");
      const sourceKind = getInspirationSourceKind(file);
      const baseFile: InspirationFile = {
        id,
        name: file.name,
        size: file.size,
        mimeType: file.type || "application/octet-stream",
        sourceKind,
        status: file.size > maxInspirationFileBytes ? "error" : isBrowserReadableTextFile(file) ? "reading" : sourceKind === "image" || sourceKind === "unsupported" ? "needs_annotation" : "needs_bridge",
        extractedTextPreview: "",
        extractionWarnings: file.size > maxInspirationFileBytes
          ? ["File exceeds the 25MB extraction limit."]
          : sourceKind === "image"
            ? ["Image upload is registered. Add a manual note unless OCR is available through a later bridge capability."]
            : sourceKind === "unsupported"
              ? ["Automatic extraction is not available for this file type. Add manual notes before using it for inspiration."]
              : needsBridgeExtraction({ id, name: file.name, size: file.size, mimeType: file.type || "application/octet-stream", sourceKind, status: "needs_bridge", extractedTextPreview: "", extractionWarnings: [], blocks: [], manualNote: "" })
                ? ["Connect the Codex bridge to extract this file type."]
                : [],
        blocks: [],
        manualNote: "",
      };

      inspirationFileRefs.current.set(id, file);
      setInspirationFiles((items) => [...items, baseFile]);

      if (file.size <= maxInspirationFileBytes && isBrowserReadableTextFile(file)) {
        try {
          const text = await file.text();
          const block = { label: "Document text", text };
          updateInspirationFile(id, {
            status: "ready",
            extractedTextPreview: compactPreview(text),
            extractionWarnings: [],
            blocks: [block],
          });
        } catch (error) {
          updateInspirationFile(id, {
            status: "error",
            extractionWarnings: [error instanceof Error ? error.message : "Could not read this file in the browser."],
          });
        }
      }
    }
  };
  const handleFileInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.currentTarget.files) {
      void handleInspirationFiles(event.currentTarget.files);
      event.currentTarget.value = "";
    }
  };
  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDraggingInspiration(false);
    if (event.dataTransfer.files.length) {
      void handleInspirationFiles(event.dataTransfer.files);
    }
  };
  const analyzeManualNote = (file: InspirationFile) => {
    const note = file.manualNote.trim();
    if (!note) {
      updateInspirationFile(file.id, {
        status: "needs_annotation",
        extractionWarnings: ["Add a manual note before analyzing this file for writing inspiration."],
      });
      setInspirationNotice("Add a manual note that names the relevant topic, reading, method, or slide content.");
      return true;
    }
    const blocks = [{ label: "Manual note", text: note }];
    const source = { ...file, blocks, extractedTextPreview: compactPreview(note), status: "analyzed" as const };
    const insights = buildInsightsFromText(source, blocks, activeWritingContext);
    updateInspirationFile(file.id, {
      status: "analyzed",
      blocks,
      extractedTextPreview: compactPreview(note),
      extractionWarnings: ["Insights came from user-entered manual notes, not automatic file extraction."],
    });
    storeInsightsForFile(file.id, insights);
    setInspirationNotice(insights.length ? "Manual note analyzed. Confirm specific insights before using them in the evidence map." : "Manual note saved, but no usable insight was detected.");
    return true;
  };
  const analyzeInspirationFile = async (fileId: string) => {
    const fileMeta = inspirationFiles.find((file) => file.id === fileId);
    if (!fileMeta) return;

    if (fileMeta.sourceKind === "image" || fileMeta.sourceKind === "unsupported" || (fileMeta.manualNote.trim() && ["needs_annotation", "needs_bridge", "error"].includes(fileMeta.status))) {
      analyzeManualNote(fileMeta);
      return;
    }

    if (fileMeta.blocks.length && !needsBridgeExtraction(fileMeta)) {
      const insights = buildInsightsFromText(fileMeta, fileMeta.blocks, activeWritingContext);
      updateInspirationFile(fileId, { status: "analyzed" });
      storeInsightsForFile(fileId, insights);
      setInspirationNotice(insights.length ? "Text file analyzed. Confirm each insight before it enters the evidence map." : "No usable insight was detected in this text file.");
      return;
    }

    const file = inspirationFileRefs.current.get(fileId);
    if (!file) {
      updateInspirationFile(fileId, { status: "error", extractionWarnings: ["Browser file handle is no longer available. Remove and upload the file again."] });
      return;
    }
    if (file.size > maxInspirationFileBytes) {
      updateInspirationFile(fileId, { status: "error", extractionWarnings: ["File exceeds the 25MB extraction limit."] });
      return;
    }

    updateInspirationFile(fileId, { status: "analyzing", extractionWarnings: [] });
    try {
      const config = getInitialAIConfig();
      const contentBase64 = await fileToBase64(file);
      const result = await extractInspirationFile(config.endpoint, config.bridgeNonce, {
        name: file.name,
        mimeType: file.type || "application/octet-stream",
        contentBase64,
      });
      const status: InspirationFileStatus = result.blocks.length ? "analyzed" : result.ok ? "needs_annotation" : "error";
      updateInspirationFile(fileId, {
        status,
        blocks: result.blocks,
        extractedTextPreview: result.preview ? compactPreview(result.preview) : "",
        extractionWarnings: result.warnings.length ? result.warnings : result.error ? [result.error] : [],
      });
      const insights = result.blocks.length ? buildInsightsFromText({ ...fileMeta, blocks: result.blocks }, result.blocks, activeWritingContext) : [];
      storeInsightsForFile(fileId, insights);
      setInspirationNotice(result.blocks.length
        ? "Bridge extraction complete. Confirm insights before using them in the evidence map."
        : "The bridge did not extract text. Add manual notes for this file.");
    } catch (error) {
      updateInspirationFile(fileId, {
        status: "needs_bridge",
        extractionWarnings: [error instanceof Error ? error.message : "Codex bridge extraction failed."],
      });
      setInspirationNotice("Connect or refresh the Codex bridge in AI Config, then retry extraction.");
    }
  };
  const removeInspirationFile = (fileId: string) => {
    inspirationFileRefs.current.delete(fileId);
    setInspirationFiles((files) => files.filter((file) => file.id !== fileId));
    setInspirationInsights((items) => items.filter((item) => item.fileId !== fileId));
    setApprovedInsights((items) => items.filter((item) => !item.startsWith(`${fileId}-`)));
  };
  const toggleInsightApproval = (insightId: string) => {
    setApprovedInsights((items) => items.includes(insightId) ? items.filter((item) => item !== insightId) : [...items, insightId]);
  };
  const updateManualNote = (fileId: string, manualNote: string) => {
    updateInspirationFile(fileId, { manualNote });
  };

  return (
    <section className="workspace writing-layout">
      <aside className="context-rail">
        <button className="back-button" onClick={backToChecklist}>Back to Checklist</button>
        <h2>Selected Programs</h2>
        <p>Writing Studio only plans documents for programmes already selected in Programs.</p>
        <div className="selected-program-stack">
          {writingGroups.length ? writingGroups.map((group) => (
            <button key={group.program.id} className={`selected-program-card ${activeGroup?.program.id === group.program.id ? "active" : ""}`} onClick={() => focusProgram(group)}>
              <strong>{group.program.name}</strong>
              <span>{group.program.institution ?? "Institution"} / {cleanDegreeLabel(group.program)}</span>
              <div className="mini-requirement-list">
                {group.requirements.map((requirement) => (
                  <span key={requirement.id}>{requirement.title} · {requirement.wordLimit}</span>
                ))}
              </div>
            </button>
          )) : (
            <div className="rail-empty">
              <strong>No selected programmes.</strong>
              <span>Add programmes from Programs first.</span>
              <button className="ghost-button wide" onClick={openPrograms}>Open Programs</button>
            </div>
          )}
        </div>
      </aside>
      <main className="checklist-panel">
        <div className="writing-steps">
          {["Brief Lock", "Prompt Detail", "Inspiration Intake", "Narrative Options", "Evidence Map", "Draft Gate"].map((step, index) => (
            <span className={index < 2 ? "done" : index === 2 ? "current" : ""} key={step}>{index + 1}. {step}</span>
          ))}
        </div>
        <div className="panel-heading compact">
          <h1>Writing Studio</h1>
          <p>{casePrograms.length} selected program{casePrograms.length === 1 ? "" : "s"} / {requirementRows.length} writing item{requirementRows.length === 1 ? "" : "s"} to plan or verify.</p>
        </div>
        {!activeGroup ? (
          <div className="empty-state writing-empty">
            <strong>No writing case selected.</strong>
            <span>Add programmes from Programs before planning narratives.</span>
            <button className="primary-outline" onClick={openPrograms}>Open Programs</button>
          </div>
        ) : (
          <>
            <section className="active-program-panel">
              <div className="case-program-heading">
                <div>
                  <h3>{activeGroup.program.institution ?? "Institution"} / {activeGroup.program.level}</h3>
                  <h2>{activeGroup.program.name}</h2>
                  <p>{cleanDegreeLabel(activeGroup.program)} / {getTeachingRoute(activeGroup.program) || "Route not classified"} / {activeGroup.program.duration}</p>
                </div>
                <a href={activeGroup.program.sourceUrl} target="_blank" rel="noreferrer">Official source</a>
              </div>
              <div className="requirement-list">
                {activeGroup.requirements.map((requirement) => {
                  const key = requirementKey(activeGroup.program, requirement);
                  return (
                    <button key={key} className={activeRequirement?.key === key ? "requirement-card selected" : "requirement-card"} onClick={() => { setActiveRequirementId(key); setApproval(""); }}>
                      <strong>{requirement.title}</strong>
                      <span>{requirement.wordLimit} / {requirement.required}</span>
                      <small>{requirement.sourceStatus}</small>
                    </button>
                  );
                })}
              </div>
            </section>
            {activeRequirement && (
              <section className="requirement-detail-panel">
                <h3>Writing Requirement Detail</h3>
                <h2>{activeRequirement.requirement.title}</h2>
                <div className="requirement-detail-grid">
                  <div><span>Prompt / task</span><strong>{activeRequirement.requirement.prompt}</strong></div>
                  <div><span>Word count</span><strong>{activeRequirement.requirement.wordLimit}</strong></div>
                  <div><span>Required</span><strong>{activeRequirement.requirement.required}</strong></div>
                  <div><span>Source</span><strong>{activeRequirement.requirement.sourceTitle}</strong></div>
                  <div><span>Status</span><strong>{activeRequirement.requirement.sourceStatus}</strong></div>
                  <div><span>Checked</span><strong>{activeRequirement.requirement.sourceChecked}</strong></div>
                </div>
                <a href={activeRequirement.requirement.sourceUrl} target="_blank" rel="noreferrer">Open official prompt/source</a>
              </section>
            )}
            <section className="inspiration-panel">
              <div className="inspiration-heading">
                <div>
                  <h3>Inspiration Files</h3>
                  <h2>Source-backed idea pool</h2>
                  <p>Upload assignments, lecture slides, readings, coursework, or notes as planning evidence. These files do not mark application materials complete.</p>
                </div>
                <span>{inspirationFiles.length} file{inspirationFiles.length === 1 ? "" : "s"} / {approvedInsightRows.length} approved insight{approvedInsightRows.length === 1 ? "" : "s"}</span>
              </div>
              <div
                className={`upload-dropzone ${draggingInspiration ? "dragging" : ""}`}
                onDragOver={(event) => { event.preventDefault(); setDraggingInspiration(true); }}
                onDragLeave={() => setDraggingInspiration(false)}
                onDrop={handleDrop}
              >
                <input
                  ref={inspirationInputRef}
                  className="sr-only"
                  type="file"
                  multiple
                  accept=".pdf,.docx,.pptx,.xlsx,.csv,.txt,.md,.markdown,.html,.htm,.json,.png,.jpg,.jpeg,.webp"
                  onChange={handleFileInputChange}
                />
                <div>
                  <strong>Drop files here</strong>
                  <span>TXT/MD/CSV/JSON/HTML preview in browser. PDF/DOCX/PPTX/XLSX use the Codex bridge. Images use manual notes in v1.</span>
                </div>
                <button className="primary-outline" onClick={() => inspirationInputRef.current?.click()}>Choose files</button>
              </div>
              {inspirationNotice && <p className="status-line warn">{inspirationNotice}</p>}
              <div className="inspiration-file-list">
                {inspirationFiles.length ? inspirationFiles.map((file) => {
                  const fileInsights = inspirationInsights.filter((insight) => insight.fileId === file.id);
                  const useManualNote = file.sourceKind === "image" || file.sourceKind === "unsupported" || file.status === "needs_annotation" || file.manualNote.trim();
                  return (
                    <article className="inspiration-file-card" key={file.id}>
                      <div className="file-card-top">
                        <div>
                          <h4>{file.name}</h4>
                          <div className="file-meta">
                            <span>{sourceKindLabels[file.sourceKind]}</span>
                            <span>{formatFileSize(file.size)}</span>
                            <span>{file.mimeType || "application/octet-stream"}</span>
                          </div>
                        </div>
                        <span className={`file-status ${file.status}`}>{inspirationStatusLabels[file.status]}</span>
                      </div>
                      {file.extractedTextPreview && <p className="file-preview">{file.extractedTextPreview}</p>}
                      {file.extractionWarnings.length > 0 && (
                        <div className="warning-list">
                          {file.extractionWarnings.map((warning) => <span key={warning}>{warning}</span>)}
                        </div>
                      )}
                      {useManualNote && (
                        <textarea
                          className="manual-note-input"
                          value={file.manualNote}
                          onChange={(event) => updateManualNote(file.id, event.currentTarget.value)}
                          placeholder="Manual note: relevant topic, method, reading, slide point, or assignment idea. Do not state an achievement unless it is truly yours."
                        />
                      )}
                      <div className="file-actions">
                        <button className="primary-outline" disabled={file.status === "analyzing"} onClick={() => void analyzeInspirationFile(file.id)}>
                          {file.status === "analyzing" ? "Analyzing" : file.manualNote.trim() && useManualNote ? "Analyze note" : "Analyze for inspiration"}
                        </button>
                        <button className="ghost-button" onClick={() => removeInspirationFile(file.id)}>Remove</button>
                      </div>
                      {fileInsights.length > 0 && (
                        <div className="insight-grid">
                          {fileInsights.map((insight) => {
                            const approved = approvedInsightSet.has(insight.id);
                            return (
                              <div className={`insight-card ${approved ? "approved" : ""}`} key={insight.id}>
                                <span>{insight.category}</span>
                                <strong>{insight.claim}</strong>
                                <p>{insight.evidenceExcerpt}</p>
                                <small>{insight.pageOrSlide} / {insight.essayUse}</small>
                                <button className={approved ? "ghost-button" : "primary-outline"} onClick={() => toggleInsightApproval(insight.id)}>
                                  {approved ? "Remove provisional insight" : "Keep as provisional insight"}
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </article>
                  );
                }) : (
                  <div className="inspiration-empty">
                    <strong>No inspiration files uploaded in this session.</strong>
                    <span>Use this area for writing inspiration only; official application materials still stay in the checklist.</span>
                  </div>
                )}
              </div>
            </section>
          </>
        )}
        {activeRequirement ? (
          <>
            <div className="writing-grid">
              <div className="option-stack">
                <h3>Narrative Options</h3>
                {narrativeOptions.map((optionItem) => (
                  <button className={`narrative-option ${selected.id === optionItem.id ? "selected" : ""}`} key={optionItem.id} onClick={() => setSelected(optionItem)}>
                    <strong>{optionItem.title}</strong>
                    <span>{optionItem.body}</span>
                  </button>
                ))}
              </div>
              <div className="evidence-map">
                <h3>Evidence Map</h3>
                <p className="active-brief">{activeRequirement.program.name}: {activeRequirement.requirement.title}</p>
                {selected.evidence.map((item) => <p className="evidence-pass" key={item}>{item}</p>)}
                {approvedInsightRows.length > 0 && (
                  <div className="approved-insight-list">
                    <h4>Provisional inspiration</h4>
                    {approvedInsightRows.map((insight) => (
                      <p className="evidence-pass uploaded" key={insight.id}>
                        {insight.category}: {insight.evidenceExcerpt}
                      </p>
                    ))}
                  </div>
                )}
                {selected.gaps.map((gap) => <div className="gap-item" key={gap}>{gap}</div>)}
              </div>
            </div>
            <div className="composer">
              <p>{gaps.length ? `${gaps.length} evidence gap${gaps.length > 1 ? "s" : ""} left. Add missing evidence or choose a different narrative.` : "Evidence gaps resolved. Structure approval is available for the selected writing item."}</p>
              <textarea placeholder="Tell the Writing Studio what evidence you can add, or choose a different narrative option." />
              <button className="primary-button" disabled={!approveEnabled} onClick={approveStructure}>Approve Structure</button>
              {approval && <p className={approval.includes("Verify") ? "status-line warn" : "status-line pass"}>{approval}</p>}
            </div>
          </>
        ) : (
          <div className="empty-state">
            <strong>Writing planning is blocked.</strong>
            <span>Select at least one programme and writing item before approving a structure.</span>
          </div>
        )}
      </main>
    </section>
  );
}

const configFormatLabels: Record<AIConfigFormat, string> = {
  env: "ENV",
  json: "JSON",
  yaml: "YAML",
  curl: "cURL",
  cli: "CLI",
};

function AIConfigView({
  state,
  setState,
}: {
  state: AIConfigPanelState;
  setState: Dispatch<SetStateAction<AIConfigPanelState>>;
}) {
  const [config, setConfig] = useState<AIConfig>(getInitialAIConfig);
  const [bridgeHealth, setBridgeHealth] = useState<{ status: BridgeHealthStatus; message: string; nonceRequired?: boolean }>({
    status: "unknown",
    message: "Bridge health has not been checked.",
  });
  const profile = getAIProviderProfile(config.providerId);
  const configValidation = validateAIConfig(config);
  const codexEndpointValidation = validateCodexEndpoint(config.endpoint);
  const preview = buildAIConfigPreview(config);
  const isCodexRuntime = profile.runtime === "codex-oauth";
  const busy = state.action !== "idle" && state.action !== "resetting";
  const now = () => new Date().toLocaleString();
  const defaultStaticBridgeBlocked = isCodexRuntime && codexEndpointValidation.kind === "bridge-http" && isGithubPagesRuntime() && isDefaultCodexEndpoint(config.endpoint) && !hasExplicitCodexEndpoint() && bridgeHealth.status !== "ready";
  const nonceBlocked = isCodexRuntime && codexEndpointValidation.kind === "bridge-http" && bridgeHealth.nonceRequired === true && !config.bridgeNonce.trim();
  const oauthControlsDisabled = !isCodexRuntime || !codexEndpointValidation.valid || busy || defaultStaticBridgeBlocked || nonceBlocked;
  const credentialOptions = profile.credentialEnvVars.length ? profile.credentialEnvVars : [config.keyEnvVar || "AI_API_KEY"];

  useEffect(() => {
    setBridgeHealth({ status: "unknown", message: "Bridge health has not been checked." });
  }, [config.endpoint, config.providerId]);

  const append = (
    message: string,
    status: AIConfigStatus,
    action: AIConfigAction = "idle",
    extra: Partial<AIConfigPanelState> = {},
  ) => {
    const timestamp = now();
    setState((previous) => ({
      ...previous,
      ...extra,
      status,
      action,
      lastCheckedAt: timestamp,
      message,
      runtime: profile.runtime,
      endpointKind: isCodexRuntime ? codexEndpointValidation.kind : undefined,
      configMessage: isCodexRuntime ? codexEndpointValidation.message : configValidation.message,
      events: [`${timestamp} / ${message}`, ...previous.events].slice(0, 8),
    }));
  };

  const run = async (action: AIConfigAction, task: () => Promise<void>) => {
    append(`Running ${action.replace("_", " ")}.`, state.status, action);
    try {
      rememberAIConfig(config);
      await task();
    } catch (error) {
      append(error instanceof Error ? error.message : "AI configuration action failed.", "error", "idle");
    }
  };

  const updateConfig = (patch: Partial<AIConfig>) => setConfig((previous) => ({ ...previous, ...patch }));
  const updateProvider = (providerId: AIProviderId) => setConfig((previous) => applyAIProviderDefaults(previous, providerId));
  const saveConfig = () => {
    rememberAIConfig(config);
    const result = validateAIConfig(config);
    append(result.valid ? "AI configuration saved locally. Runtime secrets must stay in environment variables or the selected CLI." : result.message, result.valid ? "configured" : "error", "idle");
  };

  const checkBridgeHealth = async () => {
    await run("checking_status", async () => {
      setBridgeHealth({ status: "checking", message: "Checking local bridge health." });
      const health = await probeCodexBridge(config.endpoint, config.bridgeNonce);
      const message = health.nonceRequired && !config.bridgeNonce.trim()
        ? "Bridge is reachable but requires the nonce printed by scripts/codex_oauth_bridge.mjs."
        : "Bridge health check passed.";
      setBridgeHealth({ status: "ready", message, nonceRequired: health.nonceRequired });
      append(message, health.nonceRequired && !config.bridgeNonce.trim() ? "static_blocked" : "unchecked", "idle");
    });
  };

  const checkStatus = async (refreshToken: boolean) => {
    await run(refreshToken ? "refreshing_status" : "checking_status", async () => {
      const account = await readCodexAccount(config.endpoint, refreshToken, config.bridgeNonce);
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
      const login = await startCodexLogin(config.endpoint, flow, config.bridgeNonce);
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
      await logoutCodex(config.endpoint, config.bridgeNonce);
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
      action: "idle",
      message: "Panel reset. No token data was read or stored.",
      events: [],
      runtime: profile.runtime,
      endpointKind: isCodexRuntime ? codexEndpointValidation.kind : undefined,
      configMessage: configValidation.message,
    });
  };

  return (
    <section className="source-page">
      <div className="panel-heading">
        <div>
          <h1>AI Configuration</h1>
          <p>Hermes-style provider setup: choose an AI runtime, model, credential source, and export format. Codex OAuth is one provider option, not the whole configuration layer.</p>
        </div>
        <span className={`oauth-state ${state.status}`}>{state.status.replace("_", " ")}</span>
      </div>
      <div className="oauth-grid">
        <div className="oauth-panel oauth-panel-wide">
          <h3>Provider Setup</h3>
          <div className="config-grid">
            <label className="config-field" htmlFor="ai-provider">
              <span className="field-label">Provider</span>
              <select id="ai-provider" className="select-input" value={config.providerId} onChange={(event) => updateProvider(event.target.value as AIProviderId)}>
                {AI_PROVIDER_PROFILES.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
              </select>
            </label>
            <label className="config-field" htmlFor="ai-format">
              <span className="field-label">Output format</span>
              <select id="ai-format" className="select-input" value={config.configFormat} onChange={(event) => updateConfig({ configFormat: event.target.value as AIConfigFormat })}>
                {(Object.keys(configFormatLabels) as AIConfigFormat[]).map((item) => <option key={item} value={item}>{configFormatLabels[item]}</option>)}
              </select>
            </label>
            <label className="config-field" htmlFor="ai-model">
              <span className="field-label">Model</span>
              <input id="ai-model" className="text-input" value={config.model} onChange={(event) => updateConfig({ model: event.target.value })} spellCheck={false} />
            </label>
            {profile.credentialEnvVars.length > 0 && (
              <label className="config-field" htmlFor="ai-key-env">
                <span className="field-label">Credential environment variable</span>
                <input id="ai-key-env" className="text-input" list="ai-key-env-options" value={config.keyEnvVar} onChange={(event) => updateConfig({ keyEnvVar: event.target.value })} spellCheck={false} />
                <datalist id="ai-key-env-options">
                  {credentialOptions.map((item) => <option key={item} value={item} />)}
                </datalist>
              </label>
            )}
            {profile.runtime !== "codex-oauth" && profile.runtime !== "cli" && (
              <label className="config-field" htmlFor="ai-base-url">
                <span className="field-label">API base URL</span>
                <input id="ai-base-url" className="text-input" value={config.baseUrl} onChange={(event) => updateConfig({ baseUrl: event.target.value })} spellCheck={false} />
              </label>
            )}
            {isCodexRuntime && (
              <>
                <label className="config-field" htmlFor="ai-endpoint">
                  <span className="field-label">Codex bridge or app-server endpoint</span>
                  <input id="ai-endpoint" className="text-input" value={config.endpoint} onChange={(event) => updateConfig({ endpoint: event.target.value })} spellCheck={false} />
                </label>
                <label className="config-field" htmlFor="ai-bridge-nonce">
                  <span className="field-label">Local bridge nonce</span>
                  <input id="ai-bridge-nonce" className="text-input" value={config.bridgeNonce} onChange={(event) => updateConfig({ bridgeNonce: event.target.value })} placeholder="Paste codex_bridge_nonce printed by the bridge" spellCheck={false} />
                </label>
              </>
            )}
            {profile.runtime === "cli" && (
              <label className="config-field config-field-wide" htmlFor="ai-cli-command">
                <span className="field-label">CLI command template</span>
                <textarea id="ai-cli-command" className="command-input" value={config.cliCommand} onChange={(event) => updateConfig({ cliCommand: event.target.value })} spellCheck={false} />
              </label>
            )}
          </div>
          <p className={configValidation.valid ? "status-line pass" : "status-line error"}>{configValidation.message}</p>
          {isCodexRuntime && <p className={bridgeHealth.status === "ready" && !nonceBlocked ? "status-line pass" : "status-line error"}>{defaultStaticBridgeBlocked ? "Static Pages default bridge is blocked until /health succeeds." : bridgeHealth.message}</p>}
          <ul className="provider-notes">
            {profile.notes.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
        <div className="oauth-panel oauth-panel-wide">
          <h3>{preview.title}</h3>
          <pre>{preview.body}</pre>
          <p>Secrets are represented as environment variable names. Do not paste raw API keys into this browser page.</p>
        </div>
        <div className="oauth-panel">
          <h3>Configuration Controls</h3>
          <p>{state.message}</p>
          <div className="button-row">
            <button className="primary-button" disabled={busy} onClick={saveConfig}>Save Config</button>
            <button className="primary-button" disabled={!isCodexRuntime || !codexEndpointValidation.valid || busy || codexEndpointValidation.kind !== "bridge-http"} onClick={checkBridgeHealth}>Probe Bridge</button>
            <button className="primary-button" disabled={oauthControlsDisabled} onClick={() => checkStatus(false)}>Check Status</button>
            <button className="ghost-button" disabled={oauthControlsDisabled} onClick={() => startLogin("browser")}>Browser OAuth</button>
            <button className="ghost-button" disabled={oauthControlsDisabled} onClick={() => startLogin("device")}>Device Code</button>
            <button className="ghost-button" disabled={oauthControlsDisabled} onClick={() => checkStatus(true)}>Refresh Auth</button>
            <button className="ghost-button" disabled={oauthControlsDisabled} onClick={disconnect}>Logout</button>
            <button className="ghost-button" onClick={resetPanel}>Reset Panel</button>
          </div>
        </div>
        <div className="oauth-panel">
          <h3>Runtime Snapshot</h3>
          <div className="info-row"><span>Provider</span><strong>{profile.label}</strong></div>
          <div className="info-row"><span>Runtime</span><strong>{profile.runtime}</strong></div>
          <div className="info-row"><span>Model</span><strong>{config.model}</strong></div>
          <div className="info-row"><span>Credential</span><strong>{profile.credentialEnvVars.length ? config.keyEnvVar : "No browser secret"}</strong></div>
          <div className="info-row"><span>Last check</span><strong>{state.lastCheckedAt ?? "Not checked"}</strong></div>
          {isCodexRuntime && <div className="info-row"><span>Account</span><strong>{state.accountLabel ?? "Not connected"}</strong></div>}
          {state.authUrl && <a className="source-card compact-link" href={state.authUrl} target="_blank" rel="noreferrer">Open browser OAuth URL</a>}
          {state.verificationUrl && <a className="source-card compact-link" href={state.verificationUrl} target="_blank" rel="noreferrer">Open device verification URL</a>}
          {state.userCode && <p className="device-code">{state.userCode}</p>}
        </div>
        <div className="oauth-panel">
          <h3>Adapter Contract</h3>
          <pre>{`AI config shape:
{
  "provider": "${config.providerId}",
  "model": "${config.model}",
  "credential": "environment variable or CLI session",
  "format": "${config.configFormat}"
}

Codex compatibility:
GET /codex/status
POST /codex/start-oauth { "flow": "browser" | "device" }
POST /codex/refresh
POST /codex/logout
POST /writing/inspiration/extract`}</pre>
          <p>Public Pages deployments must use a localhost or HTTPS bridge for browser-restricted local runtimes.</p>
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
  const [casePrograms, setCasePrograms] = useState<Program[]>([]);
  const [aiConfigState, setAIConfigState] = useState<AIConfigPanelState>({
    status: "unchecked",
    action: "idle",
    message: "No configuration check has run. Save a provider setup before connecting a local runtime.",
    events: [],
  });
  const inspirationFileRefs = useRef<Map<string, File>>(new Map());
  const [inspirationFiles, setInspirationFiles] = useState<InspirationFile[]>([]);
  const [inspirationInsights, setInspirationInsights] = useState<InspirationInsight[]>([]);
  const [approvedInsights, setApprovedInsights] = useState<string[]>([]);
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
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0 });
  }, [activeView]);
  const addCaseProgram = (program: Program) => {
    setCasePrograms((items) => items.some((item) => item.id === program.id) ? items : [...items, program]);
  };
  const toggleCaseProgram = (program: Program) => {
    setCasePrograms((items) => items.some((item) => item.id === program.id) ? items.filter((item) => item.id !== program.id) : [...items, program]);
  };
  const openChecklist = () => {
    addCaseProgram(activeProgram);
    setActiveView("Materials");
  };
  const openWriting = () => {
    addCaseProgram(activeProgram);
    setActiveView("Writing Studio");
  };
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
          <ProgramTable level={level} rows={rows} selected={activeProgram} setSelected={setSelected} catalogue={selectedCatalogue} casePrograms={casePrograms} toggleCaseProgram={toggleCaseProgram} />
          {rows.length ? <Inspector program={activeProgram} openChecklist={openChecklist} inCase={casePrograms.some((item) => item.id === activeProgram.id)} toggleCaseProgram={toggleCaseProgram} /> : <CatalogueInspector catalogue={selectedCatalogue} />}
        </div>
      )}
      {activeView === "Materials" && <MaterialsView program={activeProgram} casePrograms={casePrograms} toggleCaseProgram={toggleCaseProgram} openWriting={openWriting} backToPrograms={() => setActiveView("Programs")} />}
      {activeView === "Writing Studio" && (
        <WritingView
          casePrograms={casePrograms}
          backToChecklist={() => setActiveView("Materials")}
          openPrograms={() => setActiveView("Programs")}
          inspirationFileRefs={inspirationFileRefs}
          inspirationFiles={inspirationFiles}
          setInspirationFiles={setInspirationFiles}
          inspirationInsights={inspirationInsights}
          setInspirationInsights={setInspirationInsights}
          approvedInsights={approvedInsights}
          setApprovedInsights={setApprovedInsights}
        />
      )}
      {activeView === "AI Config" && <AIConfigView state={aiConfigState} setState={setAIConfigState} />}
    </div>
  );
}
