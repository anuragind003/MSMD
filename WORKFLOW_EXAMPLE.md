# Complete Workflow Example: Door Latch Mechanism

This document walks through the complete synthesis process using the **Door Latch Mechanism** task as a concrete example.

---

## 📋 Step 1: Input - Design Task

**File**: `tasks/door_latch_task.json`

```json
{
  "task_name": "Door Latch Mechanism",
  "description": "A 2-state mechanism to act as a door latch, with handle and bolt as I/O elements.",
  "elements": {
    "E1": "handle",
    "E2": "bolt"
  },
  "elemental_functions": [
    {
      "ef_id": "EF1",
      "type": "Type-1.1",
      "description": "Apply torque on handle to retract bolt.",
      "behavior": [
        { "element": "E1", "effort": "-", "motion": "-" },
        { "element": "E2", "effort": "0", "motion": "+" }
      ]
    },
    {
      "ef_id": "EF2",
      "type": "Type-2",
      "description": "Handle cannot be over-rotated.",
      "behavior": [
        { "element": "E1", "effort": "-", "motion": "0" },
        { "element": "E2", "effort": "0", "motion": "0" }
      ]
    },
    {
      "ef_id": "EF3",
      "type": "Type-3",
      "description": "Release handle, spring returns it.",
      "behavior": [
        { "element": "E1", "effort": "0", "motion": "+" },
        { "element": "E2", "effort": "0", "motion": "-" }
      ]
    },
    {
      "ef_id": "EF4",
      "type": "Type-1.2",
      "description": "Push bolt in (slamming), handle does not move.",
      "behavior": [
        { "element": "E1", "effort": "0", "motion": "0" },
        { "element": "E2", "effort": "+", "motion": "+" }
      ]
    }
  ]
}
```

**What the system sees:**
- Task: Door latch with handle (E1) and bolt (E2)
- 4 Elemental Functions to satisfy:
  - **EF1** (Type-1.1): Rotate handle → retract bolt
  - **EF2** (Type-2): Constraint/stopper (prevent over-rotation)
  - **EF3** (Type-3): Spring return mechanism
  - **EF4** (Type-1.2): Variable constraint (bolt can move independently)

---

## 🤖 Step 2: Gemini AI - Initial Building Block Selection

**What happens:**

The system calls Gemini AI with this prompt:

```
TASK: A 2-state mechanism to act as a door latch, with handle and bolt as I/O elements.

ELEMENTAL FUNCTIONS REQUIRED:
- EF1: Type-1.1 - Apply torque on handle to retract bolt.
- EF2: Type-2 - Handle cannot be over-rotated.
- EF3: Type-3 - Release handle, spring returns it.
- EF4: Type-1.2 - Push bolt in (slamming), handle does not move.

Please rank mechanisms that can serve as a good starting point...
```

**Gemini AI Response (example):**

```json
[
  {
    "name": "Slider-Crank",
    "score": 0.95,
    "reasoning": "Perfect match - converts rotational input (handle) to linear motion (bolt retraction), which is exactly what EF1 requires"
  },
  {
    "name": "Rack and Pinion",
    "score": 0.85,
    "reasoning": "Good match - also converts rotation to translation, suitable for door latch mechanism"
  },
  {
    "name": "Four-Bar Linkage",
    "score": 0.45,
    "reasoning": "Less suitable - provides rotation-to-rotation, not the linear motion needed for bolt"
  }
]
```

**System Output:**
```
[Gemini AI Ranking Results]
  1. Slider-Crank: 0.95 - Perfect match - converts rotational input...
  2. Rack and Pinion: 0.85 - Good match - also converts rotation...
  3. Four-Bar Linkage: 0.45 - Less suitable - provides rotation-to-rotation...

 -> Found 2 initial solution(s)
   - Slider-Crank (DOF: 1, Source: ai_retrieval)
   - Rack and Pinion (DOF: 1, Source: ai_retrieval)
```

**Result:** System selects **Slider-Crank** as the primary initial solution (score > 0.1 threshold).

---

## 🎯 Step 3: Initial Solution Creation

**What happens:**

The system creates a Slider-Crank mechanism graph:

```
Elements:
- E0: Ground
- E1: Crank (handle)
- E2: Coupler
- E3: Slider (bolt)

Joints:
- E0 ↔ E1: Revolute (R) - Ground to Crank
- E1 ↔ E2: Revolute (R) - Crank to Coupler
- E2 ↔ E3: Revolute (R) - Coupler to Slider
- E0 ↔ E3: Prismatic (P) - Ground to Slider (linear guide)

DOF: 1 ✓ (single input mechanism)
Connected: True ✓
```

