from heapq import merge

import pandas as pd
from PIL.ImageCms import Flags
from numpy.testing.print_coercion_tables import print_new_cast_table
from pandas import read_sql
from sqlalchemy import create_engine



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
attendance = pd.read_sql("SELECT * FROM employees;", engine)
leave_requests = pd.read_sql("SELECT * FROM employees;", engine)
performance_reviews = pd.read_sql("SELECT * FROM employees;", engine)

 ########## Basics #############


'''
query = """
    SELECT employee_id, first_name, last_name, salary 
    FROM employees 
    WHERE salary > 50000 
    ORDER BY salary DESC;
"""

df = pd.read_sql(query, engine)
'''
### write if there is any missing values :
#pandas
check_cols=['employee_id', 'first_name', 'last_name', 'email',
              'hire_date', 'department_id', 'salary', 'employment_status']
missing_col= employees[check_cols].isnull().sum()
#or missing_mask = employees[check_cols].isnull().any(axis=1)
print(missing_col)
## using filtering
print("____________using filtering method______________-")
print(employees[employees['department_id'].isnull()])

#using sql

missing_query = """
select * from employees where employee_id is null or first_name is null or last_name is null or department_id is null
"""
missing_col_sql = pd.read_sql(missing_query,engine)
print(missing_col_sql)

#### using coalease and fillna method ###########
print("  ___________ using coalease and fillna method ____________")
### pandas using the fillna method to fill a dpet_id
employees['department_id']= employees['department_id'].fillna(1)
print(employees.isnull().sum())
#also filling the termination_Date
employees["filled_date"]=employees['termination_date'].fillna(pd.Timestamp.today().normalize())
result1=employees[['first_name','filled_date']]
print(result1)

#sql
coalesce_query= """
select first_name,department_id,coalesce(department_id,1) as filled_Data from employees

"""
colesce_query_q=pd.read_sql(coalesce_query,engine)
print(colesce_query_q)
coalesce_query1 = """
select first_name,termination_date,coalesce(termination_date,current_date()) as new_date_termination from employees
"""
print("Q1. Rank employees by salary within each department (top 1)")
#### Q1. Rank employees by salary within each department (top 1)
merged=pd.merge(employees,departments,on='department_id',how='inner')
merged['dept_sal_ranking']=merged.groupby('department_name')['salary'].rank(method='max',ascending=False)
print(merged)
q1=merged.loc[merged['dept_sal_ranking']<=1,['first_name','salary','dept_sal_ranking','department_name']]
print(q1[['first_name','salary','dept_sal_ranking','department_name']])
#or using boolean
q1=merged[merged['dept_sal_ranking']<=1][['first_name','department_name','salary']]
print(q1)
### now for sql-
Q1_sql = """
select * from ( select e.first_name,d.department_name, rank () over ( partition by d.department_name order by e.salary)
as dept_avg_ranking from employees e join departments d on d.department_id=e.department_id ) t where dept_avg_ranking<=1
"""
q1_sql_ans=pd.read_sql(Q1_sql,engine)
print(q1_sql_ans.head(3))
print("____________________________________________________________")
print("Question 2: Find salary difference between employees and department average  Is each employee paid above or below their deppt")
#### Q2 -- Question 2: Find salary difference between employees and department average  Is each employee paid above or below their department's average?
# merged=employees[employees['employment_status'].str.lower()=='active'].merge(departments,on='department_id')
active= employees[employees['employment_status'].str.lower()=='active'].copy()
merged=pd.merge(active,departments,on='department_id',how='inner')
merged['dept_avg_salary']=merged.groupby('department_name')['salary'].transform('mean')
merged['dept_salary_difference']=merged['salary']-merged['dept_avg_salary']
#classify
merged['performance_rating']='average'
merged.loc[merged['salary']>merged['dept_avg_salary'],'performance_rating'] = 'Above AVG'
merged.loc[merged['salary'] < merged['dept_avg_salary'], 'performance_rating'] = 'Below average'
q2=merged[['first_name','department_name','dept_avg_salary','dept_salary_difference','performance_rating']]
print(q2)
#### Q2 for sql
Q2_sql = """
select e.first_name,d.department_name, avg(e.salary) over ( partition by d.department_name) as dept_avg_salary,
e.salary-avg(e.salary) over (partition by d.department_name) as difference_Sal,
case when e.salary> avg(e.salary) over (partition by d.department_name) then 'TOP SALARY'
     when e.salary<avg(e.salary) over (partition by d.department_name) then 'Bottom salary'
     else 'Average'
     end as performance_rating from employees e join departments d on e.department_id=d.department_id
"""
Q2=pd.read_sql(Q2_sql,engine)
print(Q2.head(3))
print("________________________________________")
### Question 3 : Q3. Calculate cumulative salary cost by hire date
# Business Question
# As employees joined the company, how did total salary commitment grow?
# ###############
active = employees[employees['employment_status'] == 'Active'].sort_values('hire_date').copy()
active['running_total_salary']=active['salary'].cumsum()
active['cumulative_employee_count']=range(1,len(active)+1)
q3 = active[['first_name', 'hire_date', 'salary',
             'running_total_salary', 'cumulative_employee_count']]
