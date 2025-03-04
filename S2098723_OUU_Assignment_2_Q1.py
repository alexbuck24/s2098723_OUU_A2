#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 12:54:54 2025

@author: alexbuck
"""
import gurobipy as gp
from gurobipy import GRB

# Data taken straight from the figure
scenarios = [1,2,3,4]
probs = {1: 0.4, 2: 0.3, 3: 0.2, 4: 0.1}
D = {(1,"First_Class"): 25, (1,"Buisness_Class"): 60, (1,"Economy"):200 ,
     (2,"First_Class"): 20, (2,"Buisness_Class"): 40,(2,"Economy"): 180,
     (3,"First_Class"): 10, (3,"Buisness_Class"): 25,(3,"Economy"): 175,
     (4,"First_Class"): 5,  (4,"Buisness_Class"): 10,(4,"Economy"): 150}

model= gp.Model("ScotRail")
model.setParam("OutputFlag", 0) 


# First-stage decision variables
n = 3
c = {"First_Class": 2, "Buisness_Class": 1.5, "Economy": 1}
K = {"First_Class": 3,"Buisness_Class": 2,"Economy": 1}
seat_types = ["First_Class", "Buisness_Class", "Economy"]
x = {}
for i in seat_types:
    x[i] = model.addVar(lb=0, vtype= GRB.INTEGER, name=f"x_{i}") #Positive integer constraints
model.addConstr(gp.quicksum(c[i] * x[i] for i in seat_types) <= 200) # Space constraint
# Create second-stage variables and constraints for each scenario
y = {}
for i in scenarios:
    for j in seat_types:
        y[(i,j)] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"y_{i,j}") # we can only sell non negative integer number of tickets
        model.addConstr(y[(i,j)]<= x[j]) #We can't sell more seats than we have installed
        model.addConstr(y[(i,j)] <= D[(i,j)]) # We can't sell more seats than what the demand is

obj = gp.quicksum(probs[i]*gp.quicksum(y[(i,j)]* K[j] for j in seat_types) for i in scenarios)
model.setObjective(obj, GRB.MAXIMIZE)
model.optimize()
stochastic_obj = model.objVal
x_sol = {}
y_sol = {}
# Retrieve and print the solution
for j in seat_types:
    x_sol[j] = x[j].X
    for i in scenarios:
        y_sol[(i,j)] = y[(i,j)].X


print(f"Optimal objective value: {stochastic_obj}") 
print(f"Optimal first-stage decisions: {x_sol}")
print(f"Optimal second-stage solutions: {y_sol}")

    
'''Finding mean value solution'''

Mean_demand = {}
for j in seat_types:
    Mean_demand[j] = gp.quicksum(probs[i]* D[(i,j)] for i in scenarios)
    
model2 = gp.Model("Scot_rail_mean")
model2.setParam("OutputFlag", 0) 
x2 = {}
for j in seat_types:
    x2[j] = model2.addVar(lb=0, vtype= GRB.INTEGER, name=f"x2_{j}")

model2.addConstr(gp.quicksum(c[i] * x2[i] for i in seat_types) <= 200) # Space constraint
for j in seat_types:
    model2.addConstr(x2[j] <= Mean_demand[j])
obj2 = gp.quicksum(x2[i]*K[i] for i in seat_types)
model2.setObjective(obj2, GRB.MAXIMIZE)
model2.optimize()
x2_sol = {}
for j in seat_types:
    x2_sol[j] = x2[j].X     
model3 = gp.Model("Scot_rail_mean_punish")
model3.setParam("OutputFlag", 0) 
y3 = {}
for i in scenarios:
    for j in seat_types:
        y3[(i,j)] = model3.addVar(lb=0, vtype=GRB.INTEGER, name=f"y_{i}") # we can only sell non negative integer number of tickets
        model3.addConstr(y3[(i,j)]<= x2_sol[j]) #We can't sell more seats than we have installed
        model3.addConstr(y3[(i,j)] <= D[(i,j)]) #We can't sell more seats than what the demand is
obj3 = gp.quicksum(probs[i]*gp.quicksum(y3[(i,j)]* K[j] for j in seat_types) for i in scenarios)
model3.setObjective(obj3, GRB.MAXIMIZE)
# Solve the model
model3.optimize()

y3_sol = {}
for i in scenarios:
    for j in seat_types:
        y3_sol[(i,j)] = y3[(i,j)].X
    
mean_value_obj = model3.objVal
VSS =  stochastic_obj - mean_value_obj
print(f'VSS = {VSS}')

'''Perfect info'''


# Store results
objectives_values = {}  # Store objective values for each scenario
decisions = {}          # Store ticket sales decisions for each scenario

# Solve a separate optimization problem for each scenario
for i in scenarios:
    # Create a new model for each scenario
    model = gp.Model(f"ScotRail_perfect_info_scenario_{i}")
    model.setParam("OutputFlag", 0) 

    # Decision variables: tickets sold for each category
    y_4 = {} #New dictionary of decision variables for each scenario
    for j in seat_types:
        y_4[j] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"y_{j}")

    # Space constraint: total seat allocation should not exceed 200
    model.addConstr(gp.quicksum(c[i] * y_4[i] for i in seat_types) <= 200) # Space constraint

    # Demand constraint: can't sell more seats than demand in scenario i
    for j in seat_types:
        model.addConstr(y_4[j] <= D[(i,j)]) #We can't sell more seats than what the demand is

    # Objective function: maximize revenue for scenario i
    model.setObjective(gp.quicksum(y_4[j] * K[j] for j in seat_types), GRB.MAXIMIZE)

    # Optimize for this scenario
    model.optimize()

    # Store results if an optimal solution is found
    objectives_values[i] = model.objVal  # Store objective value for scenario i
    decisions[i] = [y_4[j].X for j in seat_types]  # Store ticket sales decisions for scenario i

# Print results
#print("Optimal Objective Values per Scenario:", objectives_values) 
#for i in scenarios:
    #print(f"Scenario {i}: Ticket Sales = {decisions[i]}")
perfect_expectation = gp.quicksum(objectives_values[i]* probs[i] for i in scenarios)
EVPI = perfect_expectation - stochastic_obj
print(f"EVPI is {EVPI}")
