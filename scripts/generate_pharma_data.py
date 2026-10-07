"""
Synthetic data generator for the Pastela Pharmaceuticals pharmacovigilance
analytics portfolio project.

Produces five CSV tables in ../raw/ :
    doctors.csv, medications.csv, patients.csv, treatments.csv, adverse_events.csv

All identities and clinical values are fictitious. Adverse-event occurrence is
sampled from a hidden logistic risk function (age, dose vs. typical dose,
medication risk tier, polypharmacy count) so the resulting dataset carries
genuine, learnable signal for the downstream ML notebooks -- it is not random
noise. Everything is seeded for reproducibility.

On top of that, inject_site_anomalies() adds a pedagogical site-level scenario
for risk-based monitoring: per-site reporting-lag fluctuation, two sites with
delayed data capture (late reports + unentered backlog) and one site with a
strong sex imbalance. Every injected value is plausible at record level.

Usage:
    python generate_pharma_data.py
"""

import os
import numpy as np
import pandas as pd
from faker import Faker
from datetime import date, timedelta

SEED = 42
rng = np.random.default_rng(SEED)
fake = Faker("en_US")
Faker.seed(SEED)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

TODAY = date(2026, 8, 17)

N_DOCTORS = 200
N_PATIENTS = 20_000

# ---------------------------------------------------------------------------
# Doctors
# ---------------------------------------------------------------------------

SPECIALTIES = [
    "Cardiology", "Oncology", "Neurology", "Infectious Disease", "Endocrinology",
    "Internal Medicine", "Psychiatry", "Rheumatology", "Pulmonology", "Nephrology",
    "Family Medicine", "Geriatrics",
]

HOSPITALS = [
    "Meridian General Hospital", "St. Alden Medical Center", "Northgate University Hospital",
    "Riverside Health Institute", "Lakeview Regional Hospital", "Crestwood Memorial Hospital",
    "Harborview Clinical Center", "Pinecrest Community Hospital", "Ashford Medical Center",
    "Summit Health System",
]


def generate_doctors(n=N_DOCTORS):
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "doctor_id": i,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "specialty": rng.choice(SPECIALTIES),
            "license_number": f"MD-{10000 + i}",
            "hospital": rng.choice(HOSPITALS),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Medications
# Each entry also carries internal-only "risk_weight" and "typical_dose_mg"
# used purely to drive realistic treatment/adverse-event generation. Neither
# column is written to medications.csv -- they represent latent risk factors
# an analyst would have to infer from the data, not read off a label.
# ---------------------------------------------------------------------------

