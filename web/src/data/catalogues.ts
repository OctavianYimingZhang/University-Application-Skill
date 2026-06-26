import type { CatalogueProgramOption, InstitutionCatalogue, InstitutionGroup, Program, ProgramLevel, Region } from "../types";
import { cambridgeCatalogueChecked, cambridgePrograms } from "./cambridgePrograms";

const checked = "2026-06-25";

const docsByLevel: Record<ProgramLevel, string[]> = {
  Undergraduate: ["Application form", "Academic transcript", "English language evidence if required", "Personal statement or essays", "Reference or school report"],
  Postgraduate: ["Application form", "Degree transcript", "English language evidence if required", "Statement of purpose", "Reference", "CV or resume if requested", "Research proposal if required"],
};

const regionFee: Record<Region, string> = {
  "United Kingdom": "Programme fee published on official course page",
  "United States": "Tuition and cost of attendance published by institution",
  Singapore: "Programme fee published by university admissions or Registrar office",
};

const regionLanguage: Record<Region, string> = {
  "United Kingdom": "IELTS/TOEFL/PTE requirements vary by programme",
  "United States": "TOEFL/IELTS/Duolingo policies vary by school and applicant background",
  Singapore: "English requirements vary by qualification and programme",
};

function option(id: string, level: ProgramLevel, name: string, award: string, url: string, note = "Official programme page"): CatalogueProgramOption {
  return { id, level, name, award, url, note };
}

function source(level: ProgramLevel, label: string, url: string, coverage: InstitutionCatalogue["sources"][number]["coverage"], note: string) {
  return { level, label, url, coverage, note };
}

