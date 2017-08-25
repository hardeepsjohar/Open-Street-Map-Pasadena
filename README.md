# Open-Street-Map-Pasadena

Clean up Open Street Map street names and zip codes in Pasadena using Python.  
Extract data about Pasadena.

## Getting Started

1. Download Open Street Map file here:    
https://www.openstreetmap.org/#map=13/34.1247/-118.0944

2. Place OSM file in the same folder as the remaining files.

3. Make sure Python 2.7 is active and run Open_street_map.py.  5 CSV files   
will be created in the same directory.

4. Install SQLite (https://dev.mysql.com/doc/mysql-getting-started/en/)

5. In Terminal, create a new database by running the following command:   
$ sqlite3 new.db

6. Create a table and its schema for 1 CSV file by running the following   
command:   
sqlite> CREATE TABLE myTable() <-- Before running, build the table schema   
using schema.py.

7. Repeat this for the remaining 4 CSV files.

8. Set mode to CSV   
sqlite> .mode csv

9. Run this command with the appropriate file name and associated table name:   
sqlite> .import newFile.csv myTable

10. Install Jupyter Notebook to follow along with the (.ipynb) iPython  
Notebook file here: (http://jupyter.readthedocs.io/en/latest/install.html)

## Authors

* **Hardeep S Johar** - *Initial work* - [HardeepSJohar](https://github.com/hardeepsjohar)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* OpenStreetMap
* Pasadena
