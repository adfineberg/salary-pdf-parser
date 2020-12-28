# salary-pdf-parser
Parse out salary tables and stats from pdf files from https://maya.tase.co.il/reports/finance

To install, create a virtual env and run:

`pip install -r requirements.txt`

To run the script, have a directory containing the downloaded pdfs with filenames in the format 'YY-company.pdf' - for example '19-migdal.pdf'. 
Then run the command: 

`python main.py directory_path`

This will create within the `directory_path` two sub-directories: `output` and `tables`. 
The `output` directory will contain `all_stats.csv` with a row per company and columns for min, max, and mean for every year (currently the years are hardcoded 13,14,18,19).
The `tables` directory will contain a table per pdf file of the higest salaries table.
