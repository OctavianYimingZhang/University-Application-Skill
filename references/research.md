# Research and Selection Rules

Admissions facts change. Verify current facts before using them.

## Source Hierarchy

Use sources in this order:

1. Official university program pages, department pages, catalog pages, and graduate/undergraduate admissions pages.
2. Official application systems and application guides, such as UCAS, Common App, university portals, or country-specific centralized systems.
3. Official government visa, work authorization, credential, and immigration pages.
4. Official test providers and university equivalency pages for IELTS, TOEFL, PTE, Duolingo, GRE, GMAT, SAT, ACT, AP, IB, A-level, or local exams.
5. Recognized ranking providers only for ranking claims, with year and ranking type stated.
6. Peer-reviewed papers, textbooks, or official academic references for subject-mechanism explanations used in essays.

Do not rely on agent blogs, marketing agencies, influencer posts, forums, social media, Q&A sites, or unsupported traditional medicine claims.

## Verification Standard

For each program-level, application-route, or visa/residence fact, create or update a `SourceEvidence` object and record:

- Source URL.
- Page title or institution.
- Fact supported by that source.
- Date checked.
- Whether the fact is official, ranking-provider, government, test-provider, peer-reviewed, or unverified.
- Staleness period appropriate to the fact. Deadlines, fees, visa rules, and test-score policies should be treated as stale quickly unless the official page gives a cycle-specific date.

If a source cannot verify a fact, write "Needs official check" rather than guessing.

## Ontology-First Research Loop

For every researched candidate:

1. Create or update `Institution`.
2. Create or update `Program`.
3. Resolve the likely `ApplicationSystem` or route.
4. Create an `ApplicationCase` for the applicant-program pair.
5. Convert each requirement into a `RequirementRule`.
6. Attach `SourceEvidence` to every rule.
7. Create `Task` objects for unresolved facts, missing documents, source conflicts, deadline checks, and route checks.
8. Create `RiskFlag` objects for academic, budget, deadline, visa, document, source-conflict, and fit risks.

Do not treat the workbook as the source of truth. It is a view over these objects.

## School Shortlist Logic

Build around 10 schools unless the user asks for another count. Use:

- Reach: academically possible but high competition, ranking, prerequisite, funding, or portfolio risk.
- Target: credible fit with clear evidence, but still competitive.
- Safer: comparatively stronger eligibility or lower risk, not guaranteed admission.

Never claim admission probability as a percentage unless a reliable source directly supports it.

Evaluate each school on:

- Eligibility fit: GPA scale, prerequisite courses, degree background, language, tests, portfolio, work experience, and accreditation.
- Program availability: exact programs in the target field and adjacent fields.
- Budget fit: tuition, living cost signals, scholarships, deposits, and expected total cost.
- Ranking fit: school, subject, domestic, professional, or no ranking requirement.
- City/campus fit: location, campus, commute, climate, lifestyle, industry or research ecosystem.
- Career/research fit: employment path, PhD path, professional accreditation, lab/supervisor fit, internship or placement structure.
- Timing fit: deadlines, rolling admissions, document readiness, visa timing.
- Route complexity: centralized system, direct portal, ranking of choices, counselor flow, post-offer document dependency, residence permit, visa case, or institution-led immigration step.

## Program Drill-Down Logic

After a school is shortlisted:

- Search official department, faculty, school, catalog, and application pages for all relevant programs.
- Include adjacent programs if they satisfy the student's goals, for example computational biology for a biology student with coding evidence.
- Compare exact curriculum, required modules, electives, dissertation/capstone, lab or studio work, placements, accreditation, campus, fees, duration, and entry requirements.
- Identify whether the program is undergraduate, taught, research-based, professional, conversion, pathway, or restricted-entry.
- Explain why each rejected program is rejected.

## Ranking and Country Notes

Always state the ranking source and year. Do not mix university ranking, subject ranking, domestic ranking, and department reputation as if they are the same metric.

Country-specific admissions systems, visa rules, fee status, work rights, and credential requirements must be checked from official pages during the task. Do not assume current rules from memory.

## Route Resolution

Resolve route before final checklists. Common route families include:

- UK undergraduate: UCAS plus program-specific official university checks.
- UK postgraduate: university portal or field-specific centralized route where official evidence confirms it.
- US undergraduate: Common App, Coalition, university portal, or another official route.
- US F/M route: SEVP-approved school, post-offer I-20, SEVIS fee, DS-160, interview, and entry timing as official pages require.
- Canada: institution application, DLI/LOA, province-specific PAL/TAL or CAQ where official rules apply, and study permit route.
- Australia: provider application, CoE, subclass 500 route, and current Genuine Student evidence requirements where official rules apply.
- Germany: direct application, uni-assist, VPD, Hochschulstart, blocked-account or visa/residence route as official rules require.
- Netherlands: Studielink or institutional route, and institution-led residence permit flow where official rules apply.
- Sweden: Universityadmissions.se, ranked choices, application/tuition fee rules, and residence permit route.

If no official source confirms the route for a specific program and applicant profile, set route status to `needs_official_check` and create a blocking route-verification task.
