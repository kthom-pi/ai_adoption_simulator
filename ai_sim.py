import mesa
import random

# ==========================================
# 1. CONSTANTS & CONFIGURATION
# ==========================================

HUMAN = 0
AUGMENTED = 1
AUTOMATED = 2
DISPLACED = 3
UBI_RECIPIENT = 4 

STATE_MAP = {
    HUMAN: {"name": "Human", "color": "#808080", "shape": "rect", "scale": 0.5},
    AUGMENTED: {"name": "AI Augmented", "color": "#4285f4", "shape": "circle", "scale": 0.7},
    AUTOMATED: {"name": "Fully Automated", "color": "#ff0000", "shape": "circle", "scale": 0.8},
    DISPLACED: {"name": "Displaced", "color": "#ffd700", "shape": "rect", "scale": 0.75}, 
    UBI_RECIPIENT: {"name": "UBI Opt-Out", "color": "#32CD32", "shape": "rect", "scale": 1.0} 
}

# ==========================================
# 2. HELPER CLASSES
# ==========================================

class SectionHeader(mesa.visualization.TextElement):
    def __init__(self, text):
        self.text = text
    def render(self, model):
        return f"<h3 style='margin-top: 20px; color: #333; border-bottom: 2px solid #eee; padding-bottom: 5px;'>{self.text}</h3>"

class LeaderboardElement(mesa.visualization.TextElement):
    def render(self, model):
        html = "<div style='font-family: monospace; border: 1px solid #ddd; padding: 10px; background: #fafafa; display: flex; gap: 10px; flex-wrap: wrap;'>"
        for state_code in [AUTOMATED, AUGMENTED, HUMAN, DISPLACED, UBI_RECIPIENT]:
            role_data = STATE_MAP[state_code]
            role_name = role_data["name"]
            color = role_data["color"]
            agents = [a for a in model.schedule.agents if a.state == state_code]
            top_list = sorted(agents, key=lambda a: a.wealth, reverse=True)[:10]
            html += f"<div style='flex: 1; min-width: 120px;'>"
            html += f"<b style='color:{color}; border-bottom: 1px solid {color}; display:block; margin-bottom:5px;'>{role_name}</b>"
            if not top_list:
                html += "<span style='color:#ccc; font-size: 0.8em;'>None</span>"
            else:
                for a in top_list:
                    html += f"<span style='font-size: 0.8em;'>#{a.unique_id}: <b>${a.wealth:.0f}</b></span><br>"
            html += "</div>"
        html += "</div>"
        return html

# ==========================================
# 3. AGENT CLASS
# ==========================================

class WorkerAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = HUMAN
        self.wealth = model.starting_wealth 
        self.displaced_by = None 
        self.revenue = 0 

    def move(self):
        # UBI Recipients and Displaced do NOT move
        if self.pos is None or self.state == DISPLACED or self.state == UBI_RECIPIENT:
            return

        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        
        valid_steps = []
        for pos in possible_steps:
            cell_contents = self.model.grid.get_cell_list_contents(pos)
            
            # GHOST LOGIC: 
            # A cell is valid if it is EMPTY or only contains GHOSTS (UBI_RECIPIENT)
            blocking_agents = [a for a in cell_contents if a.state != UBI_RECIPIENT]
            
            if not blocking_agents:
                valid_steps.append(pos)

        if valid_steps:
            new_position = self.random.choice(valid_steps)
            self.model.grid.move_agent(self, new_position)

    def step(self):
        if self.pos is None:
            return

        # --- ECONOMICS ---
        if self.state != AUTOMATED:
            self.wealth += self.model.ubi_payment

        if self.state != AUTOMATED:
            self.wealth -= self.model.cost_of_living
        else:
            gross_income = self.revenue
            tax_bill = gross_income * self.model.robot_tax_rate
            net_income = gross_income - tax_bill
            self.model.government_pot += tax_bill
            self.wealth += net_income

        # --- BEHAVIOR ---
        if self.state == UBI_RECIPIENT:
            if self.wealth <= 0:
                self.model.total_removed += 1  
                self.model.removed_this_step += 1       
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
            return

        elif self.state == DISPLACED:
            cellmates = self.model.grid.get_cell_list_contents(self.pos)
            active_squatters = [a for a in cellmates if a.state != DISPLACED and a.state != UBI_RECIPIENT and a != self]
            if not active_squatters and self.random.random() < self.model.hiring_chance:
                if self.random.random() < self.model.upskill_chance:
                    self.state = AUGMENTED
                else:
                    self.state = HUMAN
                self.displaced_by = None
                self.model.total_retrained += 1      
                self.model.retrained_this_step += 1 
                return 
            
        elif self.state == AUTOMATED:
            self.move()
            neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
            auto_neighbors = [n for n in neighbors if n.state == AUTOMATED]
            if len(auto_neighbors) >= self.model.combination_threshold:
                target = self.random.choice(auto_neighbors)
                self.revenue += target.revenue 
                self.wealth += target.wealth
                self.model.total_merged += 1  
                self.model.grid.remove_agent(target)
                self.model.schedule.remove(target)
                return 
            
        else:
            self.move()
            current_wage = 0
            if self.state == HUMAN: 
                current_wage = self.model.wage_human
                self.wealth += current_wage
            elif self.state == AUGMENTED: 
                current_wage = self.model.wage_augmented
                self.wealth += current_wage
            
            if self.wealth <= 0:
                self.model.total_removed += 1  
                self.model.removed_this_step += 1       
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
                return 

            neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
            n_augmented = len([n for n in neighbors if n.state == AUGMENTED])
            n_automated = len([n for n in neighbors if n.state == AUTOMATED])
            robot_neighbors = [n for n in neighbors if n.state == AUTOMATED]

            if self.state == HUMAN and n_augmented >= self.model.adopt_human_augmented_thresh:
                if self.random.random() < self.model.adopt_human_augmented_prob:
                    self.state = AUGMENTED
                    return

            if self.state == AUGMENTED and n_augmented >= self.model.automation_threshold:
                if self.random.random() < self.model.automation_chance:
                    self.state = AUTOMATED
                    self.revenue = self.model.wage_augmented 
                    return

            if n_automated >= self.model.displacement_threshold:
                self.state = DISPLACED
                self.displaced_by = AUTOMATED
                self.model.displaced_this_step += 1
                if robot_neighbors:
                    loot_share = current_wage / len(robot_neighbors)
                    for robot in robot_neighbors:
                        robot.revenue += loot_share
                return

