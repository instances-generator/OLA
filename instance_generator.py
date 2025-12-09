import os
import random
import numpy

# This program generates a random instance for the CPLEX solver, or CPO with intervals and can also be used for a metaheuristic instance.


# --- Global Configuration ---
global_with_setup_time = True
all_rooms_possible = False
global_with_schedule = False

use_random = False
num_operations_min = 100
num_operations_max = 150
num_surgeons_min = 15
num_surgeons_max = 35
num_rooms_min = 15
num_rooms_max = 27
num_op_types_min = 3
num_op_types_max = 10

num_operations = 60
num_surgeons = 15
num_rooms = 16
num_op_types = 12

num_patients = num_operations
infection_time = 30
latex_time = 30


def add_variables(num_surgeons, num_rooms, num_operations, num_op_types, infection_time, latex_time):
    string = ""
    string += "num_surgeons=" + str(num_surgeons) + ";\n"
    string += "num_rooms=" + str(num_rooms) + "; \n"
    string += "num_operations=" + str(num_operations) + "; \n"
    string += "num_op_types=" + str(num_op_types) + "; \n"
    string += "num_patients=" + str(num_operations) + "; \n"
    string += "infection_time=" + str(infection_time) + "; \n"
    string += "latex_time=" + str(latex_time) + "; \n"
    return string


def add_room_eligibility_for_operation(num_operations, num_rooms, percentage=0.9):
    '''In the model, this is variable A.
       We assume that each operation can be performed in 90% of the rooms on average.'''
    matrix = []
    if all_rooms_possible:
        percentage = 1
    for i in range(num_operations):
        all_zeros = True
        row = []
        for j in range(num_rooms):
            if j == num_rooms - 1 and all_zeros:
                row.append(1)
                continue
            rand = random.uniform(0, 1)
            if rand >= percentage:
                row.append(0)
            else:
                row.append(1)
                all_zeros = False
        matrix.append(row)
    return "A = " + str(matrix) + "; \n"


def add_surgeon_assignment_random_version(num_surgeons, num_operations):
    '''This is variable C [C][O].
       Each surgeon has an equal chance of performing each operation.'''
    matrix = []
    for i in range(num_surgeons):
        matrix.append([])
    for i in range(num_operations):
        rand = random.randint(0, num_surgeons - 1)
        for j in range(num_surgeons):
            if rand == j:
                matrix[j].append(1)
            else:
                matrix[j].append(0)
    return "C = " + str(matrix) + "; \n"


def add_surgeon_assignment_for_operation(num_surgeons, num_operations):
    '''This is variable C [C][O].
       Each surgeon alternates cyclically for each operation.'''
    matrix = []
    for i in range(num_surgeons):
        matrix.append([])
    for i in range(num_operations):
        current_surgeon = i % num_surgeons
        for j in range(num_surgeons):
            if current_surgeon == j:
                matrix[j].append(1)
            else:
                matrix[j].append(0)
    return matrix, "C = " + str(matrix) + "; \n"


def add_surgeon_schedule(num_surgeons, with_schedule=True):
    '''We assume hospital hours are 0,300 and there are only 3 schedule types:
       Morning (0,50), Afternoon (50,100), and Both (0,300), all equiprobable.'''
    max_val = 900
    start_time = []
    end_time = []
    global global_with_schedule
    for i in range(num_surgeons):
        rand = random.randint(0, 2)
        if not global_with_schedule:
            rand = 2
        if rand == 0:
            start_time.append(0)
            end_time.append(int(max_val / 2))
        if rand == 1:
            start_time.append(int(max_val / 2))
            end_time.append(max_val)
        if rand == 2:
            start_time.append(0)
            end_time.append(max_val)
    return "start_time = " + str(start_time) + "; \n" + "end_time= " + str(end_time) + "; \n"


def add_patient_conditions(num_operations, probability=0.1):
    '''We assume each patient has a 1/10 chance of being infectious and same for latex allergy.'''
    infectious = []
    latex_allergy = []
    num_patients = num_operations
    for i in range(num_patients):
        rand_latex = random.uniform(0, 1)
        rand_infectious = random.uniform(0, 1)
        if rand_latex <= probability:
            latex_allergy.append(1)
        else:
            latex_allergy.append(0)
        if rand_infectious <= probability:
            infectious.append(1)
        else:
            infectious.append(0)
    return "I = " + str(infectious) + "; \n" + "L= " + str(latex_allergy) + "; \n"


def add_operation_patient_identity(num_operations):
    '''[O][P] - We keep it simple, identity matrix.'''
    num_patients = num_operations
    matrix = []
    for i in range(num_patients):
        row = []
        for j in range(num_patients):
            if i == j:
                row.append(1)
            else:
                row.append(0)
        matrix.append(row)
    return "K = " + str(matrix) + "; \n"


