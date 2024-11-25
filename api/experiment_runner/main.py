# main.py
from bayesian_optimization import BayesianOptimization
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Configuration of router parameters
parameter_bounds = np.array([
    [0, 1],      # route_randomization
    [0, 1],      # exploration_percentage
    [0, 1],      # static_info_weight
    [0, 1],      # dynamic_info_weight
    [0, 1],      # exploration_weight
    [0, 10000],  # data_freshness_threshold
    [0, 60]      # re-routing_frequency
])

def wait_for_crowdnav():
    """Wait for crowdnav to be ready"""
    import requests
    max_attempts = 30
    for _ in range(max_attempts):
        try:
            response = requests.get('http://localhost:8080/monitor')
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def main():
    # Wait for crowdnav to be ready
    if not wait_for_crowdnav():
        print("Crowdnav not responding")
        return

# Initialize and run optimization
bo = BayesianOptimization(parameter_bounds)
best_params, best_value, history = bo.optimize(num_iterations=50)

# Save detailed results including all iterations and their corresponding values and parameters.
results_df = pd.DataFrame({
    'iteration': history['iterations'],
    'value': history['values'],
    'best_value': history['best_values'],
    'parameters': history['params']
})

results_df.to_csv('/code/results/data/baseline_results.csv', index=False)

# Create and save the plot from iteration data.
plt.figure(figsize=(10, 6))
plt.plot(results_df['iteration'], results_df['value'], 'b-', label='Current Value', alpha=0.5)
plt.plot(results_df['iteration'], results_df['best_value'], 'r-', label='Best Value')
plt.title('Best Value Over Iterations')
plt.xlabel('Iteration')
plt.ylabel('Performance Metric')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('/code/results/visualizations/best_value_plot.png', dpi=300)
plt.close()