export const institutionCatalogues: InstitutionCatalogue[] = [
  {
    id: "oxford",
    name: "University of Oxford",
    shortName: "Oxford",
    group: "UK Core",
    region: "United Kingdom",
    checked,
    sources: [
      source("Undergraduate", "Undergraduate courses A-Z", "https://www.ox.ac.uk/admissions/undergraduate/courses/course-listing", "Complete HTML", "UG course names and URLs are exposed in the official A-Z page."),
      source("Postgraduate", "Graduate course search", "https://www.ox.ac.uk/admissions/graduate/courses/find-your-course", "Search/API required", "Official search tool; automated clients may hit Cloudflare and must use browser/API handling."),
    ],
    examples: [
      option("oxford-ug-biochemistry", "Undergraduate", "Biochemistry (Molecular and Cellular)", "BA", "https://www.ox.ac.uk/admissions/undergraduate/courses/course-listing/biochemistry-molecular-and-cellular"),
      option("oxford-ug-computer-science", "Undergraduate", "Computer Science", "BA", "https://www.ox.ac.uk/admissions/undergraduate/courses/course-listing/computer-science"),
      option("oxford-pg-advanced-computer-science", "Postgraduate", "Advanced Computer Science", "MSc", "https://www.ox.ac.uk/admissions/graduate/courses/msc-advanced-computer-science"),
      option("oxford-pg-computer-science", "Postgraduate", "Computer Science", "DPhil", "https://www.ox.ac.uk/admissions/graduate/courses/dphil-computer-science"),
    ],
    extractionNote: "Use the UG A-Z list directly; use the official graduate search with taught/research filters for PG.",
    caveat: "PG search output is tool dependent; do not infer a complete PG list from isolated detail pages.",
  },
  {
    id: "cambridge",
    name: "University of Cambridge",
    shortName: "Cambridge",
    group: "UK Core",
    region: "United Kingdom",
    checked: cambridgeCatalogueChecked,
    sources: [
      source("Undergraduate", "Undergraduate courses", "https://www.undergraduate.study.cam.ac.uk/courses", "Complete HTML", "Course names and links are exposed in one official page."),
      source("Postgraduate", "Postgraduate course directory", "https://www.postgraduate.study.cam.ac.uk/courses", "Paginated HTML", "Official Drupal Views directory; crawl pagination and taught/research filters."),
    ],
    examples: [
      option("cambridge-ug-computer-science", "Undergraduate", "Computer Science", "BA (Hons) and MEng", "https://www.undergraduate.study.cam.ac.uk/courses/computer-science-ba-hons-meng"),
      option("cambridge-ug-engineering", "Undergraduate", "Engineering", "BA (Hons) and MEng", "https://www.undergraduate.study.cam.ac.uk/courses/engineering-ba-hons-meng"),
      option("cambridge-pg-advanced-computer-science", "Postgraduate", "Advanced Computer Science", "MPhil", "https://www.postgraduate.study.cam.ac.uk/courses/directory/cscsmpacs"),
      option("cambridge-pg-2d-materials", "Postgraduate", "2D Materials of Tomorrow", "PhD", "https://www.postgraduate.study.cam.ac.uk/courses/directory/egegpdtwo"),
    ],
    programs: cambridgePrograms,
    extractionNote: "Official Cambridge catalogue rows loaded: 33 undergraduate courses and 359 postgraduate directory rows.",
    caveat: "Some PG entries are closed for the current cycle; status is preserved from the official directory row.",
  },
  {
    id: "imperial",
    name: "Imperial College London",
    shortName: "Imperial",
    group: "UK Core",
    region: "United Kingdom",
    checked,
    sources: [
      source("Undergraduate", "Undergraduate course search", "https://www.imperial.ac.uk/study/courses/?courseType=Undergraduate", "Paginated HTML", "Official course cards are server-rendered and paginated."),
      source("Postgraduate", "Postgraduate taught course search", "https://www.imperial.ac.uk/study/courses/?courseType=Postgraduate%20taught", "Paginated HTML", "Official PGT cards are server-rendered and paginated."),
      source("Postgraduate", "Doctoral route guidance", "https://www.imperial.ac.uk/study/apply/postgraduate-doctoral/application-process/choose-course/", "Official index", "Doctoral discovery is route/project based rather than a complete central degree list."),
    ],
    examples: [
      option("imperial-ug-aeronautical-engineering", "Undergraduate", "Aeronautical Engineering", "MEng", "https://www.imperial.ac.uk/study/courses/undergraduate/2027/aeronautical-engineering/"),
      option("imperial-ug-biochemistry", "Undergraduate", "Biochemistry", "BSc", "https://www.imperial.ac.uk/study/courses/undergraduate/2027/biochemistry-bsc/"),
      option("imperial-pg-advanced-computing", "Postgraduate", "Advanced Computing", "MSc", "https://www.imperial.ac.uk/study/courses/postgraduate-taught/2026/advanced-computing/"),
      option("imperial-pg-advanced-aeronautical", "Postgraduate", "Advanced Aeronautical Engineering", "MSc", "https://www.imperial.ac.uk/study/courses/postgraduate-taught/2026/advanced-aeronautical-engineering/"),
    ],
    extractionNote: "Use courseType query values exactly and crawl pagination.",
    caveat: "Doctoral programmes should be modelled as route/project discovery unless Imperial publishes a central doctoral catalogue.",
  },
  {
    id: "ucl",
    name: "UCL",
    shortName: "UCL",
    group: "UK Core",
    region: "United Kingdom",
    checked,
    sources: [
      source("Undergraduate", "Undergraduate degrees", "https://www.ucl.ac.uk/prospective-students/undergraduate/degrees", "Complete HTML", "Result anchors expose UG degree names and links."),
      source("Postgraduate", "Graduate taught degrees", "https://www.ucl.ac.uk/prospective-students/graduate/taught-degrees", "Complete HTML", "Taught degree anchors are exposed in HTML."),
      source("Postgraduate", "Graduate research degrees", "https://www.ucl.ac.uk/prospective-students/graduate/research-degrees", "Complete HTML", "Research degree anchors are exposed in HTML."),
    ],
    examples: [
      option("ucl-ug-anthropology", "Undergraduate", "Anthropology", "BSc", "https://www.ucl.ac.uk/prospective-students/undergraduate/degrees/anthropology-bsc-2026"),
      option("ucl-ug-biochemistry", "Undergraduate", "Biochemistry", "BSc", "https://www.ucl.ac.uk/prospective-students/undergraduate/degrees/biochemistry-bsc-2026"),
      option("ucl-pg-advanced-audiology", "Postgraduate", "Advanced Audiology", "MSc", "https://www.ucl.ac.uk/prospective-students/graduate/taught-degrees/advanced-audiology-msc"),
      option("ucl-pg-anthropology", "Postgraduate", "Anthropology", "MPhil/PhD", "https://www.ucl.ac.uk/prospective-students/graduate/research-degrees/anthropology-mphil-phd"),
    ],
    extractionNote: "Parse anchors under UG, taught PG, and research PG catalogue paths.",
    caveat: "Keep taught and research postgraduate entries as separate programme types.",
  },
  {
    id: "lse",
    name: "London School of Economics and Political Science",
    shortName: "LSE",
    group: "UK Core",
    region: "United Kingdom",
    checked,
    sources: [
      source("Undergraduate", "Programme search", "https://www.lse.ac.uk/programmes/search-courses", "Search/API required", "Search page embeds a partial first batch; full UG list requires pagination/search."),
      source("Postgraduate", "Graduate available programmes", "https://www.lse.ac.uk/study-at-lse/Graduate/Available-programmes", "Complete HTML", "Graduate availability page exposes programme links and status columns."),
    ],
    examples: [
      option("lse-ug-accounting-finance", "Undergraduate", "Accounting and Finance", "BSc", "https://www.lse.ac.uk/study-at-lse/undergraduate/bsc-accounting-and-finance"),
      option("lse-ug-economics", "Undergraduate", "Economics", "BSc", "https://www.lse.ac.uk/study-at-lse/undergraduate/bsc-economics"),
      option("lse-pg-data-science", "Postgraduate", "Data Science", "MSc", "https://www.lse.ac.uk/study-at-lse/graduate/msc-data-science"),
      option("lse-pg-computational-social-science", "Postgraduate", "Computational Social Science", "MPhil/PhD", "https://www.lse.ac.uk/study-at-lse/graduate/mphilphd-computational-social-science"),
    ],
    extractionNote: "Use the programme search for UG and the graduate availability table for PG.",
    caveat: "Graduate link text can include programme codes; preserve codes separately before display cleanup.",
  },
  {
    id: "lbs",
    name: "London Business School",
    shortName: "LBS",
    group: "UK Core",
    region: "United Kingdom",
    checked,
    sources: [
      source("Undergraduate", "No undergraduate degree catalogue", "https://www.london.edu/about/london-business-school/programmes", "No degree catalogue", "LBS does not publish an undergraduate degree catalogue."),
      source("Postgraduate", "Masters degrees", "https://www.london.edu/masters-degrees", "Complete HTML", "Masters portfolio links are exposed in official HTML."),
      source("Postgraduate", "PhD programme", "https://www.london.edu/phd", "Official index", "PhD and subject-area doctoral pages are official."),
    ],
    examples: [
      option("lbs-pg-mim", "Postgraduate", "Masters in Management", "MSc", "https://www.london.edu/masters-degrees/masters-in-management"),
      option("lbs-pg-mfa", "Postgraduate", "Masters in Financial Analysis", "MSc", "https://www.london.edu/masters-degrees/masters-in-financial-analysis"),
      option("lbs-pg-mba", "Postgraduate", "MBA", "MBA", "https://www.london.edu/masters-degrees/mba"),
      option("lbs-pg-finance-phd", "Postgraduate", "Finance", "PhD", "https://www.london.edu/faculty-and-research/finance/phd-programme"),
    ],
    extractionNote: "Classify degree programmes separately from executive education, online short courses, and summer school.",
    caveat: "No undergraduate degree options are listed for LBS.",
  },
  {
    id: "kcl",
    name: "King's College London",
    shortName: "KCL",
    group: "UK Core",
    region: "United Kingdom",
    checked,
    sources: [
      source("Undergraduate", "Undergraduate courses", "https://www.kcl.ac.uk/study/undergraduate/courses", "Search/API required", "Static HTML exposes a first batch; full coverage needs Contensis/browser execution."),
      source("Postgraduate", "Postgraduate taught A-Z", "https://www.kcl.ac.uk/study/postgraduate-taught/postgraduate-taught-courses-a-z", "Search/API required", "Static HTML is incomplete without app/API data."),
      source("Postgraduate", "Postgraduate research areas", "https://www.kcl.ac.uk/study/postgraduate-research/areas", "Search/API required", "Official PGR area index; full extraction needs app/API data."),
    ],
    examples: [
      option("kcl-ug-accounting-finance", "Undergraduate", "Accounting & Finance", "BSc", "https://www.kcl.ac.uk/study/undergraduate/courses/accounting-finance-bsc"),
      option("kcl-ug-ai", "Undergraduate", "Artificial Intelligence", "BSc", "https://www.kcl.ac.uk/study/undergraduate/courses/artificial-intelligence-bsc"),
      option("kcl-pg-advanced-computing", "Postgraduate", "Advanced Computing", "MSc", "https://www.kcl.ac.uk/study/postgraduate-taught/courses/advanced-computing-msc"),
      option("kcl-pg-neuroscience", "Postgraduate", "Basic & Clinical Neuroscience", "MPhil/PhD", "https://www.kcl.ac.uk/study/postgraduate-research/areas/basic-and-clinical-neuroscience-mdres-mphil-phd"),
    ],
    extractionNote: "Use official catalogue entry points; full extraction likely needs browser-context JS or authorised Contensis feed access.",
    caveat: "Do not treat static HTML alone as complete KCL coverage.",
  },
  {
    id: "manchester",
    name: "The University of Manchester",
    shortName: "Manchester",
    group: "UK Core",
    region: "United Kingdom",
    checked,
    sources: [
      source("Undergraduate", "Undergraduate courses 2026", "https://www.manchester.ac.uk/study/undergraduate/courses/2026/", "Complete HTML", "Official `/xml/` fragment contains all UG rows."),
      source("Postgraduate", "Masters courses", "https://www.manchester.ac.uk/study/masters/courses/list/", "Complete HTML", "Official `/xml/` fragment contains all masters rows."),
      source("Postgraduate", "Postgraduate research programmes", "https://www.manchester.ac.uk/study/postgraduate-research/programmes/list/", "Complete HTML", "Official `/xml/` fragment contains all PGR rows."),
    ],
    examples: [
      option("manchester-ug-accounting", "Undergraduate", "Accounting", "BSc", "https://www.manchester.ac.uk/study/undergraduate/courses/2026/07808/bsc-accounting/"),
      option("manchester-ug-aerospace", "Undergraduate", "Aerospace Engineering", "BEng", "https://www.manchester.ac.uk/study/undergraduate/courses/2026/03333/beng-aerospace-engineering/"),
      option("manchester-pg-advanced-cs", "Postgraduate", "Advanced Computer Science", "MSc", "https://www.manchester.ac.uk/study/masters/courses/list/21573/msc-advanced-computer-science/"),
      option("manchester-pgr-accounting-finance", "Postgraduate", "Accounting and Finance", "PhD", "https://www.manchester.ac.uk/study/postgraduate-research/programmes/list/19378/phd-accounting-and-finance/"),
    ],
    extractionNote: "Fetch each catalogue `/xml/` fragment and resolve course links against the parent URL.",
    caveat: "UG path is entry-year-specific and must be refreshed when Manchester rolls the catalogue year.",
  },
  {
    id: "warwick",
    name: "University of Warwick",
    shortName: "Warwick",
    group: "UK Core",
    region: "United Kingdom",
    checked,
    sources: [
      source("Undergraduate", "Undergraduate courses", "https://warwick.ac.uk/study/undergraduate/courses/", "Search/API required", "UG list is available through the official SiteBuilder2 data-entry JSON API."),
      source("Postgraduate", "Postgraduate courses", "https://warwick.ac.uk/study/postgraduate/courses/", "Complete HTML", "PG programme cards are exposed in the official page HTML."),
    ],
    examples: [
      option("warwick-ug-accounting-finance", "Undergraduate", "Accounting and Finance", "BSc", "https://warwick.ac.uk/study/undergraduate/courses/bsc-accounting-finance"),
      option("warwick-ug-biochemistry", "Undergraduate", "Biochemistry", "BSc", "https://warwick.ac.uk/study/undergraduate/courses/bsc-biochemistry"),
      option("warwick-pg-biomedical-engineering", "Postgraduate", "Biomedical Engineering", "MSc", "https://warwick.ac.uk/study/postgraduate/courses/msc-biomedical-engineering"),
      option("warwick-pg-business-management", "Postgraduate", "Business and Management", "MRes/PhD", "https://warwick.ac.uk/study/postgraduate/courses/mres-phd-business-management"),
    ],
    extractionNote: "For UG, use Warwick SiteBuilder2 API and exclude hidden entries.",
    caveat: "PG combines taught and research cards; preserve tags from source.",
  },
  {
    id: "edinburgh",
    name: "The University of Edinburgh",
    shortName: "Edinburgh",
    group: "UK Core",
    region: "United Kingdom",
    checked,
    sources: [
      source("Undergraduate", "Undergraduate A-Z", "https://study.ed.ac.uk/programmes/undergraduate-a-z", "Complete HTML", "Degree Finder rows are server-rendered."),
      source("Postgraduate", "Postgraduate taught A-Z", "https://study.ed.ac.uk/programmes/postgraduate-taught-a-z", "Complete HTML", "Degree Finder rows are server-rendered."),
      source("Postgraduate", "Postgraduate research A-Z", "https://study.ed.ac.uk/programmes/postgraduate-research-a-z", "Complete HTML", "Degree Finder rows are server-rendered."),
    ],
    examples: [
      option("edinburgh-ug-accounting-finance", "Undergraduate", "Accounting and Finance", "MA (Hons)", "https://study.ed.ac.uk/programmes/undergraduate/464-accounting-and-finance"),
      option("edinburgh-ug-applied-math", "Undergraduate", "Applied Mathematics", "BSc (Hons)", "https://study.ed.ac.uk/programmes/undergraduate/429-applied-mathematics"),
      option("edinburgh-pg-ai-business", "Postgraduate", "AI for Business", "MSc", "https://study.ed.ac.uk/programmes/postgraduate-taught/1138-ai-for-business"),
      option("edinburgh-pgr-agriculture-food-security", "Postgraduate", "Agriculture and Food Security", "PhD/MScR", "https://study.ed.ac.uk/programmes/postgraduate-research/957-agriculture-and-food-security"),
    ],
    extractionNote: "Parse Degree Finder Drupal view rows under each A-Z page.",
    caveat: "Use study.ed.ac.uk Degree Finder rather than older www.ed.ac.uk study pages.",
  },
];

