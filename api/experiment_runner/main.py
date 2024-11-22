from bayesian_optimization import BayesianOptimization
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Configuration of router parameters
parameter_bounds = np.array([
    [0, 1],  # route_randomization
    [0, 1],  # exploration_percentage
    [0, 1],  # static_info_weight
    [0, 1],  # dynamic_info_weight
    [0, 1],  # exploration_weight
    [0, 10000],  # data_freshness_threshold
    [0, 60]  # re-routing_frequency
])

# Initialize Bayesian Optimization
bo = BayesianOptimization(parameter_bounds)

# Run optimization
best_params, best_value = bo.optimize(num_iterations=50)  # Adjust number of iterations

# Record results
results = {'best_params': best_params, 'best_value': best_value}

# Save results
results_df = pd.DataFrame([results])
results_df.to_csv('/code/results/data/baseline_results.csv', index=False)

# Visualize results
plt.plot(results_df['best_value'])
plt.title('Best Value Over Iterations')
plt.xlabel('Iteration')
plt.ylabel('Performance Metric')
plt.savefig('results/visualizations/best_value_plot.png')
