from heapq import merge

import pandas as pd
from PIL.ImageCms import Flags
from numpy.testing.print_coercion_tables import print_new_cast_table
from pandas import read_sql
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, PowerTransformer
from statsmodels.stats.outliers_influence import variance_inflation_factor

from practice_project import today
'''

# 2. Build the MySQL Connection URL
# Format: mysql+mysqlconnector://USER:PASSWORD@HOST:PORT/DBNAME
DATABASE_URL = f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

# 3. Create SQLAlchemy Engine
engine = create_engine(DATABASE_URL)
'''
import os
from dotenv import load_dotenv

# 1. Load the variables from the .env file into the environment
load_dotenv()

# 2. Fetch the credentials securely
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST", "localhost")  # Fallback to 'localhost' if missing
PORT = os.getenv("DB_PORT", "3306")
DBNAME = os.getenv("DB_NAME")

# 3. Build the Connection URL
DATABASE_URL = (
    f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}" )

engine = create_engine(DATABASE_URL)






# Example SQL Query
employee = "SELECT * FROM employees LIMIT 10;"

# Fetch data using Pandas



# Pass the query directly
employees = pd.read_sql("SELECT * FROM employees;", engine)
jobs = pd.read_sql("SELECT * FROM jobs;", engine)
departments = pd.read_sql("SELECT * FROM departments;", engine)
locations = pd.read_sql("SELECT * FROM locations;", engine)
employee_projects = pd.read_sql("SELECT * FROM employee_projects;", engine)
salary_history = pd.read_sql("SELECT * FROM salary_history;", engine)
projects = pd.read_sql("SELECT * FROM projects;", engine)
attendance = pd.read_sql("SELECT * FROM attendance;", engine)
leave_requests = pd.read_sql("SELECT * FROM leave_requests;", engine)
performance_reviews = pd.read_sql("SELECT * FROM performance_reviews;", engine)
print(projects.columns)
print(attendance.columns)
print(leave_requests.columns)
print(performance_reviews.columns)
print(salary_history.columns)
print(employee_projects.columns)
print(projects)
print(attendance)
print(leave_requests)
print(performance_reviews)
print(salary_history)
print(attendance)
print(employee_projects)

print("________________________________________________________________________________________________")
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, PowerTransformer
from statsmodels.stats.outliers_influence import variance_inflation_factor

# 2. Aggregations (Many-to-One -> One-to-One per employee)
emp_proj_agg = employee_projects.groupby('employee_id').agg(
    total_projects=('project_id', 'count'),
    total_hours_allocated=('hours_allocated', 'sum')
).reset_index()

attendance_agg = attendance.groupby('employee_id').agg(
    total_absences=('status', lambda x: (x == 'Absent').sum()),
    total_late_days=('status', lambda x: (x == 'Late').sum())
).reset_index()

perf_agg = performance_reviews.groupby('employee_id').agg(
    avg_performance_score=('rating', 'mean'),
    latest_performance_score=('rating', 'last'),
    review_count = ('rating','count')
).reset_index()

leave_agg = leave_requests.groupby('employee_id').agg(
    total_leaves_taken=('days_requested', 'sum')
).reset_index()

salary_history['salary_increase'] = salary_history['new_salary'] - salary_history['old_salary']
salary_agg = salary_history.groupby('employee_id').agg(
    old_salary=('old_salary', 'min'),
    employee_max_salary=('new_salary', 'max'),
    salary_change_count= ('salary_history_id','count'),
    total_salary_increase = ('salary_increase','sum')
).reset_index()

# 3. Join into Master DataFrame
df = (
    employees
    .merge(jobs, on='job_id', how='left',suffixes=('','_job'))
    .merge(departments, on='department_id', how='left',suffixes=('','_dept'))
    .merge(locations, on='location_id', how='left',suffixes=('','_loc'))
    .merge(emp_proj_agg, on='employee_id', how='left')
    .merge(attendance_agg, on='employee_id', how='left')
    .merge(perf_agg, on='employee_id', how='left')
    .merge(leave_agg, on='employee_id', how='left')
    .merge(salary_agg, on='employee_id', how='left')
)
print(df.columns)
if 'max_salary' in df.columns:
    df = df.rename(columns={'max_salary': 'job_max_salary'})
# Fill unrecorded activity metrics with zero
zero_fill_cols = ['total_projects', 'total_hours_allocated', 'total_absences', 'total_late_days', 'total_leaves_taken']
df[zero_fill_cols] = df[zero_fill_cols].fillna(0)
print(df.columns)

'''
Predictive Modeling Use Cases
ML Engineer Target (employment_status): Binary classification predicting employee attrition
 (Active vs Terminated) based on salary metrics, project hours, and tenure.

Data Scientist Target (salary): Regression model to identify features driving pay gaps across departments and job titles.

Data Analyst Focus: Feature interaction between project allocation 
(total_hours_allocated) and frequency of salary raises (salary_changes_count).

'''

df = df.rename(columns={
    'max_salary_x': 'job_max_salary',      #job_max_salary — the ceiling of the official pay band for that job title.
    'max_salary_y': 'employee_max_salary'  # What this employee earned
})

#Fill missing activity metrics with zero for unrecorded activity
'''
checkout if its empty put zero
zero_fill_cols = [
    'total_projects', 'total_hours_allocated', 'total_absences', 
    'total_late_days', 'total_leaves_taken', 'salary_change_count', 'total_salary_increase'
]
df[zero_fill_cols] = df[zero_fill_cols].fillna(0)

'''
df['hire_date'] = pd.to_datetime(df['hire_date'])
today = pd.Timestamp.today().normalize()
df['tenure_years'] = (today - df['hire_date']).dt.days/365.25
# now checking for churn
df['is_churned'] = (df['employment_status'].str.lower() !='active').astype(int)

# 3. Salary position in job band & compliance check
# Prevent division by zero if min_salary == max_salary
#Using employee_max_salary in that formula would produce something like
# "how close is this person's current pay to the highest they've ever made"

