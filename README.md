# SQL Metadata Lineage
### This package helps you to find first level lineage / column level dependency in a given query
### Get SQL metadata (first level lineage) for most type of sql queries with inner sub-queries and other complex joins
### Get column level base logic after analyzing query

###### Sample input.sql
```
    SELECT investments.month_nm AS month_nm,
           acquisitions.companies_acquired,
           investments.companies_rec_investment
      FROM (
            SELECT acq.acquired_month_nm AS month_nm,
                   COUNT(DISTINCT acq.company_permalink) AS companies_acquired
              FROM tutorial.crunchbase_acquisitions acq
             GROUP BY 1
           ) acquisitions

      FULL JOIN (
            SELECT invst.funded_month_nm AS month_nm,
                   COUNT(DISTINCT invst.company_permalink) AS companies_rec_investment
              FROM tutorial.crunchbase_investments invst
             GROUP BY 1
           ) investments

        ON acquisitions.month_nm = investments.month_nm

```
### table_map, column_map = sql_metadata_lineage.get_metadata("input.sql")
### Output text

**** Database.Table alias mapping ****

Subquery mapping alias: acquisitions
	acq -> tutorial.crunchbase_acquisitions
Subquery mapping alias: investments
		invst -> tutorial.crunchbase_investments


**** Column, Database and Table mapping ****

month_nm -> tutorial.crunchbase_investments.funded_month_nm
companies_acquired -> count(DISTINCT tutorial.crunchbase_acquisitions.company_permalink)
companies_rec_investment -> count(DISTINCT tutorial.crunchbase_investments.company_permalink)

### table_map dictionary output
{'acquisitions': {'acq': 'tutorial.crunchbase_acquisitions'},
  'investments': {'invst': 'tutorial.crunchbase_investments'}}

### column_map dictionary output
{'month_nm': 'tutorial.crunchbase_investments.funded_month_nm',
  'companies_acquired': 'count(DISTINCT tutorial.crunchbase_acquisitions.company_permalink)',
  'companies_rec_investment': 'count(DISTINCT tutorial.crunchbase_investments.company_permalink)'}

### Can directly provide sql query as input
### table_map, column_map = sql_metadata.get_metadata('''
```
 SELECT investments.month_nm AS month_nm,
           acquisitions.companies_acquired,
           investments.companies_rec_investment
      FROM (
            SELECT acq.acquired_month_nm AS month_nm,
                   COUNT(DISTINCT acq.company_permalink) AS companies_acquired
              FROM tutorial.crunchbase_acquisitions acq
             GROUP BY 1
           ) acquisitions

      FULL JOIN (
            SELECT invst.funded_month_nm AS month_nm,
                   COUNT(DISTINCT invst.company_permalink) AS companies_rec_investment
              FROM tutorial.crunchbase_investments invst
             GROUP BY 1
           ) investments

        ON acquisitions.month_nm = investments.month_nm
```
### ''')