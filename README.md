# Employee Churn Prediction Model

## 📋 Project Overview

This project builds a machine learning model to predict **employee churn** — whether an employee will leave the company (Active vs Terminated). The model helps HR teams identify at-risk employees before they resign.

**Target Variable:** `is_churned` (0 = Active, 1 = Churned/Terminated)
**Problem Type:** Binary Classification
**Model Used:** RandomForestClassifier

---

## 🎯 Business Problem

Employee turnover is expensive. Replacing an employee costs 50-200% of their annual salary. This model helps:

- **Identify** employees at high risk of leaving
- **Prioritize** retention efforts
- **Understand** what drives churn (compensation, workload, performance)
- **Act** before the employee resigns

---

## 📊 Data Sources

The project pulls data from multiple database tables:

| Table | What It Contains | Purpose |
|-------|-----------------|---------|
| `employees` | Employee demographics, hire date, status | Base data |
| `jobs` | Job titles, salary bands (min/max) | Role context |
| `departments` | Department names | Grouping |
| `locations` | City, state, country | Geographic context |
| `employee_projects` | Projects and hours allocated | Workload signal |
| `attendance` | Absences and late days | Behavioral signal |
| `performance_reviews` | Performance ratings | Performance signal |
| `leave_requests` | Leave days taken | Behavioral signal |
| `salary_history` | Salary changes over time | Compensation signal |

---

## 🔧 Feature Engineering

### Raw Data → Engineered Features

| Original Column | Engineered Feature | Formula | Why |
|-----------------|-------------------|---------|-----|
| `hire_date` | `tenure_years` | (today - hire_date) / 365.25 | Direct measure of experience |
| `employment_status` | `is_churned` | status != 'active' | Target variable |
| `salary`, `min_salary`, `max_salary` | `salary_band_position` | (salary - min) / (max - min) | Relative pay (0-1 scale) |
| `salary` | `below_job_minimum` | salary < min_salary | Compliance flag |
| `salary` | `above_job_maximum` | salary > max_salary | Overpayment flag |
| `total_hours_allocated`, `total_projects` | `hours_per_project` | hours / projects | Workload intensity |
| `job_title` | `job_level` | 0-5 mapping | Ordinal hierarchy |
| `tenure_years` | `tenure_group` | Binned categories | Ordinal grouping |

### Why `salary_band_position` is Critical

Raw salary misleads the model:
- Engineer at $90,000 (top of band) = Happy → Low churn
- VP at $110,000 (bottom of band) = Unhappy → High churn

The model sees $110,000 > $90,000 and incorrectly predicts the VP is safer!

**Solution:** `salary_band_position` normalizes salary to 0-1 scale:
- 0.0 = at minimum (underpaid for role)
- 0.5 = middle
- 1.0 = at maximum (well-paid for role)

Now the model learns: **"Employees at bottom of their band churn more"** regardless of absolute salary.

---

## 📈 Outlier Handling Strategy

### Why Cap Outliers (Not Remove)

Capping keeps valuable signal. Removing deletes real employees.

| Column | Outliers | Decision | Factor | Why |
|--------|----------|----------|--------|-----|
| `salary` | 3 | CAP | 1.5 | Executives are real, cap for modeling |
| `min_salary` | 3 | CAP | 1.5 | Same reason |
| `job_max_salary` | 3 | CAP | 1.5 | Same reason |
| `employee_max_salary` | 3 | CAP | 1.5 | Same reason |
| `total_hours_allocated` | 14 | CAP | 1.5 | Overworked is real but extreme |
| `total_salary_increase` | 13 | CAP | 3.0 | Promotions are REAL and important |
| `total_absences` | 34 | CAP | 3.0 | Health issues are REAL |
| `total_late_days` | 1 | KEEP | — | Real behavior |
| `total_leaves_taken` | 1 | KEEP | — | Real behavior |
| `avg_performance_score` | 6 | KEEP | — | Top performers are real |
| `latest_performance_score` | 16 | KEEP | — | Top performers are real |

### The Rule: 1.5 vs 3.0

- **1.5 (Tight):** For values that should be normal (hours, tenure)
- **3.0 (Wide):** For values that CAN be extreme and valid (promotions, absences)

### Why Capping Works
Without Capping:
Employee Z: $500,000 salary increase (CEO)
Model learns: "Big raises are normal"
Predicts: $150,000 increase for normal employee ❌ WRONG

With Capping:
Employee Z: capped at $30,000
Model learns: "Raises are moderate"
Predicts: $15,000 increase for normal employee ✅ CORRECT

text