# 1. salary position within the JOB's official band (0 = at minimum, 1 = at maximum, >1 = above band max)
# guard against min_salary == job_max_salary to avoid dividing by zero
band_width = df['job_max_salary'] - df['min_salary']
df['salary_band_position'] = np.where(
    band_width == 0,
    np.nan,  # can't compute a meaningful position if the band has no width
    (df['salary'] - df['min_salary']) / band_width
)
print(df['salary_band_position'])

#compliance flag — paid below the official minimum for their role
df['below_job_minimum'] = df['salary'] < df['min_salary']
# 3. flag — paid above the official ceiling for their role (also worth knowing)
df['above_job_maximum'] = df['salary'] > df['job_max_salary']

# how far can employee salary can change
df['salary_vs_own_salary'] = df['salary'] - df['employee_max_salary']
df['salary_below_own_peak'] = df['salary'] < df['min_salary']

# 5. Workload ratio - hours per project
df['hours_per_project'] = df['total_hours_allocated'] / df['total_projects'].replace(0,np.nan)

df['tenure_group'] = pd.cut(df['tenure_years'],bins=[0, 1, 3, 5, 10, 50],
                            labels=['<1yr', '1-3yr', '3-5yr', '5-10yr', '10yr+'],
                            include_lowest=True)



#unique Identifiers and date columns
id_and_date_cols = ['employee_id', 'first_name', 'last_name', 'email', 'phone',
                     'hire_date', 'date_of_birth', 'termination_date', 'manager_id',
                     'job_id', 'department_id', 'location_id']
### for skew
numerical_candidates = [
    'salary', 'min_salary', 'job_max_salary', 'employee_max_salary',
    'salary_band_position', 'salary_vs_own_peak',
    'total_hours_allocated', 'hours_per_project', 'total_salary_increase', 'tenure_years',
    'total_projects', 'total_absences', 'total_late_days', 'total_leaves_taken',
    'salary_change_count', 'review_count', 'avg_performance_score', 'latest_performance_score'
]

numerical_candidates = [c for c in numerical_candidates if c in df.columns]
print(numerical_candidates)

categorical_nominal  = [ c for c in  ['gender', 'employment_status',
                                    'department_name', 'city', 'country'] if c in df.columns]

# ordinal categoricals  — order matters, one-hot would throw that away
categorical_ordinal = ['tenure_group']

ordinal_categorical = ['job_title']
job_hierarchy = [['Junior', 'Mid', 'Senior', 'Lead', 'Manager', 'Director']]


print(((df['is_churned']==1).sum()))

for col in numerical_candidates:
    print(df[col].name ,df[col].skew())


########### graph for QQ and Histogram
import matplotlib.pyplot as plt
import seaborn as sns

'''
def plot_distribution_diagnostics(dataframe, num_cols):
    """Histogram + Q-Q plot per column, and prints skew so the transform choice is data-driven."""
    skew_report = {}
    for col in num_cols:
        data = dataframe[col].dropna()
        skew_val = stats.skew(data)
        skew_report[col] = skew_val

        fig, axes = plt.subplots(1, 2, figsize=(12, 3.5))
        sns.histplot(data, kde=True, ax=axes[0], color='skyblue')
        axes[0].set_title(f'{col}  (skew={skew_val:.2f})')
        stats.probplot(data, dist="norm", plot=axes[1])
        axes[1].set_title(f'Q-Q: {col}')
        plt.tight_layout()
        plt.show()
    return skew_report


skew_report = plot_distribution_diagnostics(df, numerical_candidates)
print("\nSkew per column:", skew_report)

''' ####
# ======================================================================
# STEP 4 — TRANSFORM DECISION, based on the measured skew above
#
#   |skew| <= 1                          -> no transform, just scale
#   skew > 1 AND all values > 0          -> log1p   (dollar amounts, hours: strictly positive, wide range)
#   skew > 1 AND has zeros (count data)  -> sqrt     (absences, late days: zero-inflated counts)
#   contains negatives / unclear shape   -> Yeo-Johnson (handles zero/negative, picks its own lambda)
'''
salary, min_salary, job_max_salary, employee_max_salary	1.74–2.24	log1p (positive $ amounts)
total_absences	1.05	sqrt (zero-inflated count)
total_salary_increase	2.08	check before deciding — see below
total_hours_allocated	0.88	no transform
total_projects	0.93	no transform
everything else	≤1	no transform


'''
'''
log1p_cols, sqrt_cols, yeo_johnson_cols, no_transform_cols = [], [], [], []

for col in numerical_candidates:
    data = df[col].dropna()
    skew_val = skew_report[col]
    has_negative = (data < 0).any()
    has_zero = (data == 0).any()

    if abs(skew_val) <= 1:
        no_transform_cols.append(col)
    elif has_negative:
        yeo_johnson_cols.append(col)  # e.g. salary_vs_own_peak can be negative
    elif has_zero:
        sqrt_cols.append(col)  # e.g. total_absences, total_late_days
    else:
        log1p_cols.append(col)  # e.g. salary, total_hours_allocated

print("\nlog1p:", log1p_cols)
print("sqrt:", sqrt_cols)
print("yeo-johnson:", yeo_johnson_cols)
print("no transform needed:", no_transform_cols)

'''

print((df['total_salary_increase'] < 0).sum(), "negative (pay cuts)")
print((df['total_salary_increase'] == 0).sum(), "zero (no raise yet)")


import numpy as np
from scipy import stats
'''
import matplotlib.pyplot as plt

for col in numerical_candidates  :
    # Create box plot
   
    plt.boxplot(df[col])
    plt.title("Basic Box Plot")
    plt.show()

'''
# Clean all column names across the DataFrame

# 1. Clean column names
df.columns = df.columns.str.strip()