print(q3)
###sql part for Q3
Q3_sql= """
select first_name,salary,sum(salary) over (order by hire_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as Cum_salary,
count(*) over (order by hire_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as total_emp  from employees
where employment_status='Active'
"""
Q3_SQL3=pd.read_sql(Q3_sql,engine)
print(Q3_SQL3)



#Q4. Find departments whose average salary is above company averageBusiness Question
#Which departments have higher-than-company-average salaries?

active = employees[employees['employment_status'] == 'Active']
dept_avg=active.groupby('department_id')['salary'].mean().reset_index(name='avg_dept_salary')
company_avg=active['salary'].mean()
dept_avg=pd.merge(dept_avg,departments[['department_id','department_name']],on='department_id',how='inner')
dept_avg['company_avg_salary']=company_avg
dept_avg['dept_Avg_salary']=dept_avg['avg_dept_salary']
dept_avg['salary_difference']=dept_avg['dept_Avg_salary']-dept_avg['company_avg_salary']
Q4=dept_avg[dept_avg['dept_Avg_salary']>dept_avg['company_avg_salary']].sort_values('salary_difference',ascending=False)
print(Q4[['department_name','avg_dept_salary','company_avg_salary','salary_difference']])


### SQL
Q4_sql="""
with dept_average as (
select avg(salary) as avg_dept_salary,department_id from employees group by department_id
),
company_avg as ( select avg(salary) as avg_comp_salary from employees)

select d.department_name,da.avg_dept_salary as department_Average,ca.avg_comp_salary as company_Avg,
da.avg_dept_salary-ca.avg_comp_salary as salary_difference
from dept_average da join departments d
on da.department_id=d.department_id cross join company_avg ca where da.avg_dept_salary>ca.avg_comp_salary

"""
# or #
Q4_or="""
select d.department_name,avg(e.salary) as Avg_dept_salary,(select avg(salary) from employees ) as Avg_company_salary,
avg(e.salary)- (select avg(salary) from employees ) as salary_difference
from employees e join departments d on e.department_id= d.department_id
group by department_name having avg(e.salary) > (select avg(salary) from employees )
"""
print(pd.read_sql(Q4_or,engine))

#Q5 Top 3 employee per department
active = employees[employees['employment_status'] == 'Active'].copy()
active['rank_Dept'] =active.groupby('department_id')['salary'].rank(method='first',ascending='False')
merged =pd.merge(active,departments,on='department_id',how='left')
Q5=merged[merged['rank_Dept']<=1][['first_name','department_name','salary','rank_Dept']]
print(Q5)

#### SQL ###########
Q5_SQL = """
with ranked_employee as ( select e.first_name,e.department_id,e.salary,
row_number() over ( partition by e.department_id order by e.salary desc ) as dept_rank 
from employees as e )

select d.department_name,ra.salary,ra.dept_rank from departments d join ranked_employee ra
on d.department_id=ra.department_id where dept_rank<=2
"""
print(pd.read_sql(Q5_SQL,engine))

###########   Q6  ##############
active = employees[employees['employment_status'] == 'Active'].copy()
today = pd.Timestamp.today().normalize()
active['hire_date'] = pd.to_datetime(active['hire_date'])
active['years_employed'] = ((today - active['hire_date']).dt.days / 365.25).astype(int)
active['days_employed'] = (today - active['hire_date']).dt.days
active['tenure_category']='Veterian 5 years'
active.loc[active['years_employed']<1,'tenure_category'] = 'New (<1 year)'
active.loc[active['years_employed'].between(1,2),'tenure_category'] = 'Intermediate (1-2 years)'
active.loc[active['years_employed'].between(3,4),'tenure_category'] = 'Experienced (3-4 years)'
merged = pd.merge(active,departments,on='department_id',how='inner')
Q6=merged.groupby(['department_name','tenure_category'])['days_employed'].agg(
    employ_count='count',
    avg_days_employed='mean'
)
print(Q6.head(5))


