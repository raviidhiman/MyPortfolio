# Content reconciliation (Phase 0 item 4, updated)

Sources compared: the prototype's `const S` data (in `index.html`) vs
`Ravi_Dhiman_Website_Content_and_Profile.docx` (the content source of truth).
Nothing below has been applied to the site yet; that is Phase 2 and needs the confirmations listed.

Legend: **OK** = supported by the content doc. **CONFIRM** = the doc itself says to confirm.
**DECISION** = needs an owner choice. **OMIT** = no source, so it must not be shown.

## Questions from the Phase 0 report that the content doc answers

| Earlier question | Answer from the doc |
|---|---|
| Public email? | `ravidhiman8673@gmail.com` may be shown publicly (doc section 1 and 8). Phone stays hidden. |
| Contact form wanted? | Yes: name, email, message (doc section 8). Placement/styling is still a design choice (see below). |
| Social links | Instagram, GitHub, LinkedIn and the research PDF URL are given verbatim (doc sections 1 and 11). They have not been checked for liveness. |

## Section by section

| Section | Prototype today | Content doc | Status / action |
|---|---|---|---|
| Hero headline | "AI/ML and full-stack developer" | Proposed: "Full-Stack Developer \| Data Analyst \| AI/ML Enthusiast" (editable) | DECISION: keep the prototype wording or adopt the proposed headline. Doc says to confirm display name, headline and location. |
| Location | none | Jind, Haryana, India (confirm before publishing) | CONFIRM. Show nothing until confirmed. |
| About | 2 placeholder items | One intro paragraph (MCA graduate, AI/ML; JS, React, Node, SQL, Python) | OK for "Who I am". "What drives me" has no source; the doc's last sentence (practical, maintainable software; data into insights) could be used. DECISION. Doc forbids stating years of experience or seniority. |
| Skills | 5 tiles: Python, JavaScript, React, SQL & Databases, AI/ML, each with placeholder text | 5 groups (Programming & web; Data & ML; Databases & backend; AI & LLM; Tools & deployment) plus additional areas | Proposal: 5 tiles, one per group, listing only the items named in the doc. **RAG, LangChain, LangGraph are excluded** until Ravi confirms hands-on ability. No proficiency levels are shown. DECISION on the tile layout. |
| Projects | 3 placeholders ("Project One/Two/Three") | 4 suggested featured (Remote Job Market Pipeline, Olist Analytics, ThreadSource, Brain Stroke Risk Prediction), plus Liverr (optional). CV Platform and Medical Shop Inventory are listed with no description. | DECISION: final order and which to feature. No demo URLs exist, so none are shown. CV Platform and Medical Shop: title only, or omit, until descriptions are verified. |
| Project facts | n/a | Olist: "roughly 96.5k delivered orders" (verify); ThreadSource: Razorpay is **test mode** only; Remote Job Pipeline: confirm live status | The 96.5k figure is not displayed until verified. Razorpay is described as test mode. No deployment claims. |
| Experience | 1 placeholder | Labmentix Pvt. Ltd. (remote) Full Stack Web Dev Intern, Jul 2025 to Jan 2026; Sensation Software Solutions Pvt. Ltd. MERN Intern, Jul to Aug 2025. Both marked "confirm". Prior-note tasks (portfolio page, quiz game, snake game) are unconfirmed. | CONFIRM, and note the two date ranges overlap (Jul to Aug 2025), so confirm. No responsibilities are provided, so none are written. DECISION: show role/org/dates flagged, or hold back until confirmed. |
| Education | Degree, Higher Secondary, Certifications (placeholders) | MCA (AI & ML), CRSU Jind, 2024 to 2026, CGPA 8 (confirm). BCA 2019 to 2022, 68%, **institution unknown**. Class XII 2019, 64.8%. Class X 2017, 71.6%. | CGPA CONFIRM. BCA institution CONFIRM, so the field stays empty. **No certifications are in the doc, so that placeholder item is removed.** "Higher Secondary" maps to Class XII/X. |
| Research | "Brain Stroke Risk Prediction ... dissertation work, **not a published paper**" | A publication PDF exists at the IJCSC URL; the dissertation topic is "Comparative Analysis of Machine Learning Algorithms for Brain Stroke Risk Prediction". The doc says not to assume the paper has the same title. | **CONFLICT.** The prototype's "not a published paper" statement contradicts the doc. Plan: two records, (1) dissertation/project, (2) publication with the direct PDF link and unverified metadata marked "to confirm". Title/authors/journal/date will be read from the PDF itself. If I cannot fetch it, I will ask you to upload it. |
| Research focus item | placeholder | Algorithms: Logistic Regression, Random Forest, SVM; evaluation: accuracy, precision, recall, F1, ROC-AUC | OK. Must not be described as a clinical diagnostic tool. |
| Contact | placeholder email/handles | Email, GitHub, LinkedIn, Instagram given; contact form wanted | OK. The mailto row and the 4 social icons use the real values. |
| Admin modal | Mentions Supabase login | Blueprint: Brevo OTP, owner allowlist | Replace the stub text in Phase 5. |

## Open confirmations (owner)

1. Headline wording and public location.
2. MCA final CGPA and exact dates; BCA awarding institution.
3. Are RAG, LangChain, LangGraph hands-on skills? (Default: not listed.)
4. Internship dates and responsibilities; whether the overlapping Jul to Aug 2025 dates are right.
5. Featured project order; any verified live-demo or repository URLs; whether to include Liverr, CV Platform, Medical Shop.
6. Verified KPI numbers for Olist (the 96.5k figure).
7. Research: is the published IJCSC paper the same work as the dissertation? (The PDF should answer this once read.)
8. Show CONFIRM-flagged items publicly (flagged) or hold back until confirmed?

## Design-impact notes for Phase 2

* The 3D world is built from `S.length` (7 sections), so the section set stays fixed. Only the items inside sections change.
* More or fewer items per section is safe: panels and accordions render from the item list.
* Drive Mode sign text comes from `street` and `title`, so those two fields are not edited casually.
* Item text containing `<` or `&` must be escaped when rendered (Phase 9 safe-render helper).
