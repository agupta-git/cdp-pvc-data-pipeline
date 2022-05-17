#****************************************************************************
#  Source File Name: enrich.py
#  Author: Anshul Gupta
#***************************************************************************/

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import pyspark.sql.functions as F

## CREATE SPARK SESSION
spark = SparkSession.builder.appName('Enrich').getOrCreate()
spark.conf.set("spark.sql.legacy.allowCreatingManagedTableUsingNonemptyLocation", "true")
print("JOB STARTED")

## LOAD DATA FROM HDFS
fs = "hdfs://user/angupta/covid-outreach"
covid_rate_by_soc_det = spark.read.csv(fs + "/covid-19-case-rate-by-social-det.csv", header=True, inferSchema=True)
covid_demo_rate_cumulative = spark.read.csv(fs + "/covid-19-demographic-rate-cumulative.csv", header=True, inferSchema=True)
cdph_data_dictionary = spark.read.csv(fs + "/covid-19-equity-metrics-data-dictionary.csv", header=True, inferSchema=True)
members_profile = spark.read.csv(fs + "/member_profile.csv", header=True, inferSchema=True)

## CLEANUP DATABASES
print("DATABASE CLEANUP STARTED...")
spark.sql("DROP DATABASE IF EXISTS CDPH CASCADE")
spark.sql("DROP DATABASE IF EXISTS MEMBER CASCADE")
print("DATABASE CLEANUP COMPLETED")

## CREATE DATABASES
print("CREATE DATABASE STARTED...")
spark.sql("CREATE DATABASE CDPH")
spark.sql("CREATE DATABASE MEMBER")
print("CREATE DATABASE COMPLETED")

## POPULATE RAW DATA
print("POPULATE RAW DATA STARTED...")

print("LOADING CDPH.COVID_RATE_BY_SOC_DET...")
# rename columns that conflict with Hive keywords
covid_rate_by_soc_det = covid_rate_by_soc_det.withColumnRenamed('date', 'load_date')
covid_rate_by_soc_det = covid_rate_by_soc_det.withColumnRenamed('sort', 'priority_sort')
covid_rate_by_soc_det.write.mode("overwrite").saveAsTable('CDPH.COVID_RATE_BY_SOC_DET', format="parquet")

print("LOADING CDPH.COVID_DEMO_RATE_CUMULATIVE...")
covid_demo_rate_cumulative.write.mode("overwrite").saveAsTable('CDPH.COVID_DEMO_RATE_CUMULATIVE', format="parquet")

print("LOADING CDPH.DATA_DICTIONARY...")
cdph_data_dictionary.write.mode("overwrite").saveAsTable('CDPH.DATA_DICTIONARY', format="parquet")

print("LOADING MEMBER.MEMBER_PROFILE...")
members_profile.write.mode("overwrite").saveAsTable('MEMBER.MEMBER_PROFILE', format="parquet")
print("POPULATE RAW DATA COMPLETED")

## POPULATE ENRICHED DATA
print("POPULATE ENRICHED DATA STARTED...")
# classify members based on age social factor. This is to be later used in targeting members whose age group is signifantly impacted by covid-19.
sql_target_members_by_age_group = "with cte_covid_demo_rate_cumulative_upd as ( \
  select *, \
    case \
      when a.demographic_set_category = '0-17' then '0' \
      when a.demographic_set_category = '18-49' then '18' \
      when a.demographic_set_category = '50-64' then '50' \
      when a.demographic_set_category = '65+' then '65' \
    end as low_point, \
    case \
      when a.demographic_set_category = '0-17' then '17' \
      when a.demographic_set_category = '18-49' then '49' \
      when a.demographic_set_category = '50-64' then '64' \
      when a.demographic_set_category = '65+' then '999' \
    end as high_point \
  from cdph.covid_demo_rate_cumulative a \
  where a.demographic_set = 'age_gp4' \
) \
select distinct c.name, c.email, c.age, b.demographic_set_category \
from cte_covid_demo_rate_cumulative_upd b \
join member.member_profile c on c.age between b.low_point and b.high_point"
table_target_members_by_age_group = spark.sql(sql_target_members_by_age_group)
print("LOADING MEMBER.TARGET_MBRS_BY_AGE_GROUP...")
table_target_members_by_age_group.write.mode("overwrite").saveAsTable('MEMBER.TARGET_MBRS_BY_AGE_GROUP', format="parquet")

# classify members based on income social factor. This is to be later used in targeting members whose income group is signifantly impacted by covid-19.
sql_target_members_by_income = "with cte_covid_rate_by_soc_det_upd as ( \
  select *, \
    case \
      when a.social_tier = 'above $120K' then '120000' \
      when a.social_tier = '$100k - $120k' then '100000' \
      when a.social_tier = '$80k - $100k' then '80000' \
      when a.social_tier = '$60k - $80k' then '60000' \
      when a.social_tier = '$40k - $60k' then '40000' \
      when a.social_tier = 'below $40K' then '0' \
    end as low_point, \
    case \
      when a.social_tier = 'above $120K' then '999999999' \
      when a.social_tier = '$100k - $120k' then '120000' \
      when a.social_tier = '$80k - $100k' then '100000' \
      when a.social_tier = '$60k - $80k' then '80000' \
      when a.social_tier = '$40k - $60k' then '60000' \
      when a.social_tier = 'below $40K' then '40000' \
    end as high_point \
  from cdph.covid_rate_by_soc_det a \
  where a.social_det = 'income' \
) \
select distinct c.name, c.email, c.income, b.social_tier \
from cte_covid_rate_by_soc_det_upd b \
join member.member_profile c on c.income between b.low_point and b.high_point"
table_target_members_by_income = spark.sql(sql_target_members_by_income)
print("LOADING MEMBER.TARGET_MBRS_BY_INCOME...")
table_target_members_by_income.write.mode("overwrite").saveAsTable('MEMBER.TARGET_MBRS_BY_INCOME', format="parquet")
print("POPULATE ENRICHED DATA COMPLETED")

print("JOB COMPLETED")