# ============================================
# Q7. Employees earning above their department average
# ============================================
active = employees[employees['employment_status'] == 'Active'].copy()
dept_avg = active.groupby('department_id')['salary'].mean().reset_index(name='dept_avg_salary')
merged = pd.merge(active, departments, on='department_id', how='inner')
merged = pd.merge(merged, dept_avg, on='department_id', how='inner')
print(merged.columns)
merged['employee_name'] = merged['first_name'] + ' ' + merged['last_name']
merged['dept_avg_salary'] = merged['dept_avg_salary'].round(2)
merged['difference'] = (merged['salary'] - merged['dept_avg_salary']).round(2)
q7 = merged[merged['salary'] > merged['dept_avg_salary']][['employee_name', 'department_name', 'salary', 'dept_avg_salary', 'difference']]
print("Q7: Employees above department average\n",q7)

####################    # ============================================
# Q8. Departments where budget exceeds salary cost
# ============================================           #############

active = employees[employees['employment_status'] == 'Active']
dept_salary = active.groupby('department_id')['salary'].sum().reset_index(name='total_salary_cost')
merged = pd.merge(departments, dept_salary, on='department_id', how='left')
merged['total_salary_cost'] = merged['total_salary_cost'].fillna(0)
print(merged['total_salary_cost'])
merged['budget_surplus'] = merged['budget']-merged['total_salary_cost']
q8 = merged[merged['budget'] > merged['total_salary_cost']][['department_name', 'budget', 'total_salary_cost', 'budget_surplus']]
print(q8)

Q8_sql="""
WITH dept_salary AS ( SELECT department_id, SUM(salary) AS total_salary_cost FROM employees
WHERE employment_status = 'Active' GROUP BY department_id ) 

select d.department_name,d.budget,coalesce(ds.total_salary_cost,0) as total_salary_cost,
d.budget-coalesce(ds.total_salary_cost,0) as budget_Surplus
from departments d left join dept_salary ds on ds.department_id=d.department_id 
where d.budget> coalesce(ds.total_salary_cost,0);

"""
########## Q9     using the previous salary function #########
active = employees[employees['employment_status'] == 'Active'].sort_values(['department_id', 'hire_date']).copy()
active['previous_hire_salary'] = active.groupby('department_id')['salary'].shift(1)
print(active['previous_hire_salary'].head(4))
merged = pd.merge(active, departments, on='department_id', how='inner')
merged['employee_name'] = merged['first_name'] + ' ' + merged['last_name']
result = merged[['employee_name', 'department_name', 'hire_date', 'salary', 'previous_hire_salary']].sort_values('hire_date', ascending=False)
print("Previous hire's salary within department\n",result.head(3))

### USING THE SQL #
Q9_sql = """
SELECT CONCAT(e.first_name, ' ', e.last_name) AS employee_name, e.hire_date,
 d.department_name, e.salary, (select avg(e2.salary) from employees e2 where e2.department_id=e.department_id
 and e2.hire_date<e.hire_date as previous_hire_salary ) from employees e JOIN departments AS d ON e.department_id = d.department_id
 WHERE e.employment_status = 'Active' ORDER BY e.hire_date DESC;
"""
Q9_sql_or = """
SELECT 
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    d.department_name,
    e.hire_date,
    e.salary AS current_hire_salary,lag(e.salary) over (partition by e.department_id order by e.hire_date) as previous_sal
    from employees AS e
JOIN departments AS d ON e.department_id = d.department_id
WHERE e.employment_status = 'Active'
ORDER BY e.hire_date DESC;

"""

###Q10 total summary of a employee
# 1. filter active, compute years employed
active = employees[employees['employment_status'] == 'Active'].copy()
today = pd.Timestamp.today().normalize()
active['hire_date']= pd.to_datetime(active['hire_date'])
active['years_employed'] = ((today - active['hire_date']).dt.days / 365.25)
merged = pd.merge(active, departments, on='department_id', how='inner')
summary = merged.groupby(['department_id', 'department_name']).agg(
    total_employees=('salary', 'count'),
    avg_salary=('salary', 'mean'),
    min_salary=('salary', 'min'),
    max_salary=('salary', 'max'),
    avg_years_employed=('years_employed', 'mean')
).reset_index()
print(summary.head(3))
summary['department_salary_tier'] = 'Cost Efficient Department'
summary.loc[summary['avg_salary'] >= 75000, 'department_salary_tier'] = 'Standard Salary Department'
summary.loc[summary['avg_salary'] >= 100000, 'department_salary_tier'] = 'Premium Salary Department'
# Team size category
summary['team_size_category'] = 'Small Team'
summary.loc[summary['total_employees'] >= 3, 'team_size_category'] = 'Medium Team'
summary.loc[summary['total_employees'] >= 5, 'team_size_category'] = 'Large Team'

