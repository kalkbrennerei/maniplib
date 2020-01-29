import copy
from maniplib.manipulation_utils import *

def lex(a,b):
	'''
	returns the candidate that wins lexicographic tie-breaking

	:param a: candidate
	:param b: candidate

	:returns: candidate index that wins
	:rtype: int
	'''
	if a>b:
		return a
	if b>a:
		return b
	return 0

def get_manip_kegroup(z, c, scoremap, X_res):
	'''
	calculates winning kegroup after manipulative votes casted according to X_res

	:param z: score of this iteration's least preferred egroup member (int)
	:param c: this iteration's least preferred egroup member index (int)
	:param scoremap: scores for all candidates (dict)
	:param X_res: optimal set of supported candidates for given c (list)

	:returns: size-k set of co-winning candidates
	:rtype: list
	'''
	# strongest k-k_star candidates
	S = [cand for cand in scoremap if scoremap[cand] > z]
	S.extend([cand for cand in scoremap if scoremap[cand] == z and lex(cand, c) == cand])
	S.append(c)
	S.extend(X_res)
	return S

def compute_weights(scoremap, z, c, C_star):
	'''
	computes weights according to approvals needed to get into kegroup

	:param scoremap: scores for all candidates (dict)
	:param z: score of this iteration's least preferred egroup member (int)
	:param c: this iteration's least preferred egroup member index (int)
	:param C_star: candidates to compute weights of (list)

	:returns: weights of candidates
	:rtype: list
	'''
	W = []

	for cand in C_star:
		if lex(cand, c) == c:
			# candidate has to outperform c
			W.append(z-scoremap[cand]+1)
		else:
			# candidate wins according to tie-breaking
			W.append(z-scoremap[cand])

	return W

def distribute_remaining(r, C_star, s_star, k_star, W, X, strength_order):
	'''
	distribute remaining votes on winning candidates, candidates that cannot win etc. to check if iteration is valid

	:param r: number of manipulative votes (int)
	:param C_star: candidates that can possibly join egroup (list)
	:param s_star: number of approvals to be distributed (int)
	:param k_star: number of remaining members of egroup (int)
	:param W: weights of candidates (list)
	:param X: supported candidates (list)
	:param strength_order: ordering of the candidates according to nonmanipulative votes (list)

	:returns: number of approvals that are impossible to distribute
	:rtype: int
	'''
	# remaining approvals after spending r approvals on each candidate from X
	remaining = s_star - r*k_star
	safe_cand = [cand for cand in strength_order if cand not in C_star]

	# remaining approvals after spending r approvals on each candidate from C\C*
	remaining -= r*len(safe_cand)

	# give one approval less than needed to candidates C*\X_res
	unapproved = [w-1 for w in W if W.index(w) not in X]
	remaining -= sum(unapproved)

	return remaining


def knapsack_parameters(k, r, l, c, z, scoremap):
	'''
	compute knapsack parameters

	:param k: winning egroup size (int)
	:param r: number of manipulative votes (int)
	:param l: parameter of bloc-rule (int)
	:param c: this iteration's least preferred egroup member index (int)
	:param z: score of this iteration's least preferred egroup member (int)
	:param scoremap: scores for all candidates (dict)

	:returns: 
		* **k_star** – number of remaining members of egroup (int)
		* **s_star** – number of approvals to be distributed (int)
		* **C_star** – candidates that can possibly join egroup (list)
	:rtype: tuple (k_star, s_star, C_star)
	'''

	# candidates that are k-egroup members anyways
	C_plus = [cand for cand in scoremap if scoremap[cand] > z]
	C_plus.extend([cand for cand in scoremap if scoremap[cand] == z and lex(cand, c) == cand])

	# check if choice of c is feasible
	if len(C_plus) >= k:
		return None, None, None

	# compute additional approvals nedded for c
	s = z - scoremap[c]

	# compute number of remaining candidates that need to join kegroup
	k_star = k-len(C_plus)-1

	# compute remaining number of approvals that manipulators can give
	# this will be knapsack capacity
	s_star = r*l - s

	# select candidates that can possibly join kegroup
	# this will be knapsack items
	C_remaining = [cand for cand in scoremap if cand not in C_plus and cand != c]
	C_star = [cand for cand in C_remaining if scoremap[cand] > z-r]
	C_star.extend([cand for cand in C_remaining if scoremap[cand] == z-r and lex(cand, c) == cand])

	if len(C_star) < k_star:
		return None, None, None

	return k_star, s_star, C_star

def compute_efficiency(n, W, P):
	'''
	computes efficiency of items in W and P

	:param n: number of items (int)
	:param W: item weights (list)
	:param P: item values (list)

	:returns: item indices ordered according to efficiency
	:rtype: list
	'''
	eff = [j for j in range(n)]
	eff.sort(key=lambda j: P[j]/W[j], reverse=True)

	return eff

