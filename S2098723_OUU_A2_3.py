#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 17:36:24 2025

@author: alexbuck
"""


'''Question 3'''

import data as Data
import gurobipy as gp
from gurobipy import Model, GRB

cities = Data.cities # set of cities
scenarios = Data.scenarios # set of scenarios
theta = Data.theta # unit cost of delivery to city n in the first stage
theta_s = Data.theta_prime # unit cost of transportion between city n and center in the second stage

h = Data.h # unit cost of unused inventory
g = Data.g # unit cost of shortage 
I = Data.I # inventory of the center at the beginning
Yn = Data.Yn # inventory of city n at the beginning
demand = Data.demand # demand of city n under scenario k
prob = 1.0/len(scenarios) # probability of scenario k
N = len(Yn)
model = Model("Question 3")
model.setParam("OutputFlag", 0) 
x = {}
for i in cities:
    x[i]= model.addVar(lb=0)
model.addConstr(gp.quicksum(x[i] for i in cities)<= I)
# Create second-stage variables and constraints for each scenario
u = {}
v = {}
z = {}
s = {}

for i in scenarios:
    for j in cities:
        u[(j,i)] =  model.addVar(lb=0)
        v[(j,i)] =  model.addVar(lb=0)
        z[(j,i)] =  model.addVar(lb=0)
        s[(j,i)] =  model.addVar(lb=0)
        
        model.addConstr(Yn[j] + x[j] + v[(j,i)] + s[(j,i)] == demand[(j, i)] + z[(j,i)] + u[(j,i)])
    model.addConstr(I + gp.quicksum(u[(j,i)] for j in cities) >=  gp.quicksum(v[(j,i)]+ x[j] for j in cities))

# Objective Function: Minimize expected total cost
obj = (
    gp.quicksum(theta[j] * x[j] for j in cities)  # First-stage cost
    + prob * gp.quicksum(
        gp.quicksum((theta_s[j] *(v[(j,i)] + u[(j,i)]))+ (h * z[(j,i)]) + (g * s[(j,i)]) for j in cities )
        for i in scenarios
    )  # Expected second-stage costs
)
model.setObjective(obj, GRB.MINIMIZE)
# Solve the model
model.optimize()

first_stage_decisions = {}

for i in cities:
    first_stage_decisions[i] = x[i].X 

print(f"The first stage decisions are : {first_stage_decisions}")

solution_time = model.Runtime

print(f"Solution time: {solution_time:.4f} seconds")

optimal_obj = model.ObjVal
print(f'The optimal objective value is {optimal_obj:.4f}')

    
    