Q_10_Sql="""

select d.department_name,e.first_name,e.salary,
ntile(4) over (partition by e.department_id order by e.salary desc ) as salary_quarter,
round(percent_rank() over( partition by e.department_id order by e.salary desc),2) as percentile_rank
 FROM employees AS e JOIN departments AS d ON e.department_id = d.department_id
 WHERE e.employment_status = 'Active' ORDER BY d.department_name, e.salary DESC;

"""

######################
########## # Filter to keep only departments with more than 10 employees
# df_large_depts = df[df.groupby('department_id')['employee_id'].transform('count') > 10]



# Q11. Salary quartiles and percentile rank
active = employees[employees['employment_status'] == 'Active'].copy()
active['salary_quartile'] = active.groupby('department_id')['salary'].transform(
    lambda s:pd.qcut(s.rank(method='first',ascending=False),4,labels=[1,2,3,4])
)
active['percentile_rank'] = active.groupby('department_id')['salary'].rank(pct=True).round(3)
quartile_labels = {1: 'Top 25%', 2: 'Upper Middle', 3: 'Lower Middle', 4: 'Bottom 25%'}
active['quartile_label'] = active['salary_quartile'].map(quartile_labels)
merged = pd.merge(active, departments, on='department_id', how='inner')
merged['employee_name'] = merged['first_name'] + ' ' + merged['last_name']
q14 = (merged[['department_name', 'employee_name', 'salary', 'salary_quartile', 'percentile_rank', 'quartile_label']]
       .sort_values(['department_name', 'salary'], ascending=[True, False]))
print("Salary quartiles\n",q14)

Q_11_SQL="""

SELECT d.department_name, CONCAT( e.first_name, ' ', e.last_name ) AS employee_name, e.salary,
 NTILE(4) OVER ( PARTITION BY e.department_id ORDER BY e.salary DESC ) AS salary_quartile, 
 ROUND( PERCENT_RANK() OVER ( PARTITION BY e.department_id ORDER BY e.salary ), 3 ) AS percentile_rank,
 CASE WHEN NTILE(4) OVER ( PARTITION BY e.department_id ORDER BY e.salary DESC ) = 1 THEN 'Top 25%'
 WHEN NTILE(4) OVER ( PARTITION BY e.department_id ORDER BY e.salary DESC ) = 2 THEN 'Upper Middle' 
 WHEN NTILE(4) OVER ( PARTITION BY e.department_id ORDER BY e.salary DESC ) = 3 THEN 'Lower Middle' ELSE 'Bottom 25%' END AS quartile_label
 FROM employees AS e JOIN departments AS d ON e.department_id = d.department_id
 WHERE e.employment_status = 'Active' ORDER BY d.department_name, e.salary DESC;

"""

# q12
# ============================================
# Employee + department + location detail
# ============================================
active = employees[employees['employment_status'] == 'Active'].copy()
active['employee_name'] = active['first_name'] + ' ' + active['last_name']

merged = pd.merge(active, departments, on='department_id', how='inner')
merged = pd.merge(merged, locations, on='location_id', how='inner')
merged['location'] = merged['city'] + ', ' + merged['state'] + ', ' + merged['country']

result = merged[['employee_name', 'email', 'hire_date', 'salary', 'department_name', 'location', 'country']].sort_values(['department_name'])
print(result)

# ============================================
print("_____________________ Department salary analysis by location_________________________  ")
# ============================================ 13

# 1. filter active, aggregate per department
active = employees[employees['employment_status'] == 'Active']
dept_info = pd.merge(departments, active, on='department_id', how='inner') \
    .groupby(['department_id', 'budget', 'location_id']).agg(
        employee_count=('salary', 'count'),
        avg_salary=('salary', 'mean')
    ).reset_index()

print(dept_info)

# 2. merge with locations, roll up to city level
merged = pd.merge(locations, dept_info, on='location_id', how='inner')

# 3. weighted average salary per location (weighted by headcount)
merged['salary_x_count'] = merged['avg_salary'] * merged['employee_count']

result = merged.groupby(['location_id', 'city', 'state']).apply(
    lambda g: pd.Series({
        'dept_count': g['department_id'].nunique(),
        'emp_count': g['employee_count'].sum(),
        'location_avg_salary': g['salary_x_count'].sum() / g['employee_count'].sum(),
        'total_budget': round(g['budget'].sum(), 2),
        'budget_per_employee': round(g['budget'].sum() / g['employee_count'].sum(), 2)
    }), include_groups=False
).reset_index()

#include this include_group = False 0r

# First aggregate the data
result1 = merged.groupby(['location_id', 'city', 'state']).agg(
    dept_count=('department_id', 'nunique'),
    emp_count=('employee_count', 'sum'),
    total_budget=('budget', 'sum'),
    salary_x_count_sum=('salary_x_count', 'sum')
).reset_index()

