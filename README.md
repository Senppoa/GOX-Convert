# GOX-Convert

**GOX-Convert** is a file format conversion tool for computational chemistry, supporting bidirectional conversion between Gaussian and ORCA quantum chemistry software file formats.

## Overview

This tool supports conversion between the following file formats:

- **Gaussian Formats**: `.log` (output files), `.gjf` (input files)
- **ORCA Formats**: `.inp` (input files)
- **Universal Formats**: `.xyz` (molecular structure files)

## Supported Atoms

The tool includes built-in mapping from atomic numbers to element symbols for common atoms, including:
- Main group elements: H, He, Li, Be, B, C, N, O, F, Ne, Na, Mg, Al, Si, P, S, Cl, Ar, K, Ca
- Transition metals: Fe, Co, Ni, Cu, Zn, Zr, Rh, Pd, Ag, Ir, Pt, Au
- Halogens and others: Br, I

## Main Features

### 1. log to xyz

Extract the final optimized molecular structure from Gaussian log output files and save in xyz format.

**Features:**
- Automatically check for normal termination
- Search for Standard orientation from the end of the file to ensure the final structure is captured
- Support batch processing of entire folders
- Generate success/failure file lists

### 2. log to gjf

Convert Gaussian log files to new gjf input files for subsequent calculations.

**Features:**
- Automatically extract charge and spin multiplicity
- Support custom calculation methods, basis sets, and keywords
- Support Link1 multi-step calculations
- Option to add nosave keyword

### 3. xyz to gjf

Convert xyz structure files to Gaussian input files.

**Features:**
- Automatically read atom count and title
- Support custom calculation parameters
- Batch processing of multiple files

### 4. gjf to xyz

Extract molecular coordinates from Gaussian input files and save in xyz format.

**Features:**
- Automatically identify coordinate sections
- Correctly handle charge and spin multiplicity lines
- Support Link1 separators

### 5. gjf to inp

Convert Gaussian input files to ORCA input files.

**Features:**
- Support custom functionals and basis sets
- Configurable number of parallel cores and memory
- Support additional ORCA keywords

### 6. xyz to inp

Convert xyz structure files directly to ORCA input files.

**Features:**
- Preserve molecular structure information
- Support complete ORCA calculation parameter settings

### 7. inp to gjf

Convert ORCA input files to Gaussian input files.

**Features:**
- Parse ORCA coordinate sections
- Convert to Gaussian format

### 8. log to inp

Directly convert Gaussian log files to ORCA input files.

**Features:**
- Extract final optimized structure
- Generate ORCA format input files

## Installation Requirements

### Dependencies

```bash
pip install tqdm natsort
```

### Python Version

- Python 3.6 or higher

## Usage

### Import as a Module

```python
from gaussian_orca_converter import GaussianConverter

# Initialize the converter
converter = GaussianConverter(input_path="path/to/input", output_path="path/to/output")

# log to xyz
converter.log_to_xyz(check_termination=True, save_success_list=True)

# log to gjf
converter.log_to_gjf(
    nproc='32',
    mem='64GB',
    method='b3lyp',
    basis='def2svp',
    extra_keywords='opt freq',
    charge=0,
    mult=1
)

# xyz to gjf
converter.xyz_to_gjf(
    nproc='32',
    mem='64GB',
    method='b3lyp',
    basis='def2svp',
    extra_keywords='opt freq',
    charge=0,
    mult=1
)

# gjf to xyz
converter.gjf_to_xyz()

# gjf to inp
converter.gjf_to_inp(
    job_type="Opt NumFreq",
    functional="wB97M-V",
    basis_set="def2-TZVPD",
    nproc=32,
    maxcore=20000
)

# xyz to inp
converter.xyz_to_inp(
    job_type="Opt NumFreq",
    functional="wB97M-V",
    basis_set="def2-TZVPD",
    nproc=32,
    maxcore=20000
)

# inp to gjf
converter.inp_to_gjf(
    nproc='32',
    mem='64GB',
    method='b3lyp',
    basis='def2svp',
    extra_keywords='opt freq'
)

# log to inp
converter.log_to_inp(
    job_type="Opt NumFreq",
    functional="wB97M-V",
    basis_set="def2-TZVPD",
    nproc=32,
    maxcore=20000
)
```