# 2. Define numerical candidate columns from your schema
numerical_cols = [
    'salary', 'min_salary', 'job_max_salary', 'salary_band_position',
    'total_hours_allocated', 'total_salary_increase', 'tenure_years',
    'hours_per_project', 'total_projects', 'total_absences',
    'total_late_days', 'total_leaves_taken', 'avg_performance_score'
]
''' #### info 

# 3. Safe Outlier Calculation Loop
for col in numerical_cols:
    # Check if column actually exists in the DataFrame being used
    if col not in df.columns:
        print(f"Skipping {col}: Not found in DataFrame")
        continue

    # Ensure column is numeric
    df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calculate quantiles safely on non-null values
    clean_series = df[col].dropna()
    if not clean_series.empty:
        q1 = clean_series.quantile(0.25)
        q3 = clean_series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        print(f"{col} -> IQR: {iqr:.2f} | Bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")

## for some meaning-full outcomes i can't winsorize some outliers right? i need them if for basics and depending
# on the project we might cap it . BUT which decisions to keep them or which analytical questions to winsorize them ???

'''


"""

"""
outlier_report = []

for col in numerical_candidates:
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    mask = (df[col] < lower) | (df[col] > upper)

    outlier_report.append({
        'column': col,
        'Q1': q1,
        'Q3': q3,
        'lower_bound': lower,
        'upper_bound': upper,
        'outlier_count': mask.sum()
    })
"""  ### info 
def cap_outliers(dataframe,column,factor=1.5):

     q1 =dataframe[column].quantile(0.25)
     q3 =dataframe[column].quantile(0.75)
     iqr = q3 - q1
     lower_limit = q1 - factor * iqr
     upper_limit = q3 + factor * iqr

     dataframe[column]=dataframe[column].clip(lower_limit,upper_limit)
     return dataframe


# 4. columns that actually have real outliers worth capping (standard 1.5x factor)
cols_to_cap = ['salary', 'min_salary', 'job_max_salary', 'employee_max_salary',
               'total_hours_allocated', 'total_salary_increase']

for col in cols_to_cap:
    df = cap_outliers(df,col,factor=1.5)

df = cap_outliers(df, 'total_absences', factor=3.0)

"""


''' ### info 
With factor=3.0: upper limit = 1 + 3×1 = 4. This pushes the cutoff further out, 
so only genuinely extreme absence counts (5, 10, 20+ days)
 get capped, and normal variation is left alone.
'''







# r IQRCapper is designed for: cap them, don't delete them, so you keep the signal that "this person earns a lot"
# i havent capped here
"""
What the table is telling you

For each column: Q1/Q3 are the 25th/75th percentiles (the "normal" middle half of the data). 
lower_bound/upper_bound = Q1 - 1.5×IQR and Q3 + 1.5×IQR — anything outside that range is flagged as an outlier. 
outlier_count = how many rows fall outside.

Most columns are clean — hours_per_project, tenure_years, total_projects, 
salary_change_count, review_count all have 0 outliers. Nothing to do there.

The salary group (salary, min_salary, job_max_salary, employee_max_salary) — 
3 outliers each. These are almost certainly your genuine high earners (executives, senior leadership).
 This is exactly the case your IQRCapper is designed for: cap them, don't delete them, 
 so you keep the signal that "this person earns a lot" without letting a few extreme dollar values distort the scaler.

total_hours_allocated (14) and total_salary_increase (13). Same story — real high-workload employees
 and employees who got unusually large raises. Cap, don't drop.

total_absences — 34 outliers, which looks alarming but isn't a data problem. 
Look at its Q1/Q3: 0 and 1. Because the middle 50% of employees have between 0 and 1 absences,
 the IQR is tiny, so anyone with 3+ absences gets flagged. That's not 34 broken rows — 
 it's just what happens when you run the 1.5×IQR rule on a narrow, zero-inflated count column. 
 This is precisely why you routed it to sqrt + cap instead of leaving it raw: 
 the sqrt transform compresses that tail so it stops dominating the model.

avg_performance_score (6) and latest_performance_score (16). Same narrow-IQR effect — on a 1–5 scale,
 the bound sits at 1.5, so anyone scoring a flat 1 gets flagged. These are real low performers,
not errors. Capping them is mild and fine (it just pulls a 1.0 up toward 1.5), but there's nothing to "fix" here.

One column to treat differently: salary_band_position. Its outliers (3, with a lower bound of ‑0.465 and upper bound of 1.45) 
aren't noise — a value below 0 or above 1 means the employee is paid below the job minimum or above the job maximum,
 which you already capture explicitly in below_job_minimum/above_job_maximum. If you IQR-cap this column too,
  you'll blunt that exact signal right when it's most informative 
  (e.g. someone way overpaid relative to their band, right before they leave). 
  Recommendation: leave salary_band_position out of the IQRCapper step — let the flag columns carry that information instead.
""" # inffo about the report
outlier_report = pd.DataFrame(outlier_report)

pd.set_option('display.max_columns', None)

# Show all rows (optional - use with caution if the dataset is huge)
pd.set_option('display.max_rows', None)

# Prevent long text inside cells from getting cut off
pd.set_option('display.max_colwidth', None)
print(outlier_report)
### for corr()
print(df[numerical_candidates].corr())
sns.heatmap(df[numerical_candidates].corr(), annot=True, cmap='coolwarm')
plt.show()

##checking for vif
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# ---------------------------------------------------------
# 1. Select predictor columns
# ---------------------------------------------------------



# Keep only columns that actually exist
predictor_columns = [
    col for col in numerical_cols
    if col in df.columns
]

# ---------------------------------------------------------
# 2. Create numeric dataset for VIF
# ---------------------------------------------------------

X_vif = df[predictor_columns].select_dtypes(
    include=np.number
).copy()

# ---------------------------------------------------------
# 3. Handle missing values
# ---------------------------------------------------------

X_vif = X_vif.dropna()

# ---------------------------------------------------------
# 4. Calculate VIF
# ---------------------------------------------------------

vif_data = pd.DataFrame()

vif_data['feature'] = X_vif.columns

vif_data['VIF'] = [
    variance_inflation_factor(
        X_vif.values,
        i
    )
    for i in range(X_vif.shape[1])
]

# ---------------------------------------------------------
# 5. Sort from highest to lowest
# ---------------------------------------------------------

vif_data = vif_data.sort_values(
    by='VIF',
    ascending=False
).reset_index(drop=True)

print(vif_data)


