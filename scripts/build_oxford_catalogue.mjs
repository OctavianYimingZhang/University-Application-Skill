#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "web", "src", "data", "oxfordPrograms.ts");
const CHECKED = new Date().toISOString().slice(0, 10);

const OXFORD_ORIGIN = "https://www.ox.ac.uk";
const UG_REFERER = `${OXFORD_ORIGIN}/admissions/undergraduate/courses/course-listing`;
const PG_REFERER = `${OXFORD_ORIGIN}/admissions/graduate/courses/find-your-course`;
const SORT_QUERY = "sort%5Bsearch_api_relevance%5D%5Bpath%5D=search_api_relevance&sort%5Bsearch_api_relevance%5D%5Bdirection%5D=desc&sort%5Bpage_title%5D%5Bpath%5D=page_title&sort%5Bpage_title%5D%5Bdirection%5D=asc";

const LISTINGS = [
  {
    key: "Undergraduate",
    prefix: "oxford-ug-",
    listingId: 163,
    referer: UG_REFERER,
    note: "Official Oxford undergraduate listing API row",
    expectedMinimum: 50,
  },
  {
    key: "Postgraduate",
    prefix: "oxford-pg-",
    listingId: 3405,
    referer: PG_REFERER,
    note: "Official Oxford graduate listing API row",
    expectedMinimum: 400,
  },
];

const USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";

function tsString(value) {
  return JSON.stringify(value ?? "", null, 0);
}