MEDICATIONS = [
    # brand_name, active_ingredient, manufacturer, form, concentration_mg, who_atc_category, rx, risk_weight, typical_dose_mg, commonality
    ("Lipiverol 40mg", "Atorvastatin", "Pfizer", "Tablet", 40.0, "C10AA01 - HMG-CoA reductase inhibitor (statin)", 1, "LOW", 40, 9),
    ("Corvastan 20mg", "Rosuvastatin", "AstraZeneca", "Tablet", 20.0, "C10AA07 - HMG-CoA reductase inhibitor (statin)", 1, "LOW", 20, 6),
    ("Glucophage 850mg", "Metformin", "Merck", "Tablet", 850.0, "A10BA02 - Biguanide antidiabetic", 1, "LOW", 850, 9),
    ("Ibuprovex 400mg", "Ibuprofen", "Bayer", "Tablet", 400.0, "M01AE01 - Propionic acid NSAID", 0, "MEDIUM", 400, 8),
    ("Naproxil 500mg", "Naproxen", "Roche", "Tablet", 500.0, "M01AE02 - Propionic acid NSAID", 0, "MEDIUM", 500, 5),
    ("Amoxiclear 500mg", "Amoxicillin", "GSK", "Capsule", 500.0, "J01CA04 - Broad-spectrum penicillin", 1, "LOW", 500, 8),
    ("Azivex 250mg", "Azithromycin", "Pfizer", "Tablet", 250.0, "J01FA10 - Macrolide antibiotic", 1, "LOW", 250, 6),
    ("Enalapan 10mg", "Enalapril", "Novartis", "Tablet", 10.0, "C09AA02 - ACE inhibitor", 1, "LOW", 10, 8),
    ("Lisinal 10mg", "Lisinopril", "Merck", "Tablet", 10.0, "C09AA03 - ACE inhibitor", 1, "LOW", 10, 7),
    ("Omeprazine 20mg", "Omeprazole", "AstraZeneca", "Capsule", 20.0, "A02BC01 - Proton pump inhibitor", 0, "LOW", 20, 9),
    ("Pantorix 40mg", "Pantoprazole", "Takeda", "Tablet", 40.0, "A02BC02 - Proton pump inhibitor", 0, "LOW", 40, 6),
    ("Methoxan 2.5mg", "Methotrexate", "Teva", "Tablet", 2.5, "L01BA01 - Antimetabolite / DMARD", 1, "HIGH", 15, 3),
    ("Prozamine 20mg", "Fluoxetine", "Eli Lilly", "Capsule", 20.0, "N06AB03 - SSRI antidepressant", 1, "MEDIUM", 20, 6),
    ("Sertraline Normon 50mg", "Sertraline", "Normon", "Tablet", 50.0, "N06AB06 - SSRI antidepressant", 1, "MEDIUM", 50, 6),
    ("Warfacil 5mg", "Warfarin", "Bristol-Myers Squibb", "Tablet", 5.0, "B01AA03 - Vitamin K antagonist anticoagulant", 1, "HIGH", 5, 4),
    ("Apixarel 5mg", "Apixaban", "Pfizer", "Tablet", 5.0, "B01AF02 - Factor Xa inhibitor anticoagulant", 1, "HIGH", 5, 4),
    ("Doxorubin 50mg", "Doxorubicin", "Roche", "Injection", 50.0, "L01DB01 - Anthracycline antineoplastic", 1, "HIGH", 60, 2),
    ("Cisplatek 50mg", "Cisplatin", "Teva", "Injection", 50.0, "L01XA01 - Platinum antineoplastic", 1, "HIGH", 75, 2),
    ("Oxycontal 10mg", "Oxycodone", "Purdue", "Tablet", 10.0, "N02AA05 - Opioid analgesic", 1, "HIGH", 10, 3),
    ("Morfilex 10mg", "Morphine", "Mallinckrodt", "Injection", 10.0, "N02AA01 - Opioid analgesic", 1, "HIGH", 10, 2),
    ("Cyclosporal 100mg", "Cyclosporine", "Novartis", "Capsule", 100.0, "L04AD01 - Calcineurin-inhibitor immunosuppressant", 1, "HIGH", 150, 2),
    ("Tacrolim 5mg", "Tacrolimus", "Astellas", "Capsule", 5.0, "L04AD02 - Calcineurin-inhibitor immunosuppressant", 1, "HIGH", 5, 2),
    ("Prednivex 20mg", "Prednisone", "Pfizer", "Tablet", 20.0, "H02AB07 - Systemic corticosteroid", 1, "MEDIUM", 20, 6),
    ("Dexanorm 4mg", "Dexamethasone", "Merck", "Tablet", 4.0, "H02AB02 - Systemic corticosteroid", 1, "MEDIUM", 4, 4),
    ("Diazepron 5mg", "Diazepam", "Roche", "Tablet", 5.0, "N05BA01 - Benzodiazepine anxiolytic", 1, "MEDIUM", 5, 4),
    ("Loraxil 1mg", "Lorazepam", "Wyeth", "Tablet", 1.0, "N05BA06 - Benzodiazepine anxiolytic", 1, "MEDIUM", 1, 4),
    ("Risperal 2mg", "Risperidone", "Janssen", "Tablet", 2.0, "N05AX08 - Atypical antipsychotic", 1, "MEDIUM", 2, 3),
    ("Olanzapex 10mg", "Olanzapine", "Eli Lilly", "Tablet", 10.0, "N05AH03 - Atypical antipsychotic", 1, "MEDIUM", 10, 3),
    ("Furosemal 40mg", "Furosemide", "Sanofi", "Tablet", 40.0, "C03CA01 - Loop diuretic", 1, "LOW", 40, 6),
    ("Hydrochlon 25mg", "Hydrochlorothiazide", "Merck", "Tablet", 25.0, "C03AA03 - Thiazide diuretic", 1, "LOW", 25, 6),
    ("Salbutrix 100mcg", "Salbutamol", "GSK", "Inhaler", 0.1, "R03AC02 - Short-acting beta-2 agonist bronchodilator", 0, "LOW", 0.1, 6),
    ("Fluticort 250mcg", "Fluticasone", "GSK", "Inhaler", 0.25, "R03BA05 - Inhaled corticosteroid", 0, "LOW", 0.25, 5),
    ("Metoprolan 50mg", "Metoprolol", "AstraZeneca", "Tablet", 50.0, "C07AB02 - Beta-1 selective blocker", 1, "LOW", 50, 8),
    ("Atenolix 50mg", "Atenolol", "AstraZeneca", "Tablet", 50.0, "C07AB03 - Beta-1 selective blocker", 1, "LOW", 50, 6),
    ("Amlodipex 5mg", "Amlodipine", "Pfizer", "Tablet", 5.0, "C08CA01 - Dihydropyridine calcium channel blocker", 1, "LOW", 5, 7),
    ("Levotirox 100mcg", "Levothyroxine", "Abbott", "Tablet", 0.1, "H03AA01 - Thyroid hormone replacement", 1, "LOW", 0.1, 7),
    ("Acyclovex 400mg", "Acyclovir", "GSK", "Tablet", 400.0, "J05AB01 - Antiviral (herpesvirus)", 1, "MEDIUM", 400, 3),
    ("Ceftrixon 1g", "Ceftriaxone", "Roche", "Injection", 1000.0, "J01DD04 - Third-generation cephalosporin", 1, "LOW", 1000, 3),
    ("Vancomex 1g", "Vancomycin", "Eli Lilly", "Injection", 1000.0, "J01XA01 - Glycopeptide antibiotic", 1, "MEDIUM", 1000, 2),
    ("Insugen 100U/mL", "Insulin Glargine", "Sanofi", "Injection", 100.0, "A10AE04 - Long-acting insulin analogue", 1, "MEDIUM", 100, 4),
]

