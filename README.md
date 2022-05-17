# _WORK IN PROGRESS_
# A Data Pipeline in Cloudera Data Platform (CDP)
## Use Case - Accelerate COVID-19 outreach programs using CDP Private Cloud environment
As a healthcare provider / public health official, I want to respond equitably to the COVID-19 pandemic as quickly as possible, and serve all the communities that are adversely impacted in the state of California.  
I want to use health equity data reported by California Department of Public Health (CDPH) to **identify impacted members** and accelerate the launch of outreach programs.
## Design
**Collect** - Ingest data from https://data.chhs.ca.gov/dataset/covid-19-equity-metrics using NiFi.  
**Enrich** - Transform the dataset using Spark and load Hive tables.  
**Report** - Gather insights using Hive tables and Data Visualization (TBD).  
**Predict** - Connect to Hive tables and build Machine Learning (ML) models of your choice. TBD

## Implementation
**Prerequisites:**  
- A modern browser such as Google Chrome and Firefox.
- An existing CDP Private Cloud environment with following services - Hadoop Distributed File System (HDFS), Atlas, NiFi, Spark, Hive on Tez, Hue, HBase, TBD 
- Add data/member_profile.csv to your storage directory.
- Add data/covid-19-equity-metrics-data-dictionary.csv to your storage directory. 

**Steps to create this data pipeline, are as follows:**  
> Please note that this data pipeline's documentation is in accordance with CDP Runtime Version 7.1.7. 
### Step #1 - Setup NiFi Flow
- Go to NiFi user interface and upload NiFi-CDPH.xml as a template.
- NiFi-CDPH.xml uses PutHDFS processor to connect to an existing HDFS directory. **Please change the properties in this processor to use your own HDFS directory.**
- Execute the flow and ensure InvokeHTTP processors are able to get [covid19case_rate_by_social_det.csv](https://data.chhs.ca.gov/dataset/f88f9d7f-635d-4334-9dac-4ce773afe4e5/resource/11fa525e-1c7b-4cf5-99e1-d4141ea590e4/download/covid19case_rate_by_social_det.csv) and [covid19demographicratecumulative.csv](https://data.chhs.ca.gov/dataset/f88f9d7f-635d-4334-9dac-4ce773afe4e5/resource/b500dae2-9e58-428e-b125-82c7e9b07abb/download/covid19demographicratecumulative.csv). Verify that these files are added to your storage directory.
- For reference, here's a picture of the flow in NiFi user interface -

  ![NiFi Flow](https://user-images.githubusercontent.com/2523891/168928614-87e9ba25-47a7-4aa6-861f-8f45ff698f6a.png)
---
### Step #2 - Setup PySpark Job
- SSH in to the cluster and make enrich.py program available in any directory. **Please change the _fs_ variable in enrich.py program to point to your HDFS directory**.
- Execute the following command - ```/bin/spark-submit enrich_pvc.py``` and monitor logs to ensure it's finished successfully. It takes approx. 4 minutes to finish.
- Following Hive tables are created by this job:
  - cdph.data_dictionary
  - cdph.covid_rate_by_soc_det
  - cdph.covid_demo_rate_cumulative
  - member.member_profile
  - member.target_mbrs_by_income
  - member.target_mbrs_by_age_group
---
### Step #3 - Identify impacted members in Hue editor
- Open Hue editor and explore the Hive tables created by PySpark job.
  ```sql
  -- Raw Data
  select * from cdph.data_dictionary a;
  select * from cdph.covid_rate_by_soc_det a;
  select * from cdph.covid_demo_rate_cumulative a;
  select * from member.member_profile a;
  ```
- TBD - either provide analysis queries or point to CDSW Data Viz
- Based on this dataset, **below $40K** is the most impacted income group in terms of COVID-19 cases, and **65+** is the most impacted age group in terms of COVID-19 related deaths. You can now use this information, to filter members that are in these categories.
- Execute the following queries to get impacted members:
  ```sql
  select * from member.target_mbrs_by_income a where social_tier = 'below $40K';
  select * from member.target_mbrs_by_age_group a where demographic_set_category = '65+';
  ```
---
### Step #7 - View Hive tables in TBD
- Go to Data Catalog user interface. Select any Hive table created in this exercise and see its lineage, schema, audits, etc.
---