const usTop: Array<[string, string, string, string, string, string, string, string]> = [
  ["princeton", "Princeton University", "Princeton", "Undergraduate fields of study", "https://ua.princeton.edu/fields-study", "Graduate fields of study", "https://gradschool.princeton.edu/academics/degrees-requirements/fields-study", "US News 2026 top-30 cutoff source list"],
  ["mit", "Massachusetts Institute of Technology", "MIT", "MIT degree charts", "https://catalog.mit.edu/degree-charts/#undergraduatedegreestextcontainer", "MIT degree charts", "https://catalog.mit.edu/degree-charts/#graduatedegreestextcontainer", "US News 2026 top-30 cutoff source list"],
  ["harvard", "Harvard University", "Harvard", "Harvard Program Browser", "https://www.harvard.edu/programs/?degree_levels=undergraduate", "Harvard Program Browser", "https://www.harvard.edu/programs/?degree_levels=graduate", "US News 2026 top-30 cutoff source list"],
  ["stanford", "Stanford University", "Stanford", "Stanford Bulletin programs", "https://bulletin.stanford.edu/programs", "Stanford Bulletin programs", "https://bulletin.stanford.edu/programs", "US News 2026 top-30 cutoff source list"],
  ["yale", "Yale University", "Yale", "Yale College majors", "https://catalog.yale.edu/ycps/majors-in-yale-college/", "GSAS degree-granting departments and programs", "https://catalog.yale.edu/gsas/degree-granting-departments-programs/", "US News 2026 top-30 cutoff source list"],
  ["uchicago", "University of Chicago", "UChicago", "College programs of study", "http://collegecatalog.uchicago.edu/thecollege/programsofstudy/", "Graduate Announcements", "http://graduateannouncements.uchicago.edu/", "US News 2026 top-30 cutoff source list"],
  ["jhu", "Johns Hopkins University", "Johns Hopkins", "Program Explorer", "https://e-catalogue.jhu.edu/programs/", "Program Explorer", "https://e-catalogue.jhu.edu/programs/", "US News 2026 top-30 cutoff source list"],
  ["penn", "University of Pennsylvania", "Penn", "Undergraduate programs", "https://catalog.upenn.edu/undergraduate/programs/", "Graduate programs", "https://catalog.upenn.edu/graduate/programs/", "US News 2026 top-30 cutoff source list"],
  ["caltech", "California Institute of Technology", "Caltech", "Areas of Study and Research", "https://catalog.caltech.edu/current/areas-of-study-and-research/", "Areas of Study and Research", "https://catalog.caltech.edu/current/areas-of-study-and-research/", "US News 2026 top-30 cutoff source list"],
  ["duke", "Duke University", "Duke", "Undergraduate Instruction Bulletin", "https://undergraduate.bulletins.duke.edu/", "Duke bulletins index", "https://registrar.duke.edu/bulletins/", "US News 2026 top-30 cutoff source list"],
  ["northwestern", "Northwestern University", "Northwestern", "Undergraduate Programs A-Z", "https://catalogs.northwestern.edu/undergraduate/programs-az/", "Graduate Degree Programs", "https://www.northwestern.edu/academics/graduate-a-to-z.html", "US News 2026 top-30 cutoff source list"],
  ["brown", "Brown University", "Brown", "Undergraduate concentrations", "https://bulletin.brown.edu/the-college/concentrations/", "Graduate Program Finder", "https://graduateprograms.brown.edu/", "US News 2026 top-30 cutoff source list"],
  ["vanderbilt", "Vanderbilt University", "Vanderbilt", "Undergraduate 2026-27 catalogue", "https://www.vanderbilt.edu/catalogs/kuali/undergraduate-26-27.php", "Registrar catalog index", "https://registrar.vanderbilt.edu/catalogs/", "US News 2026 top-30 cutoff source list"],
  ["cornell", "Cornell University", "Cornell", "Courses of Study programs", "https://courses.cornell.edu/programs/#Undergraduate_Programs", "Courses of Study graduate and professional programs", "https://courses.cornell.edu/programs/#Graduate_Research_Programs", "US News 2026 top-30 cutoff source list"],
  ["rice", "Rice University", "Rice", "Programs of Study", "https://ga.rice.edu/programs-study/", "Graduate degree chart", "https://ga.rice.edu/graduate-students/academic-opportunities/degree-chart/", "US News 2026 top-30 cutoff source list"],
  ["wustl", "Washington University in St. Louis", "WashU", "Programs of Study", "https://bulletin.wustl.edu/programs/", "Programs of Study", "https://bulletin.wustl.edu/programs/", "US News 2026 top-30 cutoff source list"],
  ["dartmouth", "Dartmouth College", "Dartmouth", "ORC undergraduate departments/programs", "https://dartmouth.smartcatalogiq.com/en/current/orc/departments-programs-undergraduate", "ORC graduate departments/programs", "https://dartmouth.smartcatalogiq.com/en/current/orc/departments-programs-graduate", "US News 2026 top-30 cutoff source list"],
  ["columbia", "Columbia University", "Columbia", "Columbia College departments/programs", "https://bulletin.columbia.edu/columbia-college/departments-instruction/", "Areas of Study", "https://www.columbia.edu/content/academics/areas-study", "US News 2026 top-30 cutoff source list"],
  ["notre-dame", "University of Notre Dame", "Notre Dame", "Academic Programs", "https://catalog.nd.edu/programs/", "Graduate School degree programs", "https://graduateschool.nd.edu/degree-programs/", "US News 2026 top-30 cutoff source list"],
  ["berkeley", "University of California, Berkeley", "UC Berkeley", "Undergraduate Catalog programs", "https://undergraduate.catalog.berkeley.edu/programs", "Graduate Catalog programs", "https://graduate.catalog.berkeley.edu/programs", "US News 2026 top-30 cutoff source list"],
  ["ucla", "University of California, Los Angeles", "UCLA", "Departments, Programs, and Freestanding Minors", "https://registrar.ucla.edu/academics/departments-programs-and-freestanding-minors", "Graduate Programs A-Z", "https://grad.ucla.edu/programs/", "US News 2026 top-30 cutoff source list"],
  ["cmu", "Carnegie Mellon University", "Carnegie Mellon", "Degrees Offered", "http://coursecatalog.web.cmu.edu/degreesoffered/", "Graduate Degrees", "http://coursecatalog.web.cmu.edu/degreesoffered/graduate-degrees/", "US News 2026 top-30 cutoff source list"],
  ["emory", "Emory University", "Emory", "Emory College majors and minors", "https://catalog.college.emory.edu/academics/concentrations/index.html", "Laney degree programs", "https://gs.emory.edu/degree-programs/index.html", "US News 2026 top-30 cutoff source list"],
  ["georgetown", "Georgetown University", "Georgetown", "Schools and Programs", "https://bulletin.georgetown.edu/schools-programs/", "Graduate Programs", "https://grad.georgetown.edu/programs/", "US News 2026 top-30 cutoff source list"],
  ["umich", "University of Michigan Ann Arbor", "Michigan", "Undergraduate majors", "https://admissions.umich.edu/academics-majors/majors-degrees", "Graduate programs", "https://rackham.umich.edu/programs-of-study/", "US News 2026 top-30 cutoff source list"],
  ["unc", "University of North Carolina at Chapel Hill", "UNC", "Undergraduate programs of study", "https://catalog.unc.edu/undergraduate/programs-study/", "Graduate catalog", "https://catalog.unc.edu/graduate/", "US News 2026 top-30 cutoff source list"],
  ["uva", "University of Virginia", "UVA", "Undergraduate programs", "https://records.ureg.virginia.edu/content.php?catoid=72&navoid=6706", "Graduate Record 2026-2027", "https://records.ureg.virginia.edu/index.php?catoid=73", "US News 2026 top-30 cutoff source list"],
  ["usc", "University of Southern California", "USC", "Undergraduate Education", "https://catalogue.usc.edu/content.php?catoid=21&navoid=8858", "Graduate Degree Programs", "https://catalogue.usc.edu/content.php?catoid=21&navoid=8600", "US News 2026 top-30 cutoff source list"],
  ["ucsd", "University of California, San Diego", "UC San Diego", "Undergraduate majors", "https://admissions.ucsd.edu/why/majors/index.html", "Graduate programs", "https://grad.ucsd.edu/programs/", "US News 2026 top-30 cutoff source list"],
  ["uf", "University of Florida", "Florida", "Undergraduate majors", "https://catalog.ufl.edu/UGRD/majors/", "Graduate majors by college", "https://gradcatalog.ufl.edu/graduate/programs-college/", "US News 2026 rank-30 tie included"],
  ["ut-austin", "University of Texas at Austin", "UT Austin", "Undergraduate degree programs", "https://catalog.utexas.edu/undergraduate/the-university/degree-programs/", "Graduate degree programs", "https://catalog.utexas.edu/graduate/graduate-study/degree-programs/", "US News 2026 rank-30 tie included"],
];

