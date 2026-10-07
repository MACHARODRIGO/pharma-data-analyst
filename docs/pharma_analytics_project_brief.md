# Pharmacovigilance Risk Analytics — Pastela Pharmaceuticals

End-to-end data analyst portfolio project (Python, SQL, Tableau) simulating a pharmacovigilance risk-analytics workflow for a fictional pharma company. Covers SQL extraction, data cleaning, statistical inference, and ML (logistic regression & decision trees) to predict adverse drug event risk, with results exported for Tableau.
*Portfolio exercise. Pastela Pharmaceuticals, all people, emails, and events
described below are fictitious and were created for pedagogical purposes.*

---

## Background on the Pastela Pharmaceuticals scenario

Congratulations on your new role as a **Data Analyst** on Pastela
Pharmaceuticals' internal **Data & Analytics** team!

Pastela Pharmaceuticals is a mid-size pharmaceutical company that manufactures
and distributes prescription medications across cardiology, oncology,
endocrinology, and infectious disease. Like every pharma manufacturer, Pastela
is legally required to monitor the safety of its products after they reach
patients — a discipline called **pharmacovigilance**. The internal
Pharmacovigilance (Drug Safety) department is responsible for collecting,
investigating, and reporting adverse drug reactions.

The Data & Analytics team has been asked to help the Pharmacovigilance
department move from *reactive* case review (waiting for an adverse event to
be reported, then investigating it) to *proactive* risk monitoring: using the
treatment and patient data Pastela already has to flag which currently active
treatments are statistically most likely to produce an adverse event, so
safety staff can prioritize outreach and monitoring before something happens.

**Note:** This project's dataset was synthetically generated for pedagogical
purposes and does not describe any real patient, physician, or medication
event.

---

## Team members at Pastela Pharmaceuticals

| Name | Role | Email | Team |
|---|---|---|---|
| Marta Fields | Director of Data & Analytics | marta.fields@pastelapharma.com | Data & Analytics |
| Julian Cross | Data Analytics Manager (your supervisor) | julian.cross@pastelapharma.com | Data & Analytics |
| Priya Anand | Senior Data Analyst (your colleague) | priya.anand@pastelapharma.com | Data & Analytics |
| Diego Ferreira | Senior Project Manager | diego.ferreira@pastelapharma.com | Data & Analytics |
| Helena Brooks | Head of Pharmacovigilance | helena.brooks@pastelapharma.com | Drug Safety |
| Marcus Lee | Regulatory Affairs Manager | marcus.lee@pastelapharma.com | Regulatory Affairs |

Your teammates on the Data & Analytics team have deep technical backgrounds —
keep messages to them concise and code-forward. Helena and Marcus are program
and compliance leads without a technical background, so explanations aimed at
them should stay in plain language and focus on business impact, not
implementation detail. **Helena has a visual impairment**, which matters
directly for how any Tableau dashboard delivered to her must be designed
(see the accessibility notes in the notebooks).

---

## Meeting notes

You've just been given access to the company network and a Pastela email
account (rodrigo.machado@pastelapharma.com). Opening your inbox, you find
the following email from your supervisor.

> **From:** Julian Cross, Data Analytics Manager
> **To:** you
> **Cc:** Priya Anand
> **Subject:** Welcome — Pharmacovigilance risk project
>
> Welcome to the team! If you're reading this, your accounts are all set up.
>
> You're joining a new project with our Pharmacovigilance department. They've
> been collecting structured data on patients, prescribers, medications,
> treatments, and reported adverse events for years, but it's never been used
> for anything beyond individual case review. Helena Brooks (Head of
> Pharmacovigilance) has asked us to help her team get ahead of adverse events
> instead of only reacting to them.
>
> Here's what I took away from last week's leadership meeting, organized by
> who raised each point:
>
> **Diego Ferreira, Senior Project Manager**
> - The team has put together a milestone plan (Plan → Analyze → Construct →
>   Execute) so we can track deliverables and keep Pharmacovigilance in the
>   loop.
> - I'm coordinating directly with Helena and Marcus Lee on what they need to
>   see in the final dashboard.
>
> **Priya Anand, Senior Data Analyst**
> - The five source tables (doctors, medications, patients, treatments,
>   adverse events) need to be inspected and cleaned before anything else
>   happens.
> - We need to understand, through EDA, what the data can and can't tell us
>   about adverse-event risk before we commit to a model.
> - Once we have a model, we need to check that it's actually reliable and not
>   just fitting noise.
>
> **Marta Fields, Director of Data & Analytics**
> - Before we show Pharmacovigilance anything, we need to be confident the
>   model meets the bar for a decision-support tool, not a toy.
> - Once we're confident in a final model, I'll need the two or three talking
>   points I can bring to the executive review.
>
> **My own note:** I'd like this built in Python end-to-end — extraction,
> cleaning, modeling — with the results published to Tableau so
> Pharmacovigilance can explore it themselves rather than waiting on us for
> every question.
>
> Welcome aboard,
> Julian Cross
> Data Analytics Manager, Pastela Pharmaceuticals

A second email follows from Priya, with the concrete ask:

> **From:** Priya Anand, Senior Data Analyst
> **To:** you
> **Cc:** Julian Cross
> **Subject:** RE: Welcome — Pharmacovigilance risk project
>
> Nice to (virtually) meet you! I'm in the final stretch of another project,
> so I could really use your help getting this one off the ground.
>
> Before we do a full EDA, could you:
> 1. Build dataframes for the five source tables and get a clear picture of
>    each column's dtype, null counts, and which columns are actually useful
>    for a risk model versus just descriptive.
> 2. Engineer a few meaningful variables — patient age at treatment start,
>    BMI, how many concurrent treatments a patient is on (polypharmacy),
>    dose relative to the medication's typical dose — anything that a
>    logistic regression or decision tree could actually use.
> 3. Put together descriptive stats and a first pass at which factors look
>    associated with adverse events, so we have something to bring to Helena
>    and Marcus when we scope the model with them.
>
> Once that's solid, we'll move on to training and evaluating the actual
> classifier, and figure out the Tableau side together.
>
> Thanks,
> Priya Anand
> Senior Data Analyst, Pastela Pharmaceuticals

---

## Stakeholder interview — scoping the objective

Before writing any code, you set up a short call with Helena Brooks and Marcus
Lee to make sure the model solves the problem they actually have.

**You:** What decision would this model help you make that you can't make
today?

**Helena:** Right now we only look closely at a treatment after someone files
an adverse-event report. I want a way to see, across all *active* treatments,
which ones are most likely to produce a reportable adverse event, so my team
can check in with those patients proactively.

**You:** When you say "likely to produce an adverse event," do you care about
any adverse event, or specifically the severe ones?

**Helena:** Start with any adverse event as the primary target — mild events
still matter for monitoring — but I want severity visible in the dashboard so
we can filter down to severe/fatal cases when we triage.

**You:** Marcus, from a regulatory angle, is there anything the model needs to
avoid doing?

**Marcus:** Don't build anything that looks like it's making a clinical
diagnosis or a prescribing recommendation. This needs to stay a
*prioritization* tool for our monitoring team, not clinical decision support.
Also, whatever goes in the dashboard needs a plain-language explanation of
what "risk score" means — our auditors will ask.

**You:** Understood. And for the dashboard itself — any constraints I should
design around?

**Helena:** Yes — I have a visual impairment, so please don't rely on color
alone to distinguish risk levels. Use text labels, icons, or patterns in
addition to color, and make sure any chart has enough contrast.

This conversation is what turns the notebooks' broad ask ("help with
adverse-event risk") into a concrete, scoped machine learning objective:
**predict the probability that a given active treatment will result in an
adverse event, using patient, treatment, and medication attributes, and
surface that risk score — with severity, not diagnosis or prescribing advice —
in an accessible Tableau dashboard.**

---

## Task list and deliverables

1. **Plan** — confirm the objective above; identify the target variable
   (`adverse_event_flag`) and candidate predictors; list open questions.
2. **Extract (SQL)** — connect to the source tables with Python and pull only
   the columns needed for analysis via a filtering join query.
3. **Clean & engineer (Python)** — handle nulls/duplicates; engineer age, BMI,
   polypharmacy count, dose ratio; encode categoricals; scale numerics.
4. **Analyze (Statistics)** — descriptive statistics, distribution checks, and
   formal hypothesis tests / a statistical model to establish which factors
   are actually associated with adverse events before trusting an ML model.
5. **Model (ML)** — train and compare a Logistic Regression and a Decision
   Tree classifier; evaluate with a held-out test set.
6. **Export** — write the enriched, scored dataset out for Tableau.
7. **Visualize (Tableau)** — design an accessible dashboard for Helena's team
   with KPIs, filters, and a plain-language explanation of the risk score.
8. **Communicate** — a one-page executive summary for Marta and Julian:
   what was done, what the model found, and recommended next steps.

---

## Skills coverage

| Requested competency | Where it's covered |
|---|---|
| Data-Driven Decision-Making | Stakeholder interview → scoped objective; executive summary |
| Advanced Analytics | Full extraction → modeling → export pipeline |
| Statistical Inference | Hypothesis tests + `statsmodels` Logit coefficients/p-values (Analyze stage) |
| Descriptive Statistics | `describe()`, distribution plots (Analyze stage) |
| Applied Machine Learning | Logistic Regression + Decision Tree pipeline (Construct stage) |
| Decision Tree Learning | Decision Tree classifier + interpretation (Construct stage) |
| Interviewing Skills | Stakeholder interview with Helena/Marcus above |
| Logistic Regression | scikit-learn + statsmodels logistic models |
| Statistics / Statistical Methods / Statistical Modeling | Analyze stage end-to-end |
| Workflow Management | PACE structure; task list above; SQL → Python → Tableau pipeline |
| Data Structures | Relational schema (5 tables); pandas DataFrames |
| Supervised Learning | Binary classification of `adverse_event_flag` |
| Probability Distribution / Probability & Statistics | Distribution plots, hypothesis tests, model probabilities |
| Data Cleansing | Cleaning & feature engineering task |
| Interactive Data Visualization | Tableau dashboard design section |
| Professional Development | Portfolio framing, executive summary, stakeholder interview |

---

## Reference schema

See [`raw/schema_pharma_analytics_db.sql`](../raw/schema_pharma_analytics_db.sql)
for the full table definitions (`Doctors`, `Medications`, `Patients`,
`Treatments`, `Adverse_Events`) and [`raw/`](../raw/) for the generated CSV
data (20,000 patients and their associated records).

Start with
[`data_analysis_portfolio_pharma.ipynb`](../data_analysis_portfolio_pharma.ipynb)
and compare your work against
[`exemplar_data_analysis_portfolio_pharma.ipynb`](../exemplar_data_analysis_portfolio_pharma.ipynb)
once you're done.
