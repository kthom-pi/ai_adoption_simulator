# AI Adoption Simulator

An agent-based model exploring the economic dynamics of AI and automation adoption in labor markets. Built with Mesa framework.

![Simulation Preview](https://img.shields.io/badge/Mesa-3.0+-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)

## Overview

This simulation models how AI and automation technologies spread through an economy, affecting workers, wages, and wealth distribution. Agents represent economic units that can transition between different states (human workers, AI-augmented workers, fully automated capital, displaced workers, or UBI recipients) based on their neighbors and economic conditions.

## Preview
https://github.com/user-attachments/assets/3c9b5688-be7b-4da4-aac4-b3c179dc5846

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Agent Types](#agent-types)
- [How It Works](#how-it-works)
- [Parameters Explained](#parameters-explained)
- [Interpreting the Graphs](#interpreting-the-graphs)
- [Economic Experiments](#economic-experiments)
- [Technical Details](#technical-details)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/kthom-pi/ai_adoption_simulator.git
cd ai_adoption_simulator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

Run the simulation:
```bash
python ai_sim.py
```

The server will launch at `http://127.0.0.1:8521` where you can interact with the visualization and adjust parameters in real-time.

## Agent Types

### 1. **Human Workers** (Gray Squares)
- Traditional workers performing manual labor
- **Income**: `wage_human` per step (default: $1.0)
- **Costs**: `cost_of_living` per step (default: $1.0)
- **Movement**: Active - moves randomly to adjacent cells (see [Movement Mechanics](#movement-mechanics))
- **Transitions**:
  - → AI Augmented (influenced by nearby augmented neighbors; see [Square Influence](#square-influence-radius-2-moore-in-depth))
  - → Displaced (crowded out by augmented workers or automated systems)

### 2. **AI Augmented Workers** (Blue Circles)
- Workers enhanced by AI tools and automation
- **Income**: `wage_augmented` per step (default: $2.5)
- **Costs**: `cost_of_living` per step
- **Movement**: Active - moves randomly to adjacent cells
- **Productivity**: Higher wage than human workers
- **Transitions**:
  - → **Automation event** (see “conservation of labor agents” below)
  - → Displaced (replaced by automated systems)

### 3. **Fully Automated** (Red Circles)
- Autonomous AI systems/robots (capital)
- **Income**: `revenue` per step (taxed)
  - Seeded automated agents start with `revenue = wage_augmented` and `wealth = 0` (see [`model.EvolutionaryModel.__init__`](model.py)).
  - Automated agents can also accumulate additional revenue via displacement “loot sharing” from nearby displaced workers (see [`agent.WorkerAgent.step`](agent.py)).
- **Costs**: None (machines don’t pay living costs)
- **Tax**: Subject to `robot_tax_rate` on revenue; taxes accumulate in `government_pot` (see [`agent.WorkerAgent.step`](agent.py))
- **Movement**: Active - moves randomly to adjacent cells
- **Special Ability**: Can merge with nearby automated agents (capital consolidation)
- **Transitions**:
  - → Merged entity (combines with nearby automated agents)

### 4. **Displaced Workers** (Yellow Squares)
- Workers who lost their jobs to automation/pressure
- **Income**: Transfers/UBI only
- **Costs**: `cost_of_living` per step (burning savings)
- **Movement**: None - stationary
- **Transitions**:
  - → Human or AI Augmented (rehired if their cell is not occupied by active workers; see [`agent.WorkerAgent.step`](agent.py))
  - → Removed (if wealth reaches zero)

### 5. **UBI Recipients** (Green Squares)
- Individuals who opted out of traditional labor
- **Income**: Transfers/UBI only
- **Costs**: `cost_of_living` per step
- **Movement**: None - stationary
- **Special**: Acts as a “ghost” for movement (doesn’t block other agents)
- **Transitions**:
  - → Removed (if wealth reaches zero)

## How It Works

### Grid Structure
- The simulation runs on a **30x30 toroidal grid** (900 cells).
  - Visualization grid is configured in [server.py](server.py).
  - Model grid defaults are configured in [`model.EvolutionaryModel.__init__`](model.py) (`width=30`, `height=30`).
- Each cell represents an **economic position** or job opportunity.
- Agents can technically share cells (Mesa `MultiGrid`), but **movement rules restrict “active” agents from stepping into cells occupied by any non-UBI agent** (see [Movement Mechanics](#movement-mechanics)).

### Step Sequence

Each simulation step follows this sequence:

#### 1. **Economics Phase** (All Agents)
- **Robot Tax Collection**: Automated agents pay `robot_tax_rate` into a government pool (`government_pot`) (see [`agent.WorkerAgent.step`](agent.py)).
- **Transfers / UBI Distribution (configurable split)**:
  - The government pool is split between two recipient groups:
    - **UBI group**: agents in state `UBI_RECIPIENT`
    - **Worker dividend group**: other non-automated agents (typically `HUMAN`, `AUGMENTED`, `DISPLACED`)
  - The split is controlled by **`ubi_class_tax_share`** (see [`model.EvolutionaryModel.step`](model.py)):
    - `ubi_class_tax_share = 0.70` means **70%** of the pool is shared among UBI recipients
    - The remaining **30%** is shared among the other non-automated agents
- **Cost of Living**: All non-automated agents pay living costs.
- **Wage Payment**:
  - Human workers earn `wage_human`
  - Augmented workers earn `wage_augmented`
  - Automated agents earn `revenue` minus robot tax

#### 2. **Behavior Phase** (By Agent Type)

**For UBI Recipients:**
- Check if wealth ≤ 0 → Remove from simulation
- No other actions

**For Displaced Workers:**
- Check if current cell is free of **active squatters** (agents that are *not* `DISPLACED` and *not* `UBI_RECIPIENT`)
- If free, attempt rehiring:
  - `hiring_chance` probability of getting rehired
  - If rehired, `upskill_chance` determines if they become Augmented or Human
- (Removal happens for UBI recipients; displaced removal happens in the worker logic branch when applicable—see [`agent.WorkerAgent.step`](agent.py))

**For Automated Agents:**
1. **Move** to a random adjacent cell
2. Count automated neighbors (Moore neighborhood, 8 cells)
3. If automated neighbors ≥ `combination_threshold`:
   - Merge with random automated neighbor
   - Combine revenue and wealth
   - Remove merged agent

**For Workers (Human & Augmented):**
1. **Move** to a random adjacent cell
2. Earn wage for this step
3. Check if wealth ≤ 0 → Remove from simulation
4. Compute **square influence** (radius-2 Moore neighborhood; see next section)
5. **Check transition conditions:**

   **Human Workers:**
   - If augmented neighbors ≥ `adopt_human_augmented_thresh`:
     - Roll `human_displacement_chance`: → Displaced (efficiency squeeze)
     - Else roll `adopt_human_augmented_prob`: → Augmented (adoption)

   **Augmented Workers (Automation + “conservation of labor agents”):**
   - If augmented neighbors ≥ `automation_threshold` and roll `automation_chance` succeeds:
     - **Spawn** a new `AUTOMATED` agent at the same location
     - Convert the original augmented worker to `DISPLACED`
     - New robot IDs are allocated via [`model.EvolutionaryModel.get_next_id`](model.py)
     - Implemented in [`agent.WorkerAgent.step`](agent.py)

   **Both:**
   - If automated neighbors ≥ `displacement_threshold`:
     - → Displaced
     - Worker’s current wage is redistributed as added `revenue` to the nearby robots considered in the same square influence neighborhood

#### 3. **Data Collection**
- Record all metrics for graphs and analysis (see [`model.EvolutionaryModel.datacollector`](model.py)).

---

### Square Influence (Radius-2 Moore) — In Depth

State transitions for **Human** and **Augmented** workers use an expanded “square” neighborhood (not just immediate adjacency). This is calculated in [`agent.WorkerAgent.step`](agent.py):

```py
neighbors = self.model.grid.get_neighbors(
    self.pos, moore=True, include_center=False, radius=2
)
```

#### 1) What “radius=2 Moore” means (geometrically)

- **Moore neighborhood** includes diagonals (a square, not a plus-shape).
- With `radius=2`, you get a **5×5 square** centered on the agent.
- With `include_center=False`, the agent’s own cell is excluded.

So the maximum number of neighbor *cells* considered is:

$$
(2r+1)^2 - 1 = (2\cdot 2 + 1)^2 - 1 = 5^2 - 1 = 24
$$

Because the grid is toroidal (`MultiGrid(..., torus=True)` in [`model.EvolutionaryModel.__init__`](model.py)), neighborhoods that would spill “off the edge” wrap around to the opposite side.

#### 2) What is counted from that neighborhood

From this set of neighbor agents, the worker computes:

- $n_{aug}$: number of neighbors in state `AUGMENTED`
- $n_{auto}$: number of neighbors in state `AUTOMATED`

Conceptually:

$$
n_{aug} = \sum_{j \in \mathcal{N}_{r=2}} \mathbf{1}[state(j)=AUGMENTED]
\qquad
n_{auto} = \sum_{j \in \mathcal{N}_{r=2}} \mathbf{1}[state(j)=AUTOMATED]
$$

where $\mathcal{N}_{r=2}$ is the radius-2 Moore neighborhood and $\mathbf{1}[\cdot]$ is 1 if true else 0.

#### 3) How those counts affect decisions (mechanically)

- **Human “efficiency squeeze” / adoption**
  - Condition: $n_{aug} \ge \texttt{adopt_human_augmented_thresh}$
  - Then:
    - with probability `human_displacement_chance`: Human → Displaced
    - else with probability `adopt_human_augmented_prob`: Human → Augmented

- **Augmented automation event (capital creation + labor displacement)**
  - Condition: $n_{aug} \ge \texttt{automation_threshold}$ and Bernoulli(`automation_chance`) succeeds
  - Then:
    - create new robot (AUTOMATED) at the same cell
    - original augmented worker becomes DISPLACED

- **Automation displacement pressure (robots displacing labor)**
  - Condition: $n_{auto} \ge \texttt{displacement_threshold}$
  - Then:
    - worker becomes DISPLACED
    - their wage is split across robot neighbors (in that same neighborhood) as added robot revenue

#### 4) Practical implications vs the old “adjacent only” influence

Previously, “influence” often meant just the 8 immediately adjacent cells. Now, each worker’s local pressure field can include up to **24** nearby positions, which tends to:
- increase the likelihood of crossing thresholds (more opportunities to “see” augmented/automated agents),
- produce broader spatial cascades (mid-range spillovers),
- reduce dependence on perfect adjacency.

> Note: Movement still uses immediate adjacency (radius 1); it’s the **transition influence** that uses radius 2.

---

### Movement Mechanics

**Who Moves:**
- ✅ Human workers
- ✅ AI Augmented workers
- ✅ Fully Automated agents
- ❌ Displaced workers (stationary)
- ❌ UBI recipients (stationary)

**Movement Pattern:**
- **Moore neighborhood**: 8 adjacent cells (including diagonals) (see [`agent.WorkerAgent.move`](agent.py))
- **Random selection**: Agent picks randomly from valid cells
- **Collision detection**:
  - An active mover can only step into a cell if it contains **no blocking agents**
  - The only non-blocking (“ghost”) occupants are `UBI_RECIPIENT` agents
  - Implemented by filtering out cells with *any* agent whose state is not `UBI_RECIPIENT` in [`agent.WorkerAgent.move`](agent.py)

**Example:**
```
[·] [A] [·]
[H] [X] [U]  ← X can move to any [·] or [U] cell, but not [A] or [H]
[·] [D] [·]  ← D blocks movement (not passable), U is passable (ghost)
```

## Parameters Explained

The interactive UI (Mesa server) exposes parameters with human-friendly labels. The tables below include:
- **UI Label**: what you see in the control panel
- **Parameter**: the underlying model/server parameter key

### Global Parameters

| UI Label | Parameter | Default | Range | Description |
|---|---|---:|---|---|
| `[Global] Total Agents` | `N` | 350 | 100-400 | Total number of agents in simulation |
| `[Global] Starting Wealth` | `starting_wealth` | 50 | 10-200 | Initial wealth for each agent |
| `[Global] Cost of Living` | `cost_of_living` | 1.0 | 0.0-5.0 | Amount deducted from non-automated agents per step |

### Policy Parameters

| UI Label | Parameter | Default | Range | Description |
|---|---|---:|---|---|
| `[Policy] % of Total Pop on UBI` | `initial_ubi_fraction` | 0.0 | 0.0-1.0 | Percentage of population starting as UBI recipients |
| `[Policy] Robot Tax Rate` | `robot_tax_rate` | 0.0 | 0.0-1.0 | Tax rate on automated agent revenue (funds transfers/UBI) |
| `[Policy] Tax % to UBI Class` | `ubi_class_tax_share` | 0.5 | 0.0-1.0 | Fraction of robot-tax pool allocated to the UBI class (rest goes to other non-automated agents) |

### Seed Parameters

| UI Label | Parameter | Default | Range | Description |
|---|---|---:|---|---|
| `[Seeds] Human (Remainder)` | `seeds_human` | 300 | 0-400 | Number of agents starting as Human workers |
| `[Seeds] Augmented` | `seeds_augmented` | 20 | 0-100 | Number of agents starting as AI Augmented |
| `[Seeds] Automated` | `seeds_automated` | 20 | 0-50 | Number of agents starting as Fully Automated |

### Economic Parameters

| UI Label | Parameter | Default | Range | Description |
|---|---|---:|---|---|
| `[Econ] Wage: Human` | `wage_human` | 1.0 | 0.0-10.0 | Income per step for human workers |
| `[Econ] Wage: Augmented` | `wage_augmented` | 2.5 | 0.0-10.0 | Income per step for augmented workers |

### Transition Parameters

| UI Label | Parameter | Default | Range | Description |
|---|---|---:|---|---|
| `[Trans] Human->Aug Neighbors` | `adopt_human_augmented_thresh` | 3 | 1-8 | Augmented neighbors needed to pressure human adoption (in the radius-2 square influence neighborhood) |
| `[Trans] Human->Aug Chance` | `adopt_human_augmented_prob` | 0.3 | 0.0-1.0 | Probability human adopts AI when threshold met |
| `[Trans] Efficiency Disp. Chance` | `human_displacement_chance` | 0.1 | 0.0-1.0 | Chance human is displaced by efficiency pressure |
| `[Trans] Aug->Auto Density` | `automation_threshold` | 4 | 1-8 | Augmented neighbors needed to trigger automation (radius-2 square influence neighborhood) |
| `[Trans] Aug->Auto Chance` | `automation_chance` | 0.1 | 0.0-1.0 | Probability augmented worker triggers an automation event |
| `[Trans] Displacement Pressure` | `displacement_threshold` | 2 | 1-8 | Automated neighbors needed to displace workers (radius-2 square influence neighborhood) |
| `[Trans] Auto Combine Density` | `combination_threshold` | 2 | 1-8 | Automated neighbors needed to trigger merger (immediate adjacency) |

### System Parameters

| UI Label | Parameter | Default | Range | Description |
|---|---|---:|---|---|
| `[System] Hiring Chance` | `hiring_chance` | 0.30 | 0.0-1.0 | Probability displaced worker gets rehired |
| `[System] Upskill Chance` | `upskill_chance` | 0.3 | 0.0-1.0 | Probability rehired worker becomes augmented vs human |
| `Random Seed (Optional)` | `seed` | 123 | (integer) | Reproducibility for runs (set blank/None for random) |

## Interpreting the Graphs

### 1. **Wealth Leaderboard**
Shows top 10 wealthiest agents by category.
- **Use**: Identify wealth concentration patterns
- **Watch for**: Automated agents accumulating massive wealth through mergers

### 2. **Population Dynamics**
Line chart showing agent counts over time.
- **Human** (gray): Traditional workforce
- **Augmented** (blue): AI-enhanced workers
- **Automated** (red): Capital/robots
- **Displaced** (yellow): Unemployed
- **UBI Recipients** (green): Alternative economy participants

**Interpret:**
- Declining human + augmented = workforce contraction
- Rising automated = capital replacing labor
- Rising displaced = unemployment crisis
- Steady UBI = stable alternative economy

### 3. **Employment Dynamics (Flows)**
Shows labor market churn.
- **Displaced**: Current unemployment
- **Fired (Step)**: New displacements this step
- **Hired (Step)**: Successful rehires this step
- **Removed (Step)**: Agents leaving simulation (death/bankruptcy)

**Interpret:**
- High fired + low hired = deteriorating job market
- Spikes in removed = economic crisis

### 4. **Economic Health (Capital vs Labor vs State)**
Bar chart and line chart showing wealth distribution.

**Bar Chart:**
- **Wealth_Labor**: Total wealth held by human + augmented workers
- **Wealth_Capital**: Total wealth held by automated agents
- **Wealth_State**: Total wealth held by UBI recipients

**Line Chart:**
- Individual category wealth over time

**Interpret:**
- Capital > Labor = wealth concentration in automation
- Declining labor wealth = workforce impoverishment
- Growing state wealth = UBI system working

### 5. **Fiscal Policy Monitor**
Tracks transfer/UBI viability relative to living costs.
- **UBI (Opt-Out)**: per-person transfer to `UBI_RECIPIENT` agents
- **UBI (Worker Div)**: per-person transfer to other non-automated agents (e.g., Human/Augmented/Displaced)
- **Cost of Living**: survival threshold

**Interpret:**
- Transfer > Cost of Living = sustainable for that group
- Transfer < Cost of Living = insufficient support
- Growing gap = economic stress

### 6. **Simulation Integrity**
Agent conservation tracking.
- **Alive**: Current agent count
- **Total Removed**: Cumulative removals (wealth ≤ 0)
- **Merged (Singularity)**: Cumulative automated consolidation events

**Interpret:**
- With the current automation rule, an automation event **spawns a new automated agent** while the original labor agent becomes displaced (see [`agent.WorkerAgent.step`](agent.py)).
  - This means total agent count can grow above the initial `N` (until merges/removals counteract it).
- “Conservation” here refers to **labor-agent continuity**: augmented workers aren’t deleted when capital is created; they persist as displaced labor.

## Economic Experiments

### Experiment 1: Universal Basic Income Viability
**Question**: Can robot taxes fund adequate UBI?

**Setup:**
- `robot_tax_rate`: 0.5
- `initial_ubi_fraction`: 0.2
- `seeds_automated`: 50
- Optional: set `ubi_class_tax_share` to bias transfers toward UBI recipients

**Watch**: Does UBI/transfer per person stay above cost of living? Do UBI recipients survive?

### Experiment 2: Adoption Cascades
**Question**: How does AI adoption spread through populations?

**Setup:**
- `seeds_augmented`: 5 (small seed)
- `adopt_human_augmented_thresh`: 2 (easy adoption)
- `adopt_human_augmented_prob`: 0.8 (high adoption rate)

**Watch**: Speed of augmented population growth. Does it reach saturation?

### Experiment 3: Automation Unemployment
**Question**: What displacement threshold causes mass unemployment?

**Setup:**
- Vary `displacement_threshold`: 1, 2, 3, 4
- `seeds_automated`: 30

**Watch**: Displaced population over time. Is there a critical threshold?

### Experiment 4: Wealth Inequality
**Question**: Does automation concentrate wealth?

**Setup:**
- `combination_threshold`: 2 (easy merging)
- `robot_tax_rate`: 0.0 (no redistribution)
- Run 500 steps

**Watch**: Wealth_Capital vs Wealth_Labor ratio. Leaderboard concentration.

### Experiment 5: Retraining Effectiveness
**Question**: Can displaced workers re-enter the economy?

**Setup:**
- `hiring_chance`: Vary 0.1, 0.5, 0.9
- `upskill_chance`: 0.8 (favor augmented rehiring)

**Watch**: Hired (Step) vs Fired (Step) ratio. Displaced population stabilization.

### Experiment 6: Living Wage Crisis
**Question**: What happens when wages don't cover living costs?

**Setup:**
- `wage_human`: 0.5
- `cost_of_living`: 1.5
- `wage_augmented`: 2.0

**Watch**: Human population decline rate. Pressure to adopt AI.

### Experiment 7: Singularity Scenario
**Question**: What happens when automation fully consolidates?

**Setup:**
- `seeds_automated`: 100
- `combination_threshold`: 1 (mergers always happen)
- `displacement_threshold`: 1 (high displacement)

**Watch**: Time to single mega-automated agent. Total wealth concentration.

### Experiment 8: Mixed Economy Stability
**Question**: Can humans, augmented, and UBI coexist?

**Setup:**
- `initial_ubi_fraction`: 0.3
- `robot_tax_rate`: 0.4
- Balanced seeds: 100/100/50/100 (H/Aug/Auto/UBI)

**Watch**: Population stability over 1000 steps. Wealth distribution balance.

## Technical Details

### File Structure
```
ai_adoption_simulator/
├── ai_sim.py          # Entry point
├── model.py           # Model class (EvolutionaryModel)
├── agent.py           # Agent class (WorkerAgent)
├── server.py          # Visualization server
├── constants.py       # Agent states and configurations
├── requirements.txt   # Dependencies
└── README.md          # This file
```

### Key Classes

**`EvolutionaryModel`** (model.py)
- Manages grid, scheduler, and global economics
- Handles robot tax collection and transfer/UBI distribution (including split by `ubi_class_tax_share`)
- Allocates unique IDs for spawned robots via [`model.EvolutionaryModel.get_next_id`](model.py)
- Collects data for visualization

**`WorkerAgent`** (agent.py)
- Individual agent logic and state transitions
- Movement and neighbor detection
- Economic actions (earning, spending)
- Implements radius-2 square influence for worker transitions in [`agent.WorkerAgent.step`](agent.py)

### Running Batch Experiments

### Export Data from Interactive Mode

While running the interactive simulation, you can export data programmatically:

```python
from model import EvolutionaryModel

# Create and run model
model = EvolutionaryModel(robot_tax_rate=0.5, seeds_automated=50)
for i in range(100):
    model.step()

# Export to CSV
model_data = model.datacollector.get_model_vars_dataframe()
agent_data = model.datacollector.get_agent_vars_dataframe()

model_data.to_csv('model_results.csv')
agent_data.to_csv('agent_results.csv')
```

### Run Pre-defined Experiments

Run batch experiments using the `batch_run.py` script:

```bash
python batch_run.py
```

This will run the default UBI viability experiment and save results to the `results/` directory.

### Available Pre-defined Experiments

Edit `batch_run.py` and uncomment experiments:

```python
if __name__ == "__main__":
    # experiment_ubi_viability()
    # experiment_adoption_cascades()
    # experiment_displacement_threshold()
    experiment_wealth_inequality()  # Run this one
```

### Run Custom Experiments

Create your own experiments:

```python
from batch_run import experiment_custom

experiment_custom({
    "robot_tax_rate": 0.3,
    "initial_ubi_fraction": 0.1,
    "wage_augmented": 3.0,
    "seeds_automated": 40
}, steps=1000, name="my_experiment")
```

### Output Files

Results are saved to `results/` directory with timestamps:
- `{experiment_name}_model_{timestamp}.csv` - Model-level metrics per step
- `{experiment_name}_agents_{timestamp}.csv` - Agent-level data per step

**Model CSV columns:**
- All population counts (Human, Augmented, Automated, Displaced, UBI Recipients)
- All wealth metrics (TotalWealth_Human, TotalWealth_Augmented, etc.)
- Flow metrics (Fired, Hired, Removed per step)
- Policy metrics (e.g., UBI / transfers, Cost of Living)
- All input parameters (for comparison across experiments)

**Agent CSV columns:**
- Agent ID
- Step number
- State (0=Human, 1=Augmented, 2=Automated, 3=Displaced, 4=UBI)
- Wealth
- Revenue (for automated agents)
- Position on grid

### Customization
To add new agent types or behaviors:
1. Add state constant to `constants.py`
2. Implement logic in `agent.py` step method
3. Update `STATE_MAP` for visualization
4. Add data collectors in `model.py`

## Contributing
Contributions welcome!

## License
MIT License - See LICENSE file for details

## Citation
If you use this simulator in research, please cite:
```
@software{ai_adoption_simulator,
  author = {Kenneth Thomas},
  title = {AI Adoption Simulator},
  year = {2025},
  url = {https://github.com/kthom-pi/ai_adoption_simulator}
}
```

## Acknowledgments
Built with [Mesa](https://github.com/projectmesa/mesa) - Agent-Based Modeling in Python