def add_operation_type(num_operations, num_op_types, matrix_C):
    '''[O][TO] (TO = Type of Operation)'''
    num_surgeons = len(matrix_C)

    # Assign a random type to each surgeon
    type_per_surgeon = [random.randint(0, num_op_types - 1) for _ in range(num_surgeons)]

    # Initialize matrix [O][TO]
    matrix = [[0 for _ in range(num_op_types)] for _ in range(num_operations)]

    for o in range(num_operations):
        for c in range(num_surgeons):
            if matrix_C[c][o] == 1:
                op_type = type_per_surgeon[c]
                matrix[o][op_type] = 1
                break  # Only one surgeon per operation, so we can break

    return "T = " + str(matrix) + "; \n"


def add_operation_times(num_operations):
    '''We assume the duration of an operation follows a log-normal law, prep between 5 and 30 min, cleaning between 10 and 20 min.'''
    prep_time = []
    surgery_time = []
    cleaning_time = []
    for i in range(num_operations):
        tp_prep = random.randint(5, 30)
        tp_surgery = int(numpy.random.lognormal(4, 0.5) + 1)
        tp_cleaning = random.randint(10, 20)

        prep_time.append(tp_prep)
        surgery_time.append(tp_surgery)
        cleaning_time.append(tp_cleaning)
    string = ""
    string += "TP = " + str(prep_time) + "; \n"
    string += "TC = " + str(surgery_time) + "; \n"
    string += "TN = " + str(cleaning_time) + "; \n"
    return string


def add_setup_times_between_types(num_op_types, upper_bound_random=60):
    '''[TO][TO] - We assume it takes between 0 and 60 min to switch operation types.'''
    matrix = []
    for i in range(num_op_types):
        matrix.append([])
        for j in range(num_op_types):
            if i == j or not global_with_setup_time:
                matrix[i].append(0)
            else:
                matrix[i].append(random.randint(0, upper_bound_random))
    return "TCSTO = " + str(matrix) + "; \n"


def add_surgeon_room_eligibility(num_surgeons, num_rooms):
    # [C][S]
    row = []
    for i in range(num_surgeons):
        for j in range(num_rooms):
            rand = random.randint(0, 1)
            row.append(rand)
    return "CS = " + str(row) + "; \n"


def add_surgeon_specialty(num_surgeons, num_specialties):
    # [C][P]
    row = []
    for i in range(num_surgeons):
        for j in range(num_specialties):
            rand = random.randint(0, 1)
            row.append(rand)
    return "CP = " + str(row) + "; \n"


def create_file(num_operations, num_surgeons, num_rooms, num_op_types,
                latex_time, infection_time):
    string = "\n"
    string += add_variables(num_operations=num_operations,
                            num_op_types=num_op_types,
                            num_rooms=num_rooms, num_surgeons=num_surgeons, latex_time=latex_time,
                            infection_time=infection_time)

    string += add_room_eligibility_for_operation(num_rooms=num_rooms,
                                                 num_operations=num_operations)

    # --- Surgeon Modification ---
    matrix_chir, mot = add_surgeon_assignment_for_operation(num_surgeons=num_surgeons,
                                                            num_operations=num_operations)
    string += mot

    string += add_surgeon_schedule(num_surgeons=num_surgeons)
    string += add_patient_conditions(num_operations=num_operations)
    string += add_operation_type(num_operations=num_operations,
                                 num_op_types=num_op_types,
                                 matrix_C=matrix_chir)
    string += add_operation_times(num_operations=num_operations)
    string += add_setup_times_between_types(num_op_types=num_op_types)

    string += "\n"
    return string


def generate_n_instances(n=10, output_folder=None):
    if output_folder is None:
        raise ValueError("An output folder path must be provided.")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for i in range(n):
        if use_random:
            # If random is True, variables are drawn randomly
            num_operations_loc = random.randint(num_operations_min, num_operations_max)
            num_surgeons_loc = random.randint(num_surgeons_min, num_surgeons_max)
            num_rooms_loc = random.randint(num_rooms_min, num_rooms_max)
            num_op_types_loc = random.randint(num_op_types_min, num_op_types_max)
        else:
            # Otherwise, use global variables
            num_operations_loc = num_operations
            num_surgeons_loc = num_surgeons
            num_rooms_loc = num_rooms
            num_op_types_loc = num_op_types

        content = create_file(
            num_operations=num_operations_loc,
            num_op_types=num_op_types_loc,
            num_surgeons=num_surgeons_loc,
            num_rooms=num_rooms_loc,
            latex_time=latex_time,
            infection_time=infection_time
        )

        global global_with_setup_time
        if global_with_setup_time:
            str_st = "_ST"
        else:
            str_st = ""
        random_id = random.randint(0, 99999)

        output_file = os.path.join(output_folder,
                                   "o" + str(num_operations_loc) + "_c" + str(num_surgeons_loc) + "_s" + str(
                                       num_rooms_loc) + str_st + "_num_" + str(i) + "_id_" + str(random_id) + ".txt")
        with open(output_file, 'w') as f:
            f.write(content)
            print(output_file + " generated successfully")


current_directory = os.getcwd()
output_path = os.path.join(current_directory, "generation_result")

generate_n_instances(n=1, output_folder=output_path)
print("Program finished")