MED_COLUMNS = [
    "brand_name", "active_ingredient", "manufacturer", "pharmaceutical_form",
    "concentration_mg", "who_atc_category", "requires_prescription",
    "risk_weight", "typical_dose_mg", "commonality",
]


def generate_medications():
    df = pd.DataFrame(MEDICATIONS, columns=MED_COLUMNS)
    df.insert(0, "medication_id", range(1, len(df) + 1))
    return df


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------

BLOOD_TYPES = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
BLOOD_TYPE_P = [0.37, 0.34, 0.09, 0.03, 0.07, 0.06, 0.02, 0.02]

REG_START = date(2020, 1, 1)
REG_END = date(2026, 6, 1)


def random_date(start: date, end: date, size=None):
    delta_days = (end - start).days
    offsets = rng.integers(0, max(delta_days, 1), size=size)
    if size is None:
        return start + timedelta(days=int(offsets))
    return [start + timedelta(days=int(o)) for o in offsets]


def generate_patients(n=N_PATIENTS):
    sex = rng.choice(["M", "F"], size=n)
    # age skewed toward adults, mean ~52, range clipped 18-95
    age_years = np.clip(rng.normal(52, 18, size=n), 18, 95)
    birth_dates = [TODAY - timedelta(days=int(a * 365.25)) for a in age_years]

    height_cm = np.where(
        sex == "M",
        np.clip(rng.normal(175, 7, size=n), 150, 200),
        np.clip(rng.normal(162, 6, size=n), 140, 190),
    ).round(0)
    weight_kg = np.where(
        sex == "M",
        np.clip(rng.normal(82, 14, size=n), 45, 160),
        np.clip(rng.normal(68, 13, size=n), 40, 150),
    ).round(1)

    registration_dates = random_date(REG_START, REG_END, size=n)

    rows = {
        "patient_id": np.arange(1, n + 1),
        "first_name": [fake.first_name_male() if s == "M" else fake.first_name_female() for s in sex],
        "last_name": [fake.last_name() for _ in range(n)],
        "birth_date": birth_dates,
        "sex": sex,
        "weight_kg": weight_kg,
        "height_cm": height_cm.astype(int),
        "blood_type": rng.choice(BLOOD_TYPES, size=n, p=BLOOD_TYPE_P),
        "registration_date": registration_dates,
    }
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Treatments + Adverse Events
# ---------------------------------------------------------------------------

