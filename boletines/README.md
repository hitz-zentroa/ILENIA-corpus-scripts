## Code to download data from Official Gazettes of Basque Country

This folder contains 4 scripts to download articles from the Official Gazettes of Basque Country, Gipuzkoa and Araba.
The *bob* folder bontains scripts to download articles from the Official Gazette of Bizkaia.
This folder also includes a script for anonymizing sensitive information extracted from the gazette articles.


 - *bopv_api_request.py*
This script downloads articles from the Official Gazette of the Basque Country (BOPV/EHAA) using the public API provided by the Basque Government in their [Open Data portal](https://opendata.euskadi.eus/api-bopv/?api=bopv). *Note: the API only provides data from 2008 onwards.*
The script receives the following arguments as input:
	- `directory`: Path to the directory where the data will be stored. 
	- `añoinicio`: Start year (integer). 
	- `añofin`: End year (integer). 
	- `idioma`: Language of the data, must be either [eu] (Basque) or [es] (Spanish).
	Example:
	```python
	python bopv_api_request.py ./data 2015 2020 eu
	```
 - *bog_scrape.py*
 This script downloads articles from the Official Gazette of Gipuzkoa (BOG/GAO). As there is no public API the articles are scrapped from the [web](https://egoitza.gipuzkoa.eus/es/bog). 
 The script receives the following arguments as input:
	 - `directory`: Path to the directory where the data will be stored. 
	- `añoinicio`: Start year (integer). 
	- `añofin`: End year (integer). 
	- `idioma`: Language of the data, must be either [eu] (Basque) or [es] (Spanish).
Example:
	```python
	python bog_scrape.py ./data 2008 2020 eu
	```
 - *botha_scrape.py*
 This script downloads articles from the Official Gazette of Alava (BOTHA/ALHAO). As there is no public API the articles are scrapped from the [web](https://www.araba.eus/botha/inicio/sgbo5001.aspx).
 The script receives the following arguments as input:
	 - `directory`: Path to the directory where the data will be stored. 
	- `añoinicio`: Start year (integer). 
	- `añofin`: End year (integer).  
In this case, the language is not passed as arguments, because both languages (Spanish and Basque) are downloaded simultaneously.
Example:
	```python
	python botha_scrape.py ./data 2008 2020
	```

 - *bon_scrape.py*
 This script downloads articles from the Official Gazette of Navarra (BON/NAO). As there is no public API the articles are scrapped from the [web](https://bon.navarra.es/eu/hasiera).
 The script receives the following arguments as input:
	 - `directory`: Path to the directory where the data will be stored. 
	- `añoinicio`: Start year (integer). 
	- `añofin`: End year (integer).  
In this case, the language is not passed as arguments, because both languages (Spanish and Basque) are downloaded simultaneously.
Example:
	```python
	python bon_scrape.py ./data 2008 2020
	```
- *anonymize_jsonl.py*
This script detects and anonymizes sensitive entities in the extracted gazette content, including national ID numbers (DNI, NIE), email addresses, social security numbers, and bank account numbers (IBAN). The detected sensitive data is replaced with a placeholder, e.g. <DNI>.
The script receives the following arguments as input:
	- `input`: input file name/path
   	- `output`: output file name/path
 	- `field`: name of the field to anonymize (field of the json)
	- `lang`: language for the placeholder, basque (eu) or spanish (es)
 Example:
 ```python
    python anonymize_jsonl.py --input input.jsonl --output output.jsonl --field texto --lang eu
```
