PRAGMA foreign_keys=ON;
CREATE TABLE geography(code TEXT PRIMARY KEY,name TEXT NOT NULL,group_name TEXT);
CREATE TABLE countries(code TEXT PRIMARY KEY,name TEXT NOT NULL,group_name TEXT,FOREIGN KEY(code) REFERENCES geography(code));
CREATE TABLE coverage(id INTEGER PRIMARY KEY AUTOINCREMENT,group_name TEXT,code TEXT,name TEXT,year INTEGER,antigen TEXT,antigen_description TEXT,coverage_category TEXT,coverage_category_description TEXT,target_number REAL,doses REAL,coverage REAL);
CREATE TABLE incidence_rate(id INTEGER PRIMARY KEY AUTOINCREMENT,group_name TEXT,code TEXT,name TEXT,year INTEGER,disease TEXT,disease_description TEXT,denominator TEXT,incidence_rate REAL);
CREATE TABLE reported_cases(id INTEGER PRIMARY KEY AUTOINCREMENT,group_name TEXT,code TEXT,name TEXT,year INTEGER,disease TEXT,disease_description TEXT,cases REAL);
CREATE TABLE vaccine_introduction(id INTEGER PRIMARY KEY AUTOINCREMENT,iso_3_code TEXT,country_name TEXT,who_region TEXT,year INTEGER,description TEXT,intro TEXT);
CREATE TABLE vaccine_schedule(id INTEGER PRIMARY KEY AUTOINCREMENT,iso_3_code TEXT,country_name TEXT,who_region TEXT,year INTEGER,vaccine_code TEXT,vaccine_description TEXT,schedule_rounds INTEGER,target_pop TEXT,target_pop_description TEXT,geoarea TEXT,age_administered TEXT,source_comment TEXT);
CREATE TABLE data_quality_log(table_name TEXT PRIMARY KEY,source_file TEXT,source_rows INTEGER,cleaned_rows INTEGER,duplicates_removed INTEGER,missing_key_rows INTEGER,notes TEXT);
-- Because source data includes country, WHO-region and global codes in the same facts,
-- the distributed build uses geography as the parent dimension and triggers to enforce code integrity.
