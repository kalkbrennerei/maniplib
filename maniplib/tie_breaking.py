from gurobipy import *
from maniplib.manipulation_utils import *

def get_candidate_indices(T, candidates, m):
	'''
	get a list of candidates indicies from optimized model

	:param T: types, tuples of utility values (list)
	:param candidates: all candidate indices (list)
	:param m: model

	:return: candidate indices
	:rtype: list
	'''
	solution = []

	# copy candidate list
	candidates_copy = candidates.copy()

	for idx, type_vector in enumerate(T):

		# get solution count for each type
		value = int(m.getVarByName("X["+str(idx)+"]").X)

		# add l candidates of this type the solution
		# for two candidates of the same type, the one that appears first will be chosen
		for l in range(value):

			# get candidate index from candidate list
			can_idx = candidates_copy.index(type_vector)
			
			# candmap indices ranges from 1 to numcandidates
			solution.append(can_idx+1)
			candidates_copy[can_idx] = "REMOVED"

	return solution


def egal_opt(utilities, r, k):
	'''
	egalitarian optimistic tie-breaking

	:param utilities: manipulators utilities {manipulator_index:utility} (list)
	:param r: number of manipulators (int)
	:param k: egroup-size (int)

	:return: winning candidate indices from utilities
	:rtype: list
	'''
	T,T_count, candidates = get_types(utilities)
	t = len(T)

	# Create a new model with variable s that has to be maximized, decision vector X
	# X[i] indicates the number of candidates of type T[i] in an optimal k-egroup
	m = Model("tb_egal")
	m.setParam( 'OutputFlag', False )
	s = m.addVar(vtype=GRB.INTEGER, name="s")  
	X = m.addVars(t, vtype=GRB.INTEGER, name="X")

	# Set objective: maximization of s
	m.setObjective(s, GRB.MAXIMIZE)

	# Add constraint: for type T[i]: X[i] <= T_count[i]
	for i in range(t):
		m.addConstr(X[i] <= T_count[i])

	# Add constraint: sum of all selected types equals k
	m.addConstr(sum([X[i] for i in range(t)]) == k)

	#Add constraint: last constraint TODO: add description
	for l in range(r):
		m.addConstr(sum([X[i]*T[i][l] for i in range(t)]) >= s)  

	# Optimize model
	m.optimize()

	return get_candidate_indices(T, candidates, m)