export const usAndSingaporeCatalogues: InstitutionCatalogue[] = [
  ...usTop.map(([id, name, shortName, ugLabel, ugUrl, pgLabel, pgUrl, rankNote]) => ({
    id,
    name,
    shortName,
    group: "US News Top 30" as InstitutionGroup,
    region: "United States" as Region,
    rankNote,
    checked,
    sources: [
      source("Undergraduate", ugLabel, ugUrl, "Official index", "Official undergraduate programme catalogue or admissions major index."),
      source("Postgraduate", pgLabel, pgUrl, "Official index", "Official graduate/professional programme catalogue or graduate school programme index."),
    ],
    examples: [
      option(`${id}-ug-catalogue`, "Undergraduate", `${shortName} undergraduate programme catalogue`, "UG", ugUrl, "Open official UG programme index"),
      option(`${id}-pg-catalogue`, "Postgraduate", `${shortName} postgraduate programme catalogue`, "Graduate", pgUrl, "Open official graduate programme index"),
    ],
    extractionNote: "Coverage is implemented through official catalogue/index entry points; individual hard requirements must be read from the relevant programme page.",
    caveat: "U.S. institutions distribute requirements across schools, departments, and admissions offices; the app marks unsupported details as source gaps.",
  })),
  {
    id: "nus",
    name: "National University of Singapore",
    shortName: "NUS",
    group: "Singapore",
    region: "Singapore",
    rankNote: "Singapore expansion requested by user",
    checked,
    sources: [
      source("Undergraduate", "Undergraduate programmes", "https://www.nus.edu.sg/oam/undergraduate-programmes", "Official index", "Official NUS undergraduate programme index."),
      source("Postgraduate", "Postgraduate programme portal", "https://study.nus.edu.sg/programme", "Search/API required", "Official NUS postgraduate programme portal with public Salesforce-backed search."),
    ],
    examples: [
      option("nus-ug-programmes", "Undergraduate", "NUS undergraduate programme catalogue", "UG", "https://www.nus.edu.sg/oam/undergraduate-programmes", "Open official UG programme index"),
      option("nus-pg-programmes", "Postgraduate", "NUS postgraduate programme catalogue", "Graduate", "https://study.nus.edu.sg/programme", "Open official postgraduate programme portal"),
    ],
    extractionNote: "Use official NUS admissions and Registrar programme pages, then follow faculty-specific requirement pages.",
    caveat: "Faculty programme pages may carry separate eligibility, English, and fee details.",
  },
  {
    id: "ntu",
    name: "Nanyang Technological University",
    shortName: "NTU",
    group: "Singapore",
    region: "Singapore",
    rankNote: "Singapore expansion requested by user",
    checked,
    sources: [
      source("Undergraduate", "Degree programmes", "https://www.ntu.edu.sg/education/degree-programmes", "Official index", "Official NTU central degree programme index."),
      source("Postgraduate", "Graduate College programmes", "https://www.ntu.edu.sg/graduate-college/admissions/programme/graduate-programmes", "Official index", "Official NTU Graduate College programme listing."),
    ],
    examples: [
      option("ntu-ug-programmes", "Undergraduate", "NTU undergraduate programme catalogue", "UG", "https://www.ntu.edu.sg/education/degree-programmes", "Open official central degree programme index"),
      option("ntu-pg-programmes", "Postgraduate", "NTU graduate programme catalogue", "Graduate", "https://www.ntu.edu.sg/graduate-college/admissions/programme/graduate-programmes", "Open official graduate programme listing"),
    ],
    extractionNote: "Use official NTU admissions programme pages and follow college/school detail links.",
    caveat: "NTU graduate taught/research route details are often school-specific.",
  },
];