# Then calculate derived columns
result1['location_avg_salary'] = (result1['salary_x_count_sum'] / result1['emp_count']).round(2)
result1['budget_per_employee'] = (result1['total_budget'] / result1['emp_count']).round(2)
result1['total_budget'] = result1['total_budget'].round(2)
result1= result1.drop('salary_x_count_sum', axis=1)
print(result1)
# Drop the temporary column


 #SQL_13
sql_13= """
with dept_info as ( select d.department_id,d.budget,d.location_id,count(e.employee_id) as employee_count,
avg(e.salary) as avg_salary from departments d join employees e on d.department_id=e.department_id group by
d.department_id,d.budget,d.location_id )

select l.city,l.state,count(df.department_id) as dept_count,sum(df.employee_count) as total_employee,
ROUND(SUM(df.avg_salary * df.employee_count) / NULLIF(SUM(df.employee_count), 0), 2) AS location_avg_salary,
ROUND(SUM(df.budget) / NULLIF(SUM(df.employee_count), 0), 2) AS budget_per_person 
from locations l  join dept_info df on
df.location_id = l.location_id group by l.location_id,l.city,l.state
"""
print(pd.read_sql(sql_13,engine))


# ============================================
# Salary distribution by job, department, location + comparison
# ============================================
# 1. filter active, merge job/department/location
active = employees[employees['employment_status'] == 'Active']
merged = pd.merge(active, jobs, on='job_id', how='inner')
merged = pd.merge(merged, departments, on='department_id', how='inner')
merged = pd.merge(merged, locations, on='location_id', how='inner')

# 2. group and aggregate, keep groups with 2+ employees
salary_summary = merged.groupby(['job_title', 'department_id', 'department_name', 'city']).agg(
    employee_count=('salary', 'count'),
    min_salary=('salary', 'min'),
    avg_salary=('salary', 'mean'),
    max_salary=('salary', 'max'),
    salary_stdv=('salary', 'std')
).reset_index()
#salary_summary = salary_summary[salary_summary['employee_count'] >= 2]
print(salary_summary)

# 3. sort so shift() lines up correctly (LAG needs matching ORDER BY)
salary_summary = salary_summary.sort_values(['job_title', 'department_name'])

# 4. LAG within each job_title, ordered by department_name
salary_summary['previous_dept_salary'] = salary_summary.groupby('job_title')['avg_salary'].shift(1)
salary_summary['difference_from_prev_dept'] = (
    salary_summary['avg_salary'] - salary_summary['previous_dept_salary']
).round(2)

result = salary_summary[['job_title', 'department_name', 'city', 'employee_count',
                          'min_salary', 'max_salary', 'difference_from_prev_dept']]
print(result)


##################'''
'''
WITH company_metrics AS ( SELECT AVG(salary) AS company_avg, MAX(salary) AS company_max 
FROM employees WHERE employment_status = 'Active' ),

ranked_employees AS ( SELECT e.employee_id, e.department_id, e.job_id, CONCAT( e.first_name, ' ', e.last_name ) AS employee_name,
e.salary, AVG(e.salary) OVER ( PARTITION BY e.department_id ) AS dept_avg,
RANK() OVER ( PARTITION BY e.department_id ORDER BY e.salary DESC ) AS dept_rank,
NTILE(100) OVER ( ORDER BY e.salary DESC ) AS salary_percentile_group 
FROM employees AS e WHERE e.employment_status = 'Active' )

SELECT re.employee_name, j.job_title, d.department_name, re.salary, ROUND(re.dept_avg, 2) AS dept_avg, re.dept_rank,
ROUND(cm.company_avg, 2) AS company_avg, ROUND(cm.company_max, 2) AS company_max, ROUND( re.salary - re.dept_avg, 2 ) AS diff_from_dept_avg,
 ROUND( re.salary - cm.company_avg, 2 ) AS diff_from_company_avg, 
 CASE WHEN re.salary_percentile_group <= 10 THEN 'Top 10%' WHEN re.salary_percentile_group <= 25 THEN 'Top 25%' 
 WHEN re.salary_percentile_group >= 75 THEN 'Bottom 25%' ELSE 'Middle 50%' END AS salary_percentile_tier 
 FROM ranked_employees AS re JOIN departments AS d ON re.department_id = d.department_id
 JOIN jobs AS j ON re.job_id = j.job_id
 CROSS JOIN company_metrics AS cm ORDER BY d.department_name, re.salary DESC;
'''

# ============================================
# Compare employees against department and company benchmarks
# ============================================
active = employees[employees['employment_status'] == 'Active'].copy()