---

## 🔍 Correlation & VIF Analysis

### Correlation Matrix Findings

| Pair | Correlation | Decision |
|------|-------------|----------|
| salary ↔ min_salary | 0.93 | Drop one |
| salary ↔ job_max_salary | 0.93 | Drop one |
| salary ↔ employee_max_salary | 0.93 | Drop one |
| total_projects ↔ total_hours | 0.74 | Drop one |
| avg_performance ↔ latest_performance | 0.77 | Drop one |

### VIF (Variance Inflation Factor) Results

| Feature | VIF | Decision | Reason |
|---------|-----|----------|--------|
| salary | 170.42 | DROP | Target variable! |
| job_max_salary | 92.88 | DROP | Leakage (VIF > 10) |
| min_salary | 76.14 | DROP | Leakage (VIF > 10) |
| salary_band_position | 23.24 | DROP | Leakage (derived from target) |
| total_hours_allocated | 14.36 | KEEP | Drops below 5 after cleanup |
| total_projects | 9.58 | KEEP | Drops below 5 after cleanup |
| hours_per_project | 6.53 | DROP | Redundant math |
| total_salary_increase | 1.81 | KEEP | VIF < 5 |
| All others | < 1.1 | KEEP | VIF < 5 |

### The Golden Rule

- **VIF < 5:** Safe to keep
- **VIF 5-10:** Moderate multicollinearity, consider dropping
- **VIF > 10:** Severe multicollinearity, MUST drop

---

## 🛠️ Preprocessing Pipeline

### Leakage-Free Outlier Capper

```python
class IQRCapper(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        # Learn bounds from TRAINING data ONLY
        ...
    def transform(self, X):
        # Apply bounds to both train and test
        ...
Why this prevents leakage:

Bounds learned from training data only

Test data transformed using training bounds

No information from test leaks into training

Pipeline Structure
python
preprocessor = ColumnTransformer([
    ('numeric', numeric_pipeline, numeric_cols),       # 1.5 cap + scale
    ('skewed', skewed_pipeline, skewed_cols),          # 3.0 cap + Yeo-Johnson + scale
    ('uncapped', uncapped_pipeline, uncapped_cols),    # scale only
    ('nominal', nominal_pipeline, nominal_cols),       # one-hot encode
])
📊 Model Results
Performance Metrics
Metric	Score	What It Means
ROC-AUC	0.9871	Near-perfect separation of churners vs non-churners
Accuracy	98.00%	98 out of 100 predictions correct
Precision	87.50%	Of those flagged as churn, 87.5% actually churned
Recall	100.00%	Caught ALL actual churners (0 missed)
F1 Score	93.33%	Balance of precision and recall
Metric Explanations
ROC-AUC (0.9871)
Measures model's ability to distinguish between classes

0.5 = random guessing

1.0 = perfect separation

0.9871 = Excellent

Accuracy (98.00%)
Percentage of correct predictions

(True Positives + True Negatives) / Total

98% = Excellent

Precision (87.50%)
Of all employees flagged as "will churn," how many actually churned?

True Positives / (True Positives + False Positives)

87.5% = 14 correct out of 16 flagged

Recall (100.00%)
Of all employees who actually churned, how many did we catch?

True Positives / (True Positives + False Negatives)

100% = Caught ALL 14 churners!

F1 Score (93.33%)
Harmonic mean of precision and recall

Balances both metrics

93.33% = Excellent

Confusion Matrix
text
                Predicted Stay    Predicted Churn
Actual Stay          84                 2
Actual Churn          0                14
True Negatives: 84 (correctly predicted stay)

False Positives: 2 (predicted churn, actually stayed)

False Negatives: 0 (predicted stay, actually churned) ← Perfect!

True Positives: 14 (correctly predicted churn)

Why Recall = 100% is Important
For churn prediction, missing a churner is worse than a false alarm:

Miss a churner → Employee leaves, cost of replacement

False alarm → HR checks in, no harm done

100% recall means we caught every single employee who left.

🎯 Key Insights
salary_band_position is the strongest predictor of churn

Employees at bottom of their pay band are highest risk

High absences + low performance + short tenure = very high risk

Job level matters: junior employees churn more than executives

Promotions reduce churn: big raises = loyalty

🚀 How to Use
python
# Load model
import joblib
model = joblib.load('churn_model.pkl')

# Predict for new employee
new_employee = pd.DataFrame({...})
processed = preprocessor.transform(new_employee)
churn_prob = model.predict_proba(processed)[:, 1]

# 0.85 = 85% churn risk → HR should intervene!
