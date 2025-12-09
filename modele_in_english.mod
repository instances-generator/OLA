/*********************************************
 * OPL 22.1.1.0 Model
 * Author: M_CHOURAQUI's Interval Model
 *********************************************/

using CP;

/* ==========================================================
   1. DATA DEFINITION
   ========================================================== */
int num_surgeons = ...;
int num_rooms = ...;
int num_operations = ...;
int num_op_types = ...;
// Equipment variables removed

int num_patients = ...;
// Block logic: 4 rooms per block
int num_blocks = (num_rooms + 3) div 4; 

range Operations = 0..num_operations-1;
range Rooms = 0..num_rooms-1;
range Surgeons = 0..num_surgeons-1;
range OpTypes = 0..num_op_types-1;
range Blocks = 0..num_blocks-1;

// Maps each room to a block index
int Room_Block[r in Rooms] = r div 4;

int infection_time = ...;
int latex_time = ...;
int max_wait_limit = 40; 
int max_time = 10000;
int w = 1; 

/* --- Inputs --- */
int A[Operations][Rooms] = ...; 
int C[Surgeons][Operations] = ...; 


int start_time[Surgeons] = ...; 
int end_time[Surgeons] = ...;   

int I[Operations] = ...; 
int L[Operations] = ...; 

int T[Operations][OpTypes] = ...; 
int TP[Operations] = ...; 
int TC[Operations] = ...; 
int TN[Operations] = ...; 

// Total Time = Prep + Cut + Nettoyage
int TT[o in Operations] = TP[o] + TC[o] + TN[o]; 

// TS removed
int TCSTO[OpTypes][OpTypes] = ...; 

/* ==========================================================
   2. TRANSITIONS
   ========================================================== */
// Matrix calculating setup time between two operations (o1 -> o2)
// Logic: Infection cleanup + Latex prep + Type switching setup
int TransMatrix[o1 in Operations][o2 in Operations] = 
    (I[o1] * infection_time) + 
    (L[o2] * (1 - L[o1]) * latex_time) +
    sum(t1 in OpTypes, t2 in OpTypes) (T[o1][t1] * T[o2][t2] * TCSTO[t1][t2]);

tuple triplet { int id1; int id2; int value; };
{triplet} TransitionTuples = { <o1, o2, TransMatrix[o1][o2]> | o1 in Operations, o2 in Operations };

/* ==========================================================
   3. DECISION VARIABLES
   ========================================================== */

// --- OPTIMIZATION 1: Master Interval ---
dvar interval op[o in Operations] size TT[o]; 

dvar interval op_room[o in Operations][r in Rooms] optional size TT[o];
dvar interval op_surgeon[o in Operations][s in Surgeons] optional size TC[o];
// op_mat removed

dvar sequence seq_rooms[r in Rooms] in all(o in Operations) op_room[o][r] types all(o in Operations) o;
dvar sequence seq_surgeons[s in Surgeons] in all(o in Operations) op_surgeon[o][s];
// seq_mat removed

// --- OPTIMIZATION 2: Block Variable ---
// Assigns a surgeon to a specific block of rooms
dvar int Surgeon_Block_Assignment[Surgeons] in Blocks; 

dvar int+ max_wait;
dvar int+ total_delay; // formerly theta
dvar int+ makespan;    // formerly Cmax  

/* ==========================================================
   4. OBJECTIVE
   ========================================================== */
minimize makespan + (total_delay * w);

/* ==========================================================
   5. CONSTRAINTS
   ========================================================== */
subject to {

  // Define Makespan (Based on master interval)
  makespan == max(o in Operations) endOf(op[o]);

  // --- A. Allocation & Compatibility ---
  forall(o in Operations) {
     // Solver chooses ONE room among authorized ones (A[o][r]==1)
     alternative(op[o], all(r in Rooms : A[o][r] == 1) op_room[o][r]);
  }

  // --- B. Synchronization (Via Master) ---
  
  // Surgeons
  forall(o in Operations, s in Surgeons : C[s][o] == 1) {
    presenceOf(op_surgeon[o][s]) == 1;
    // Direct synchronization with master: Surgeon starts after Prep Time (TP)
    startOf(op_surgeon[o][s]) == startOf(op[o]) + TP[o];
  }
  
  // Surgeons not involved (Cleaning/Other)
  forall(o in Operations, s in Surgeons : C[s][o] == 0)
    presenceOf(op_surgeon[o][s]) == 0;


  // --- C. No Overlap ---
  // Rooms have transition times
  forall(r in Rooms) noOverlap(seq_rooms[r], TransitionTuples, true);
  // Surgeons cannot clone themselves
  forall(s in Surgeons) noOverlap(seq_surgeons[s]);

  // --- D. Business Logic ---

  // Schedules & Delay (Theta)
  forall(s in Surgeons, o in Operations)
    startOf(op_surgeon[o][s], start_time[s]) >= start_time[s];

  forall(s in Surgeons, o in Operations : C[s][o] == 1)
      total_delay >= endOf(op_surgeon[o][s], 0) - end_time[s];

  // BLOCK CONSTRAINT (Optimized Linear Version)
  // If a surgeon performs an operation in a room, that room must be in the surgeon's assigned block
  forall(s in Surgeons) {
    forall(o in Operations : C[s][o] == 1) { 
        forall(r in Rooms) {
            presenceOf(op_room[o][r]) => (Surgeon_Block_Assignment[s] == Room_Block[r]);
        }
    }
  }

  // --- E. Max Wait Time ---
  max_wait <= max_wait_limit;

  forall(s in Surgeons) {
    forall(o in Operations : C[s][o] == 1) { 
      // If there is a previous operation for this surgeon...
      (typeOfPrev(seq_surgeons[s], op_surgeon[o][s], -1, -1) != -1) => 
         // ...the gap between them must not exceed max_wait
         (startOf(op_surgeon[o][s]) - endOfPrev(seq_surgeons[s], op_surgeon[o][s], 0, 0) <= max_wait);
    }
  }
}

/* ==========================================================
   6. MAIN SCRIPTING
   ========================================================== */
main {
  // 1. Load data
  thisOplModel.generate();

  // 2. Start Search
  cp.startNewSearch();

  writeln("*************************************************");
  writeln("* SOLUTION LOG                                  *");
  writeln("*************************************************");

  // 3. Loop: While a better solution is found
  while (cp.next()) {
    var time = cp.info.SolveTime;
    var obj = cp.getObjValue();
    
    // Access decision variables via thisOplModel
    var valMakespan = thisOplModel.makespan.solutionValue;
    var valDelay = thisOplModel.total_delay.solutionValue;
    
    writeln("Time: " + time + "s | Obj: " + obj + " | Makespan: " + valMakespan + " | Delay: " + valDelay);
  }
  
  writeln("*************************************************");
  writeln("* END OF SEARCH                                 *");
  writeln("*************************************************");
}