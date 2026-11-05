from dataclasses import replace

import pandas as pd
import numpy as np
from fontTools.subset import subset
from pandas import read_csv


df=pd.read_csv( r"C:\Users\User\Desktop\real project for wall\Project 2 course demand\Online_Courses.csv")
print(df)
print(df.head(3))

#here click > for more practice #
'''
########## convert the (spaces into _) []
df.columns=(df.columns
           .str.strip()
           .str.lower()
           .str.replace(" ","_")
           )
print(df.columns)
df.rename(columns={"number_of_viewers":"views",
                   "'sub-category":"sub_category"},inplace=True
          )
print(df.columns)
#rating str ############
df["rating"]=(df["rating"]
            .astype(str)
            .str.extract(r"([\d\.]+)")[0]
            .astype(float))
print(df["rating"])

##### views clenaing like 25k views
def clean_view(x):
    if pd.isna(x): return np.nan
    v= str(x).replace(",","").strip().lower()
    if "k" in v:
        return float(v.replace("m",""))*1000
    elif "m" in v:
        return float(v.replace("m",""))*1000000
    elif v.replace(".","").isdigit():
        return float(v)
    else:
        return  np.nan

df["views"]=df["views"].apply(clean_view)
print(df["views"])

######### hour 5hours #### 4 weeks # converting into hours
def to_hour(text):
    if pd.isna(text): return np.nan
    v=str(text).lower()
    number_list= [float(x) for x in v.split() if x.replace(".","",1).isdigit()]
    num=number_list[0] if number_list else np.nan
    if "month" in v:
        return num * 60  # 60 hours per month
    elif "week" in v:
        return num * 15  # 15 hours per week
    elif "day" in v:
        return num * 2  # 2 hours per day
    elif "hour" in v or "hr" in v or "h" in v:
        return num
    else:
        return np.nan

####### substitle check ##########
df["subtitle_language"]=(df["subtitle_languages"].astype(str).str.replace("Subtitles:","",1).str.strip()
                        )
print(df["subtitle_language"].head(3))
df["list_subtitle"]=df["subtitle_language"].str.strip(",")
print("_________  __ __ __ __ __ __ __ __ __ __ __ ____________")

####################
df["subtitle_languages_list"] = df["subtitle_language"].apply(
    lambda x: [lang.strip() for lang in x] if isinstance(x, list) else []
)

#############   converting into hours
###### converting into hours
def convert_hours(text):
    if pd.isna(text): return np.nan
    words=str(text).lower().split() #["a',"ad']"3","5678"]  #
    total_hours=0.0
    for i,word in enumerate(words):
        if word.replace(".","",1).isdigit(): #check if a number
            num=float(word) #conver into words
            if i+1<len(words):
                unit=words[i+1]
                if "month" in unit:
                    total_hours += num * 60
                elif "week" in unit:
                    total_hours += num * 15
                elif "day" in unit:
                    total_hours += num * 2
                elif "hour" in unit or "hr" in unit or unit == "h":
                    total_hours += num

    return total_hours

df["hours"]=df["duration"].apply(convert_hours)
print(df[["hours","title"]])

#################
df.drop_duplicates(subset=["title"], inplace=True)


########### questions and work

skills_exploded = df.assign(skill=df["skills"].str.split(",")).explode("skill")
skills_exploded["skill"] = skills_exploded["skill"].str.strip()
#
skill_stats = (
    skills_exploded.groupby("skill")
    .agg(total_courses=("title", "count"),
         top_views=("views", "max"))
    .reset_index()
)
q10 = (
    pd.merge(skill_stats, skills_exploded,
             left_on=["skill", "top_views"],
             right_on=["skill", "views"],
             how="left")[["skill", "total_courses", "title", "category", "views"]]
    .rename(columns={"title": "top_course_title", "views": "course_views"})
    .sort_values("total_courses", ascending=False
                 )
 )
print(q10.head(5))
print(skill_stats.columns)


print("___________________________________________________________________")

def convert_to_hours(text):
    if pd.isna(text): return np.nan
    t = str(text).lower()
    num_list = [float(x) for x in t.split() if x.replace('.', '', 1).isdigit()]
    num = num_list[0] if num_list else np.nan

    if "month" in t: return num * 60
    elif "week" in t: return num * 15
    elif "day" in t: return num * 2
    elif "hour" in t or "hr" in t: return num
    else: return np.nan

df["manyhours"]=df["duration"].apply(convert_to_hours)
print(df[["title","manyhours"]])


'''
#practice against