# ==========================================
# 4. MODEL CLASS (UPDATED REVENUE INIT)
# ==========================================

class EvolutionaryModel(mesa.Model):
    def __init__(self, N=350, width=20, height=20, 
                 starting_wealth=50, cost_of_living=1.0,
                 wage_human=1.0, wage_augmented=2.5, 
                 seeds_human=300, seeds_augmented=20, seeds_automated=20, 
                 initial_ubi_fraction=0.0, 
                 adopt_human_augmented_thresh=3, adopt_human_augmented_prob=0.3,
                 automation_threshold=4, automation_chance=0.1,
                 displacement_threshold=2, combination_threshold=2,  
                 hiring_chance=0.30, upskill_chance=0.3,
                 robot_tax_rate=0.0,
                 enable_logging=False, seed=None): 
                 
        super().__init__(seed=seed)
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        
        self.initial_N = N 
        self.starting_wealth = starting_wealth
        self.cost_of_living = cost_of_living
        self.wage_human = wage_human
        self.wage_augmented = wage_augmented
        
        self.seeds_human = seeds_human 
        self.seeds_augmented = seeds_augmented
        self.seeds_automated = seeds_automated
        self.initial_ubi_fraction = initial_ubi_fraction

        self.adopt_human_augmented_thresh = adopt_human_augmented_thresh
        self.adopt_human_augmented_prob = adopt_human_augmented_prob
        self.automation_threshold = automation_threshold
        self.automation_chance = automation_chance
        self.displacement_threshold = displacement_threshold
        self.combination_threshold = combination_threshold
        self.hiring_chance = hiring_chance
        self.upskill_chance = upskill_chance
        
        self.robot_tax_rate = robot_tax_rate
        self.government_pot = 0
        self.ubi_payment = 0

        self.total_retrained = 0
        self.total_removed = 0
        self.total_merged = 0     
        self.removed_this_step = 0 
        self.retrained_this_step = 0 
        self.displaced_this_step = 0 

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Human": lambda m: self.count_state(m, HUMAN),
                "Augmented": lambda m: self.count_state(m, AUGMENTED),
                "Automated": lambda m: self.count_state(m, AUTOMATED),
                "Displaced": lambda m: self.count_state(m, DISPLACED),
                "UBI Recipients": lambda m: self.count_state(m, UBI_RECIPIENT),
                
                "Fired (Step)": lambda m: m.displaced_this_step,
                "Hired (Step)": lambda m: m.retrained_this_step,
                "Removed (Step)": lambda m: m.removed_this_step,
                
                "TotalWealth_Human": lambda m: self.sum_wealth(m, HUMAN),
                "TotalWealth_Augmented": lambda m: self.sum_wealth(m, AUGMENTED),
                "TotalWealth_Automated": lambda m: self.sum_wealth(m, AUTOMATED), 
                "TotalWealth_UBI": lambda m: self.sum_wealth(m, UBI_RECIPIENT),
                "Total Wealth": lambda m: sum([a.wealth for a in m.schedule.agents]),
                
                "Wealth_Labor": lambda m: self.sum_wealth(m, HUMAN) + self.sum_wealth(m, AUGMENTED),
                "Wealth_Capital": lambda m: self.sum_wealth(m, AUTOMATED),
                "Wealth_State": lambda m: self.sum_wealth(m, UBI_RECIPIENT),

                "Alive": lambda m: m.schedule.get_agent_count(),
                "Total Removed": lambda m: m.total_removed,
                "Merged (Singularity)": lambda m: m.total_merged,
                
                "UBI (Per Person)": lambda m: m.ubi_payment,
                "Cost of Living": lambda m: m.cost_of_living 
            }
        )

        all_coords = [(x, y) for x in range(self.grid.width) for y in range(self.grid.height)]
        self.random.shuffle(all_coords) 

        current_agent_count = 0
        
        def place_chunk(state_type, count):
            nonlocal current_agent_count
            for _ in range(int(count)):
                if current_agent_count >= N: return
                if not all_coords: return
                a = WorkerAgent(current_agent_count, self)
                a.state = state_type
                
                # --- LOGIC UPDATE: ROBOT INITIALIZATION ---
                if state_type == AUTOMATED:
                    # 1. REVENUE: Starts high (Legacy Capital) to fund UBI
                    a.revenue = self.wage_augmented
                    # 2. WEALTH: Starts at 0 (Machines have no savings)
                    a.wealth = 0 
                # ------------------------------------------

                x, y = all_coords.pop()
                self.schedule.add(a)
                self.grid.place_agent(a, (x, y))
                current_agent_count += 1            

        place_chunk(AUTOMATED, self.seeds_automated)
        place_chunk(AUGMENTED, self.seeds_augmented)
        total_ubi_count = int(self.initial_N * self.initial_ubi_fraction)
        place_chunk(UBI_RECIPIENT, total_ubi_count)
        remaining_slots = N - current_agent_count
        if remaining_slots > 0:
            place_chunk(HUMAN, remaining_slots)

    @staticmethod
    def count_state(model, state):
        return len([a for a in model.schedule.agents if a.state == state])

    @staticmethod
    def sum_wealth(model, state):
        agents = [a for a in model.schedule.agents if a.state == state]
        return sum([a.wealth for a in agents])

    def step(self):
        self.removed_this_step = 0 
        self.retrained_this_step = 0 
        self.displaced_this_step = 0 
        self.government_pot = 0
        self.schedule.step()
        
        biological_agents = [a for a in self.schedule.agents if a.state != AUTOMATED]
        count = len(biological_agents)
        if count > 0:
            self.ubi_payment = self.government_pot / count
        else:
            self.ubi_payment = 0
            
        self.datacollector.collect(self)

