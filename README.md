## Usage

Run the CLI on a CSV or Excel file:

```bash
data-normalizer path/to/file.csv [OPTIONS]

output/<input_name>OUT_<YYYY-MM-DD>/

If `--out` is provided, outputs are written to:

output/<out>/<input_name>OUT_<YYYY-MM-DD>/

Each run folder contains:
- Normalized CSV data
- JSON records
- SQL schema
- JSON schema
- Profiling report

### CLI Options

input_path  
Path to the input `.csv` or `.xlsx/.xls` file.

--sheet  
Excel sheet name or index (only for Excel files).  
Examples: Sheet1, 0

--preview-rows  
Number of rows to preview in the terminal (0–50).  
Default: 5

--table  
SQL table name used in the generated CREATE TABLE statement.  
Default: normalized_data

--show-schema / --no-show-schema  
Print generated SQL and JSON schemas to the terminal.  
Default: disabled

--export  
Write output files to disk.  
If not provided, no files are written.

--out  
Subfolder inside `./output` used to group runs.  
Example: results  
Outputs will be written to:  
output/results/<input_name>OUT_<YYYY-MM-DD>/

--overwrite / --no-overwrite  
Control whether existing run folders can be reused.  
Default: overwrite enabled

### Overwrite behavior

By default, outputs overwrite files in the run folder if it already exists.  
Use --no-overwrite to prevent replacing existing results.  
If the output folder already exists and overwrite is disabled, the command exits with an error.
