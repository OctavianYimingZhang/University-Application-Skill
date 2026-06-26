import type { CatalogueProgramOption } from "../types";

export const lbsCatalogueChecked = "2026-06-26";
export const lbsUndergraduateCount = 0;
export const lbsMastersCount = 10;
export const lbsResearchCount = 7;

export const lbsMastersPrograms: CatalogueProgramOption[] = [
  { id: "lbs-pg-masters-in-management", name: "Masters in Management", level: "Postgraduate", award: "Master's degree", url: "https://www.london.edu/masters-degrees/masters-in-management", note: "Official London Business School masters degree page", duration: "See official programme page", mode: "Taught" },
  { id: "lbs-pg-global-masters-in-management", name: "Global Masters in Management", level: "Postgraduate", award: "Master's degree", url: "https://www.london.edu/masters-degrees/global-masters-in-management", note: "Official London Business School masters degree page", duration: "See official programme page", mode: "Taught" },
  { id: "lbs-pg-masters-in-financial-analysis", name: "Masters in Financial Analysis", level: "Postgraduate", award: "Master's degree", url: "https://www.london.edu/masters-degrees/masters-in-financial-analysis", note: "Official London Business School masters degree page", duration: "See official programme page", mode: "Taught" },
  { id: "lbs-pg-masters-in-analytics-and-management", name: "Masters in Analytics and Management", level: "Postgraduate", award: "Master's degree", url: "https://www.london.edu/masters-degrees/masters-in-analytics-and-management", note: "Official London Business School masters degree page", duration: "See official programme page", mode: "Taught" },
  { id: "lbs-pg-mba", name: "MBA", level: "Postgraduate", award: "MBA", url: "https://www.london.edu/masters-degrees/mba", note: "Official London Business School MBA degree page", duration: "See official programme page", mode: "Taught" },
  { id: "lbs-pg-one-year-mba", name: "One-year MBA", level: "Postgraduate", award: "MBA", url: "https://www.london.edu/masters-degrees/one-year-mba", note: "Official London Business School MBA degree page", duration: "See official programme page", mode: "Taught" },
  { id: "lbs-pg-masters-in-finance-full-time", name: "Masters in Finance Full-time", level: "Postgraduate", award: "Master's degree", url: "https://www.london.edu/masters-degrees/masters-in-finance-full-time", note: "Official London Business School masters degree page", duration: "See official programme page", mode: "Taught" },
  { id: "lbs-pg-masters-in-finance-part-time", name: "Masters in Finance Part-time", level: "Postgraduate", award: "Master's degree", url: "https://www.london.edu/masters-degrees/masters-in-finance-part-time", note: "Official London Business School masters degree page", duration: "See official programme page", mode: "Taught" },
  { id: "lbs-pg-executive-mba", name: "Executive MBA", level: "Postgraduate", award: "MBA", url: "https://www.london.edu/masters-degrees/executive-mba", note: "Official London Business School Executive MBA degree page", duration: "See official programme page", mode: "Taught" },
  { id: "lbs-pg-sloan-masters-in-leadership-and-strategy", name: "Sloan Masters in Leadership and Strategy", level: "Postgraduate", award: "Master's degree", url: "https://www.london.edu/masters-degrees/sloan-masters-in-leadership-and-strategy", note: "Official London Business School masters degree page", duration: "See official programme page", mode: "Taught" },
];

export const lbsResearchPrograms: CatalogueProgramOption[] = [
  { id: "lbs-pgr-accounting", name: "Accounting", level: "Postgraduate", award: "PhD", url: "https://www.london.edu/faculty-and-research/accounting/phd-programme", note: "Official London Business School PhD subject-area page", duration: "See official programme page", mode: "Research" },
  { id: "lbs-pgr-economics", name: "Economics", level: "Postgraduate", award: "PhD", url: "https://www.london.edu/faculty-and-research/economics/phd-programme", note: "Official London Business School PhD subject-area page", duration: "See official programme page", mode: "Research" },
  { id: "lbs-pgr-finance", name: "Finance", level: "Postgraduate", award: "PhD", url: "https://www.london.edu/faculty-and-research/finance/phd-programme", note: "Official London Business School PhD subject-area page", duration: "See official programme page", mode: "Research" },
  { id: "lbs-pgr-management-science-and-operations", name: "Management Science and Operations", level: "Postgraduate", award: "PhD", url: "https://www.london.edu/faculty-and-research/management-science-and-operations/phd-programme", note: "Official London Business School PhD subject-area page", duration: "See official programme page", mode: "Research" },
  { id: "lbs-pgr-marketing", name: "Marketing", level: "Postgraduate", award: "PhD", url: "https://www.london.edu/faculty-and-research/marketing/phd-programme", note: "Official London Business School PhD subject-area page", duration: "See official programme page", mode: "Research" },
  { id: "lbs-pgr-organisational-behaviour", name: "Organisational Behaviour", level: "Postgraduate", award: "PhD", url: "https://www.london.edu/faculty-and-research/organisational-behaviour/phd-programme", note: "Official London Business School PhD subject-area page", duration: "See official programme page", mode: "Research" },
  { id: "lbs-pgr-strategy-and-entrepreneurship", name: "Strategy and Entrepreneurship", level: "Postgraduate", award: "PhD", url: "https://www.london.edu/faculty-and-research/strategy-and-entrepreneurship/phd-programme", note: "Official London Business School PhD subject-area page", duration: "See official programme page", mode: "Research" },
];

export const lbsPrograms: CatalogueProgramOption[] = [
  ...lbsMastersPrograms,
  ...lbsResearchPrograms,
];
