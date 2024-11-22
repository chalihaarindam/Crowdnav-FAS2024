import GPy
import numpy as np
from scipy.stats import norm
import requests
import json

class BayesianOptimization:
    def __init__(self, parameter_bounds, surrogate_model=None, xi=0.01):
        self.parameter_bounds = parameter_bounds
        self.surrogate_model = surrogate_model or GPy.models.GPRegression(np.zeros((1, len(parameter_bounds))), np.zeros((1, 1)))
        self.best_params = None
        self.best_value = float('-inf')
        self.xi = xi  # Add this line

    def fit(self, X, y):
        self.surrogate_model.set_XY(X, y.reshape(-1, 1))
        self.surrogate_model.optimize()

    def predict(self, X):
        mean, var = self.surrogate_model.predict(X)
        return mean.flatten(), var.flatten()

    def expected_improvement(self, X, xi=0.01):
        mu, sigma = self.predict(X)
        mu_sample = self.surrogate_model.predict(self.surrogate_model.X)[0].flatten()
        mu_sample_opt = np.max(mu_sample)
        imp = mu - mu_sample_opt - xi
        Z = imp / sigma
        ei = imp * norm.cdf(Z) + sigma * norm.pdf(Z)
        return ei

    def optimize(self, num_iterations=10):
        X = np.zeros((1, len(self.parameter_bounds)))
        y = np.array([0])

        for _ in range(num_iterations):
            if X.size == 0:
                x_next = np.random.uniform(self.parameter_bounds[:, 0], self.parameter_bounds[:, 1])
            else:
                x_next = self.suggest_next_point(X, y)

            y_next = self.objective_function(x_next)
            X = np.vstack((X, x_next))
            y = np.hstack((y, y_next))

            if y_next > self.best_value:
                self.best_value = y_next
                self.best_params = x_next

        return self.best_params, self.best_value

    def objective_function(self, params):
        # Convert params to a dictionary for API interaction
        config = {
            "route_randomization": params[0],
            "exploration_percentage": params[1],
            "static_info_weight": params[2],
            "dynamic_info_weight": params[3],
            "exploration_weight": params[4],
            "data_freshness_threshold": params[5],
            "re-routing_frequency": params[6]
        }

        # Configure the router with the provided parameters
        response = requests.put('http://localhost:8080/execute', json=config)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to configure router: {response.text}")

        # Retrieve performance metrics
        response = requests.get('http://localhost:8080/monitor')
        if response.status_code != 200:
            raise RuntimeError(f"Failed to retrieve statistics: {response.text}")

        stats = response.json()
        trip_overhead = stats.get('trip_overhead', 0)  # Default to 0 if key is missing
        routing_cost = stats.get('routing_cost', 0)  # Default to 0 if key is missing

        # Objective function: Minimize trip overhead and routing cost
        return -trip_overhead - routing_cost  # Assuming you want to maximize performance

    def suggest_next_point(self, X, y):
        # Update the surrogate model with the current data
        self.fit(X, y)

        # Define the bounds for the parameters
        bounds = self.parameter_bounds

        # Generate a random grid of points within the parameter bounds
        num_samples = 1000  # Adjust as needed
        x_samples = np.random.uniform(bounds[:, 0], bounds[:, 1], (num_samples, len(bounds)))

        # Predict mean and variance at the sampled points
        mu_samples, sigma_samples = self.predict(x_samples)
        mu_sample_opt = np.max(y)

        # Expected Improvement acquisition function
        with np.errstate(divide='warn'):
            imp = mu_samples - mu_sample_opt - self.xi
            Z = imp / sigma_samples
            ei = imp * norm.cdf(Z) + sigma_samples * norm.pdf(Z)

        # Find the index of the maximum expected improvement
        next_point_index = np.argmax(ei)
        return x_samples[next_point_index]
