# Operating Room Scheduling Instance Generator

## 📋 Description

This Python project generates synthetic data instances for the **Operating Room Scheduling Problem**. The output files are formatted to be directly used as data input (`.dat` style) for optimization solvers like **IBM ILOG CPLEX**.

It simulates a hospital environment with surgeons, operating rooms, and patients, generating complex constraints such as room eligibility, surgeon availability, and sequence-dependent setup times.

## 🚀 Features

- **Randomized or Fixed Generation:** Create unique datasets with variable sizes or use fixed parameters for consistent testing.
- **Configurable Parameters:** Easily adjust the number of surgeons, rooms, operations, and operation types.
- **Detailed Constraints:**
  - Room eligibility (Matrix `A`)
  - Surgeon assignment (Matrix `C`)
  - Operation types & Setup times (Matrix `T`, `TCSTO`)
  - Patient specificities (Infectious status, Latex allergy)
  - Surgeon working hours (Start/End times)

## 🛠️ Prerequisites

- Python 3.x
- NumPy

To install the required library:

```bash
pip install numpy
```

## ⚙️ Configuration

You can modify the global variables at the top of the script to change the instance characteristics:

```python
use_random = False             # Set to True to generate random instance sizes
num_operations = 60            # Fixed number of operations
num_surgeons = 15              # Number of surgeons
num_rooms = 16                 # Number of available rooms
global_with_setup_time = True  # Enable/Disable sequence-dependent setup times
global_with_schedule = False   # Enable/Disable specific surgeon shifts
```
## 📂 Output Format

The script generates `.txt` files in the `generation_result/` directory. These files are formatted as OPL data files.
Here is a dictionary of the generated variables found in the output files:

| Variable | Dimension | Description |
| :--- | :--- | :--- |
| `num_surgeons` | Scalar | Total number of surgeons |
| `num_rooms` | Scalar | Total number of operating rooms |
| `num_operations` | Scalar | Total number of surgeries to schedule |
| `num_op_types` | Scalar | Total number of operation types |
| `infection_time` | Scalar | Time required for infectious cleaning |
| `latex_time` | Scalar | Time required for latex allergy cleaning |
| `A` | [Ops][Rooms] | Binary matrix: 1 if the room is eligible for the operation |
| `C` | [Surg][Ops] | Binary matrix: 1 if the surgeon performs the operation |
| `T` | [Ops][Types] | Binary matrix: Operation type assignment |
| `TP` | [Ops] | Preparation time vector |
| `TC` | [Ops] | Surgery (Cut) time vector |
| `TN` | [Ops] | Cleaning/Nettoyage time vector |
| `TCSTO` | [Type][Type] | Setup time matrix when switching between operation types |
| `start_time` | [Surg] | Surgeon shift start time |
| `end_time` | [Surg] | Surgeon shift end time |
| `I` | [Ops] | Binary vector: 1 if patient is infectious |
| `L` | [Ops] | Binary vector: 1 if patient is allergic to latex |

Room's blocks are supposed to follow the patern : of each groups of four rooms are in the same block
 
 ## 📂 Output Format


# 🏥 Medical Constraints (Latex & Infectious)

Specific scheduling rules apply based on patient conditions:

* **Latex Allergy:** If a patient is allergic to latex, a specific cleaning/setup protocol (requiring more time) is needed **before** their operation starts.
    * *Exception:* This extra setup time is skipped if it is the first operation of the day or if the operation takes place immediately after another patient who is also allergic to latex.

* **Infectious :** If a patient is flagged as infectious (High Resistant Bacteria), a deep cleaning (requiring more time) is necessary **after** their operation.
    * *Exception:* This extra cleaning time is skipped if the immediately following operation in the same room is also for an infectious patient.