# columns to drop
'''
Why drop min_salary and job_max_salary? salary_band_position already encapsulates both features into a normalized 
single score between $0$ and $1$. Keeping all three introduces severe multicollinearity ($VIF > 10$)
.Why drop employee_max_salary? It shares identical statistical bounds with salary ($Q1 = 59890.915$, $Q3 = 101486.54$).

''' # depends on what to find ? which columns to drop
_info_cols_to_drop = [
    # Redundant / Collinear Pairs
    'employee_max_salary',  # Exact duplicate of 'salary' statistics (Q1/Q3 are identical)
    'min_salary',  # Information captured directly in 'salary_band_position'
    'job_max_salary',  # Information captured directly in 'salary_band_position'

    # Static / Low-Signal Metrics
    'review_count',  # Heavily collinear with 'tenure_years'
    'salary_change_count',  # Heavily collinear with 'tenure_years'
]
"""
If the goal is to predict Employee Resignation (Churn Risk), the raw numbers mislead the model completely
:How the Model Sees It: The model thinks, "$\$110,000$ is greater than $90,000, so the Senior Manager must be happier 
and less likely to quit than the Engineer."The Human Reality:Suppose the normal pay range for
 that Engineer is $\$60,000$ to $\$90,000$. At $90,000, the engineer is at the absolute top of their pay bracket. 
 They feel valued, well-paid, and happy.Suppose the normal pay range
  for a Senior Manager is $\$110,000$ to $\$180,000$. At 110,000$, the manager is at the absolute bottom of their pay grade. 
  They feel underpaid, frustrated, and are actively applying for new jobs.If you feed the model raw salaries,
   the model sees the higher number ($\$110,000$) and assumes the manager is safe, completely missing the fact that 
   they are unhappy and about to quit.

Junior employees (level 0) at bottom of band → Very high churn
Senior employees (level 2) at bottom of band → Moderate churn
Executives (level 5) at bottom of band → Low churn (they're still well-paid overall)
Pattern 3: Combination with Other Features
text
Bottom of band + High absences = Almost certainly churning
Bottom of band + Short tenure = Likely churning
Bottom of band + High performance = Might stay (hoping for promotion)



job_level = How senior your ROLE is
salary_band_position = How much you get paid RELATIVE to your role

Example:
┌─────────────────────────────────────────────────────────────┐
│ VP of Engineering (job_level = 4)                          │
│ Salary: $120,000                                           │
│ VP Band: $110,000 - $180,000                               │
│ salary_band_position = (120,000 - 110,000) / (180,000 - 110,000) │
│                        = 10,000 / 70,000                   │
│                        = 0.14 (Bottom of band!)            │
│                                                             │
│ 👉 High rank (4), but LOW in their band → UNHAPPY!        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Software Engineer (job_level = 0)                          │
│ Salary: $130,000                                           │
│ Engineer Band: $60,000 - $130,000                          │
│ salary_band_position = (130,000 - 60,000) / (130,000 - 60,000) │
│                        = 70,000 / 70,000                   │
│                        = 1.0 (Top of band!)                │
│                                                             │
│ 👉 Low rank (0), but TOP of their band → HAPPY!           │
└─────────────────────────────────────────────────────────────┘



"""







import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, PowerTransformer, StandardScaler , OrdinalEncoder


# ======================================================================
# 1. CUSTOM LEAKAGE-FREE OUTLIER CAPPER
# ======================================================================
df_for_executive_analysis = df.copy()

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, PowerTransformer, StandardScaler

# ======================================================================
# STEP 1 — JOB LEVEL MAPPING (FIXED HIERARCHY)
# ======================================================================
job_level_map = {
    'Chief Executive Officer': 5,
    'VP of Engineering': 4,
    'VP of Sales': 4,
    'Engineering Manager': 3,
    'HR Manager': 3,
    'Sales Manager': 3,
    'Marketing Manager': 3,
    'Finance Manager': 3,
    'Product Manager': 3,
    'Support Team Lead': 2,
    'Senior Software Engineer': 2,  # Aligned with Senior Lead level
    'Legal Counsel': 2,  # Aligned with Senior Specialist
    'IT Systems Admin': 1,  # Mid-level specialist
    'HR Specialist': 0,
    'Customer Support Rep': 0,
    'Financial Analyst': 0,
    'Marketing Analyst': 0,
    'Sales Executive': 0,
    'Recruiter': 0,
    'Software Engineer': 0,
}

# Safely map job_title and handle any unseen/missing titles
df['job_level'] = df['job_title'].map(job_level_map).fillna(0).astype(int)


'''
Use 1.5 (Short Range) When:
Column	Why Short Range is Good
total_hours_allocated	Hours should be normal (200-500), not 2000
total_late_days	Should be 1-5 days, not 100
tenure_years	Should be 1-10 years, not 100
review_count	Should be 1-5 reviews, not 50
Use 3.0 (Wide Range) When:
Column	Why Wide Range is Good
total_salary_increase	Promotions are REAL and IMPORTANT!
total_absences	Health issues are REAL!
hours_per_project	Some projects ARE huge!
total_projects	Some employees DO work on many projects!
Simple Rule of Thumb:
text
If high values are:
  ❌ ERRORS → Use 1.5 (Short range, cut them off)
  ✅ VALID   → Use 3.0 (Wide range, keep them)

Example:
  Working 2000 hours? → ERROR → 1.5
  Getting $50k raise? → VALID → 3.0
  Being late 100 days? → ERROR → 1.5
  Taking 50 sick days? → VALID → 3.0
Summary:
Factor	Range	Keeps	Removes
1.5	SHORT/TIGHT	Only normal values	ALL extremes
3.0	WIDE/LOOSE	Normal + Valid extremes	Only extreme errors
You got it exactly right! 🎯




'''
# ======================================================================
# STEP 2 — CUSTOM LEAK-FREE IQR CAPPER
# ======================================================================
class IQRCapper(BaseEstimator, TransformerMixin):

  def __init__(self, factor=1.5):
    self.factor = factor
    self.bounds_ = []

  def fit(self, X, y=None):
    X_arr = np.asarray(X)
    self.bounds_ = []
    for col_idx in range(X_arr.shape[1]):
      col_data = X_arr[:, col_idx]
      q1 = np.percentile(col_data, 25)
      q3 = np.percentile(col_data, 75)
      iqr = q3 - q1
      lower = q1 - self.factor * iqr
      upper = q3 + self.factor * iqr
      self.bounds_.append((lower, upper))
    return self

  def transform(self, X):
    X_arr = np.asarray(X).copy()
    for col_idx, (lower, upper) in enumerate(self.bounds_):
      X_arr[:, col_idx] = np.clip(X_arr[:, col_idx], lower, upper)
    return X_arr


