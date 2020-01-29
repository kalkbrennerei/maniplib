from maniplib.manipulation_utils import *

from gurobipy import *

def merge_scoremaps(scoremap, solution):
	'''
	merge manipulative approvals and unmanipulative scoremap

	:param scoremap: mapping from candidates to scores (dict)
	:param solution: number of approvals per candidate (dict)

	:returns: mapping from candidates to manipulative scores
	:rtype: dict
	'''
	# check if solution is empty
	if not solution:
		return scoremap

	new_scoremap = {}
	for cand in scoremap:
		new_scoremap[cand] = scoremap[cand] + solution[cand]

	return new_scoremap

def get_candidate_indices(m, T, r, z, candidates, scoremap):
	'''
	get approved candidate indices and amount of approvals from group counts

	:param m: number of candidates (int)
	:param T: types, tuples of utility values (list)
	:param r: number of manipulators (int)
	:param z: lowest possible score of a winning candidate (int)
	:param candidates: list of each candidate's type
	:param scoremap: mapping from candidates to scores (dict)

	:returns: number of approvals per candidate
	:rtype: dict
	'''
	# init solution dict
	solution = {}
	for cand in range(len(scoremap)+1):
		solution[cand] = 0

	# iterate over all groups
	for t in T:
		i = T.index(t)
		for j in range(r+1):
			G = cand_in_group(t, j, z, scoremap, candidates)

			# compute number of candidates from group to be approved
			x = int(m.getVarByName("X["+str(i)+","+str(j)+"]").X)
			x_p = int(m.getVarByName("X_p["+str(i)+","+str(j)+"]").X)

			app = x + x_p
			if app > len(G):
				print(m.getVarByName("X["+str(i)+","+str(j)+"]"))
				print(m.getVarByName("X_p["+str(i)+","+str(j)+"]"))
				print("app =", app, ", len(G) =", len(G), "x =", x, "x_p =", x_p)
				print(m.getConstrByName("X_p["+str(i)+","+str(j)+"]").rhs)
				# print(m.getConstrByName("X_p["+str(i)+","+str(j)+"]").lhs)
				# print(int(m.getConstrByName("X_p"+str(i)+","+str(j)).lhs))
				# outf = open(base_path + base_file_name + str(i) + ".soc", 'w')
				# PreflibUtils.write_map(cmap, nvoter, rankmap_to_voteset(rmaps, rmapscounts),outf)
				# outf.close()
				# return -1
				return {}

			# add j approvals to candidates from group that are to be approved
			for a in range(app):
				can = G[a]
				solution[can] = j

	return solution

def ILP_optimistic(z, p, b, r, l, candidates, T, scoremap):
	'''
	creates and solves an ILP in one iteration

	:param z: lowest possible score of a winning candidate (int)
	:param p: number of promoted candidates, weaker than z, but still win (int)
	:param b: number of border candidates, score exactly z (int)
	:param r: number of candidates (int)
	:param l: parameter of l-bloc rule (int)
	:param candidates: list of each candidate's type
	:param T: types, tuples of utility values (list)
	:param scoremap: mapping from candidates to scores (dict)

	:returns: number of approvals per candidate
	:rtype: dict
	'''

	# compute C+ and C- again
	C_plus = [cand for cand in scoremap if scoremap[cand] > z]
	C_minus = [cand for cand in scoremap if scoremap[cand] < z-r]

	m = Model("egalitarian")
	m.setParam( 'OutputFlag', False)

	# disable presolving
	m.setParam( 'Presolve', False)

	# create variables x_ij and x_ij+ for every type i and approvalnumber j
	# x_ij are border, x_ij+ are promoted candidates
	X_p = m.addVars(len(T), r+1, vtype = GRB.INTEGER, name = "X_p")
	X = m.addVars(len(T), r+1, vtype = GRB.INTEGER, name = "X")

	# how many approvals have to be spent to get p, b
	o = m.addVar(vtype=GRB.INTEGER, name="o")
	# how many remaining approvals have to be spent
	o_bar = m.addVar(vtype=GRB.INTEGER, name="o_bar")

	# set constraints ensuring that values of x_ij are feasable
	for t in T:
		i = T.index(t)
		for j in range(r+1):
			G = cand_in_group(t,j,z,scoremap, candidates)
			# don't make more candidates b and p than are actually there (4)
			m.addConstr((len(G) >= X_p[i,j] + X[i,j]), name = "X_p["+str(i)+","+str(j)+"]")

		G_0 = cand_in_group(t,0,z,scoremap, candidates)

		# candidates with score z have to be p or b (7)
		m.addConstr(X[i,0]+X_p[i,0] == len(G_0))

		# if r approvals are needed, candidate needs to be b (8)
		m.addConstr(X_p[i,r] == 0)

	# ensure that p and b many candidates are chosen (5),(6)
	m.addConstr(sum([sum([X[i,j] for j in range(r+1)]) for i in range(len(T))]) == b)
	m.addConstr(sum([sum([X_p[i,j] for j in range(r+1)]) for i in range(len(T))]) == p)

	# set constraints needed for the manipulation (9)
	m.addConstr(sum([sum([X[i,j]*j + X_p[i,j]*(j+1) for j in range(r+1)])for i in range(len(T))]) == o)
	# only lr votes can be spent (10)
	m.addConstr(o <= l*r)

	# set constraints needed for the distribution of the remaining approvals
	# very big equation (11)
	safe_app = r*(len(C_plus)+len(C_minus))
	m.addConstr(o_bar <= safe_app + sum([sum([len(cand_in_group(T[i],j,z,scoremap, candidates)) - X[i,j] - X_p[i,j] for j in range(r+1)]) for i in range(len(T))])*(j-1) + sum([sum([X_p[i,j] * (r-j-1) for j in range(r+1)]) for i in range(len(T))]))

	# sum of votes lr that have to be spent (12)
	m.addConstr(o_bar+o == l*r)

	m.optimize()

	# check if model is infeasible
	if m.status != GRB.Status.OPTIMAL:
		return None
		
	return get_candidate_indices(m, T, r, z, candidates, scoremap)