########## column removing extra spaces, - to _
df.columns=df.columns.str.strip().str.lower().str.replace("-","_")
df.columns=df.columns.str.strip().str.lower().str.replace(" ","_")
print(df.columns)

#### filling none with empty texts using fillna df.fillna()
df.fillna({"skills":"","category":"","sub_category": "", "language": ""},inplace=True)

############### drop columns duplicates
df.drop_duplicates(subset=["title"], inplace=True)
print(df["title"].count())
df["title"]=df["title"].drop_duplicates()
print(df["title"].count())

######### changing the (rate stars 5 to 5.0)
df["rating"]=(df["rating"].astype(str).str.extract(r"([\d\.]+)")[0]).astype(float)
print(df["rating"])

######## clean views with k and m in texts 4.6k  5.7m
##### text=str(text).replace("","").strip().lower()    // float(text.replace("",""))
def clean_views(text):
    if pd.isna(text): return np.nan
    text=str(text).replace(",","").strip().lower()
    if "k" in text:
        return float(text.replace("k",""))*1000

    elif "m" in text:
        return float(text.replace("m", "")) * 1_000_000
    elif text.replace(".", "").isdigit():
        return float(text)
    else:
        return np.nan

df["number_of_viewers"]=df["number_of_viewers"].apply(clean_views)
print(df["number_of_viewers"].head(3))

######################
#"""Convert text like '3.5 weeks and 10 days' into total hours."""
### 1)words=str(text).lower().split()  #convert into a list
#  20 for i,word in enumarate(words): if word.replace("","",1).isdigit() num=float() #check if its a digit
## if i+1<words: unit=words[i+1] checks the next word is month,day,year
#
def hour_clean(text):
    if pd.isna(text):
        return  np.nan
    words=str(text).lower().split()
    total_hour=0.0

    for i,word in enumerate(words):
        if word.replace(".","",1).isdigit():
            num=float(word)
            if i+1<len(words):
                unit=words[i+1]
                if "month" in unit:
                    total_hour+=num*60
                elif "week" in unit:
                    total_hour += num * 15
                elif "day" in unit:
                    total_hour += num * 2
                elif "hour" in unit or "hr" in unit or unit == "h":
                    total_hour+= num
    return total_hour

df["duration"]=df["duration"].apply(hour_clean)
print(df["duration"].head(3))
###############################
#substitle: []
'''
df["subtitle_languages"]=(df["subtitle_languages"].astype(str).str.replace("Subtitles:,","")).str.strip().str.split()
print(df["subtitle_languages"].head(6))
print(df)
'''
########### working with inside text [] list
df["subtitles"] = (
    df["subtitle_languages"]
    .astype(str)
    .str.replace("Subtitles:", "", case=False)
    .str.strip()
)
print(df["subtitles"])
df["languages_list"] = df["subtitles"].str.split(",")
print(df["languages_list"].head(3))

###cleaning up the values inside the list[]
df["languages_list"]=(df["languages_list"]
    .apply(lambda x:[lang.strip() for lang in x]if isinstance(x,list) else []))

####### count the number of substitle languages ######### using apply len()
df["count_inside"]=df["languages_list"].apply(len)
print(df["count_inside"].head(3))

### counting with category using explode using df.explode("col")   having[,,,]
language_category=(df.explode("languages_list")
                   .groupby(["category","languages_list"]).size().reset_index(name="count").sort_values("count",ascending=False)
                   )