FREQUENCIES = ["Once daily", "Twice daily", "Every 8 hours", "Every 12 hours", "Once weekly"]
ROUTES_ORAL = ["Oral"]
ROUTES_INJECTION = ["Intravenous", "Subcutaneous", "Intramuscular"]
ROUTES_INHALER = ["Inhalation"]

INDICATIONS_BY_CATEGORY = {
    "statin": ["Hypercholesterolemia", "Cardiovascular risk reduction"],
    "antidiabetic": ["Type 2 diabetes mellitus"],
    "nsaid": ["Osteoarthritis pain", "Tension headache", "Post-operative pain"],
    "antibiotic": ["Community-acquired pneumonia", "Urinary tract infection", "Skin and soft-tissue infection"],
    "ace": ["Essential hypertension", "Heart failure"],
    "ppi": ["Gastroesophageal reflux disease", "NSAID gastroprotection"],
    "dmard": ["Rheumatoid arthritis"],
    "ssri": ["Major depressive disorder", "Generalized anxiety disorder"],
    "anticoagulant": ["Atrial fibrillation", "Venous thromboembolism prophylaxis"],
    "antineoplastic": ["Breast cancer", "Non-small cell lung cancer", "Lymphoma"],
    "opioid": ["Severe post-operative pain", "Chronic cancer pain"],
    "immunosuppressant": ["Post-transplant immunosuppression", "Severe rheumatoid arthritis"],
    "corticosteroid": ["Chronic obstructive pulmonary disease exacerbation", "Autoimmune inflammation"],
    "benzodiazepine": ["Generalized anxiety disorder", "Insomnia"],
    "antipsychotic": ["Schizophrenia", "Bipolar disorder"],
    "diuretic": ["Essential hypertension", "Fluid overload"],
    "bronchodilator": ["Asthma", "Chronic obstructive pulmonary disease"],
    "beta_blocker": ["Essential hypertension", "Angina pectoris"],
    "ccb": ["Essential hypertension"],
    "thyroid": ["Hypothyroidism"],
    "antiviral": ["Herpes zoster", "Herpes simplex infection"],
    "insulin": ["Type 1 diabetes mellitus", "Type 2 diabetes mellitus"],
}