company_avg_salary = active['salary'].mean()
company_max_salary = active['salary'].max()

active['department_avg'] = active.groupby('department_id')['salary'].transform('mean')
active['department_ranking'] = active.groupby('department_id')['salary'].rank(method='min', ascending=False)
active['salary_percentile_group'] = pd.qcut(active['salary'].rank(method='first', ascending=False), 100, labels=False) + 1

merged = pd.merge(active, departments, on='department_id', how='inner')
merged = pd.merge(merged, jobs, on='job_id', how='inner')

merged['differ_dept_avg'] = merged['salary'] - merged['department_avg']
merged['company_salary_differ'] = merged['salary'] - company_avg_salary
merged['company_avg_salary'] = company_avg_salary
merged['company_max_salary'] = company_max_salary

merged['salary_percentile'] = 'Middle 50%'
merged.loc[merged['salary_percentile_group'] <= 10, 'salary_percentile'] = 'Top 10'
merged.loc[merged['salary_percentile_group'] <= 25, 'salary_percentile'] = 'Top 25'
merged.loc[merged['salary_percentile_group'] >= 75, 'salary_percentile'] = 'Bottom 25'

result = merged[['first_name', 'job_title', 'department_name', 'salary', 'department_avg',
                 'department_ranking', 'company_avg_salary', 'company_max_salary',
                 'differ_dept_avg', 'company_salary_differ', 'salary_percentile']].sort_values(
    ['department_name', 'salary'], ascending=[True, False])
print("Employee benchmarks")




# ============================================
# LAG and LEAD together (previous + next hire salary)
# ============================================
active = employees[employees['employment_status'] == 'Active'].sort_values(['department_id', 'hire_date']).copy()
active['employee_name'] = active['first_name'] + ' ' + active['last_name']

active['previous_hire_salary'] = active.groupby('department_id')['salary'].shift(1)
active['next_hire_salary'] = active.groupby('department_id')['salary'].shift(-1)
active['diff_from_previous'] = active['salary'] - active['previous_hire_salary']

result = active[['department_id', 'employee_id', 'employee_name', 'hire_date', 'salary',
                 'previous_hire_salary', 'next_hire_salary', 'diff_from_previous']].sort_values(['department_id', 'hire_date'])
print("LAG and LEAD (previous + next hire salary)")
print(result)


#### using lag and lead as previous and after
'''
SELECT department_id,employee_id,CONCAT(first_name, ' ', last_name) AS employee_name,hire_date,salary,
    -- Get the salary of the employee hired immediately BEFORE
    LAG(salary, 1) OVER (PARTITION BY department_id ORDER BY hire_date) AS previous_hire_salary,
    -- Get the salary of the employee hired immediately AFTER
    LEAD(salary, 1) OVER (PARTITION BY department_id ORDER BY hire_date) AS next_hire_salary,
    -- Calculate salary change compared to the previous hire
    salary - LAG(salary, 1) OVER (PARTITION BY department_id ORDER BY hire_date) AS diff_from_previous
FROM employees WHERE employment_status = 'Active'ORDER BY department_id, hire_date;
'''

############# analytical questions
#  Salary Equity & Fairness Analysis
salary_equity =  employees[employees['employment_status']=='Active'].groupby('department_id').agg(
    avg_salary=('salary', 'mean'),
    max_salary=('salary', 'max'),
    min_salary=('salary', 'min'),
    salary_std=('salary', 'std'),
    employee_count=('salary', 'count')

)
print(salary_equity.columns)
print(salary_equity[['salary_std','avg_salary','employee_count']])
salary_equity['variance_risk'] = salary_equity['salary_std'] / salary_equity['avg_salary']
print(salary_equity)

'''
Why 30%? Why Not 10% or 50%?
In corporate finance and HR statistics, Std Dev / Mean is called the Coefficient of Variation (CV). 
It measures how "spread out" salaries are compared to the average salary.
Under 15% to 20% (Normal Spread): Salaries in a healthy department naturally differ a bit based on experience and performance, 
but stay relatively close to the average.30% or Higher (High Alarm Threshold): 
A 30% variation means the highest-paid person in that department is often earning 3x to 5x more than the lowest-paid person.
'''

# Reset index to make department_id a column
salary_equity = salary_equity.reset_index()
high_risk_dept = salary_equity[salary_equity['variance_risk']>0.3] #greater than 30 %
print(high_risk_dept.columns)
print(high_risk_dept[['salary_std','avg_salary','variance_risk','department_id']])

