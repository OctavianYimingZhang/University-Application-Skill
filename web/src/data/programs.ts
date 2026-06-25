import type { Program } from "../types";

const accessed = "2026-06-25";
const ugLanding = "https://www.bmh.manchester.ac.uk/study/biosciences/";
const pgLanding = "https://www.bmh.manchester.ac.uk/study/biosciences/masters/";
const ugDocs = ["UCAS application", "Academic transcript", "English language evidence if required", "Personal statement", "Reference"];
const pgDocs = ["Online application", "Degree transcript", "English language test report if required", "Statement of purpose", "Reference", "CV if requested"];

const ugReq = (url: string) => [
  { category: "Academic" as const, label: "A-level", value: "AAA-AAB incl. specific subjects", sourceUrl: url, sourceTitle: "Programme page" },
  { category: "Academic" as const, label: "IB", value: "35 overall with HL requirements", sourceUrl: url, sourceTitle: "Programme page" },
  { category: "Language" as const, label: "English", value: "See official course page", sourceUrl: url, sourceTitle: "Programme page" },
];

const pgReq = (url: string, degree = "Upper Second honours degree or overseas equivalent") => [
  { category: "Academic" as const, label: "Degree", value: degree, sourceUrl: url, sourceTitle: "Programme page" },
  { category: "Language" as const, label: "IELTS", value: "Usually 6.5 overall; check programme page", sourceUrl: url, sourceTitle: "Programme page" },
  { category: "Language" as const, label: "TOEFL iBT", value: "Usually 90; check component scores", sourceUrl: url, sourceTitle: "Programme page" },
];

function ug(id: string, name: string, url: string, code: string, summary: string): Program {
  return {
    id,
    name: `BSc ${name}`,
    institution: "The University of Manchester",
    group: "UK Core",
    region: "United Kingdom",
    level: "Undergraduate",
    award: "BSc",
    duration: "3 years",
    mode: "Full-time",
    year: "2027 entry",
    sourceUrl: url,
    sourceTitle: "University of Manchester undergraduate course page",
    sourceStatus: "Verified",
    sourceChecked: accessed,
    code,
    fees: "Home fee for 2026 was GBP 9,790; 2027 not yet set",
    summary,
    hardRequirements: ugReq(url),
    documents: ugDocs,
  };
}

function pg(id: string, award: string, name: string, url: string, duration: string, fees: string, summary: string, degree?: string): Program {
  return {
    id,
    name: `${award} ${name}`,
    institution: "The University of Manchester",
    group: "UK Core",
    region: "United Kingdom",
    level: "Postgraduate",
    award,
    duration,
    mode: "Full-time unless official page states otherwise",
    year: "2026 entry",
    sourceUrl: url,
    sourceTitle: "University of Manchester master's course page",
    sourceStatus: "Verified",
    sourceChecked: accessed,
    code: "Direct application",
    fees,
    summary,
    hardRequirements: pgReq(url, degree),
    documents: pgDocs,
  };
}

export const sourcePages = [
  { label: "UG Biosciences landing", url: ugLanding, checked: accessed },
  { label: "PGT Biosciences landing", url: pgLanding, checked: accessed },
  { label: "BSc Genetics detail", url: "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00571/bsc-genetics/", checked: accessed },
  { label: "MSc Biotechnology and Enterprise detail", url: "https://www.manchester.ac.uk/study/masters/courses/list/07778/msc-biotechnology-and-enterprise/", checked: accessed },
];