def _category_key(who_atc_category: str) -> str:
    c = who_atc_category.lower()
    if "statin" in c:
        return "statin"
    if "biguanide" in c:
        return "antidiabetic"
    if "nsaid" in c:
        return "nsaid"
    if "penicillin" in c or "macrolide" in c or "cephalosporin" in c or "glycopeptide" in c:
        return "antibiotic"
    if "ace inhibitor" in c:
        return "ace"
    if "proton pump" in c:
        return "ppi"
    if "dmard" in c or "antimetabolite" in c:
        return "dmard"
    if "ssri" in c:
        return "ssri"
    if "anticoagulant" in c or "factor xa" in c or "vitamin k antagonist" in c:
        return "anticoagulant"
    if "antineoplastic" in c:
        return "antineoplastic"
    if "opioid" in c:
        return "opioid"
    if "immunosuppressant" in c:
        return "immunosuppressant"
    if "corticosteroid" in c:
        return "corticosteroid"
    if "benzodiazepine" in c:
        return "benzodiazepine"
    if "antipsychotic" in c:
        return "antipsychotic"
    if "diuretic" in c:
        return "diuretic"
    if "bronchodilator" in c:
        return "bronchodilator"
    if "beta-1" in c:
        return "beta_blocker"
    if "calcium channel" in c:
        return "ccb"
    if "thyroid" in c:
        return "thyroid"
    if "antiviral" in c:
        return "antiviral"
    if "insulin" in c:
        return "insulin"
    return "nsaid"


REACTION_TEMPLATES = {
    "statin": [("Myalgia", "Diffuse muscle pain with elevated creatine kinase"), ("Hepatotoxicity", "Elevated liver transaminases on routine panel")],
    "antidiabetic": [("Gastrointestinal upset", "Persistent nausea and diarrhea after dosing"), ("Lactic acidosis", "Metabolic acidosis with elevated lactate")],
    "nsaid": [("Gastrointestinal bleeding", "Upper GI hemorrhage with hematemesis"), ("Acute kidney injury", "Rise in serum creatinine after treatment start")],
    "antibiotic": [("Allergic skin reaction", "Generalized urticaria and pruritus"), ("Anaphylaxis", "Acute hypotension and airway swelling after dose")],
    "ace": [("Angioedema", "Facial and lip swelling with mild airway compromise"), ("Dry cough", "Persistent non-productive cough unresponsive to antitussives")],
    "ppi": [("Headache", "Recurrent headache following dose escalation"), ("Hypomagnesemia", "Low serum magnesium on routine labs")],
    "dmard": [("Hepatotoxicity", "Transaminases elevated 3x upper limit of normal"), ("Bone marrow suppression", "Unexplained leukopenia on follow-up labs")],
    "ssri": [("Serotonin syndrome", "Agitation, tremor and hyperreflexia"), ("Insomnia", "New-onset sleep disturbance after starting therapy")],
    "anticoagulant": [("Major hemorrhage", "Gastrointestinal bleeding requiring transfusion"), ("Bruising", "Extensive spontaneous bruising on limbs")],
    "antineoplastic": [("Neutropenia", "Severe drop in absolute neutrophil count"), ("Nausea and vomiting", "Refractory chemotherapy-induced emesis")],
    "opioid": [("Respiratory depression", "Decreased respiratory rate requiring monitoring"), ("Constipation", "Severe opioid-induced constipation")],
    "immunosuppressant": [("Nephrotoxicity", "Acute rise in serum creatinine"), ("Opportunistic infection", "New infection attributable to immunosuppression")],
    "corticosteroid": [("Hyperglycemia", "New-onset elevated glucose readings"), ("Mood disturbance", "Steroid-induced irritability and insomnia")],
    "benzodiazepine": [("Sedation", "Excessive daytime somnolence"), ("Falls", "Unwitnessed fall attributed to sedation")],
    "antipsychotic": [("Extrapyramidal symptoms", "New-onset tremor and rigidity"), ("Weight gain", "Rapid weight gain over follow-up period")],
    "diuretic": [("Hypokalemia", "Low serum potassium on routine labs"), ("Dehydration", "Orthostatic hypotension with dizziness")],
    "bronchodilator": [("Tachycardia", "Elevated heart rate after inhaler use"), ("Tremor", "Fine hand tremor following dosing")],
    "beta_blocker": [("Bradycardia", "Symptomatic low heart rate"), ("Fatigue", "New-onset persistent fatigue")],
    "ccb": [("Peripheral edema", "New lower-limb swelling"), ("Hypotension", "Symptomatic drop in blood pressure")],
    "thyroid": [("Palpitations", "New-onset tachyarrhythmia after dose increase"), ("Insomnia", "Sleep disturbance following dose adjustment")],
    "antiviral": [("Nephrotoxicity", "Rise in creatinine during therapy"), ("Rash", "Diffuse maculopapular rash")],
    "insulin": [("Hypoglycemia", "Blood glucose below 50 mg/dL with symptoms"), ("Injection site reaction", "Localized redness and swelling at injection site")],
}

