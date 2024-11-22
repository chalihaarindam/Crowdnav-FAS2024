import requests
import random
import time

API_URL = "http://localhost:8080"

class NSGA2:
    def __init__(self, pop_size=5, generations=3):  # Reduced size for testing
        self.pop_size = pop_size
        self.generations = generations

    def create_individual(self):
        return {
            "route_random_sigma": random.uniform(0, 0.3),
            "exploration_percentage": 0,
            "max_speed_and_length_factor": 0,
            "average_edge_duration_factor": 0,
            "freshness_update_factor": 0,
            "freshness_cut_off_value": 0,
            "re_route_every_ticks": 0,
            "total_car_counter": 0,
            "edge_average_influence": 0
        }

    def fitness_function(self, individual):
        try:
            print(f"Testing configuration: {individual}")
            response = requests.put(f"{API_URL}/execute", json=individual)
            if response.status_code != 200:
                print(f"Execute error: {response.status_code}")
                return [float('inf'), float('inf')]
            
            time.sleep(2)  # Wait for system to stabilize
            
            response = requests.get(f"{API_URL}/monitor")
            if response.status_code != 200:
                print(f"Monitor error: {response.status_code}")
                return [float('inf'), float('inf')]
            
            state = response.json()
            print(f"Current state: {state}")
            
            # Extract metrics (adjust based on your monitor endpoint response)
            avg_travel_time = float(state.get('averageTravelTime', float('inf')))
            avg_waiting_time = float(state.get('averageWaitingTime', float('inf')))
            
            return [avg_travel_time, avg_waiting_time]
        except Exception as e:
            print(f"Error in fitness function: {e}")
            return [float('inf'), float('inf')]

    def dominates(self, ind1, ind2):
        return all(f1 <= f2 for f1, f2 in zip(ind1, ind2)) and any(f1 < f2 for f1, f2 in zip(ind1, ind2))

    def fast_non_dominated_sort(self, population, fitness):
        n = len(population)
        domination_counts = [0] * n
        dominated_solutions = [[] for _ in range(n)]
        fronts = [[]]
        
        # Calculate domination for each solution
        for i in range(n):
            for j in range(n):
                if i != j:
                    if self.dominates(fitness[i], fitness[j]):
                        dominated_solutions[i].append(j)
                    elif self.dominates(fitness[j], fitness[i]):
                        domination_counts[i] += 1
            
            if domination_counts[i] == 0:
                fronts[0].append(i)
        
        # Generate subsequent fronts
        current_front = 0
        while fronts[current_front]:
            next_front = []
            for i in fronts[current_front]:
                for j in dominated_solutions[i]:
                    domination_counts[j] -= 1
                    if domination_counts[j] == 0:
                        next_front.append(j)
            current_front += 1
            if next_front:
                fronts.append(next_front)
        
        return [f for f in fronts if f]  # Remove empty fronts

    def run(self):
        try:
            print("Starting NSGA-II optimization...")
            population = [self.create_individual() for _ in range(self.pop_size)]
            
            for generation in range(self.generations):
                print(f"\nGeneration {generation + 1}/{self.generations}")
                
                # Evaluate fitness
                fitness = []
                for ind in population:
                    fit = self.fitness_function(ind)
                    print(f"Fitness values: {fit}")
                    fitness.append(fit)
                
                # Sort population
                fronts = self.fast_non_dominated_sort(population, fitness)
                if not fronts:
                    print("No valid fronts found")
                    continue
                
                # Create new population
                new_population = []
                for front in fronts:
                    if len(new_population) + len(front) <= self.pop_size:
                        new_population.extend([population[i] for i in front])
                    else:
                        remaining = self.pop_size - len(new_population)
                        new_population.extend([population[i] for i in front[:remaining]])
                        break
                
                population = new_population

            # Get final Pareto front
            final_fitness = [self.fitness_function(ind) for ind in population]
            final_fronts = self.fast_non_dominated_sort(population, final_fitness)
            
            return [population[i] for i in final_fronts[0]] if final_fronts else []
            
        except Exception as e:
            print(f"Error in optimization: {e}")
            return []

def main():
    try:
        print("Starting baseline strategy test...")
        nsga2 = NSGA2(pop_size=5, generations=3)  # Small population and generations for testing
        pareto_front = nsga2.run()
        
        print("\nFinal Pareto Front:")
        for solution in pareto_front:
            print(f"Configuration: {solution}")
            fitness = nsga2.fitness_function(solution)
            print(f"Fitness: {fitness}")
            
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main()