def ILP_pessimistic():
	return None

def cand_in_group(t, j, z, scoremap, candidates):
	'''
	determine the members of a group G_i,j for given types and additional score j

	:param t: type of a candidate (tuple)
	:param j: group parameter (int)
	:param z: lowest possible score of a winning candidate (int)
	:param scoremap: mapping from candidates to scores (dict)
	:param candidates: list of each candidate's type

	:returns: candidates in the group
	:rtype: list
	'''
	G = []

	# zip type list to tuples with their index
	index_list = zip(candidates, range(1, len(candidates)+1))

	# all candidate indices of type t
	cand_t = [idx for i, idx in index_list if i == t]

	# check if candidate has score z-j
	for c in cand_t:
		if scoremap[c] == z-j:
			G.append(c)

	return G

def egalitarian_manipulation(l, k, r, rankmaps, utilities):
	'''
	finds a manipulation where remaining approvals can be distributed with egalitarian evaluation using ILP

	:param l: parameter of l-bloc rule (int)
	:param k: winning egroup size (int)
	:param rankmaps: rankmaps of nonmanipulative votes
	:param utilities: manipulators utilities {manipulator_index:utility} (list)

	:returns:
		* **X** – dict of candidates to support, {candidate:numapprovals}
		* **eval** – egalitarian value of winning max_S
		* **S** – winning kegroup
		* **replaced** – number of candidates replaced (int)
	:rtype: tuple (X, eval, S, replaced)
	'''
	# prepare loop variables
	num_cand = len(utilities[0])
	score_map = get_score_map(l, rankmaps)
	min_score = min(score_map.values())
	max_score = max(score_map.values())+r

	# init optimal k-egroup as empty
	max_S = []
	max_ut = 0
	max_sol = {}

	# lowest possible score of a winning candidate
	for z in range(min_score, max_score+1):

		# candidates with a score higher than z
		C_plus = [cand for cand in score_map if score_map[cand] > z]

		# skip this iteration if there are k or more candidates winning anyways
		if len(C_plus) >= k:
			continue

		# number of promoted candidates (weaker than z, but still win)
		# upper bound for p: C+ and one candidate with score z is needed
		# winning: C+, p, some of b
		for p in range(k-len(C_plus)):
			# number of border candidates (score exactly z)
			# m-|C+|-p >= b >= k-|C+|-p
			for b in range(k-len(C_plus)-p, num_cand-len(C_plus)-p+1):

				T, T_count, candidates = get_types(utilities)

				solution = ILP_optimistic(z, p, b, r, l, candidates, T, score_map)

				# check if model is feasible
				if solution == None:
					continue

				# if solution == -1:
				# 	return -1

				# add manipulators approvals to scoremap to compute manipulative kegroup
				new_scoremap = merge_scoremaps(score_map, solution)
				new_str = get_strength_order_lex(new_scoremap)
				S = new_str[:k]

				# compute egalitarian value
				ut = egalitarian(S, utilities, r)
				
				# check if solution has greater evaluation value
				if ut > max_ut:
					max_S = S
					max_ut = ut
					max_sol = solution

	# check if manipulation results in change of kegroup
	strength_order = get_strength_order_lex(score_map)
	replaced = check_manipul(k, max_S, strength_order)

	# check if no solution was found
	if not max_sol:
		max_S = strength_order[:k]
		max_ut = egalitarian(max_S, utilities, r)
		replaced = 0

	return max_sol, max_ut, max_S, replaced