SEVERITIES = ["Mild", "Moderate", "Severe", "Fatal"]
RESOLUTIONS_BY_SEVERITY = {
    "Mild": ["Recovered", "Recovered", "Recovered", "Under evaluation"],
    "Moderate": ["Recovered", "Recovered", "Ongoing", "Under evaluation"],
    "Severe": ["Recovered", "Ongoing", "Sequelae"],
    "Fatal": ["Fatal"],
}

STATUS_VALUES = ["Active", "Completed", "Suspended"]


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def generate_treatments_and_events(patients_df, doctors_df, medications_df):
    n_patients = len(patients_df)
    n_choices = rng.choice([0, 1, 2, 3, 4], size=n_patients, p=[0.15, 0.35, 0.33, 0.12, 0.05])

    med_records = medications_df.to_dict("records")
    med_weights = np.array([m["commonality"] for m in med_records], dtype=float)
    med_weights = med_weights / med_weights.sum()

    treatments = []
    events = []
    treatment_id = 1
    event_id = 1

    patient_lookup = patients_df.set_index("patient_id")
    doctor_ids = doctors_df["doctor_id"].to_numpy()

    for patient_id, n_treat in zip(patients_df["patient_id"], n_choices):
        if n_treat == 0:
            continue
        birth_date = patient_lookup.loc[patient_id, "birth_date"]
        reg_date = patient_lookup.loc[patient_id, "registration_date"]
        chosen_meds = rng.choice(len(med_records), size=n_treat, replace=True, p=med_weights)

        for med_idx in chosen_meds:
            med = med_records[med_idx]
            start_date = random_date(max(reg_date, date(2020, 1, 2)), date(2026, 8, 1))
            if start_date < reg_date:
                start_date = reg_date

            duration_days = int(rng.choice([7, 10, 14, 30, 60, 90, 180, 365], p=[0.12, 0.1, 0.13, 0.2, 0.15, 0.13, 0.1, 0.07]))
            tentative_end = start_date + timedelta(days=duration_days)
            is_ongoing = tentative_end > TODAY or rng.random() < 0.15

            if is_ongoing:
                end_date = None
                status = "Active"
            else:
                end_date = tentative_end
                status = rng.choice(["Completed", "Suspended"], p=[0.85, 0.15])

            form = med["pharmaceutical_form"]
            if form == "Injection":
                route = rng.choice(ROUTES_INJECTION)
            elif form == "Inhaler":
                route = rng.choice(ROUTES_INHALER)
            else:
                route = "Oral"

            frequency = rng.choice(FREQUENCIES)
            dose_factor = np.clip(rng.normal(1.0, 0.25), 0.5, 2.0)
            dose_mg = round(float(med["typical_dose_mg"]) * dose_factor, 2)

            category = _category_key(med["who_atc_category"])
            indication = rng.choice(INDICATIONS_BY_CATEGORY.get(category, ["General treatment"]))

            treatments.append({
                "treatment_id": treatment_id,
                "patient_id": patient_id,
                "doctor_id": int(rng.choice(doctor_ids)),
                "medication_id": med["medication_id"],
                "start_date": start_date,
                "end_date": end_date,
                "dose_mg": dose_mg,
                "frequency": frequency,
                "route": route,
                "indication": indication,
                "status": status,
            })

            # --- hidden risk model for adverse-event occurrence ---
            age_at_start = (start_date - birth_date).days / 365.25
            dose_ratio = dose_mg / float(med["typical_dose_mg"])
            risk_map = {"LOW": 0.0, "MEDIUM": 0.9, "HIGH": 1.8}
            risk_term = risk_map[med["risk_weight"]]
            polypharmacy_term = 0.12 * (n_treat - 1)

            logit = (
                -3.35
                + 0.018 * (age_at_start - 50)
                + 0.55 * (dose_ratio - 1)
                + risk_term
                + polypharmacy_term
                + rng.normal(0, 0.35)
            )
            prob = sigmoid(logit)
            has_event = rng.random() < prob

            if has_event:
                severity_p = [0.45, 0.35, 0.15, 0.05]
                if med["risk_weight"] == "HIGH":
                    severity_p = [0.25, 0.35, 0.28, 0.12]
                elif med["risk_weight"] == "MEDIUM":
                    severity_p = [0.38, 0.36, 0.19, 0.07]
                severity = rng.choice(SEVERITIES, p=severity_p)

                reaction_type, description = REACTION_TEMPLATES.get(category, [("Adverse reaction", "Unspecified adverse reaction reported by treating physician")])[
                    int(rng.integers(0, len(REACTION_TEMPLATES.get(category, [1]))))
                ]

                max_event_offset = duration_days if not is_ongoing else max((TODAY - start_date).days, 1)
                event_offset = int(rng.integers(1, max(max_event_offset, 2)))
                event_date = start_date + timedelta(days=event_offset)
                if event_date > TODAY:
                    event_date = TODAY

                required_hosp = severity in ("Severe", "Fatal") and rng.random() < 0.75
                report_offset = int(rng.integers(0, 6))
                report_date = min(event_date + timedelta(days=report_offset), TODAY)
                resolution = rng.choice(RESOLUTIONS_BY_SEVERITY[severity])

                events.append({
                    "event_id": event_id,
                    "treatment_id": treatment_id,
                    "patient_id": patient_id,
                    "event_date": event_date,
                    "description": description,
                    "severity": severity,
                    "reaction_type": reaction_type,
                    "required_hospitalization": int(required_hosp),
                    "report_date": report_date,
                    "resolution": resolution,
                })
                event_id += 1

            treatment_id += 1

    return pd.DataFrame(treatments), pd.DataFrame(events)