**EF Validation:**
- ✅ **EF1 satisfied**: Slider-Crank provides rotation (handle) → translation (bolt)
- ❌ **EF2 not satisfied**: No stopper/constraint
- ❌ **EF3 not satisfied**: No return spring
- ❌ **EF4 not satisfied**: No variable constraint

**Visualization Saved:**
- `output/synthesis_steps/Door_Latch_Mechanism/Slider-Crank/step_000_initial.png`
- Shows: Initial Slider-Crank topology with EF1 satisfied

---

## 🔍 Step 4: A* Search - Iteration 1

**Current State:**
- Graph: Slider-Crank
- Satisfied EFs: {EF1}
- Satisfied EF Types: {Type-1.1}
- Path: []

**Goal:** Satisfy all EFs: {EF1, EF2, EF3, EF4}

**A* Algorithm:**

1. **Pick next EF to satisfy:** EF2 (Type-2 - Constraint/stopper)

2. **Find applicable rules:**
   - Current satisfied types: {Type-1.1}
   - Required type: Type-2
   - Matching rules:
     - **R3.1**: Add Stopper (Type-1.1 → Type-2, cost: 1)
     - **R6.1**: Add Over-Center (Type-1.1 → Type-2, cost: 3)

3. **Apply Rule R3.1 (cheaper):**
   ```
   Operation: ADD_STOPPER
   Action: Add fixed joint (F) between elements
   ```

4. **New Graph:**
   ```
   Previous joints + New joint:
   - E0 ↔ E3: Fixed (F) - Stopper constraint
   ```

5. **Validation:**
   - ✅ Graph connected: Yes
   - ✅ DOF valid: 1 (still valid)
   - ✅ EF2 satisfied: Stopper prevents over-rotation

6. **New State:**
   - Satisfied EFs: {EF1, EF2}
   - Satisfied EF Types: {Type-1.1, Type-2}
   - Path: [R3.1]
   - Cost: 1
   - Heuristic: 2 (2 EFs remaining)

7. **Visualization Saved:**
   - `output/synthesis_steps/.../step_001_R3.1.png`
   - Shows: Slider-Crank with stopper added

**Queue State:**
```
Priority Queue:
- (3, 1, Node(EFs={EF1,EF2}, Path=[R3.1]))  ← Current best
- (5, 3, Node(EFs={EF1,EF2}, Path=[R6.1]))  ← Alternative path
```

---

## 🔍 Step 5: A* Search - Iteration 2

**Current State:**
- Graph: Slider-Crank + Stopper
- Satisfied EFs: {EF1, EF2}
- Satisfied EF Types: {Type-1.1, Type-2}
- Path: [R3.1]

**Next EF:** EF3 (Type-3 - Return spring)

**Find applicable rules:**
- Current types: {Type-1.1, Type-2}
- Required: Type-3
- Matching rules:
  - **R4.1**: Add Return Spring (Type-1.1 → Type-3, cost: 2)
  - **R5.1**: Add Damper (Type-1.1 → Type-3, cost: 2)

**Apply Rule R4.1:**
```
Operation: ADD_RETURN_SPRING
Action: Add revolute joint with spring behavior
```

**New Graph:**
```
Previous joints + New joint:
- E1 ↔ E3: Revolute (R) - Return spring connection
```

**Validation:**
- ✅ Graph connected: Yes
- ✅ DOF valid: 1
- ✅ EF3 satisfied: Spring return mechanism added

**New State:**
- Satisfied EFs: {EF1, EF2, EF3}
- Satisfied EF Types: {Type-1.1, Type-2, Type-3}
- Path: [R3.1, R4.1]
- Cost: 3 (1 + 2)
- Heuristic: 1 (1 EF remaining)

**Visualization Saved:**
- `output/synthesis_steps/.../step_002_R4.1.png`
- Shows: Slider-Crank + Stopper + Spring

---

## 🔍 Step 6: A* Search - Iteration 3

**Current State:**
- Graph: Slider-Crank + Stopper + Spring
- Satisfied EFs: {EF1, EF2, EF3}
- Satisfied EF Types: {Type-1.1, Type-2, Type-3}
- Path: [R3.1, R4.1]

**Next EF:** EF4 (Type-1.2 - Variable constraint)

**Find applicable rules:**
- Current types: {Type-1.1, Type-2, Type-3}
- Required: Type-1.2
- Matching rule:
  - **R2.1**: Add Variable Joint (Type-1.1 → Type-1.2, cost: 2)