### Batch Processing

When the input path is a folder, the tool will automatically process all matching files in that folder:

```python
# Batch convert all log files in a folder
converter = GaussianConverter(input_path="./log_files", output_path="./xyz_files")
converter.log_to_xyz()
```

## Parameter Reference

### Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_path` | str | Required | Input file or folder path |
| `output_path` | str | None | Output folder path, defaults to `converted_files` |

### log_to_xyz Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `check_termination` | bool | True | Whether to check for normal termination |
| `save_success_list` | bool | True | Whether to save success/failure file lists |

### log_to_gjf / xyz_to_gjf / inp_to_gjf Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `nproc` | str | '32' | Number of processor cores |
| `mem` | str | '64GB' | Memory size |
| `method` | str | 'b3lyp' | Calculation method/functional |
| `basis` | str | 'def2svp' | Basis set |
| `extra_keywords` | str | 'opt freq' | Additional keywords |
| `link1_method` | str | '' | Link1 calculation method |
| `link1_basis` | str | '' | Link1 basis set |
| `charge` | int | 0 | Charge |
| `mult` | int | 1 | Spin multiplicity |
| `nosave` | bool | False | Whether to add nosave keyword |

### gjf_to_inp / xyz_to_inp / log_to_inp Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_type` | str | "Opt NumFreq" | ORCA job type |
| `functional` | str | "wB97M-V" | Functional |
| `basis_set` | str | "def2-TZVPD" | Basis set |
| `nproc` | int | 32 | Number of processor cores |
| `maxcore` | int | 20000 | Maximum memory per core (MB) |
| `extra_keywords` | str | "" | Additional ORCA keywords |

## Output Files

After conversion, the tool generates the following outputs:

1. **Converted Files**: Saved in the specified output directory
2. **success_files.txt**: List of successfully converted files (only when `save_success_list=True`)
3. **error_files.txt**: List of files that failed to convert (only when `save_success_list=True`)

## Notes

1. **File Encoding**: The tool uses UTF-8 encoding for reading and writing files
2. **Coordinate Extraction**: When converting log files, the tool searches for Standard orientation from the end of the file to ensure the final optimized structure is captured
3. **Batch Processing**: Uses `tqdm` for progress bars and `natsort` for natural sorting
4. **Error Handling**: The tool catches exceptions and continues processing other files without interrupting batch conversion

## Examples

### Example 1: Extract Optimized Structure

```python
from gaussian_orca_converter import GaussianConverter

# Extract final structure from log file
converter = GaussianConverter("molecule.log", "./output")
converter.log_to_xyz(check_termination=True)
```

### Example 2: Batch Generate ORCA Input Files

```python
from gaussian_orca_converter import GaussianConverter

# Batch convert xyz files to ORCA input files
converter = GaussianConverter("./xyz_structures", "./orca_inputs")
converter.xyz_to_inp(
    job_type="Opt Freq",
    functional="B3LYP",
    basis_set="def2-SVP",
    nproc=16,
    maxcore=4000
)
```

### Example 3: Create Multi-Step Calculation Input

```python
from gaussian_orca_converter import GaussianConverter

# Create Gaussian input file with Link1
converter = GaussianConverter("molecule.log", "./output")
converter.log_to_gjf(
    method='b3lyp',
    basis='def2svp',
    extra_keywords='opt',
    link1_method='wB97M-V',
    link1_basis='def2tzvpd',
    extra_keywords_link1='freq'
)
```

## License

This project is open source and free to use and modify.

## Author Information

Please contact tkun@mail.dlut.edu.cn for any questions, feedback, or suggestions.

## Changelog

- **2025-10-20**: Initial release with basic file format conversion functionality