# ==========================================
# 5. VISUALIZATION
# ==========================================

def agent_portrayal(agent):
    p = STATE_MAP[agent.state].copy()
    portrayal = {
        "Shape": "circle", "Filled": "true",
        "w": p["scale"], "h": p["scale"],
        "Layer": 1, "Color": p["color"]
    }
    
    # --- UBI (LAYER 0 - BACKGROUND) ---
    if agent.state == UBI_RECIPIENT:
        portrayal["Shape"] = "rect"
        portrayal["Layer"] = 0        
        portrayal["w"] = 1.0          
        portrayal["h"] = 1.0
        portrayal["stroke_color"] = "#228B22" 
    
    # --- AUTOMATED (LAYER 2 - TOP) ---
    elif agent.state == AUTOMATED:
        portrayal["Layer"] = 2
        portrayal["r"] = 0.5
        portrayal["Color"] = "#ff0000"
        
    # --- DISPLACED (LAYER 1 - MIDDLE) ---
    elif agent.state == DISPLACED:
        portrayal["Shape"] = "rect"
        portrayal["Layer"] = 1
        portrayal["w"] = 0.75
        portrayal["h"] = 0.75
        
    # --- WORKERS (LAYER 1 - MIDDLE) ---
    else:
        portrayal["Layer"] = 1
        if p["shape"] == "rect": 
             portrayal["Shape"] = "rect"
             portrayal["w"] = p["scale"]
             portrayal["h"] = p["scale"]
        else:
            portrayal["r"] = 0.5
            
    return portrayal