export const allInstitutionCatalogues = [...institutionCatalogues, ...usAndSingaporeCatalogues];

export const groups: InstitutionGroup[] = ["UK Core", "US News Top 30", "Singapore"];

export function programFromCatalogueOption(catalogue: InstitutionCatalogue, item: CatalogueProgramOption): Program {
  const sourceStatus = item.sourceStatus ?? (item.note.startsWith("Open official") ? "Catalogue linked" : "Verified");
  const duration = item.duration ?? "See official programme page";
  const mode = item.mode ?? "See official programme page";
  const status = item.status && item.status !== "Open in official directory" && !item.note.includes(item.status)
    ? ` ${item.status}.`
    : "";
  return {
    id: item.id,
    name: item.name,
    institution: catalogue.name,
    group: catalogue.group,
    region: catalogue.region,
    level: item.level,
    award: item.award,
    duration,
    mode,
    year: "Current official catalogue",
    sourceUrl: item.url,
    sourceTitle: item.note,
    sourceStatus,
    sourceChecked: catalogue.checked,
    code: item.award,
    fees: regionFee[catalogue.region],
    summary: `${item.name} at ${catalogue.name}. ${item.note}.${status}`,
    hardRequirements: [
      { category: "Academic", label: "Academic", value: "See official programme page", sourceUrl: item.url, sourceTitle: item.note },
      { category: "Language", label: "English", value: regionLanguage[catalogue.region], sourceUrl: item.url, sourceTitle: item.note },
      { category: "Fee", label: "Fees", value: regionFee[catalogue.region], sourceUrl: item.url, sourceTitle: item.note },
    ],
    documents: docsByLevel[item.level],
  };
}