# ---------------------------------------------------------------------------
# Site-level anomalies (pedagogical scenario for risk-based monitoring)
# ---------------------------------------------------------------------------
# Every value injected here is individually plausible (valid dates, valid
# sex codes, report_date >= event_date). The anomalies only become visible
# when records are aggregated by site -- which is the point: record-level
# cleaning should NOT remove them; site-level KRIs should detect them.

DELAYED_SITES = ["Summit Health System", "Northgate University Hospital"]
SEX_SKEWED_SITE = "Harborview Clinical Center"


def inject_site_anomalies(treatments_df, events_df, doctors_df, patients_df):
    site_rng = np.random.default_rng(SEED + 1)
    doctor_site = doctors_df.set_index("doctor_id")["hospital"]
    events_df = events_df.copy()
    treatments_df = treatments_df.copy()

    # 1) Sex imbalance: the skewed site mostly sees female patients
    # (e.g. a women's-health referral centre). Only the prescriber assignment
    # changes -- patient attributes and the hidden risk model are untouched.
    patient_sex = patients_df.set_index("patient_id")["sex"]
    t_site = treatments_df["doctor_id"].map(doctor_site)
    t_sex = treatments_df["patient_id"].map(patient_sex)
    skewed_doctors = doctors_df.loc[doctors_df["hospital"] == SEX_SKEWED_SITE, "doctor_id"].to_numpy()
    other_doctors = doctors_df.loc[doctors_df["hospital"] != SEX_SKEWED_SITE, "doctor_id"].to_numpy()

    move_out = (t_site == SEX_SKEWED_SITE) & (t_sex == "M") & (site_rng.random(len(treatments_df)) < 0.8)
    treatments_df.loc[move_out, "doctor_id"] = site_rng.choice(other_doctors, size=move_out.sum())
    female_elsewhere = (t_site != SEX_SKEWED_SITE) & (t_sex == "F")
    move_in_p = move_out.sum() / female_elsewhere.sum()
    move_in = female_elsewhere & (site_rng.random(len(treatments_df)) < move_in_p)
    treatments_df.loc[move_in, "doctor_id"] = site_rng.choice(skewed_doctors, size=move_in.sum())

    # 2) Baseline fluctuation: each site has its own typical reporting lag.
    site_mean_lag = {h: float(np.clip(site_rng.lognormal(np.log(2.5), 0.4), 1, 6)) for h in HOSPITALS}

    event_site = events_df["treatment_id"].map(
        treatments_df.set_index("treatment_id")["doctor_id"].map(doctor_site)
    )
    lags = np.array([site_rng.poisson(site_mean_lag[s]) for s in event_site])

    # 3) Delayed data capture: most reports at these sites arrive 20-90 days
    # late, and part of the backlog has not been entered at all yet.
    delayed = event_site.isin(DELAYED_SITES).to_numpy()
    late = delayed & (site_rng.random(len(events_df)) < 0.75)
    lags[late] = site_rng.integers(20, 91, size=late.sum())

    event_dates = pd.to_datetime(events_df["event_date"])
    report_dates = event_dates + pd.to_timedelta(lags, unit="D")
    not_yet_reported = report_dates > pd.Timestamp(TODAY)
    backlog = delayed & (site_rng.random(len(events_df)) < 0.25)
    events_df["report_date"] = report_dates.dt.date
    events_df = events_df[~(not_yet_reported.to_numpy() | backlog)].reset_index(drop=True)
    events_df["event_id"] = np.arange(1, len(events_df) + 1)

    return treatments_df, events_df


