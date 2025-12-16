## Code to download data from Official Gazettes of Basque Country

This folder contains 3 scripts to download articles from the Official Gazettes of Basque Country, Gipuzkoa and Araba:

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