######         identity the employees                #######
employ = pd.merge(high_risk_dept,employees,on='department_id',how='left')
print(employ.columns)
today = pd.Timestamp.today().normalize()
employ['hire_date']= pd.to_datetime(employ['hire_date'])
employ['tenure_years'] = (today -employ['hire_date']).dt.days/365
#employ = employ[['department_id', 'avg_salary', 'max_salary','min_salary','salary_std','employee_count', 'variance_risk','salary'
#                 ]]
print(employ[['salary_std','avg_salary','variance_risk','department_id','salary']])
employ['salary_difference'] = employ['salary'] - employ['avg_salary']
employ['salary_percent_diff'] = (employ['salary'] - employ['avg_salary']) / employ['avg_salary'] * 100
print(employ[['department_id','salary_difference','salary_percent_diff','variance_risk']])

## checking for outliers  Method 20% Rule or IQR or Z method
employ['pay_status'] = employ['salary_percent_diff'].apply(
    lambda x : 'Overpaid' if x>20 else ('Underpaid' if x<20 else 'fair')
    )
print(employ['pay_status'])

#or use IQ  R METHOD WHEN
'''
Data is skewed or contains extreme outliers 
(e.g., 9 regular employees making $50k and 1 Director making $500k).
• Data is skewed or contains extreme high/low values.
'''
# Calculate quartiles
Q1 = employ['salary'].quantile(0.25)  # 25th percentile
Q3 = employ['salary'].quantile(0.75)  # 75th percentile
IQR = Q3 - Q1  # Middle 50% range

# Define outliers (beyond 1.5 * IQR)
'''
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

employ['pay_status'] = employ['salary'].apply(
    lambda x: 'Overpaid' if x > upper_bound 
              else ('Underpaid' if x < lower_bound 
              else 'Fair')
)

'''

# analysing those ahd more than 20 %
extreme_employees = employ[employ['salary_percent_diff']>20].sort_values('salary_percent_diff',ascending=False)
print(extreme_employees.columns)

print("____years___")

print("\n⏰ SALARY BY TENURE (Risky Departments):")

employ['tenure_group'] = pd.cut(employ['tenure_years'],
                                 bins=[0, 1, 3, 5, 10, 20, 30],
                                 labels=['<1 year', '1-3 years', '3-5 years', '5-10 years', '10+ years','10-30 years'])

tenure_analysis = employ.groupby(['department_id', 'tenure_group'])['salary'].agg(['mean', 'count']).round(0)
tenure_analysis= tenure_analysis.reset_index()
print(tenure_analysis)

# 1. Filter employees earning >20% above department average
extreme_employees = employ[employ['salary_percent_diff'] > 20].copy()

# 2. Merge with jobs table to bring in job titles and salary bands
high_earners_detailed = pd.merge(
    extreme_employees,
    jobs[['job_id', 'job_title', 'min_salary', 'max_salary']],
    on='job_id',
    how='left'
)
print(high_earners_detailed[[
    'first_name','job_title', 'department_id',
    'salary', 'salary_percent_diff', 'tenure_years'
]].sort_values('salary_percent_diff', ascending=False).head(10))


high_earners_detailed['tenure_group'] = pd.cut(
    high_earners_detailed['tenure_years'],
    bins=[0, 1, 3, 5, 10, 50], # Extended to 50 to avoid NaN for tenures > 20 years
    labels=['<1 year', '1-3 years', '3-5 years', '5-10 years', '10+ years'],
    include_lowest=True
)

tenure_job_analysis = high_earners_detailed.groupby(['department_id', 'job_title', 'tenure_group']
)['salary'].agg(
    avg_salary='mean',
    employee_count='count'
).dropna().reset_index()

print("\n⏰ HIGH EARNERS BREAKDOWN BY JOB TITLE & TENURE:")
print(tenure_job_analysis)
print(tenure_job_analysis[['job_title','tenure_group','avg_salary']])

'''
Rows 3 vs 4 (Sales Executive): 1–3 years tenure averages $77.4k, while 5–10 years averages $78.4k. 
Tenured sales executives are earning almost the exact same baseline
 as newer hires (~$1k difference over years of service). This is a strong flight risk signal.
 
 and
 Employees with 1–3 years of tenure earn more than those with 3–5 or 5–10 years of tenure. 
 This is Salary Inversion—newer hires were brought in at higher market rates than tenured staff.
 
 ###########################################
 Department-Level Variation (30% Threshold): When analyzing an entire department at once
(using standard deviation divided by mean, or Coefficient of Variation), 
you use 30%. Because departments contain mixed roles (e.g., Interns + Senior Managers),
 a variance up to 25–30% is natural. Anything above 30% indicates an abnormally wide spread across the whole group.
 
 individual Employee Deviation (20% Threshold):
 When evaluating an individual employee against their department or job average, 
a $\pm 20\%$ deviation is the HR industry standard for defining compensation policy limits:
 
 ###################################3#######
 

'''
import pandas as pd