def approx(k, P):
	'''
	approximates the final value of ekp by taking the sum of the k highest weighted items

	:param k: number of items in solution (int)
	:param P: item values (list)

	:returns: approximation value
	:rtype: list
	'''
	# sort item values descendingly
	P_sorted = sorted(P, reverse=True)

	# sum up k highest values
	return sum(P_sorted[:k])

def e_kkp(n, k, W, P, c):
	'''
	solves the exact k-items Knapsack Problem by dynamic programming

	:param n: number of items (int)
	:param k: number of items in solution (int)
	:param W: item weights (list)
	:param P: item values (list)
	:param c: weight constraint (int)

	:returns: chosen items, None if no solution is possible
	:rtype: list, None
	'''
	# determine upper bound for value by using knapsack approximation
	# U = 2*H_KP(n, k, W, P, c)
	U = approx(k, P)

	# initialize Y_0 with Y_0(0,0) = 0, other values are dummy values (above capacity)
	Y = [[c+1 for l in range(k+1)] for q in range(U+1)]
	Y[0][0] = 0

	# initialize Y_1
	Y_j = copy.deepcopy(Y)

	# initialize data structure to remember chosen item indices
	chosen = [[[] for l in range(k+1)] for q in range(U+1)]
	chosen_j = copy.deepcopy(chosen)

	for j in range(n):
		# Y_j has same values as Y at this point

		# l is the number of chosen items
		for l in range(1, k+1):

			# guess summed value (P) of chosen items for l and j
			for q in range(P[j], U+1):
				# compute new weight if item j would be added
				new = Y[q-P[j]][l-1] + W[j]

				# check if new value is an improvement and less equal c
				if Y[q][l] > new:
					Y_j[q][l] = new

					# remember which items where chosen
					chosen_j[q][l] = [j]
					chosen_j[q][l].extend(chosen[q-P[j]][l-1])
				# if value is no improvement, value from iteration before stays

		# prepare Y for the next iteration
		Y = copy.deepcopy(Y_j)
		chosen = copy.deepcopy(chosen_j)

	# find maximum q such that weight is below constraint
	for q in range(U, 0, -1):
		if Y[q][k] <= c:
			return chosen[q][k]

	# no solution found
	return None

def manipulation(l, k, non_manip_rankmaps, utilities, eval_f):
	'''
	finds an l-Bloc manipulation for utilitarian and candidate-wise egalitarian evaluation

	:param l: parameter of l-bloc rule (int)
	:param k: winning egroup size (int)
	:param non_manip_rankmaps: preflib format for voters rankings (list of dicts)
	:param utilities: manipulators utilities {manipulator_index:utility} (list)
	:param eval_f: evaluation function (function)

	:returns:
		* **X** – set of candidates that should be suported, not necessarily size l (list)
		* **eval** – value of eval_f of winning max_S (int)
		* **S** – winning kegroup (list)
		* **replaced** – number of candidates replaced (int)
	:rtype: tuple (X, eval, S, replaced)
	'''
	# manipulator's count
	r = len(utilities[0])

	# determine strength order
	scoremap = get_score_map(l, non_manip_rankmaps)

	strength_order = get_strength_order_lex(scoremap)

	# prepare search for max utility
	max_eval = 0
	max_X = []
	max_S = []

	value_map = {}
	for i in range(1, len(utilities)+1):
		value_map[i] = eval_f([i], utilities)

	# fix candidate index for c, the least prefered member of the k-egroup
	# at most r*l candidates can be supported by the manipulators, k candidates have to be considered anyways
	for c in strength_order[:k+r*l]:

		# fix final score of c
		for z in range(scoremap[c], scoremap[c]+r):

			# determine knapsack parameters
			k_star, s_star, C_star = knapsack_parameters(k, r, l, c, z, scoremap)

			# check if choice of c is feasable
			if C_star == None:
				continue

			# knapsack only has to be comuted if candidates still have to be added
			if k_star != 0:
				# determine item's values by evaluation function
				P = [value_map[cand] for cand in C_star]

				# weight is number of approvals needed to be in kegroup
				W = compute_weights(scoremap, z, c, C_star)

				# compute exact k-item knapsack
				X = e_kkp(len(C_star), k_star, W, P, s_star)

				# check if knapsack is feasable
				if X == None:
					continue

				X_res = [C_star[x] for x in X]


				# check if remaining approvals can be distributed
				if distribute_remaining(r, C_star, s_star, k_star, W, X, strength_order)>0:
					continue

				# determine manipulators satisfaction
				S = get_manip_kegroup(z, c, scoremap, X_res)

			# in this case this case no candidates get replaced
			else:
				S = strength_order[:k]
				# vote for all winning candidates
				X_res = S

			eval_v = eval_f(S, utilities)

			# check if manipulators' satisfaction is maximal
			if(eval_v > max_eval):
				max_eval = eval_v
				max_X = X_res.copy()
				max_S = S.copy()

	# check if manipulation results in change of kegroup
	replaced = check_manipul(k, max_S, strength_order)

	# return X that maximizes manipulators satisfaction
	return max_X, max_eval, max_S, replaced