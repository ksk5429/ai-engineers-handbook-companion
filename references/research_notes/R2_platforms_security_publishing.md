# R2 source register (draft): AI risk and security, schemas, Firebase, ebook publishing

- Researcher: R2. Access date for every source: **2026-11-09**.
- Method: each page was fetched live (WebFetch, or curl / GitHub API for raw text). Quotes are verbatim, at most 25 words.
- Quote provenance: **[raw]** = I read the quote in the raw text myself (NIST PDF text, pandoc manual HTML, GitHub API JSON, npm registry JSON). Unmarked quotes came through the fetch tool's extraction layer, which returns quoted page text; spot-check them before print. **[paraphrase]** = the tool's summary, not page text.
- Labels: **V** = verified on the primary page. **I** = my inference. **UNVERIFIED** = not established, with the reason.
- When a page shows no date, the entry says "no date shown". Google support articles and Firebase docs pages showed no last-updated date in the fetched text.

---

## R-001 NIST AI 600-1, Generative AI Profile

- **Title:** "Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile"
- **Publisher / authors:** NIST (U.S. Department of Commerce). Chloe Autio, Reva Schwartz, Jesse Dunietz, Shomik Jain, Martin Stanley, Elham Tabassi, Patrick Hall, Kamie Roberts.
- **URL:** https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence ; PDF https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
- **DOI:** 10.6028/NIST.AI.600-1. **Report:** NIST AI 600-1 (series "NIST Trustworthy and Responsible AI").
- **Published:** July 26, 2024 (the PDF cover reads "July 2024"). **Version:** 600-1, original edition. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. Scope: "a cross-sectoral profile of and companion resource for the AI Risk Management Framework (AI RMF 1.0) for Generative AI".
  2. Its legal hook: "pursuant to President Biden's Executive Order (EO) 14110".
  3. The list's purpose [raw]: "a set of risks unique to or exacerbated by the development and use of GAI are defined below."
  4. The 12 risk names, exactly as numbered in Section 2 [raw]:
     1. CBRN Information or Capabilities
     2. Confabulation
     3. Dangerous, Violent, or Hateful Content
     4. Data Privacy
     5. Environmental Impacts
     6. Harmful Bias or Homogenization
     7. Human-AI Configuration
     8. Information Integrity
     9. Information Security
     10. Intellectual Property
     11. Obscene, Degrading, and/or Abusive Content
     12. Value Chain and Component Integration
  5. Confabulation [raw]: "The production of confidently stated but erroneous or false content (known colloquially as 'hallucinations' or 'fabrications')".
  6. Information Security [raw]: "Lowered barriers for offensive cyber capabilities, including via automated discovery and exploitation of vulnerabilities".
  7. Evidence-based scope [raw]: "speculative risks that may potentially arise in more advanced, future GAI systems are not considered."
  8. Footnote 6 [raw]: the terms "hallucination" and "fabrication" "anthropomorphize GAI, which itself is a risk related to GAI systems".
- **Caveats:**
  - EO 14110 was revoked in January 2025 (I, not checked on a primary page this session). The document itself has not been withdrawn. The NIST AI RMF hub page states: "The AI RMF 1.0 is being revised as part of the White House AI Action Plan." It names no 600-1 revision.
  - Footnote 5 groups the 12 risks into three families. In that footnote, risk 3 appears as "Dangerous or Violent Recommendations" and risk 5 as "Environmental". Cite the Section 2 names, not the footnote's.

## R-002 OWASP Top 10 for LLM Applications 2025