**Apply Rule R2.1:**
```
Operation: ADD_VARIABLE_JOINT
Action: Add variable constraint joint
```

**New Graph:**
```
Previous joints + New joint:
- E1 ↔ E2: Variable joint (allows independent motion)
```

**Validation:**
- ✅ Graph connected: Yes
- ✅ DOF valid: 1
- ✅ EF4 satisfied: Variable constraint allows bolt to move independently

**New State:**
- Satisfied EFs: {EF1, EF2, EF3, EF4} ✅ **ALL SATISFIED!**
- Satisfied EF Types: {Type-1.1, Type-1.2, Type-2, Type-3}
- Path: [R3.1, R4.1, R2.1]
- Cost: 5 (1 + 2 + 2)

**GOAL CHECK:**
```
All EFs satisfied? Yes!
Final path: R3.1 → R4.1 → R2.1
```

**Visualization Saved:**
- `output/synthesis_steps/.../step_003_FINAL.png`
- Shows: Complete mechanism satisfying all EFs

---

## ✅ Step 7: Final Solution

**Final Mechanism:**
```
Slider-Crank with:
- Stopper (R3.1): Prevents over-rotation
- Return Spring (R4.1): Returns handle to original position
- Variable Joint (R2.1): Allows independent bolt motion
```

**Satisfied EFs:**
- ✅ EF1: Rotate handle → retract bolt (Type-1.1)
- ✅ EF2: Handle cannot be over-rotated (Type-2)
- ✅ EF3: Spring returns handle (Type-3)
- ✅ EF4: Bolt can move independently (Type-1.2)

**Output Files:**
```
output/
├── solution_1_Slider-Crank.png                    # Final schematic
└── synthesis_steps/
    └── Door_Latch_Mechanism/
        └── Slider-Crank/
            ├── step_000_initial.png               # Initial Slider-Crank
            ├── step_001_R3.1.png                  # + Stopper
            ├── step_002_R4.1.png                  # + Spring
            └── step_003_FINAL.png                 # Complete mechanism
```

**Console Output:**
```
======================================================
               SYNTHESIS COMPLETE
======================================================
Successfully synthesized 1 valid mechanism(s).

--- Final Solution #1 (from 'Slider-Crank') ---
  Modification Path: R3.1 -> R4.1 -> R2.1
  -> Schematic saved to 'output/solution_1_Slider-Crank.png'
  -> Step-by-step visualizations saved to: output/synthesis_steps/Door_Latch_Mechanism/Slider-Crank/
```

---

## 📊 Complete A* Search Tree

```
                    [Initial: EF1]
                         |
                    [Apply R3.1]
                         |
              [EF1, EF2] (cost: 1)
                         |
                    [Apply R4.1]
                         |
          [EF1, EF2, EF3] (cost: 3)
                         |
                    [Apply R2.1]
                         |
    [EF1, EF2, EF3, EF4] (cost: 5) ✅ GOAL
```

**Total Transformations:** 3 rules
**Total Cost:** 5
**Final DOF:** 1 (valid)

---

## 🎨 Visualization Timeline

| Step | Image | Description | Satisfied EFs |
|------|-------|-------------|---------------|
| 0 | `step_000_initial.png` | Initial Slider-Crank | EF1 |
| 1 | `step_001_R3.1.png` | Added Stopper | EF1, EF2 |
| 2 | `step_002_R4.1.png` | Added Return Spring | EF1, EF2, EF3 |
| 3 | `step_003_FINAL.png` | Added Variable Joint | EF1, EF2, EF3, EF4 ✅ |

---

## 🔑 Key Points

1. **Gemini AI** intelligently selects Slider-Crank as the best starting point
2. **A* Search** systematically explores transformation paths
3. **EF Validation** ensures each step actually satisfies the requirements
4. **Dynamic Type Tracking** allows rules from any satisfied EF type
5. **Step-by-Step Visualization** shows the mechanism evolving
6. **Final Solution** satisfies all 4 elemental functions

---

## 🚀 Running This Example

```bash
# 1. Set up Gemini API key (optional but recommended)
export GEMINI_API_KEY="your_key_here"

# 2. Run the synthesis
python run.py

# 3. Select task: door_latch_task.json

# 4. Choose method: [1] AI (Gemini AI)

# 5. Watch the synthesis process and view results in output/
```

---

**This workflow demonstrates how the system:**
- Uses AI to intelligently select initial building blocks
- Systematically transforms mechanisms to satisfy all requirements
- Validates each step to ensure correctness
- Provides visual documentation of the entire process