# ======================================================================
# STEP 3 — COLUMN GROUPS
# ======================================================================

# 1. Plain numeric continuous features (standard 1.5x cap)
numeric_cols = [
    'total_hours_allocated',
    'hours_per_project',
    'tenure_years',
    'total_late_days',
    'total_leaves_taken',
    'salary_change_count',
    'avg_performance_score'

]

# 2. Skewed continuous features (3.0x cap + Yeo-Johnson transform)
skewed_cols = ['total_absences', 'total_salary_increase']

# 3. Uncapped ordinal / ratio numeric columns (preserves extreme signals)
#    job_level and salary_band_position are scaled without capping
uncapped_numeric_cols = ['salary_band_position', 'job_level']

# 4. Categorical nominal columns
nominal_cols = ['department_name']

# 5. Columns to drop (IDs, leakage, redundant metrics, raw text)
drop_cols = [
    'employee_id',
    'first_name',
    'last_name',
    'email',
    'phone',
    'hire_date',
    'date_of_birth',
    'termination_date',
    'manager_id',
    'job_id',
    'department_id',
    'location_id',
    'employment_status',
    'salary',
    'min_salary',
    'job_max_salary',
    'employee_max_salary',
    'total_projects',
    'above_job_maximum',
    'below_job_minimum',
    'gender',
    'city',
    'country',
    'salary_vs_own_peak',
    'tenure_group',
    'job_title',
'latest_performance_score'
]

# ======================================================================
# STEP 4 — SPLIT TRAIN & TEST FIRST (STRICT LEAKAGE PREVENTION)
# ======================================================================

X = df.drop(columns=drop_cols + ['is_churned'], errors='ignore')
y = df['is_churned']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ======================================================================
# STEP 5 — SUB-PIPELINES & COLUMN TRANSFORMER
# ======================================================================

numeric_pipeline = Pipeline([
    ('impute', SimpleImputer(strategy='median')),
    ('capper', IQRCapper(factor=1.5)),
    ('scale', StandardScaler()),
])

skewed_pipeline = Pipeline([
    ('impute', SimpleImputer(strategy='median')),
    ('capper', IQRCapper(factor=3.0)),
    ('reshape', PowerTransformer(method='yeo-johnson')),
    ('scale', StandardScaler()),
])

uncapped_numeric_pipeline = Pipeline([
    ('impute', SimpleImputer(strategy='median')),
    ('scale', StandardScaler()),
])