# 1. Filter employees earning LESS than 20% BELOW department average
underpaid_employees = employ[employ['salary_percent_diff'] < -20].copy()

# 2. Merge with jobs table to get official job titles and salary bands
underpaid_detailed = pd.merge(
    underpaid_employees,
    jobs[['job_id', 'job_title', 'min_salary', 'max_salary']],
    on='job_id',
    how='left'
)

# 3. Create tenure buckets (extending upper bound to 50 years)
underpaid_detailed['tenure_group'] = pd.cut(
    underpaid_detailed['tenure_years'],
    bins=[0, 1, 3, 5, 10, 50],
    labels=['<1 year', '1-3 years', '3-5 years', '5-10 years', '10+ years'],
    include_lowest=True
)

# 4. Group by Job Title and Tenure Group
# DO NOT put salary_percent_diff in groupby! Keep it inside .agg()
underpaid_analysis = underpaid_detailed.groupby(['job_title', 'tenure_group']).agg(
    avg_salary=('salary', 'mean'),
    avg_percent_below_dept=('salary_percent_diff', 'mean'),
    employee_count=('salary', 'count')
).dropna().reset_index()

# 5. Format numbers for clear executive reporting
underpaid_analysis['avg_salary'] = underpaid_analysis['avg_salary'].round(2)
underpaid_analysis['avg_percent_below_dept'] = underpaid_analysis['avg_percent_below_dept'].round(2)

print("--- UNDERPAID EMPLOYEES (< -20% DEVIATION) ANALYSIS ---")
print(underpaid_analysis.sort_values('avg_percent_below_dept', ascending=True))
print(underpaid_analysis[['job_title', 'tenure_group', 'avg_salary',
       'employee_count']])

'''
High Risk — Tenured Stagnation (Burnout / Flight Risk):Pattern: 
Employees in the 5-10 years or 10+ years tenure groups showing up as $ -20%$
Diagnosis: Long-term employees whose pay raises haven't kept up with external market inflation. 
They are key candidates for leaving the company.
Low Risk — Entry-Level Trajectory (Expected Low Pay):Pattern: Employees in the <1 year tenure group holding Junior titles
.Diagnosis: Normal entry placement at the bottom of a compensation band.
 This is expected and usually not a policy violation.
 Compliance Risk — Below Job Minimum:Pattern: avg_salary is lower than the official min_salary column from the jobs table.Diagnosis:
 Critical HR mistake. The employee is paid below company policy minimums regardless of department averages.
'''
### checking the budget and give a rise ####
'''
If salary_percent_of_budget is 70%: 
For a $1,000,000 budget, $700,000 goes to salaries, leaving $300,000 (30%) left over.

If salary_percent_of_budget is LESS than 70% 
(e.g., 55%): Only $550,000 goes to salaries, leaving $450,000 (45%) unused budget sitting in the bank.
meaning they have plenty of unspent money left after paying current salaries.
'''
active = employees[employees['employment_status']=='Active']
dept_salary = active.groupby('department_id')['salary'].sum().reset_index(name='total_salary')
budget_efficiency = pd.merge(dept_salary, departments[['department_id', 'department_name', 'budget']],
                              on='department_id', how='inner')


# 3. what % of the budget is actually going to salaries
budget_efficiency['salary_percent_of_budget'] = (
    budget_efficiency['total_salary'] / budget_efficiency['budget'] * 100
).round(1)

print(budget_efficiency)

# 1. find departments with budget slack (salaries < 70% of budget)
underpaid_depts = budget_efficiency[budget_efficiency['salary_percent_of_budget'] < 70].copy()

# 2. what would a 10% raise for everyone in those departments cost?
underpaid_depts['raise_cost'] = underpaid_depts['total_salary'] * 0.10

# 3. what would their new salary total be, and does it still fit the budget?
underpaid_depts['new_total_salary'] = underpaid_depts['total_salary'] + underpaid_depts['raise_cost']
# "After giving this raise, is the new payroll cost still less than or equal to the total money approved for the department?"
underpaid_depts['fits_budget'] = underpaid_depts['new_total_salary'] <= underpaid_depts['budget']

print(underpaid_depts[['department_name', 'total_salary', 'budget',
                        'raise_cost', 'new_total_salary', 'fits_budget']])

# 4. total cost across the whole company if you did this everywhere
total_cost = underpaid_depts['raise_cost'].sum()
print(f"Total cost of a 10% raise across underfunded-looking departments: ${total_cost:,.0f}")

