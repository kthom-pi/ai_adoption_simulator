# # AI Adoption Simulator

An agent-based model exploring the economic dynamics of AI and automation adoption in labor markets. Built with Mesa framework.

![Simulation Preview](https://img.shields.io/badge/Mesa-3.0+-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)

## Overview

This simulation models how AI and automation technologies spread through an economy, affecting workers, wages, and wealth distribution. Agents represent economic units that can transition between different states (human workers, AI-augmented workers, fully automated capital, displaced workers, or UBI recipients) based on their neighbors and economic conditions.

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
git clone https://github.com/yourusername/ai_adoption_simulator.git
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
- **Movement**: Active - moves randomly to adjacent cells
- **Transitions**: 
  - → AI Augmented (influenced by augmented neighbors)
  - → Displaced (crowded out by augmented workers or automated systems)

### 2. **AI Augmented Workers** (Blue Circles)
- Workers enhanced by AI tools and automation
- **Income**: `wage_augmented` per step (default: $2.5)
- **Costs**: `cost_of_living` per step
- **Movement**: Active - moves randomly to adjacent cells
- **Productivity**: 2.5x more productive than human workers
- **Transitions**: 
  - → Fully Automated (high automation pressure from neighbors)
  - → Displaced (replaced by automated systems)

### 3. **Fully Automated** (Red Circles)
- Autonomous AI systems/robots that replaced workers
- **Income**: `revenue` (inherited from displaced worker's wage)
- **Costs**: None (machines don't consume)
- **Tax**: Subject to `robot_tax_rate` on revenue
- **Movement**: Active - moves randomly to adjacent cells
- **Special Ability**: Can merge with nearby automated agents (capital consolidation)
- **Transitions**: 
  - → Merged entity (combines with nearby automated agents)

### 4. **Displaced Workers** (Yellow Squares)
- Workers who lost their jobs to automation
- **Income**: UBI payments only
- **Costs**: `cost_of_living` per step (burning savings)
- **Movement**: None - stationary
- **Transitions**: 
  - → Human or AI Augmented (rehired if space available)
  - → Removed (if wealth reaches zero)

### 5. **UBI Recipients** (Green Squares)
- Individuals who opted out of traditional labor
- **Income**: UBI payments only
- **Costs**: `cost_of_living` per step
- **Movement**: None - stationary
- **Special**: Acts as "ghost" - doesn't block other agents' movement
- **Transitions**: 
  - → Removed (if wealth reaches zero)

## How It Works

### Grid Structure
- The simulation runs on a **20x20 grid** (400 cells)
- Each cell represents an **economic position** or job opportunity
- Agents can occupy the same cell (except active workers block each other)

### Step Sequence

Each simulation step follows this sequence:

#### 1. **Economics Phase** (All Agents)
- **UBI Distribution**: Government pot (from robot taxes) divided among all biological agents
- **Cost of Living**: All non-automated agents pay living costs
- **Wage Payment**: 
  - Human workers earn `wage_human`
  - Augmented workers earn `wage_augmented`
  - Automated agents earn `revenue` minus robot tax

#### 2. **Behavior Phase** (By Agent Type)

**For UBI Recipients:**
- Check if wealth ≤ 0 → Remove from simulation
- No other actions

**For Displaced Workers:**
- Check if current cell is empty (no active workers)
- If empty, attempt rehiring:
  - `hiring_chance` probability of getting rehired
  - If rehired, `upskill_chance` determines if they become Augmented or Human
- If wealth ≤ 0 → Remove from simulation

**For Automated Agents:**
1. **Move** to random adjacent cell
2. Count automated neighbors (Moore neighborhood, 8 cells)
3. If automated neighbors ≥ `combination_threshold`:
   - Merge with random automated neighbor
   - Combine revenue and wealth
   - Remove merged agent

**For Workers (Human & Augmented):**
1. **Move** to random adjacent cell
2. Earn wage for this step
3. Check if wealth ≤ 0 → Remove from simulation
4. Count neighbors by type
5. **Check transition conditions:**

   **Human Workers:**
   - If augmented neighbors ≥ `adopt_human_augmented_thresh`:
     - Roll `human_displacement_chance`: → Displaced (efficiency squeeze)
     - Else roll `adopt_human_augmented_prob`: → Augmented (adoption)
   
   **Augmented Workers:**
   - If augmented neighbors ≥ `automation_threshold`:
     - Roll `automation_chance`: → Automated
   
   **Both:**
   - If automated neighbors ≥ `displacement_threshold`:
     - → Displaced
     - Worker's wage redistributed to neighboring robots as revenue

#### 3. **Data Collection**
- Record all metrics for graphs and analysis

### Movement Mechanics

**Who Moves:**
- ✅ Human workers
- ✅ AI Augmented workers
- ✅ Fully Automated agents
- ❌ Displaced workers (stationary)
- ❌ UBI recipients (stationary)

**Movement Pattern:**
- **Moore neighborhood**: 8 adjacent cells (including diagonals)
- **Random selection**: Agent picks randomly from valid cells
- **Collision detection**: Cannot move to cells occupied by active workers
- **Ghost mechanic**: UBI recipients don't block movement

**Example:**
```
[·] [A] [·]
[H] [X] [U]  ← X can move to any [·] or [U] cell, but not [A] or [H]
[·] [D] [·]  ← D (displaced) is also passable
```

## Parameters Explained

### Global Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `N` | 350 | 100-400 | Total number of agents in simulation |
| `starting_wealth` | 50 | 10-200 | Initial wealth for each agent |
| `cost_of_living` | 1.0 | 0.0-5.0 | Amount deducted from non-automated agents per step |

### Policy Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `initial_ubi_fraction` | 0.0 | 0.0-1.0 | Percentage of population starting as UBI recipients |
| `robot_tax_rate` | 0.0 | 0.0-1.0 | Tax rate on automated agent revenue (funds UBI) |

### Seed Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `seeds_human` | 300 | 0-400 | Number of agents starting as Human workers |
| `seeds_augmented` | 20 | 0-100 | Number of agents starting as AI Augmented |
| `seeds_automated` | 20 | 0-50 | Number of agents starting as Fully Automated |

### Economic Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `wage_human` | 1.0 | 0.0-10.0 | Income per step for human workers |
| `wage_augmented` | 2.5 | 0.0-10.0 | Income per step for augmented workers |

### Transition Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `adopt_human_augmented_thresh` | 3 | 1-8 | Augmented neighbors needed to pressure human adoption |
| `adopt_human_augmented_prob` | 0.3 | 0.0-1.0 | Probability human adopts AI when threshold met |
| `human_displacement_chance` | 0.1 | 0.0-1.0 | Chance human is displaced by efficiency pressure |
| `automation_threshold` | 4 | 1-8 | Augmented neighbors needed to trigger automation |
| `automation_chance` | 0.1 | 0.0-1.0 | Probability augmented worker becomes automated |
| `displacement_threshold` | 2 | 1-8 | Automated neighbors needed to displace workers |
| `combination_threshold` | 2 | 1-8 | Automated neighbors needed to trigger merger |

### System Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `hiring_chance` | 0.30 | 0.0-1.0 | Probability displaced worker gets rehired |
| `upskill_chance` | 0.3 | 0.0-1.0 | Probability rehired worker becomes augmented vs human |

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
Tracks UBI system viability.
- **UBI (Per Person)**: Amount each biological agent receives
- **Cost of Living**: Survival threshold

**Interpret:**
- UBI > Cost of Living = sustainable UBI
- UBI < Cost of Living = UBI insufficient
- Growing gap = economic stress

### 6. **Simulation Integrity**
Agent conservation tracking.
- **Alive**: Current agent count
- **Total Removed**: Cumulative deaths/bankruptcies
- **Merged (Singularity)**: Automated agents consolidated

**Interpret:**
- Alive + Total Removed should equal starting N + UBI seeds
- High mergers = capital consolidation (monopolization)

## Economic Experiments

### Experiment 1: Universal Basic Income Viability
**Question**: Can robot taxes fund adequate UBI?

**Setup:**
- `robot_tax_rate`: 0.5
- `initial_ubi_fraction`: 0.2
- `seeds_automated`: 50

**Watch**: Does UBI/person stay above cost of living? Do UBI recipients survive?

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
└── README.md         # This file
```

### Key Classes

**`EvolutionaryModel`** (model.py)
- Manages grid, scheduler, and global economics
- Handles UBI calculation and distribution
- Collects data for visualization

**`WorkerAgent`** (agent.py)
- Individual agent logic and state transitions
- Movement and neighbor detection
- Economic actions (earning, spending)

### Data Collection
All metrics are collected via Mesa's `DataCollector` and available for export:
```python
model = EvolutionaryModel()
for i in range(100):
    model.step()
    
df = model.datacollector.get_model_vars_dataframe()
df.to_csv('simulation_results.csv')
```

### Customization
To add new agent types or behaviors:
1. Add state constant to `constants.py`
2. Implement logic in `agent.py` step method
3. Update `STATE_MAP` for visualization
4. Add data collectors in `model.py`

## Contributing
Contributions welcome! Please open issues for bugs or feature requests.

## License
MIT License - See LICENSE file for details

## Citation
If you use this simulator in research, please cite:
```
@software{ai_adoption_simulator,
  author = {Your Name},
  title = {AI Adoption Simulator},
  year = {2025},
  url = {https://github.com/yourusername/ai_adoption_simulator}
}
```

## Acknowledgments
Built with [Mesa](https://github.com/projectmesa/mesa) - Agent-Based Modeling in Python
