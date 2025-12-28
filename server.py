import mesa
from model import EvolutionaryModel
from constants import HUMAN, AUGMENTED, AUTOMATED, DISPLACED, UBI_RECIPIENT, STATE_MAP

# ==========================================
# HELPER CLASSES
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
# VISUALIZATION FUNCTIONS
# ==========================================

def agent_portrayal(agent):
    p = STATE_MAP[agent.state].copy()
    portrayal = {
        "Shape": "circle", "Filled": "true",
        "w": p["scale"], "h": p["scale"],
        "Layer": 1, "Color": p["color"]
    }
    
    if agent.state == UBI_RECIPIENT:
        portrayal["Shape"] = "rect"
        portrayal["Layer"] = 0        
        portrayal["w"] = 1.0          
        portrayal["h"] = 1.0
        portrayal["stroke_color"] = "#228B22" 
    
    elif agent.state == AUTOMATED:
        portrayal["Layer"] = 2
        portrayal["r"] = 0.5
        portrayal["Color"] = "#ff0000"
        
    elif agent.state == DISPLACED:
        portrayal["Shape"] = "rect"
        portrayal["Layer"] = 1
        portrayal["w"] = 0.75
        portrayal["h"] = 0.75
        
    else:
        portrayal["Layer"] = 1
        if p["shape"] == "rect": 
             portrayal["Shape"] = "rect"
             portrayal["w"] = p["scale"]
             portrayal["h"] = p["scale"]
        else:
            portrayal["r"] = 0.5
            
    return portrayal

# ==========================================
# MODEL PARAMETERS
# ==========================================

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
    "human_displacement_chance": mesa.visualization.Slider("[Trans] Efficiency Disp. Chance", 0.1, 0.0, 1.0, 0.05),

    "automation_threshold": mesa.visualization.Slider("[Trans] Aug->Auto Density", 4, 1, 8, 1),
    "automation_chance": mesa.visualization.Slider("[Trans] Aug->Auto Chance", 0.1, 0.0, 1.0, 0.05),
    "displacement_threshold": mesa.visualization.Slider("[Trans] Displacement Pressure", 2, 1, 8, 1),
    "combination_threshold": mesa.visualization.Slider("[Trans] Auto Combine Density", 2, 1, 8, 1),

    "hiring_chance": mesa.visualization.Slider("[System] Hiring Chance", 0.30, 0.0, 1.0, 0.05),
    "upskill_chance": mesa.visualization.Slider("[System] Upskill Chance", 0.3, 0.0, 1.0, 0.05),
    "seed": mesa.visualization.NumberInput("Random Seed (Optional)", value=123), 
}

# ==========================================
# VISUALIZATION ELEMENTS
# ==========================================

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

# ==========================================
# SERVER
# ==========================================

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

if __name__ == "__main__":
    server.launch()