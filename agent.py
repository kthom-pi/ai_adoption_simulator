import mesa
from constants import HUMAN, AUGMENTED, AUTOMATED, DISPLACED, UBI_RECIPIENT

class WorkerAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = HUMAN
        self.wealth = model.starting_wealth 
        self.displaced_by = None 
        self.revenue = 0 

    def move(self):
        if self.pos is None or self.state == DISPLACED or self.state == UBI_RECIPIENT:
            return

        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        
        valid_steps = []
        for pos in possible_steps:
            cell_contents = self.model.grid.get_cell_list_contents(pos)
            # Ghost Logic: Blocked only if not UBI
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
        
        # CASE 0: UBI RECIPIENT
        if self.state == UBI_RECIPIENT:
            if self.wealth <= 0:
                self.model.total_removed += 1  
                self.model.removed_this_step += 1       
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
            return

        # CASE 1: DISPLACED
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
            
        # CASE 2: AUTOMATED
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
            
        # CASE 3: WORKERS
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

            # --- EFFICIENCY SQUEEZE LOGIC ---
            if self.state == HUMAN and n_augmented >= self.model.adopt_human_augmented_thresh:
                # 1. Check for Forced Displacement (The Slider)
                if self.random.random() < self.model.human_displacement_chance:
                    self.state = DISPLACED
                    self.displaced_by = AUGMENTED
                    self.model.displaced_this_step += 1
                    return
                # 2. Check for Adoption
                elif self.random.random() < self.model.adopt_human_augmented_prob:
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