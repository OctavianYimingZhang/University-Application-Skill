export type ProgramLevel = "Undergraduate" | "Postgraduate";
export type SourceStatus = "Verified" | "Catalogue linked" | "Source gap";
export type MaterialStatus = "Complete" | "In Progress" | "Unresolved" | "Not Required";
export type InstitutionGroup = "UK Core" | "US News Top 30" | "Singapore";
export type Region = "United Kingdom" | "United States" | "Singapore";

export interface Requirement {
  category: "Academic" | "Language" | "Fee" | "Document" | "Code";
  label: string;
  value: string;
  sourceUrl: string;
  sourceTitle: string;
}

export interface Program {
  id: string;
  name: string;
  institution?: string;
  group?: InstitutionGroup;
  region?: Region;
  level: ProgramLevel;
  award: string;
  duration: string;
  mode: string;
  year: string;
  sourceUrl: string;
  sourceTitle: string;
  sourceStatus: SourceStatus;
  sourceChecked: string;
  code: string;
  fees: string;
  summary: string;
  hardRequirements: Requirement[];
  documents: string[];
}

export interface MaterialItem {
  id: string;
  name: string;
  scope: string;
  status: MaterialStatus;
  evidence: string;
  check: "Pass" | "Unresolved" | "N/A";
  note: string;
}

export interface NarrativeOption {
  id: string;
  title: string;
  body: string;
  evidence: string[];
  gaps: string[];
}

export interface CatalogueProgramOption {
  id: string;
  name: string;
  level: ProgramLevel;
  award: string;
  url: string;
  note: string;
  duration?: string;
  mode?: string;
  status?: string;
  sourceStatus?: SourceStatus;
}

export interface CatalogueSource {
  level: ProgramLevel;
  label: string;
  url: string;
  coverage: "Complete HTML" | "Paginated HTML" | "Search/API required" | "No degree catalogue" | "Official index";
  note: string;
}

export interface InstitutionCatalogue {
  id: string;
  name: string;
  shortName: string;
  group: InstitutionGroup;
  region: Region;
  rankNote?: string;
  checked: string;
  sources: CatalogueSource[];
  examples: CatalogueProgramOption[];
  programs?: CatalogueProgramOption[];
  extractionNote: string;
  caveat: string;
}