export const programs: Program[] = [
  ug("bsc-biochemistry", "Biochemistry", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00521/bsc-biochemistry/", "C700", "Explore the chemistry of life through molecular and cellular biochemistry."),
  ug("bsc-biology", "Biology", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00524/bsc-biology/", "C100", "A flexible biological sciences course for broad interests across the field."),
  ug("bsc-biology-science-society", "Biology with Science and Society", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00485/bsc-biology-with-science-and-society/", "C1V3", "Combine biological sciences with social, ethical, and historical perspectives."),
  ug("bsc-biomedical-sciences", "Biomedical Sciences", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00532/bsc-biomedical-sciences/", "B940", "Apply biology-based science to medical research, monitoring, and treatment."),
  ug("bsc-biotechnology", "Biotechnology", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/08662/bsc-biotechnology/", "C560", "Connect biological science, industrial applications, and enterprise skills."),
  ug("bsc-genetics", "Genetics", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00571/bsc-genetics/", "C400", "Study genetic variation, inheritance, molecular genetics, and genome science."),
  ug("bsc-immunology", "Immunology", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/10284/bsc-immunology/", "C550", "Learn the principles and mechanisms of the immune system and disease protection."),
  ug("bsc-life-sciences", "Life Sciences", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00585/bsc-life-sciences/", "C102", "Keep biological sciences options open before transferring to a specialist course."),
  ug("bsc-medical-biochemistry", "Medical Biochemistry", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00602/bsc-medical-biochemistry/", "C724", "Explore the biochemistry of normal and diseased cells and tissues."),
  ug("bsc-medical-physiology", "Medical Physiology", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00643/bsc-medical-physiology/", "B120", "Study how cells, tissues, and organs function in health and disease."),
  ug("bsc-microbiology", "Microbiology", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00609/bsc-microbiology/", "C500", "Study bacteria, viruses, protozoa, fungi, and disease-focused microbiology."),
  ug("bsc-molecular-biology", "Molecular Biology", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00614/bsc-molecular-biology/", "C720", "Study DNA, RNA, proteins, and molecular processes regulating cells."),
  ug("bsc-neuroscience", "Neuroscience", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00617/bsc-neuroscience/", "B140", "Discover how the brain generates behaviour, perception, movement, sleep, and memory."),
  ug("bsc-pharmacology", "Pharmacology", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00634/bsc-pharmacology/", "B210", "Study how drugs act on living systems and produce therapeutic or toxic effects."),
  ug("bsc-zoology", "Zoology", "https://www.manchester.ac.uk/study/undergraduate/courses/2027/00663/bsc-zoology/", "C300", "Study animal behaviour, physiology, evolution, and ecology."),
  pg("msc-biochemistry", "MSc", "Biochemistry", "https://www.manchester.ac.uk/study/masters/courses/list/08171/msc-biochemistry/", "12 months full-time", "UK GBP 15,800; International GBP 37,800", "Gain contemporary biochemistry knowledge at cellular and molecular level.", "Upper Second with average at least 65% in biological or biomedical sciences"),
  pg("msc-bioinformatics-systems-biology", "MSc", "Bioinformatics and Systems Biology", "https://www.manchester.ac.uk/study/masters/courses/list/08854/msc-bioinformatics-and-systems-biology/", "12 months", "UK GBP 16,300; International GBP 37,800", "Integrated programme spanning bioinformatics, genomics, and systems biology.", "Upper Second in biological, medical, physical, computing, or mathematical sciences"),
  pg("msc-biological-sciences", "MSc", "Biological Sciences", "https://www.manchester.ac.uk/study/masters/courses/list/02036/msc-biological-sciences/", "1 year full-time", "UK GBP 15,800; International GBP 37,800", "Research-focused master's with world-class laboratory environments.", "Upper Second with average at least 65% in biological or biomedical sciences"),
  pg("msc-biotechnology-enterprise", "MSc", "Biotechnology and Enterprise", "https://www.manchester.ac.uk/study/masters/courses/list/07778/msc-biotechnology-and-enterprise/", "1 year full-time", "UK GBP 17,300; International GBP 40,400", "Combine bioscience research with entrepreneurial business development.", "Upper Second or overseas equivalent in biological sciences or related subjects"),
  pg("msc-cancer-research-molecular-biomedicine", "MSc", "Cancer Research and Molecular Biomedicine", "https://www.manchester.ac.uk/study/masters/courses/list/08861/msc-cancer-research-and-molecular-biomedicine/", "1 year full-time", "Official page required", "Study cancer research and molecular biomedicine through biosciences training."),
  pg("msc-cell-biology", "MSc", "Cell Biology", "https://www.manchester.ac.uk/study/masters/courses/list/08168/msc-cell-biology/", "12 months full-time", "Official page required", "Research-focused training in cell biology."),
  pg("mres-cognitive-neuroscience", "MRes", "Cognitive Neuroscience and Neuropsychology", "https://www.manchester.ac.uk/study/masters/courses/list/18907/mres-cognitive-neuroscience-and-neuropsychology/", "1 year full-time", "Official page required", "Research training in cognitive neuroscience and neuropsychology."),
  pg("msc-development-biology-stem-cells", "MSc", "Development Biology and Stem Cells", "https://www.manchester.ac.uk/study/masters/courses/list/21620/msc-development-biology-and-stem-cells-research/", "1 year full-time", "Official page required", "Research-focused development biology and stem cell training."),
  pg("mres-experimental-psychology-data-science", "MRes", "Experimental Psychology with Data Science", "https://www.manchester.ac.uk/study/masters/courses/list/18906/mres-experimental-psychology-with-data-science/", "1 year full-time", "Official page required", "Experimental psychology research training with data science."),
  pg("msc-genomic-medicine", "MSc", "Genomic Medicine", "https://www.manchester.ac.uk/study/masters/courses/list/10140/msc-genomic-medicine/", "1 year full-time", "Official page required", "Genomic medicine training for clinical and biomedical applications."),
  pg("ma-history-science-tech-medicine", "MA", "History of Science, Technology and Medicine", "https://www.manchester.ac.uk/study/masters/courses/list/21319/ma-history-of-science-technology-and-medicine/", "1 year full-time", "UK GBP 14,200; International GBP 32,600", "Humanities-led study of science, technology, medicine, and society.", "Upper Second in an appropriate discipline, including humanities or science subjects"),
  pg("msc-immunology", "MSc", "Immunology", "https://www.manchester.ac.uk/study/masters/courses/list/21758/msc-immunology/", "1 year full-time", "UK GBP 15,800; International GBP 37,800", "Gain immunology research experience in laboratory environments.", "Upper Second with average at least 65% in biological or biomedical sciences or immunology-related subject"),
  pg("msc-infection-biology", "MSc", "Infection Biology", "https://www.manchester.ac.uk/study/masters/courses/list/18915/msc-infection-biology/", "1 year", "UK GBP 15,800; International GBP 37,800", "Training for infectious diseases research."),
  pg("msc-medical-molecular-virology", "MSc", "Medical and Molecular Virology", "https://www.manchester.ac.uk/study/masters/courses/list/18112/msc-medical-and-molecular-virology/", "1 year FT or 2 years PT", "UK GBP 16,800; International GBP 38,900", "Understand viruses, diagnostics, bioinformatics, and infection control."),
  pg("msc-nanomedicine", "MSc", "Nanomedicine", "https://www.manchester.ac.uk/study/masters/courses/list/21719/msc-nanomedicine/", "12 months full-time", "UK GBP 15,800; International GBP 37,800", "Study nanomedicine, nanomaterials, and therapeutic applications."),
  pg("msc-neuroimaging", "MSc", "Neuroimaging for Clinical and Cognitive Neuroscience", "https://www.manchester.ac.uk/study/masters/courses/list/09754/msc-neuroimaging-for-clinical-and-cognitive-neuroscience/", "12 months FT", "UK GBP 15,800; International GBP 37,800", "Brain imaging methods for clinical and cognitive neuroscience."),
  pg("msc-neuroscience", "MSc", "Neuroscience", "https://www.manchester.ac.uk/study/masters/courses/list/08173/msc-neuroscience/", "12 months full-time", "UK GBP 15,800; International GBP 37,800", "Research placement and interactive neuroscience teaching.", "Upper Second with average at least 65% in biological or biomedical sciences with neuroscience units"),
  pg("msc-precision-medicine", "MSc", "Precision Medicine", "https://www.manchester.ac.uk/study/masters/courses/list/13018/msc-precision-medicine/", "12 months FT", "UK GBP 16,800; International GBP 39,400", "Training in precision, translational, and stratified medicine."),
  pg("msc-science-health-communication", "MSc", "Science and Health Communication", "https://www.manchester.ac.uk/study/masters/courses/list/18658/msc-science-and-health-communication/", "1 year FT or 2 years PT", "UK GBP 14,200; International GBP 32,600", "Professional skills for science or health communication.", "Upper Second in sciences, engineering, healthcare, social sciences, policy, media, communications, or arts"),
  pg("msc-tissue-engineering-regenerative-medicine", "MSc", "Tissue Engineering for Regenerative Medicine", "https://www.manchester.ac.uk/study/masters/courses/list/18797/msc-tissue-engineering-for-regenerative-medicine/", "12 months full-time", "UK GBP 17,300; International GBP 38,900", "Stem cells, biomaterials, tissue engineering, regenerative medicine, and cell or gene therapies."),
];
