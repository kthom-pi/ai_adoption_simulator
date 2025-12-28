"""
Batch runner for AI Adoption Simulator
Run experiments and export results to CSV
"""

from model import EvolutionaryModel
import pandas as pd
from datetime import datetime
import os

def run_single_experiment(params, steps=500, output_dir="results"):
    """
    Run a single experiment with given parameters
    
    Args:
        params: Dictionary of model parameters
        steps: Number of simulation steps to run
        output_dir: Directory to save results
    
    Returns:
        Tuple of (model_data, agent_data) DataFrames
    """
    print(f"Running experiment with params: {params}")
    
    # Create model
    model = EvolutionaryModel(**params)
    
    # Run simulation
    for i in range(steps):
        model.step()
        if i % 100 == 0:
            print(f"  Step {i}/{steps}")
    
    # Get data
    model_data = model.datacollector.get_model_vars_dataframe()
    agent_data = model.datacollector.get_agent_vars_dataframe()
    
    # Add experiment metadata to model data
    for key, value in params.items():
        model_data[f'param_{key}'] = value
    
    return model_data, agent_data

def save_results(model_data, agent_data, experiment_name, output_dir="results"):
    """
    Save experiment results to CSV files
    
    Args:
        model_data: DataFrame with model-level data
        agent_data: DataFrame with agent-level data
        experiment_name: Name for the output files
        output_dir: Directory to save files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create timestamped filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_file = os.path.join(output_dir, f"{experiment_name}_model_{timestamp}.csv")
    agent_file = os.path.join(output_dir, f"{experiment_name}_agents_{timestamp}.csv")
    
    # Save to CSV
    model_data.to_csv(model_file)
    agent_data.to_csv(agent_file)
    
    print(f"\nResults saved:")
    print(f"  Model data: {model_file}")
    print(f"  Agent data: {agent_file}")
    
    return model_file, agent_file

def run_batch_experiments(param_variations, steps=500, output_dir="results"):
    """
    Run multiple experiments with different parameter combinations
    
    Args:
        param_variations: List of parameter dictionaries
        steps: Number of steps per experiment
        output_dir: Directory to save results
    
    Returns:
        Combined DataFrames for all experiments
    """
    all_model_data = []
    all_agent_data = []
    
    for i, params in enumerate(param_variations):
        print(f"\n=== Experiment {i+1}/{len(param_variations)} ===")
        model_data, agent_data = run_single_experiment(params, steps, output_dir)
        
        # Add experiment ID
        model_data['experiment_id'] = i
        agent_data['experiment_id'] = i
        
        all_model_data.append(model_data)
        all_agent_data.append(agent_data)
    
    # Combine all experiments
    combined_model = pd.concat(all_model_data, ignore_index=True)
    combined_agent = pd.concat(all_agent_data, ignore_index=True)
    
    return combined_model, combined_agent

# ==========================================
# EXAMPLE EXPERIMENTS
# ==========================================

def experiment_ubi_viability():
    """Experiment 1: Test UBI viability with different tax rates"""
    param_variations = [
        {"robot_tax_rate": 0.0, "initial_ubi_fraction": 0.2, "seeds_automated": 50},
        {"robot_tax_rate": 0.25, "initial_ubi_fraction": 0.2, "seeds_automated": 50},
        {"robot_tax_rate": 0.5, "initial_ubi_fraction": 0.2, "seeds_automated": 50},
        {"robot_tax_rate": 0.75, "initial_ubi_fraction": 0.2, "seeds_automated": 50},
    ]
    
    model_data, agent_data = run_batch_experiments(param_variations, steps=500)
    save_results(model_data, agent_data, "ubi_viability")

def experiment_adoption_cascades():
    """Experiment 2: AI adoption spread dynamics"""
    param_variations = [
        {"seeds_augmented": 5, "adopt_human_augmented_thresh": 2, "adopt_human_augmented_prob": 0.2},
        {"seeds_augmented": 5, "adopt_human_augmented_thresh": 2, "adopt_human_augmented_prob": 0.5},
        {"seeds_augmented": 5, "adopt_human_augmented_thresh": 2, "adopt_human_augmented_prob": 0.8},
    ]
    
    model_data, agent_data = run_batch_experiments(param_variations, steps=300)
    save_results(model_data, agent_data, "adoption_cascades")

def experiment_displacement_threshold():
    """Experiment 3: Test different displacement thresholds"""
    param_variations = [
        {"displacement_threshold": 1, "seeds_automated": 30},
        {"displacement_threshold": 2, "seeds_automated": 30},
        {"displacement_threshold": 3, "seeds_automated": 30},
        {"displacement_threshold": 4, "seeds_automated": 30},
    ]
    
    model_data, agent_data = run_batch_experiments(param_variations, steps=500)
    save_results(model_data, agent_data, "displacement_threshold")

def experiment_wealth_inequality():
    """Experiment 4: Wealth concentration dynamics"""
    param_variations = [
        {"combination_threshold": 2, "robot_tax_rate": 0.0, "seeds_automated": 50},
        {"combination_threshold": 2, "robot_tax_rate": 0.5, "seeds_automated": 50},
    ]
    
    model_data, agent_data = run_batch_experiments(param_variations, steps=500)
    save_results(model_data, agent_data, "wealth_inequality")

def experiment_custom(params, steps=500, name="custom_experiment"):
    """
    Run a custom experiment with your own parameters
    
    Example:
        experiment_custom({
            "robot_tax_rate": 0.3,
            "initial_ubi_fraction": 0.1,
            "wage_augmented": 3.0
        }, steps=1000, name="my_experiment")
    """
    model_data, agent_data = run_single_experiment(params, steps)
    save_results(model_data, agent_data, name)

# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    print("AI Adoption Simulator - Batch Runner")
    print("=" * 50)
    
    # Example: Run UBI viability experiment
    experiment_ubi_viability()
    
    # Example: Run custom experiment
    # experiment_custom({
    #     "robot_tax_rate": 0.4,
    #     "seeds_automated": 60,
    #     "displacement_threshold": 2
    # }, steps=1000, name="test_run")