- **Title:** "OWASP Top 10 for LLM Applications 2025" (the site title is "OWASP Top 10 for LLMs and Gen AI Apps").
- **Publisher:** OWASP GenAI Security Project.
- **URL:** https://genai.owasp.org/llm-top-10/ ; resource page https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/
- **Released:** November 17, 2024. **Edition:** 2025, still the latest; the site mentions no 2026 Top 10. **License:** site-wide statement: "all content on the site is Creative Commons Attribution-ShareAlike v4.0." **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. The full list: LLM01:2025 Prompt Injection; LLM02:2025 Sensitive Information Disclosure; LLM03:2025 Supply Chain; LLM04:2025 Data and Model Poisoning; LLM05:2025 Improper Output Handling; LLM06:2025 Excessive Agency; LLM07:2025 System Prompt Leakage; LLM08:2025 Vector and Embedding Weaknesses; LLM09:2025 Misinformation; LLM10:2025 Unbounded Consumption.
  2. **LLM01:2025 Prompt Injection** (https://genai.owasp.org/llmrisk/llm01-prompt-injection/): "A Prompt Injection Vulnerability occurs when user prompts alter the LLM's behavior or output in unintended ways."
  3. Indirect injection: "Indirect prompt injections occur when an LLM accepts input from external sources, such as websites or files."
  4. Limits of defence: RAG and fine-tuning "do not fully mitigate prompt injection vulnerabilities"; "it is unclear if there are fool-proof methods of prevention for prompt injection".
  5. **LLM05:2025 Improper Output Handling** (https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/): "insufficient validation, sanitization, and handling of the outputs". Mitigation: "Treat the model as any other user, adopting a zero-trust approach."
  6. **LLM06:2025 Excessive Agency** (https://genai.owasp.org/llmrisk/llm062025-excessive-agency/): "the vulnerability that enables damaging actions to be performed in response to unexpected, ambiguous or manipulated outputs from an LLM."
  7. Root causes: "excessive functionality", "excessive permissions", "excessive autonomy". Mitigation: "require a human to approve high-impact actions before they are taken."
- **Caveats:**
  - The URL slugs are inconsistent (`llm01-prompt-injection` against `llm052025-...`). Copy the URLs exactly.
  - The 2023-24 list used different names (for example "Insecure Output Handling"); 2025 renamed it "Improper Output Handling" (I, from the renamed entry; the old list was not re-fetched).
  - Improper Output Handling examples (XSS, SQL injection, remote code execution via shell/eval) are [paraphrase] of the page.

## R-003 JSON Schema 2020-12 (Core and Validation) and RFC 8259

- **Titles:**
  - "JSON Schema: A Media Type for Describing JSON Documents" (draft-bhutton-json-schema-01).
  - "JSON Schema Validation: A Vocabulary for Structural Validation of JSON" (draft-bhutton-json-schema-validation-01).
- **Publisher / editors:** json-schema.org; A. Wright, H. Andrews, B. Hutton (Eds.), plus G. Dennis on Core.
- **URL:** https://json-schema.org/specification ; https://json-schema.org/draft/2020-12/json-schema-core ; https://json-schema.org/draft/2020-12/json-schema-validation
- **Version:** 2020-12 ("The current version is 2020-12!"; previous 2019-09). **Document date:** 16 June 2022 (the -01 drafts are the published texts of 2020-12). **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. Core: JSON Schema is "a JSON-based format for describing the structure of JSON data."
  2. Core overview: "JSON Schema uses keywords to assert constraints on JSON instances or annotate those instances with additional information."
  3. Validation §3: "JSON Schema validation asserts constraints on the structure of instance data."
  4. Validation §7.1: "Structural validation alone may be insufficient to allow an application to correctly utilize certain values."
  5. `format` is annotation-only by default: format evaluation options "MUST be disabled by default" (§7.2.1). The text also recommends "performing semantic validation in the application, which is the recommended best practice."
  6. **Handbook point (I):** passing schema validation proves shape, not truth. A valid LLM JSON output can still be wrong, and `format` (email, date) is not even checked unless the validator enables it.
- **RFC 8259:** "The JavaScript Object Notation (JSON) Data Interchange Format", T. Bray, Ed., December 2017, Internet Standard **STD 90**; obsoletes RFC 7159. URL https://www.rfc-editor.org/rfc/rfc8259
  1. "JavaScript Object Notation (JSON) is a lightweight, text-based, language-independent data interchange format."
  2. §2: "A JSON text is a serialized value."
  3. §8.1: JSON "exchanged between systems that are not part of a closed ecosystem MUST be encoded using UTF-8".
- **Caveats:**
  - The specification page gives no release date for 2020-12 itself. Cite "2020-12 (draft-bhutton-...-01, 16 June 2022)".
  - The §7.2.1 quote about format being disabled sits in a paragraph whose exact scope (format-annotation versus format-assertion) I saw only through the extraction layer. Re-read §7.2 before quoting it in print.

## R-004 Firebase: rules unit testing, Emulator Suite, pricing, server-side bypass

### R-004a Test your Cloud Firestore Security Rules (emulator)
- **URL:** https://firebase.google.com/docs/firestore/security/test-rules-emulator . **Publisher:** Google (Firebase docs). **Date:** no date shown. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. Package: `@firebase/rules-unit-testing`. The page states: "We recommend the v9 testing library." It also says: "For backwards compatibility, we continue to make the v8 testing library available."
  2. API names on the page: `initializeTestEnvironment`, `RulesTestEnvironment.authenticatedContext`, `.unauthenticatedContext`, `.withSecurityRulesDisabled`, `assertSucceeds`, `assertFails`.
  3. Without a rules file, "the emulator treats all projects as having open rules."
  4. "The Cloud Firestore emulator does not work with the normal Firebase Authentication flow."
  5. "The emulator automatically creates any instance that is accessed."
  6. The server bypass, on this page: "The server client libraries bypass all Cloud Firestore Security Rules".
- **npm registry** (https://registry.npmjs.org/@firebase/rules-unit-testing/latest) [raw]: version **6.0.0**; description "A set of utilities useful for testing Security Rules with the Realtime Database or Cloud Firestore emulators."; peerDependency `firebase` "^13.0.0"; engines `node` ">=24.12.0".

### R-004b Firebase Local Emulator Suite (overview + install)
- **URLs:** https://firebase.google.com/docs/emulator-suite ; https://firebase.google.com/docs/emulator-suite/install_and_configure . No date shown. **Accessed:** 2026-11-09.
  1. "The Firebase Local Emulator Suite is a set of advanced tools for developers looking to build and test apps locally".
  2. Emulated products: Cloud Firestore, Realtime Database, Cloud Storage for Firebase, Authentication, Firebase Hosting, Cloud Functions (beta), Pub/Sub (beta), Firebase Extensions (beta) [paraphrase of list].
  3. Emulators are "built for accuracy, not performance or security, and are not appropriate to use in production."
  4. Prerequisites: "Node.js version 16.0 or higher."; "JDK version 11 or higher."; "CLI version 8.14.0 or higher".
  5. Commands: `firebase init emulators`, `firebase emulators:start`, `firebase emulators:exec <scriptpath>`.

### R-004c Rules apply to client SDKs; server/Admin SDKs bypass them
- https://firebase.google.com/docs/firestore/security/get-started (no date): "Every database request from a Cloud Firestore mobile/web client library is evaluated against your security rules before reading or writing any data." Also: server client libraries "bypass all Cloud Firestore Security Rules and instead authenticate through" Google Application Default Credentials; "make sure to set up Identity and Access Management (IAM) for Cloud Firestore."
- https://firebase.google.com/docs/database/admin/start (no date): the Admin SDK app "has access to read and write all data, regardless of Security Rules." Limited privileges via `databaseAuthVariableOverride`.
- https://firebase.google.com/docs/admin/setup (no date): "Read and write Realtime Database data with full admin privileges."
- Firebase Blog, "7 tips on Firebase security rules and the Admin SDK", Hiranya Jayathilaka and Rachel Myers, March 14, 2019, https://firebase.blog/posts/2019/03/firebase-security-rules-admin-sdk-tips/ : "requests from the Firebase Admin SDK are not gated by rules."

### R-004d Firebase pricing plans
- **URL:** https://firebase.google.com/pricing . No date shown. **Accessed:** 2026-11-09.
  1. "No-cost (Spark plan)": "Generous no-cost usage limits", "No payment method needed".
  2. "Pay as you go (Blaze plan)": "Access more services and higher usage levels".
  3. Blaze includes Spark quotas: "No-cost usage from Spark plan included"; "No-cost usage on Blaze plan is calculated daily."
- **Caveats (R-004):**
  - "v9 testing library" on the docs page names the API generation (modular SDK era), while npm's current package version is 6.0.0. Do not write "rules-unit-testing v9" as a package version (I).
  - The Firestore pages say "server client libraries", not "Admin SDK"; the explicit Admin SDK wording is on the Realtime Database page and the 2019 blog. For Firestore, write "server client libraries (including the Admin SDK) bypass rules; use IAM" (I, consistent with all four sources).
  - The emulator page's JDK 11 floor may lag newer CLI releases (I; recent firebase-tools releases are reported to need a newer JDK, not checked this session).
  - The pricing page does not mention budget alerts or the exact Spark quotas; check the per-product quota table before printing numbers.

## R-005 Google Play Books Partner Center publishing requirements

All articles: Google, "Play Books Partner Center Help", support.google.com/books/partner. No dates shown. **Accessed:** 2026-11-09.

### R-005a "Book file guidelines", https://support.google.com/books/partner/answer/3424254?hl=en
  1. Formats: "Ebook content files: .epub, .pdf." "Cover files: .jpeg, .png, .tiff, .pdf."
  2. Size and length: "Each file must be less than 2 GB. This limit includes cover image files." "The book should be at least 4 pages long."
  3. Cover: "Cover files must have a minimum resolution of 640 pixels. The maximum height and width are 7,200 pixels."
  4. EPUB: "The .epub file must contain the front cover image." "The .epub file must include the complete book." "The .epub file must be validated by EpubCheck."
  5. PDF: "The .pdf file can't be password-protected." "Do not upload sample content such as an excerpt." For a PDF table of contents, "include bookmarks in the .pdf file."
  6. Naming: "Name the .epub files using the electronic ISBN." "Name your .pdf files using the print ISBN." "Don't use 10-digit or 13-digit numbers as these can be confused with ISBNs."

### R-005b "EPUB files", https://support.google.com/books/partner/answer/3316879?hl=en
  1. "Google Play Books accepts EPUB3.3,EPUB 3 and EPUB 2, though 3.3 is preferred."
  2. Validation: "An additional step you should take is to run the EpubCheck tool, a tool to validate EPUB files". It also advises opening files first in "an eReader program such as Adobe Digital Editions."
  3. "Google Play Books doesn't support non-standard audio or video tags" (the sentence continues: or JavaScript interactivity). The page's EPUB 3 table marks JavaScript unsupported.
  4. "Google Play Books supports fixed layout in EPUB 2 and EPUB 3 files."
  5. Errors: these "will appear in your Partner Center account under the Content tab for the book."
  6. Images: static GIF, JPEG, PNG, SVG; SVG max width or height 3200 [paraphrase].
  7. PDF plus EPUB: "We recommend that you send us both PDF and EPUB files for your books."

### R-005c "ISBNs", https://support.google.com/books/partner/answer/3431108?hl=en
  1. "An ISBN isn't required to submit a book to Google Books or to sell a book on Google Play."
  2. "We assign a unique identifier with the prefix GGKEY to any book that doesn't already have one."
  3. "GGKEYs are only used internally within Google."
  4. An ISBN is "issued by an ISBN registration agency" (the page gives no purchase steps).

### R-005d "Quickstart guide to add a new book", https://support.google.com/books/partner/answer/9261664?hl=en
  1. Flow: Book Catalog → "Add Book" → Book ID (GGKEY or ISBN/EAN) → Book info → Content → Pricing → Review → Publish [paraphrase of the steps].
  2. "You have to add a title in order to publish your book." "Books need at least one genre for publication."
  3. "In the Pricing tab, set the prices to sell your book."
  4. "The book will be published within 24 hours."
  5. "We don't require content for a book to be available for pre-orders."

### R-005e "Upload & update files", https://support.google.com/books/partner/answer/14173419?hl=en
  1. "You can't delete a file. You can upload a new file to replace the previous one."
  2. "Users who downloaded the old version must re-download the book to get the new version."
  3. "The content or cover doesn't process until you submit all the expected files."

### R-005f "Publisher Content Policies for Google Play Books", https://support.google.com/books/partner/answer/1067634?hl=en
  1. "To review content on Google Play Books, we use a combination of automated and human evaluation."
  2. "We prohibit content that is spammy, misleading, provides a poor user experience or contains malware."
  3. "Multiple versions of the same Book confuse our users and provide little distinguishing value."
  4. Metadata "that is confusingly similar to existing books" is prohibited.
  5. **AI disclosure:** the words "AI" and "artificial intelligence" do not appear on the page (fetch tool's report). See Not verified.
- **Caveats (R-005):**
  - "Minimum resolution of 640 pixels" does not say which dimension (shortest side, height?). Ask Partner Center support or test-upload.
  - "Must be validated by EpubCheck" (file guidelines) is stronger than "an additional step you should take" (EPUB files page). Treat EPUBCheck-clean as mandatory.
  - The EPUB files page links EpubCheck at github.com/IDPF/epubcheck, an outdated location; the current repository is github.com/w3c/epubcheck (R-006).
  - The naming rules assume an ISBN, yet the ISBN is optional. Books without one use their GGKEY as Book ID; that the filename then uses the GGKEY is my inference (I) from the article's phrase "If your books have ISBNs or GGKEYs".
  - The fetch tool rendered the filename examples as `_ISBN_.epub` and `_ISBN__frontcover.jpg`. These are probably italic placeholders, meaning `<ISBN>.epub` and `<ISBN>_frontcover.jpg` (I); confirm on the live page.
  - Not fetched: "Add a single book" (answer/3289675), "PDF file configuration" (answer/107073), Partner Center sign-up and payment or tax setup.

## R-006 EPUBCheck and EPUB 3.3 / 3.4

- **EPUBCheck:** W3C (releases made "by the DAISY Consortium for W3C"). https://github.com/w3c/epubcheck . **Accessed:** 2026-11-09.
  1. Latest release [raw, GitHub API]: **v5.4.0**, published **2026-09-15T08:42:40Z**. Prior: v5.3.0 (2025-09-01), v5.2.1 (2025-01-14).
  2. README [raw]: "EPUBCheck is the official conformance checker for EPUB publications."
  3. README [raw]: v5.4.0 is "to be used to validate both EPUB 2 and 3 files. EPUB 3 publications are checked against the EPUB 3.4 specification."
  4. Release notes [raw]: "It can be used to check conformance to the latest EPUB 3.4 W3C Candidate Recommendation." Also on Maven Central as `org.w3c:epubcheck`.
  5. README [raw]: "EPUBCheck can be run as a standalone command-line tool or used as a Java library." Wiki usage: `java -jar epubcheck.jar file.epub`.
  6. Java: pom.xml sets `<java.version>1.8</java.version>` [raw], so the jar targets Java 8 bytecode. The **runtime requirement is I: Java 8 or later.** The wiki "Running" page is stale ("Java (1.6 or above, 1.7+ recommended)"). The README states only a build requirement ("JDK 1.7 or above").
- **EPUB 3.3:** W3C, eds. Matt Garrish (DAISY), Ivan Herman (W3C). https://www.w3.org/TR/epub-33/ ; history https://www.w3.org/standards/history/epub-33/
  1. First W3C Recommendation **25 May 2023**. Later Recommendation republications: 17 Oct 2024, 7 Jan 2025, 27 Mar 2025, 13 Jan 2026.
  2. The current dated version reads "W3C Recommendation 13 January 2026" (https://www.w3.org/TR/2026/REC-epub-33-20260113/).
- **EPUB 3.4:** https://www.w3.org/TR/epub-34/ : "W3C Candidate Recommendation Draft 02 November 2026". Not a Recommendation.
- **Caveat:** Cite EPUB 3.3 as "W3C Recommendation, 25 May 2023 (latest revision 13 January 2026)". I did not check what changed in the republications.

## R-007 Pandoc User's Guide: EPUB

- **Title:** "Pandoc User's Guide". **Author:** John MacFarlane. **URL:** https://pandoc.org/MANUAL.html . The page shows no version or date. Latest pandoc release [raw, GitHub API jgm/pandoc]: **3.13**, published 2026-10-26. **Accessed:** 2026-11-09.
- **Verified facts (V) [raw]:**
  1. Output formats: "epub or epub3 (EPUB v3 book)" and "epub2 (EPUB v2)". So `-t epub` means EPUB 3.
  2. `--toc`: "Include an automatically generated table of contents". It "has no effect unless -s/--standalone is used". EPUB output is standalone by nature (I).
  3. `--epub-cover-image=FILE`: "Use the specified image as the EPUB cover. It is recommended that the image be less than 1000px in width and height."
  4. `--split-level`: "Specify the heading level at which to split an EPUB or chunked HTML document into separate files." `--epub-chapter-level` is a "Deprecated synonym".
  5. Default metadata: `<dc:title>`, `<dc:creator>`, `<dc:date>`, `<dc:language>` ("from the lang variable, or, if it is not set, the locale"), and `<dc:identifier id="BookId">` ("a randomly generated UUID").
  6. YAML fields recognized: identifier, title, creator, contributor, date, lang (legacy: language), subject, description, type, format, relation, coverage, rights, belongs-to-collection, group-position, cover-image, css (legacy: stylesheet), page-progression-direction, accessModes, accessModeSufficient, accessibilityHazards, … , ibooks.
  7. Field definitions: `lang`: "A string value in BCP 47 format." `rights`: "A string value." `cover-image`: "A string value (path to cover image)."
  8. `identifier` schemes include "ISBN-13" and "DOI". Example: `text: 'urn:isbn:9780000000000'`.
- **Caveats:**
  - The pandoc cover advice ("less than 1000px") conflicts with the Google Play cover rule (minimum 640 px, maximum 7,200 px). See Conflicts.
  - Without an `identifier`, pandoc writes a random UUID, so each build gets a new identifier unless the YAML pins one (I).

## R-008 Python 3.12 docs: unittest, hashlib

- `unittest` — Unit testing framework: https://docs.python.org/3.12/library/unittest.html (page shows "Python 3.12.16 documentation"). "The unittest unit testing framework was originally inspired by JUnit".
- `hashlib` — Secure hashes and message digests: https://docs.python.org/3.12/library/hashlib.html (3.12.16). "This module implements a common interface to many different secure hash and message digest algorithms." `hashlib.file_digest(fileobj, digest, /)`: "Added in version 3.11." Guaranteed constructors include `sha256` [paraphrase of list].
- Status (https://www.python.org/downloads/, accessed 2026-11-09): 3.12 is **security**-only (first released 2023-10-02, end of support 2028-10). The current stable release is 3.15 (3.15.2; 3.15 first released 2026-10-09). 3.14 is in bugfix.

---

## Conflicts and open questions

1. **Cover size: pandoc against Google Play.** Pandoc recommends a cover "less than 1000px"; Play requires at least 640 px and at most 7,200 px. Both fit at 640 to 999 px, but the side that the 640 px minimum applies to is unstated. Recommendation: produce one cover file inside 640 to 999 px, unless the Partner Center cover article (not found) says otherwise.
2. **EPUBCheck: mandatory or advised?** The file guidelines say "must be validated"; the EPUB files page says "should". Treat it as a release gate.
3. **EPUB version target.** Play prefers EPUB 3.3. EPUBCheck 5.4.0 checks EPUB 3 against the 3.4 Candidate Recommendation Draft and flags 3.4 "outdated" features (NCX, guide) as USAGE messages. A 3.3 file should still pass with no errors (I). Run it and report USAGE separately from ERROR and WARNING.
4. **ISBN-based naming when no ISBN exists.** The ISBN is optional, but the naming rules assume one. Open: does a GGKEY book name its files `<GGKEY>.epub`? The quickstart lets you upload in the Content tab of an existing book, which makes naming matter less for single uploads (I).
5. **Firebase "v9" against npm 6.0.0.** The docs say "v9 testing library", while the npm package is 6.0.0 and needs `firebase@^13` and Node ≥24.12. The book should pin real package versions, not the docs' "v9" label.
6. **Firestore wording.** The official Firestore docs say "server client libraries", not "Admin SDK". The explicit Admin SDK statements come from the Realtime Database docs and a 2019 blog post.
7. **NIST risk names.** Section 2 and footnote 5 differ for risks 3 and 5. Use the Section 2 names.
8. **EO 14110.** The profile cites an executive order that has since been revoked (I). The book should say "issued under EO 14110 (since revoked); the profile remains published", after checking a primary source on the revocation.

## Not verified

- **Google Play Books AI-generated content disclosure: UNVERIFIED.** The fetched Publisher Content Policies page contains no "AI" or "artificial intelligence" wording. A web search found only Google Play's *app* AI-Generated Content policy (support.google.com/googleplay/android-developer/answer/14094294), which concerns apps, not books. I found no Partner Center disclosure field or rule. Absence on one page does not prove there is no rule: check the Partner Center UI and Google's latest policy updates before publishing.
- **Dedicated Play Books cover-image article:** not located. Cover rules here come from "Book file guidelines" only.
- **Play Books account onboarding** (payments profile, tax, territories, revenue split): not fetched.
- **"PDF file configuration"** (answer/107073) and **"Add a single book"** (answer/3289675): linked but not fetched.
- **EPUBCheck minimum Java runtime:** not stated on any primary page; Java 8+ is inferred from pom.xml.
- **EPUB 3.3 republication changes** (2024 to 2026): dates verified, content of changes not.
- **Pandoc manual version:** the page shows none; 3.13 is the latest release on GitHub, not a statement on the manual page.
- **JSON Schema successor:** whether json-schema.org has announced a post-2020-12 stable release was not checked beyond the specification page, which still says 2020-12 is current.
- **Exact Spark/Blaze quotas** (Firestore reads/writes per day and so on): not recorded.
- **EO 14110 revocation:** stated from background knowledge (I); not fetched this session.
