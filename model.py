import mesa
from agent import WorkerAgent
from constants import HUMAN, AUGMENTED, AUTOMATED, DISPLACED, UBI_RECIPIENT

class EvolutionaryModel(mesa.Model):
    def __init__(self, N=350, width=30, height=30, 
                 starting_wealth=50, cost_of_living=1.0,
                 wage_human=1.0, wage_augmented=2.5, 
                 seeds_human=300, seeds_augmented=20, seeds_automated=20, 
                 initial_ubi_fraction=0.0, 
                 
                 # --- NEW PARAMETER ---
                 ubi_class_tax_share=0.5, # Default 50/50 split
                 
                 adopt_human_augmented_thresh=3, adopt_human_augmented_prob=0.3,
                 human_displacement_chance=0.1,
                 automation_threshold=4, automation_chance=0.1,
                 displacement_threshold=2, combination_threshold=2,  
                 hiring_chance=0.30, upskill_chance=0.3,
                 robot_tax_rate=0.0,
                 enable_logging=False, seed=None): 
                 
        super().__init__(seed=seed)
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        
        # --- ID MANAGEMENT (NEW) ---
        # Initialize counter at N so new agents get unique IDs starting from N
        self.current_id_counter = N 

        self.initial_N = N 
        self.starting_wealth = starting_wealth
        self.cost_of_living = cost_of_living
        self.wage_human = wage_human
        self.wage_augmented = wage_augmented
        
        self.seeds_human = seeds_human 
        self.seeds_augmented = seeds_augmented
        self.seeds_automated = seeds_automated
        self.initial_ubi_fraction = initial_ubi_fraction
        
        # Store the new split parameter
        self.ubi_class_tax_share = ubi_class_tax_share

        self.adopt_human_augmented_thresh = adopt_human_augmented_thresh
        self.adopt_human_augmented_prob = adopt_human_augmented_prob
        self.human_displacement_chance = human_displacement_chance
        
        self.automation_threshold = automation_threshold
        self.automation_chance = automation_chance
        self.displacement_threshold = displacement_threshold
        self.combination_threshold = combination_threshold
        self.hiring_chance = hiring_chance
        self.upskill_chance = upskill_chance
        
        self.robot_tax_rate = robot_tax_rate
        self.government_pot = 0
        
        # Two separate payout rates
        self.ubi_payout_opt_out = 0
        self.ubi_payout_worker = 0

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
                
                # UPDATED METRICS
                "UBI (Opt-Out)": lambda m: m.ubi_payout_opt_out,
                "UBI (Worker Div)": lambda m: m.ubi_payout_worker,
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
                
                if state_type == AUTOMATED:
                    a.revenue = self.wage_augmented
                    a.wealth = 0 

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

    # --- NEW HELPER METHOD ---
    def get_next_id(self):
        """Generates a unique ID for new agents (Robots)"""
        _id = self.current_id_counter
        self.current_id_counter += 1
        return _id

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
        
        # --- UPDATED PAYMENT CALCULATOR ---
        ubi_agents = [a for a in self.schedule.agents if a.state == UBI_RECIPIENT]
        worker_agents = [a for a in self.schedule.agents if a.state in [HUMAN, AUGMENTED, DISPLACED]]
        
        count_ubi = len(ubi_agents)
        count_workers = len(worker_agents)
        
        # Split the pot based on the slider
        pot_ubi = self.government_pot * self.ubi_class_tax_share
        pot_workers = self.government_pot * (1 - self.ubi_class_tax_share)
        
        if count_ubi > 0:
            self.ubi_payout_opt_out = pot_ubi / count_ubi
        else:
            self.ubi_payout_opt_out = 0
            
        if count_workers > 0:
            self.ubi_payout_worker = pot_workers / count_workers
        else:
            self.ubi_payout_worker = 0
            
        self.datacollector.collect(self)