nominal_pipeline = Pipeline([
    ('impute', SimpleImputer(strategy='constant', fill_value='Unknown')),
    ('encode', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
])

preprocessor = ColumnTransformer([
    ('numeric', numeric_pipeline, numeric_cols),
    ('skewed', skewed_pipeline, skewed_cols),
    ('uncapped_numeric', uncapped_numeric_pipeline, uncapped_numeric_cols),
    ('nominal', nominal_pipeline, nominal_cols),
])

# ======================================================================
# STEP 6 — FIT ON TRAIN ONLY, TRANSFORM BOTH
# ======================================================================

X_train_ready = preprocessor.fit_transform(X_train)
X_test_ready = preprocessor.transform(X_test)

print('X_train ready shape:', X_train_ready.shape)
print('X_test ready shape :', X_test_ready.shape)

print(df['job_title'].unique())

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
"""log_reg = LogisticRegression(max_iter=1000, random_state=42)
log_reg.fit(X_train_ready, y_train)
y_proba_lr = log_reg.predict_proba(X_test)[:, 1]
y_pred_lr = log_reg.predict(X_test)
#. probability of churn, for ROC-AUC (needs a score, not just 0/1)

print(f"ROC-AUC Score: {roc_auc_score(y_test, y_proba_lr):.4f}")
print(f"Accuracy:      {accuracy_score(y_test, y_pred_lr):.4f}")
print(f"Precision:     {precision_score(y_test, y_pred_lr):.4f}")
print(f"Recall:        {recall_score(y_test, y_pred_lr):.4f}")
print(f"F1 Score:      {f1_score(y_test, y_pred_lr):.4f}")
"""

# Initialize & Train Random Forest Model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_ready, y_train)

# Predict Probabilities and Binary Class
y_pred_proba = model.predict_proba(X_test_ready)[:, 1]
y_pred = model.predict(X_test_ready)

# Evaluate Metrics
print(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
print(f"Accuracy:      {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision:     {precision_score(y_test, y_pred):.4f}")
print(f"Recall:        {recall_score(y_test, y_pred):.4f}")
print(f"F1 Score:      {f1_score(y_test, y_pred):.4f}")


# Check train vs test performance
train_pred = model.predict(X_train_ready)
train_acc = accuracy_score(y_train, train_pred)

print(f"\n📊 Overfitting Check:")
print(f"Train Accuracy: {train_acc:.4f}")
print(f"Test Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
print(f"Difference:     {train_acc - accuracy_score(y_test, y_pred):.4f}")

# If difference < 0.05 → No overfitting (GOOD!)
# If difference > 0.10 → Overfitting (BAD!)
print(y_test.value_counts())
print(y_pred_proba)


# if i want to improve the model then
"""
# Adjust the decision threshold
threshold = 0.6  # Default is 0.5
y_pred_adjusted = (y_pred_proba > threshold).astype(int)

print(f"\n📊 With threshold = {threshold}:")
print(f"Precision: {precision_score(y_test, y_pred_adjusted):.4f}")
print(f"Recall:    {recall_score(y_test, y_pred_adjusted):.4f}")
print(f"F1 Score:  {f1_score(y_test, y_pred_adjusted):.4f}")

# Higher threshold = More precision, Less recall
# Lower threshold = More recall, Less precision

"""




""" #info
2. y_pred_probaThis array shows the raw probability scores output by your Random Forest for each employee in your test set
, representing the model's estimated likelihood ($0.00$ to $1.00$) that an employee will churn:Low Scores (0.00, 0.02, 0.05): 
The model is $95\%–100\%$ confident these employees will stay. Most scores fall in this low range, 
aligning with the 86 non-churners.High Scores (0.79, 0.85, 0.72): The model is $70\%–85\%$ confident these employees will churn.
Borderline Scores (0.52, 0.58, 0.28): The model senses risk, but the signal is weaker or less certain.
How Binary Decisions Are MadeBy default, scikit-learn applies a 0.50 decision threshold:
Probability > 0.50$  Flagged as 1 (Churn)Probability < 0.50  Flagged as 0 (Stay)
Looking closely at your high scores:0.79, 0.52, 0.63, 0.71, 0.76, 0.74, 0.78, 0.59, 0.85, 0.78, 0.58, 0.67, 0.79, 0.70,
 0.72, 0.60There are 16 values $\ge 0.50$.Comparing this against your actual results ($14$ real churners):
 14 True Positives: The model correctly caught all 14 actual churners ($100% Recall).
 2 False Positives: The model flagged 2 non-churners who had probabilities around $0.52$ and $0.58$
  (87.5% Precision, calculated as (14/16).
""" # info  about the accuracy ,recall and model


'''
1. Raw salary vs. salary_band_positionWhy Drop salary?
Raw salary numbers create major noise for machine learning models. 
A Software Engineer making $\$80,000$ might be extremely well-paid for their role, 
while a Senior Manager making $\$110,000$ might be severely underpaid relative to industry standards. 
If you feed raw numbers like $\$80,000$ or $\$110,000$ into a model, it only sees "higher number vs. lower number" 
and completely misses whether the person feels fairly compensated.
Why Use salary_band_position Instead?salary_band_position normalizes salary across roles into a relative scale (typically $0.0$ to $1.0$):$0.0$ = At the absolute minimum of their pay grade (underpaid relative to peers).$0.5$ = Dead center of their pay grade.$1.0$ = At the maximum salary cap for their role.This allows the model to learn a single universal rule: "Employees sitting near $0.0$ in their salary band have a high risk of churning," regardless of whether they make $\$40,000$ or $\$200,000$.2. Why Include total_late_days & total_leaves_taken?These two behavioral features act as early warning indicators (leading indicators) of employee burnout or quiet quitting:total_late_days: When an employee who was previously punctual starts showing up late frequently, it often signals a loss of engagement, dissatisfaction, or job search activity taking place outside of work.total_leaves_taken: Taking frequent or sudden leaves often precedes a formal resignation—either because the employee is attending job interviews or taking time off due to burnout.Combined with performance and compensation data, these metrics give the model direct behavioral signals before an employee actually submits their resignation.3. salary_change_count & Won't it Disadvantage People Whose Salary Didn't Change?Won't it penalize people with 0 changes?
That is actually the exact signal you want the model to pick up!If an employee has been with the company for 4 years (tenure_years = 4) but their salary_change_count is 0, it indicates promotion stagnation. Stagnant compensation is one of the single biggest drivers of employee turnover. The model compares tenure_years against salary_change_count to detect who is stuck without career progression.For New Hires: Having salary_change_count = 0 is expected and won't trigger churn risk because their tenure_years is also low (e.g., $0.5$ years).For Tenured Staff: Having salary_change_count = 0 after several years flags a high flight risk.4. avg_performance_score vs. latest_performance_score (Redundancy & Trajectory)Why keep both if they seem similar?
Keeping both allows the model to calculate performance trajectory (trend over time) without requiring a complex time-series model:High avg_performance_score + Low latest_performance_score: Indicates a top performer whose engagement is rapidly crashing (a major red flag for imminent churn or burnout).Low avg_performance_score + High latest_performance_score: Indicates an employee who started slow but is improving and getting momentum.Equal Scores: Represents consistent, steady performance over time.By feeding both into a linear or tree-based model, the model evaluates the gap between past average and recent standing.5. job_level vs. job_titleWhy Drop job_title?
Raw job titles present high-cardinality categorical data (e.g., 20+ distinct strings like "VP of Sales", "HR Specialist"). If you one-hot encode them, you create 20 sparse binary columns. Furthermore, unique roles like "CEO" might only appear once in your dataset, causing linear models to overfit or produce unreliable coefficients.How job_level Works:job_level maps every job title into a numeric ordinal rank (0 to 5):$$\text{Level 0 (Entry/Specialist)} \rightarrow \text{Level 1 (Mid)} \rightarrow \text{Level 2 (Senior/Lead)} \rightarrow \text{Level 3 (Manager)} \rightarrow \text{Level 4 (VP)} \rightarrow \text{Level 5 (CEO)}$$This compresses 20 messy strings into a single integer column that directly conveys organizational authority and baseline responsibility.6. Capping Discrete Ordinal Integers (IQRCapper Issue)What was the problem with putting job_level in numeric_pipeline?
The standard IQRCapper uses the Interquartile Range ($IQR = Q3 - Q1$) to clip extreme values.In a typical corporate dataset:~80–90% of employees are at Level 0, 1, or 2.Level 4 (VPs) and Level 5 (CEOs) make up less than 5% of the company.Because Executives are rare statistical outliers, IQRCapper would view Level 4 and Level 5 as "outliers" and clip them down to ~3.5. This would artificially flatten your hierarchy and erase the distinction between an Executive and a Manager!The Fix Implemented in the Final Pipeline:job_level was moved into uncapped_numeric_pipeline alongside salary_band_position. This skips outlier capping entirely and only applies StandardScaler(), preserving exact values (0 through 5) without clipping high-level roles.


''' # info about the columns

# Create an analysis DataFrame from X_test
test_analysis = X_test.copy()
test_analysis['churn_risk_score'] = y_pred_proba

# Churn risk by department
dept_risk = (
    test_analysis.groupby('department_name')['churn_risk_score']
    .agg(['count', 'mean', 'max'])
    .reset_index()
)
print(dept_risk.sort_values(by='mean', ascending=False))



import re
import pandas as pd

import re
import pandas as pd

####anothter way of analysing job level
def extract_job_level(title):
    if pd.isna(title):
        return 2  # Default to Mid-level

    title = str(title).lower().strip()

    # 1. Catch Sales/Account Executives FIRST so they don't trigger C-suite rules
    if re.search(r'\b(sales executive|account executive|customer executive)\b', title):
        # Optional: check if they are senior sales execs
        if 'senior' in title or 'sr' in title:
            return 3
        return 1  # Standard sales rep level

    # 2. Catch true C-Suite and Executive Management (Level 5)
    elif re.search(r'\b(vp|vice president|chief|ceo|cto|cfo|cmo|executive director|president)\b', title):
        return 5

    # 3. Catch Directors / Department Heads (Level 4)
    elif re.search(r'\b(director|head of|manager|supervisor)\b', title):
        return 4

    # 4. Catch Seniors / Leads (Level 3)
    elif re.search(r'\b(senior|sr|lead|principal|staff|expert)\b', title):
        return 3

    # 5. Catch Juniors / Entry Level (Level 1)
    elif re.search(r'\b(junior|jr|associate|assistant|entry|intern|trainee)\b', title):
        return 1

    # 6. Default Mid-Level (Level 2)
    else:
        return 2


# Apply the fix
df['job_level_part_2'] = df['job_title'].apply(extract_job_level)

# Example Usage on a new dataset:
# df['job_level'] = df['job_title'].apply(extract_job_level)
# Check average salary per level to ensure scores scale logically
#print(df.groupby('job_level_part_2')['salary'].agg(['count', 'mean', 'median']))
# See every unique job title currently mapped to Level 5
#print(df[df['job_level_part_2'] == 5]['job_title'].value_counts())

# Run this in the SAME cell as the mapping, right after it
df['job_level'] = df['job_title'].map(job_level_map).fillna(0).astype(int)
print(df['job_level'].value_counts())          # sanity check right away
print(df['job_title'].map(job_level_map).isna().sum())  # should be 0, confirming no fillna needed

# Or show unique titles by level
for level in sorted(df['job_level'].unique()):
    titles = df[df['job_level'] == level]['job_title'].unique()
    print(f"\nLevel {level}: {titles}")

print(df.groupby('job_level')['salary'].agg(['count', 'mean', 'median']))
# Count people in job_level 5
count_level_5 = (df['job_level'] == 5).sum()
print(f"Number of people in job_level 5: {count_level_5}")

print(("#_____________________________________________________________________________________________________________________#"))

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

# =============================================
# STEP 1: CUSTOM IQR CAPPER
# =============================================
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# =============================================
# STEP 1: CUSTOM IQR CAPPER
# =============================================

class IQRCapper(BaseEstimator, TransformerMixin):
    def __init__(self, factor=1.5):
        self.factor = factor

    def fit(self, X, y=None):
        X_df = pd.DataFrame(X)
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        for col in X_df.columns:
            q1, q3 = X_df[col].quantile([0.25, 0.75])
            iqr = q3 - q1
            self.lower_bounds_[col] = q1 - self.factor * iqr
            self.upper_bounds_[col] = q3 + self.factor * iqr
        return self

    def transform(self, X):
        X_df = pd.DataFrame(X).copy()
        for col in X_df.columns:
            X_df[col] = X_df[col].clip(self.lower_bounds_[col], self.upper_bounds_[col])
        return X_df.values

# =============================================
# STEP 2: DEFINE FEATURE GROUPS
# =============================================

num_cols_to_cap = ['total_salary_increase', 'total_absences']
num_cols_part_2 = [
    'tenure_years',
    'total_late_days',
    'total_leaves_taken',
    'avg_performance_score',
    'job_level',
    #'total_projects',
    'salary_change_count',
]
cate_col = ['department_name', 'gender']

# =============================================
# STEP 3: BUILD PREPROCESSOR WITH FIXES
# =============================================

# FIX 1: Add imputation + handle_unknown for categorical
cat_pipeline = Pipeline([
    ('impute', SimpleImputer(strategy='constant', fill_value='Unknown')),  # ← Fill NaN
    ('encode', OneHotEncoder(
        drop='first',
        sparse_output=False,
        handle_unknown='ignore'  # ← Ignore unknown categories
    ))
])

# Pipeline for skewed features: log -> cap -> scale
combined_pipeline = Pipeline([
    ('log1p', FunctionTransformer(np.log1p, validate=True)),
    ('capper', IQRCapper(factor=1.5)),
    ('scaler', StandardScaler()),
])

# Column Transformer
preprocessor = ColumnTransformer(
    transformers=[
        ('skewed_num', combined_pipeline, num_cols_to_cap),
        ('plain_num', StandardScaler(), num_cols_part_2),
        ('cat', cat_pipeline, cate_col),  # ← Use the fixed pipeline
    ]
)

# =============================================
# STEP 4: PREPARE DATA
# =============================================

df_part_2 = df.copy()

X = df_part_2[num_cols_part_2 + num_cols_to_cap + cate_col]
y_log = np.log1p(df_part_2['salary'])

# =============================================
# STEP 5: SPLIT DATA
# =============================================

X_train, X_test, y_train_log, y_test_log = train_test_split(
    X, y_log, test_size=0.2, random_state=42
)

# =============================================
# STEP 6: PROCESS DATA
# =============================================

X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

# =============================================
# STEP 7: TRAIN MODEL
# =============================================

model = LinearRegression()
model.fit(X_train_processed, y_train_log)

# =============================================
# STEP 8: PREDICT AND EVALUATE
# =============================================

y_pred_log = model.predict(X_test_processed)

# Convert back to dollars
r2 = r2_score(y_test_log, y_pred_log)
y_pred_dollars = np.expm1(y_pred_log)
y_test_dollars = np.expm1(y_test_log)
mae = mean_absolute_error(y_test_dollars, y_pred_dollars)

print(f'Log-Scale R2 Score: {r2:.4f}')
print(f'Actual Dollars MAE: ${mae:,.2f}')

# =============================================
# STEP 9: CHECK FOR UNKNOWN CATEGORIES
# =============================================

# See what categories were in training vs test
for col in cate_col:
    train_cats = set(X_train[col].dropna().unique())
    test_cats = set(X_test[col].dropna().unique())
    unknown = test_cats - train_cats
    if unknown:
        print(f"\n⚠️ Unknown categories in '{col}': {unknown}")
    else:
        print(f"\n✅ No unknown categories in '{col}'")


#_____________________________________________________________________________________________________________________
# Linear Regression works like an automatic detective: it scans employee records and assigns
# a dollar value ($) to every qualification, role, and demographic trait.
# "If a man and a woman have the exact same job title, same tenure, and same performance score, are they getting paid the same?"
'''
 Key Differences
Aspect	Churn Prediction	Salary Prediction
Type	Classification	Regression
Target	is_churned (0/1)	salary ($)
Question	"Will they leave?"	"How much do they earn?"
Output	Probability (0-1)	Dollar amount ($)
Model	RandomForestClassifier	LinearRegression
Metrics	Accuracy, Recall, F1	R², MAE
Target Transform	None	Log transform (log1p)
Capping Factor	1.5 & 3.0	1.5 only
Categorical Encoding	OneHotEncoder	OneHotEncoder
Part 4: Why Different Approaches?
Churn Prediction (Classification):
python
# Why RandomForestClassifier?
# - Handles non-linear relationships
# - Works well with mixed data types
# - Gives feature importance
# - Robust to outliers

# Why no target transform?
# - Target is binary (0/1)
# - Can't log transform binary values
# - Already bounded
Salary Prediction (Regression):
python
# Why LinearRegression?
# - Simple and interpretable
# - Works well with linear relationships
# - Fast to train
# - Coefficients are meaningful

# Why log transform target?
# - Salary is right-skewed (1.74)
# - Log makes it more normal
# - Predictions become percentages
# - Handles outliers better
Part 5: The Different Capping Factors
Churn Prediction:
python
# Two different factors used
numeric_pipeline = Pipeline([
    ('capper', IQRCapper(factor=1.5)),  # Normal features
])

skewed_pipeline = Pipeline([
    ('capper', IQRCapper(factor=3.0)),  # Skewed features (salary_increase, absences)
])
Salary Prediction:
python
# Only one factor used
combined_pipeline = Pipeline([
    ('capper', IQRCapper(factor=1.5)),  # All capped features
])
Why Different?
Prediction	Factor	Why
Churn	1.5 for normal	Hours, tenure shouldn't be extreme
Churn	3.0 for skewed	Promotions, absences are valid extremes
Salary	1.5 for all	Simpler approach, target is log-transformed
Part 6: Visual Comparison
Churn Prediction Flow:
text
Employee Data
    ↓
Preprocessing (impute, cap, scale, encode)
    ↓
RandomForestClassifier
    ↓
Probability of Churn (0.0 - 1.0)
    ↓
Threshold (0.5)
    ↓
Prediction: Churn (1) or Stay (0)
Salary Prediction Flow:
text
Employee Data
    ↓
Preprocessing (log, cap, scale, encode)
    ↓
LinearRegression
    ↓
Predicted Log Salary
    ↓
np.expm1() - Convert back
    ↓
Predicted Salary ($)
Part 7: Which One to Use?
Goal	Use This	Why
Identify who will leave	Churn Prediction	Classification gives probability
Set fair salaries	Salary Prediction	Regression gives dollar amount
Retention planning	Churn Prediction	Know who's at risk
Budget planning	Salary Prediction	Know expected costs
HR compliance	Salary Prediction	Ensure fair pay
Part 8: Combined Analysis
You Can Use Both Together:
python
# Step 1: Predict who will churn
churn_prob = churn_model.predict_proba(X_test)[:, 1]

# Step 2: Predict their salary
predicted_salary = salary_model.predict(X_test_processed)

# Step 3: Combined analysis
analysis = pd.DataFrame({
    'employee_id': test_ids,
    'churn_risk': churn_prob,
    'predicted_salary': predicted_salary,
    'actual_salary': y_test_dollars
})

# Find high-risk employees who are underpaid
high_risk_underpaid = analysis[
    (analysis['churn_risk'] > 0.7) & 
    (analysis['predicted_salary'] > analysis['actual_salary'])
]

print(f"High-risk underpaid employees: {len(high_risk_underpaid)}")
# These employees need immediate attention!
🎯 Summary
Aspect	Churn Prediction	Salary Prediction
What it predicts	Will they leave?	How much do they earn?
Output	Probability (0-1)	Dollars ($)
Model type	Classification	Regression
Algorithm	RandomForest	LinearRegression
Metrics	ROC-AUC, Recall, F1	R², MAE
Your Result	98% accuracy, 100% recall	R²=0.84, MAE=$10,696
Use case	Retention planning	Budget planning
The Key Insight:
text
Both models are EXCELLENT! 🎉

Churn Model: 98% accurate, caught ALL 14 churners
Salary Model: 84% accurate, off by only $10k

Together, they give you:
1. WHO is at risk of leaving
2. HOW MUCH they should be paid

Use both for complete HR analytics!



# Step 1: Predict who will churn
churn_prob = churn_model.predict_proba(X_test)[:, 1]

# Step 2: Predict their salary
predicted_salary = salary_model.predict(X_test_processed)

# Step 3: Combined analysis
analysis = pd.DataFrame({
    'employee_id': test_ids,
    'churn_risk': churn_prob,
    'predicted_salary': predicted_salary,
    'actual_salary': y_test_dollars
})

# Find high-risk employees who are underpaid
high_risk_underpaid = analysis[
    (analysis['churn_risk'] > 0.7) & 
    (analysis['predicted_salary'] > analysis['actual_salary'])
]

print(f"High-risk underpaid employees: {len(high_risk_underpaid)}")
# These employees need immediate attention!

'''