print(language_category)

########### the cleaning part of the more data  ###################



# 3️⃣ Skills popularity
# we use df.assign() so that it doesnt change the original dataframe
# val=(df.assign(col_name=df[col].funtion()).explode() )
skills_demand=(df.assign(skill=df["skills"].str.split(",")).explode("skill") )
skills_demand["skill"]=(skills_demand["skill"].astype(str) .str.replace(r"[-•\t\n\r]", "", regex=True)
    .str.strip()
    .str.title() )
print(skills_demand.head(4))

##### fixing the corrections of data names:

corrections={ "Datenanalyse": "Data Analysis",
    "Datenbereinigung": "Data Cleaning" }

skills_demand["skill"]=skills_demand["skill"].replace(corrections)

#skills_demand["skill"]=skills_demand[skills_demand["skill"]!=""]




print("               ###### now analysing ########                     ")

#  1️⃣ Course Distribution
print("️⃣ Course Distribution\n")
# .size() means counting the same type rows
course_demand=(df.groupby(["category","sub_category","course_type"])
               .size().reset_index(name="total_courses").
               sort_values("total_courses",ascending=False)
               )

print(course_demand.head(3))

# 2️⃣ Average Views
print("2️⃣ Average Views\n")

avg_views=(df.groupby(["category","sub_category"])
           .agg(total_views=("number_of_viewers","sum"),
                total_course=("title","count")
           ).reset_index()
           )
print(avg_views.head(3))


print("3️⃣ Common Skills\n")
common_skill=(skills_demand.groupby(["category","skill"]).size()
              .reset_index(name="total_courses").
              sort_values(["category", "total_courses"], ascending=[True, False])
              )

print(common_skill.head(3))

# 4️⃣ Language Distribution
print("️⃣ Language Distribution\n")
language_distribution=(df.groupby("language").
                       agg(total_courses=("title","count"),
                           total_views=("number_of_viewers","sum"),
                           max_rating=("rating","mean")
                       ).reset_index().sort_values("total_courses",ascending=False))


print(language_distribution)

#index gives only the category index
print("5️⃣ Language Preferences for Top 5 Categories\n")

top5=df.groupby("category")["number_of_viewers"].sum().nlargest(3).index
language_preferences=(df[df["category"].isin(top5)]
                      .groupby(["category","language"])
                      .agg(total_view=("number_of_viewers","sum"),
                           total_course=("title","count")
                           )
                      )
print(language_preferences)

##################################################
print("7️⃣ Top 3 Instructors per Category/Subcategory")
######################################################
top_instructors=(df.groupby(["category","sub_category","instructors"])
                 .agg(total_views=("number_of_viewers","sum")))
print(top_instructors)


### # 9️⃣ Skill Variety vs Viewership
print("### # 9️⃣ Skill Variety vs Viewership")
###################################################
skill_view=skills_demand.groupby(["category","sub_category"])["skills"].unique().reset_index(name="unique_skills")
print(skill_view.head(3))

q9=(skill_view.merge(df,on=["category","sub_category"]).groupby(["category","sub_category"])["number_of_viewers"].mean()
    .reset_index(name="views").sort_values("views",ascending=False))
print(q9.head(3))


# 1️⃣1️⃣ Top Category & Course Type
#here idxmax() Find the index of the row with the maximum value
top_category=df.groupby("category")["number_of_viewers"].sum().idxmax()
top=df[df["category"]==top_category].groupby(["category","course_type"])["number_of_viewers"].sum().reset_index(name="top_views")
print(top)


# STEP 10: EXPORT TO EXCEL and to sheets
#with pd.ExcelWriter("Project2_Course_demand",engine="openpyxl") as writer:
    #q1.to_excel(writer, sheet_name="Course_Distribution", index=False)
    #q2.to_excel(writer, sheet_name="Average_Views", index=False)