def main():
    print("Generating doctors...")
    doctors_df = generate_doctors()

    print("Generating medications...")
    medications_df = generate_medications()

    print("Generating patients...")
    patients_df = generate_patients()

    print("Generating treatments and adverse events...")
    treatments_df, events_df = generate_treatments_and_events(patients_df, doctors_df, medications_df)

    print("Injecting site-level anomalies...")
    treatments_df, events_df = inject_site_anomalies(treatments_df, events_df, doctors_df, patients_df)

    # Drop internal-only generation columns before export
    medications_export = medications_df.drop(columns=["risk_weight", "typical_dose_mg", "commonality"])

    doctors_df.to_csv(os.path.join(OUT_DIR, "doctors.csv"), index=False)
    medications_export.to_csv(os.path.join(OUT_DIR, "medications.csv"), index=False)
    patients_df.to_csv(os.path.join(OUT_DIR, "patients.csv"), index=False)
    treatments_df.to_csv(os.path.join(OUT_DIR, "treatments.csv"), index=False)
    events_df.to_csv(os.path.join(OUT_DIR, "adverse_events.csv"), index=False)

    print("\n--- Summary ---")
    print(f"doctors:         {len(doctors_df):,}")
    print(f"medications:     {len(medications_export):,}")
    print(f"patients:        {len(patients_df):,}")
    print(f"treatments:      {len(treatments_df):,}")
    print(f"adverse_events:  {len(events_df):,}")
    incidence = len(events_df) / len(treatments_df) * 100
    print(f"adverse event incidence: {incidence:.2f}% of treatments")

    # referential integrity spot checks
    assert treatments_df["patient_id"].isin(patients_df["patient_id"]).all()
    assert treatments_df["doctor_id"].isin(doctors_df["doctor_id"]).all()
    assert treatments_df["medication_id"].isin(medications_export["medication_id"]).all()
    assert events_df["treatment_id"].isin(treatments_df["treatment_id"]).all()
    assert events_df["patient_id"].isin(patients_df["patient_id"]).all()
    print("Referential integrity checks passed.")


if __name__ == "__main__":
    main()
