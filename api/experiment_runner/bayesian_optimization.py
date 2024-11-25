# bayesian_optimization.py
import GPy
import numpy as np
from scipy.stats import norm
import requests
import time 

class BayesianOptimization:
    def __init__(self, parameter_bounds, surrogate_model=None, xi=0.01):
        self.parameter_bounds = parameter_bounds
        # Initialize GPy with proper bounds
        if surrogate_model is None:
            X = np.zeros((1, len(parameter_bounds)))
            Y = np.zeros((1, 1))
            kernel = GPy.kern.RBF(input_dim=len(parameter_bounds), variance=1.0, lengthscale=1.0)
            self.surrogate_model = GPy.models.GPRegression(X, Y, kernel)
        else:
            self.surrogate_model = surrogate_model
        
        self.best_params = None
        self.best_value = float('-inf')
        self.xi = xi
        self.history = {'iterations': [], 'values': [],'best_values' : [] ,'params': []}

    def fit(self, X, y):
        self.surrogate_model.set_XY(X, y.reshape(-1, 1))
        self.surrogate_model.optimize()

    def predict(self, X):
        mean, var = self.surrogate_model.predict(X)
        return mean.flatten(), var.flatten()

    def expected_improvement(self, X):
        mu, sigma = self.predict(X)
        mu_sample = self.surrogate_model.predict(self.surrogate_model.X)[0].flatten()
        mu_sample_opt = np.max(mu_sample)
        imp = mu - mu_sample_opt - self.xi
        Z = imp / sigma
        ei = imp * norm.cdf(Z) + sigma * norm.pdf(Z)
        return ei

    def optimize(self, num_iterations=10):
        X = np.zeros((1, len(self.parameter_bounds)))
        y = np.array([0])
        
        for i in range(num_iterations):
            if X.size == 0:
                x_next = np.random.uniform(self.parameter_bounds[:, 0], self.parameter_bounds[:, 1])
            else:
                x_next = self.suggest_next_point(X, y)
                print(f"Parameters: {x_next}")
            
            y_next = self.objective_function(x_next)
            print(f"Objective value: {y_next}")
            X = np.vstack((X, x_next))
            y = np.hstack((y, y_next))
            
            # Store iteration data
            self.history['iterations'].append(i)
            self.history['values'].append(y_next)
            self.history['params'].append(x_next.tolist())
            
            # Update best value if needed
            if y_next > self.best_value:
                self.best_value = y_next
                self.best_params = x_next
            
            # Store best value at each iteration
            self.history['best_values'].append(self.best_value)

        return self.best_params, self.best_value, self.history

    def objective_function(self, params):
        
        try:
            config = {
            "route_random_sigma": float(params[0]),
            "exploration_percentage": float(params[1]),
            "max_speed_and_length_factor": float(params[2]),
            "average_edge_duration_factor": float(params[3]),
            "freshness_update_factor": float(params[4]),
            "freshness_cut_off_value": float(params[5]),
            "re_route_every_ticks": int(params[6]),
            "total_car_counter": 750,
            "edge_average_influence": 140
            }


            # Execute new configuration
            response = requests.put('http://localhost:8080/execute', json=config)
            response.raise_for_status()
            time.sleep(10)
            
            # Get updated metrics
            response = requests.get('http://localhost:8080/monitor')
            response.raise_for_status()
            
            data = response.json()
            car_stats = data['car_stats']

            # Get the actual metrics from car_stats
            trip_overhead = float(car_stats['total_trip_overhead_average'])
            routing_duration = float(car_stats['routing_duration'])
            total_complaints = float(car_stats['total_complaints'])
        
            # Print raw response for debugging
            print(f"Raw response: {data}")

            # Calculate objective value (negative because we want to minimize)
            objective_value = (trip_overhead + routing_duration + total_complaints)

            print(f"Trip overhead: {trip_overhead}, Routing duration: {routing_duration}, Complaints: {total_complaints}")
            return objective_value
        
        except requests.exceptions.RequestException as e:
            print(f"Error in objective function: {e}")
            return float('-inf')

    def suggest_next_point(self, X, y):
        self.fit(X, y)
        bounds = self.parameter_bounds
        num_samples = 1000
        x_samples = np.random.uniform(bounds[:, 0], bounds[:, 1], (num_samples, len(bounds)))
        ei = self.expected_improvement(x_samples)
        return x_samples[np.argmax(ei)]