model_params = {
    "N": mesa.visualization.Slider("[Global] Total Agents", 350, 100, 400, 10),
    "starting_wealth": mesa.visualization.Slider("[Global] Starting Wealth", 50, 10, 200, 10),
    "cost_of_living": mesa.visualization.Slider("[Global] Cost of Living", 1.0, 0.0, 5.0, 0.1),

    "initial_ubi_fraction": mesa.visualization.Slider("[Policy] % of Total Pop on UBI", 0.0, 0.0, 1.0, 0.05),

    "seeds_human": mesa.visualization.Slider("[Seeds] Human (Remainder)", 300, 0, 400, 10),
    "seeds_augmented": mesa.visualization.Slider("[Seeds] Augmented", 20, 0, 100, 1),
    "seeds_automated": mesa.visualization.Slider("[Seeds] Automated", 20, 0, 50, 1),

    "robot_tax_rate": mesa.visualization.Slider("[Policy] Robot Tax Rate", 0.0, 0.0, 1.0, 0.05),

    "wage_human": mesa.visualization.Slider("[Econ] Wage: Human", 1.0, 0.0, 10.0, 0.1),
    "wage_augmented": mesa.visualization.Slider("[Econ] Wage: Augmented", 2.5, 0.0, 10.0, 0.1),

    "adopt_human_augmented_thresh": mesa.visualization.Slider("[Trans] Human->Aug Neighbors", 3, 1, 8, 1),
    "adopt_human_augmented_prob": mesa.visualization.Slider("[Trans] Human->Aug Chance", 0.3, 0.0, 1.0, 0.05),
    "automation_threshold": mesa.visualization.Slider("[Trans] Aug->Auto Density", 4, 1, 8, 1),
    "automation_chance": mesa.visualization.Slider("[Trans] Aug->Auto Chance", 0.1, 0.0, 1.0, 0.05),
    "displacement_threshold": mesa.visualization.Slider("[Trans] Displacement Pressure", 2, 1, 8, 1),
    "combination_threshold": mesa.visualization.Slider("[Trans] Auto Combine Density", 2, 1, 8, 1),

    "hiring_chance": mesa.visualization.Slider("[System] Hiring Chance", 0.30, 0.0, 1.0, 0.05),
    "upskill_chance": mesa.visualization.Slider("[System] Upskill Chance", 0.3, 0.0, 1.0, 0.05),
    "seed": mesa.visualization.NumberInput("Random Seed (Optional)", value=123), 
}

grid = mesa.visualization.CanvasGrid(agent_portrayal, 20, 20, 500, 500)
leaderboard = LeaderboardElement()

chart_pop = mesa.visualization.ChartModule([
    {"Label": "Human", "Color": "#808080"},
    {"Label": "Augmented", "Color": "#4285f4"},
    {"Label": "Automated", "Color": "#ff0000"},
    {"Label": "Displaced", "Color": "#ffd700"},
    {"Label": "UBI Recipients", "Color": "#32CD32"} 
], canvas_height=150, canvas_width=500)

chart_employment = mesa.visualization.ChartModule([
    {"Label": "Displaced", "Color": "#ffd700"},      
    {"Label": "Fired (Step)", "Color": "#ff9900"},   
    {"Label": "Hired (Step)", "Color": "#00ff00"},   
    {"Label": "Removed (Step)", "Color": "#800080"}  
], canvas_height=150, canvas_width=500)

chart_capital_bar = mesa.visualization.BarChartModule([
    {"Label": "Wealth_Labor", "Color": "#4285f4"},
    {"Label": "Wealth_Capital", "Color": "#ff0000"},
    {"Label": "Wealth_State", "Color": "#32CD32"}
], canvas_height=150, canvas_width=500)

chart_wealth = mesa.visualization.ChartModule([
    {"Label": "TotalWealth_Human", "Color": "#808080"},
    {"Label": "TotalWealth_Augmented", "Color": "#4285f4"},
    {"Label": "TotalWealth_Automated", "Color": "#ff0000"},
    {"Label": "TotalWealth_UBI", "Color": "#32CD32"},
    {"Label": "Total Wealth", "Color": "Black"}
], canvas_height=150, canvas_width=500)

chart_fiscal = mesa.visualization.ChartModule([
    {"Label": "UBI (Per Person)", "Color": "#00ff00"},
    {"Label": "Cost of Living", "Color": "#ff0000"} 
], canvas_height=150, canvas_width=500)

chart_integrity = mesa.visualization.ChartModule([
    {"Label": "Alive", "Color": "Black"},
    {"Label": "Total Removed", "Color": "#800080"},       
    {"Label": "Merged (Singularity)", "Color": "#00ced1"} 
], canvas_height=150, canvas_width=500)

server = mesa.visualization.ModularServer(
    EvolutionaryModel, 
    [
        grid, 
        SectionHeader("Wealth Leaderboard (Top 10 by Class)"),
        leaderboard, 
        SectionHeader("Population Dynamics"),
        chart_pop,
        SectionHeader("Employment Dynamics (Flows)"),
        chart_employment, 
        SectionHeader("Economic Health (Capital vs Labor vs State)"),
        chart_capital_bar, 
        chart_wealth,
        SectionHeader("Fiscal Policy Monitor (UBI vs Cost of Living)"), 
        chart_fiscal,
        SectionHeader("Simulation Integrity (Agent Conservation)"),
        chart_integrity
    ], 
    "Evolutionary Automata Simulation", 
    model_params
)
server.launch()