function slugify(value) {
  return String(value)
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function withPage(url, pageNumber) {
  const separator = url.includes("?") ? "&" : "?";
  return pageNumber === 0 ? url : `${url}${separator}page=${pageNumber}`;
}

function endpoint(listingId) {
  return `${OXFORD_ORIGIN}/api/listing/${listingId}?${SORT_QUERY}`;
}

async function loadPlaywright() {
  const candidates = [
    process.env.PLAYWRIGHT_PACKAGE,
    process.env.PLAYWRIGHT_PACKAGE_PATH,
    "playwright",
  ].filter(Boolean);

  const errors = [];
  for (const candidate of candidates) {
    try {
      if (candidate.startsWith("/") || candidate.startsWith(".")) {
        return await import(pathToFileURL(path.resolve(candidate)).href);
      }
      return await import(candidate);
    } catch (error) {
      errors.push(`${candidate}: ${error.message}`);
    }
  }
  throw new Error(`Could not import Playwright. Set PLAYWRIGHT_PACKAGE to the package entrypoint. Tried: ${errors.join("; ")}`);
}

function chromeExecutable() {
  const candidates = [
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return candidate;
  }
  return undefined;
}

async function fetchListingPage(browser, url, referer) {
  let lastFailure = "";
  for (let attempt = 1; attempt <= 12; attempt += 1) {
    const context = await browser.newContext({ userAgent: USER_AGENT });
    const page = await context.newPage();
    try {
      await page.goto(referer, { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForTimeout(1200 + attempt * 250);
      const result = await page.evaluate(async (targetUrl) => {
        const response = await fetch(targetUrl, {
          credentials: "include",
          headers: { accept: "application/json" },
        });
        return { status: response.status, text: await response.text() };
      }, url);
      const trimmed = (result.text || "").trim();
      if (result.status === 200 && trimmed.startsWith("{")) {
        return JSON.parse(trimmed);
      }
      const blocked = trimmed.includes("cf-mitigated") || trimmed.includes("Just a moment") || trimmed.includes("challenge");
      lastFailure = `status ${result.status}; body ${trimmed.slice(0, 220)}`;
      if (!blocked && result.status !== 403) {
        throw new Error(`Unexpected Oxford response ${lastFailure}`);
      }
    } catch (error) {
      lastFailure = error.message || String(error);
      if (attempt === 12) {
        throw error;
      }
    } finally {
      await context.close().catch(() => {});
    }
    await new Promise((resolve) => setTimeout(resolve, 1300 * attempt));
  }
  throw new Error(`Oxford listing fetch failed for ${url}: ${lastFailure}`);
}

async function fetchListing(browser, config) {
  const first = await fetchListingPage(browser, endpoint(config.listingId), config.referer);
  const total = Number(first?.meta?.count || 0);
  const firstItems = Array.isArray(first.items) ? first.items : [];
  if (!total || !firstItems.length) {
    throw new Error(`Oxford ${config.key} listing returned no count/items`);
  }
  const pageSize = firstItems.length;
  const pageCount = Math.ceil(total / pageSize);
  const items = [...firstItems];

  for (let pageNumber = 1; pageNumber < pageCount; pageNumber += 1) {
    const data = await fetchListingPage(browser, withPage(endpoint(config.listingId), pageNumber), config.referer);
    items.push(...(Array.isArray(data.items) ? data.items : []));
    await new Promise((resolve) => setTimeout(resolve, 650));
  }

  if (items.length !== total) {
    throw new Error(`Oxford ${config.key} listing count mismatch: fetched ${items.length}, meta.count ${total}`);
  }
  if (items.length < config.expectedMinimum) {
    throw new Error(`Oxford ${config.key} listing unexpectedly small: ${items.length}`);
  }
  return items;
}

async function parseItems(page, config, items) {
  const parsed = await page.evaluate(
    ({ rows, level, prefix, note, origin }) => {
      const clean = (value) => String(value || "").replace(/\s+/g, " ").trim();
      const slugifyLocal = (value) => clean(value)
        .toLowerCase()
        .replace(/&/g, " and ")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
      const fieldMap = (root) => {
        const fields = {};
        root.querySelectorAll("dt").forEach((dt) => {
          const label = clean(dt.textContent).replace(/:$/, "");
          const value = clean(dt.nextElementSibling?.textContent || "");
          if (label && value) fields[label] = value;
        });
        return fields;
      };
      const modeFromExpectedLength = (value) => {
        const modes = [];
        if (/Full time/i.test(value)) modes.push("Full time");
        if (/Part time/i.test(value)) modes.push("Part time");
        if (/Variable intensity/i.test(value)) modes.push("Variable intensity");
        return modes.length ? modes.join("; ") : "See official programme page";
      };

      return rows.map((item) => {
        const template = document.createElement("template");
        template.innerHTML = item.markup || "";
        const root = template.content;
        const heading = clean(root.querySelector("h2,h3,h4")?.textContent);
        const anchor = root.querySelector("a[href]");
        const title = heading || clean(anchor?.textContent);
        const href = anchor ? new URL(anchor.getAttribute("href"), origin).href : "";
        const fields = fieldMap(root);
        const allText = clean(root.textContent);
        const beforeTitle = title && allText.includes(title) ? clean(allText.slice(0, allText.indexOf(title)).replace("Graduate", "").replace("Undergraduate", "")) : "";

        const isUndergraduate = level === "Undergraduate";
        const duration = isUndergraduate ? (fields["Course duration"] || "See official programme page") : (fields["Expected length"] || "See official programme page");
        const mode = isUndergraduate ? "Undergraduate" : modeFromExpectedLength(duration);
        const statusParts = isUndergraduate
          ? [
              fields["Entry qualifications"] ? `Entry qualifications: ${fields["Entry qualifications"]}` : "",
              fields["UCAS code"] ? `UCAS: ${fields["UCAS code"]}` : "",
            ]
          : [
              beforeTitle,
              fields["Expected start date"] ? `Expected start date: ${fields["Expected start date"]}` : "",
              fields["English language level"] ? `English language level: ${fields["English language level"]}` : "",
            ];

        const slugSource = href ? new URL(href).pathname : (title || item.id);
        return {
          id: `${prefix}${slugifyLocal(slugSource)}`,
          name: title,
          level,
          award: isUndergraduate ? "Undergraduate" : "Graduate",
          url: href,
          note,
          duration,
          mode,
          status: statusParts.filter(Boolean).join("; "),
        };
      }).filter((row) => row.name && row.url);
    },
    {
      rows: items,
      level: config.key,
      prefix: config.prefix,
      note: config.note,
      origin: OXFORD_ORIGIN,
    },
  );

  const seen = new Set();
  const unique = [];
  for (const row of parsed) {
    let id = row.id || `${config.prefix}${slugify(row.name)}`;
    if (seen.has(id)) id = `${id}-${unique.length}`;
    seen.add(id);
    unique.push({ ...row, id });
  }
  if (unique.length !== items.length) {
    throw new Error(`Oxford ${config.key} parse mismatch: parsed ${unique.length}, fetched ${items.length}`);
  }
  return unique;
}

function renderRows(name, rows) {
  const lines = [`export const ${name}: CatalogueProgramOption[] = [`];
  for (const row of rows) {
    const fields = [
      `id: ${tsString(row.id)}`,
      `name: ${tsString(row.name)}`,
      `level: ${tsString(row.level)}`,
      `award: ${tsString(row.award)}`,
      `url: ${tsString(row.url)}`,
      `note: ${tsString(row.note)}`,
      `duration: ${tsString(row.duration)}`,
      `mode: ${tsString(row.mode)}`,
    ];
    if (row.status) fields.push(`status: ${tsString(row.status)}`);
    lines.push(`  { ${fields.join(", ")} },`);
  }
  lines.push("];");
  return lines.join("\n");
}

function writeOutput(ugRows, pgRows) {
  const output = [
    'import type { CatalogueProgramOption } from "../types";',
    "",
    `export const oxfordCatalogueChecked = ${tsString(CHECKED)};`,
    `export const oxfordUndergraduateCount = ${ugRows.length};`,
    `export const oxfordPostgraduateCount = ${pgRows.length};`,
    "",
    renderRows("oxfordUndergraduatePrograms", ugRows),
    "",
    renderRows("oxfordPostgraduatePrograms", pgRows),
    "",
    "export const oxfordPrograms: CatalogueProgramOption[] = [",
    "  ...oxfordUndergraduatePrograms,",
    "  ...oxfordPostgraduatePrograms,",
    "];",
    "",
  ].join("\n");
  fs.writeFileSync(OUT, output, "utf8");
}

async function main() {
  const playwright = await loadPlaywright();
  const chromium = playwright.chromium || playwright.default?.chromium;
  if (!chromium) {
    throw new Error("Playwright import succeeded, but no chromium launcher was exported");
  }
  const executablePath = chromeExecutable();
  const browser = await chromium.launch({
    headless: process.env.OXFORD_HEADLESS === "0" ? false : true,
    args: ["--disable-blink-features=AutomationControlled"],
    ...(executablePath ? { executablePath } : {}),
  });
  try {
    const parseContext = await browser.newContext({ userAgent: USER_AGENT });
    const page = await parseContext.newPage();
    const [ugConfig, pgConfig] = LISTINGS;
    const ugItems = await fetchListing(browser, ugConfig);
    const ugRows = await parseItems(page, ugConfig, ugItems);
    const pgItems = await fetchListing(browser, pgConfig);
    const pgRows = await parseItems(page, pgConfig, pgItems);
    await parseContext.close();
    writeOutput(ugRows, pgRows);
    console.log(`Wrote ${path.relative(ROOT, OUT)}: ${ugRows.length} UG rows, ${pgRows.length} PG rows`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
