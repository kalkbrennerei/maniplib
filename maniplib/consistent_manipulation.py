from maniplib.manipulation_utils import *

def get_distinguished_cand(c, r, l, non_manip_rankmaps, strength_order):
	'''
	get candidates that can be stronger than c by adding r manipulative votes ordered by strength

	:param c: dropped candidate index (int)
	:param r: number of manipulators (int)
	:param l: parameter of l-bloc rule (int)
	:param non_manip_rankmaps: preflib format for voters rankings (list of dicts)
	:param strength_order: ordering of the candidates according to nonmanipulative votes (list)

	:returns: distinguished candidates
	:rtype: list
	'''
	D = []

	scores = get_score_map(l, non_manip_rankmaps)
	sc = scores[c]

	# TODO: optimization by not checking kept candidates in the first place
	# iterate over strength order to keep order in distiguished candidates
	for can in strength_order:
		# add cand if has same score as dropped candidate and is weaker by lex tb
		if scores[can] == sc and can > c:
			D.append(can)
		# add candidate if r votes make him stronger than c
		if scores[can] < sc and scores[can]+r > sc:
			D.append(can)
		# check lex tie breaking if cand (with r manip votes) and c have the same score
		if scores[can]+r == sc and can < c:
			D.append(can)

	return D

def get_most_valuable(n, utilities, D, eval_f):
	'''
	extracts n most valuable candidates according to the evaluation function

	:param n: number of most valuable caniddates to be extracted (int)
	:param utilities: manipulators utilities {manipulator_index:utility} (list)
	:param D: candidate indices to extract from (list)
	:param eval_f: evaluation function (function)

	:returns: most valuable candidates indices
	:rtype: list
	'''
	valuable = []

	if n > len(D):
		return valuable

	utilities_v = {}

	# calculate utility value according to eval_f
	for i in D:
		utilities_v[i] = eval_f([i], utilities)

	# find n candidates with max utilitiy values
	for i in range(n):
		m = max(utilities_v.keys(), key=(lambda key: utilities_v[key]))
		valuable.append(m)
		utilities_v[m] = 0

	return valuable

def get_manip_kegroup(r, k, X, l, non_manip_rankmaps):
	'''
	calculates winning kegroup after manipulative votes casted consistently according to X (needed to compute manipulators utility)

	:param r: number of manipulative votes (int)
	:param k: winning egroup size (int)
	:param X: optimal set of supported candidates for given t of kept candidates (list)
	:param l: parameter of bloc-rule (int)
	:param non_manip_rankmaps: preflib format for voters rankings (list of dicts)

	:returns: size-k set of co-winning candidates
	:rtype: list
	'''
	scores = get_score_map(l, non_manip_rankmaps)

	for can in X:
		scores[can]+=r

	strength_order = get_strength_order_lex(scores)

	return strength_order[:k]

def get_p(k, diff, X, strength_order):
	'''
	determine how many candidates get "kicked out" if adding weakest candidates

	:param k: winning egroup size (int)
	:param diff: how many candidates needed to complete l votes (int)
	:param X: optimal set of supported candidates for given t of kept candidates (list)
	:param strength_order: ordering of the candidates according to nonmanipulative votes (list)
	
	:returns: number of candidates "kicked out"
	:rtype: int
	'''
	# choose diff weakest candidates from C\X and keep their indices in strength order
	A = [can for can in strength_order if can not in X][-diff:]
	A.extend(X)

	# sort A by strength order
	A.sort(key=lambda can: strength_order.index(can))

	# choose k strongest candidates from A+X
	B = A[:k]
	
	# how many valuable candidates from X get kicked out
	p = len([b for b in B if b not in X])

	return p

def optimal_supported_cand(k, l, t, D, strength_order, utilities, eval_f):
	'''
	finds an optimal supported candidate set for a given t of kept candidates

	:param k: winning egroup size (int)
	:param l: parameter of l-bloc rule (int)
	:param t: number of kept candidates (int)
	:param D: set of distinguished candidates (list)
	:param strength_order: ordering of the candidates according to nonmanipulative votes (list)
	:param utilities: manipulators utilities {manipulator_index:utility} (list)
	:param eval_f: evaluation function e.g. utilitarian (function)

	:returns: optimal set of supported candidates for given t of kept candidates (list)
	:rtype: list
	'''
	# k-t most valuable candidates from D
	X = get_most_valuable(k-t, utilities, D, eval_f)

	# add stronger candidates that hopefully don't influence the choice of other candidates in X
	arb = min(t, l-len(X))
	X.extend(strength_order[:arb])

	diff = l-len(X)

	# more candidates needed to use l votes, choose strategically
	if diff != 0:
		p = get_p(k, diff, X, strength_order)

		# add p most valuable candidates from D\X
		D_del_X = [d for d in D if d not in X]
		X.extend(get_most_valuable(p, utilities, D_del_X, eval_f))
		
		if diff-p != 0:
			# add diff-p weakest candidates of C\X to X
			X.extend([can for can in strength_order if can not in X][-(diff-p):])

	return X

def consistent_manipulation(l, k, non_manip_rankmaps, utilities, eval_f):
	'''
	finds a manipulation where manipulators vote consistently (if there is any)

	:param l: parameter of l-bloc rule (int)
	:param k: winning egroup size (int)
	:param non_manip_rankmaps: rankmaps of nonmanipulative votes
	:param utilities: manipulators utilities {manipulator_index:utility} (list)
	:param eval_f: evaluation function (finction)

	:returns:
		* **X** – list of l candidates that the manipulators have to support
		* **eval** – evaluation value of the winning group
		* **S** – is the winning group under manipulation
		* **replaced** – is the number of candidates exchanged from the nonmanipulative group
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

	# iterate over the number of candidates to be kept
	for t in range(max(k-l, 0), min(k+1, len(strength_order))):

		# determine dropped candidate (strongest candidate who is not part of the kegroup)
		dropped_can = strength_order[t]

		# compute distinguished candidates that can still win with manipulative votes
		D = get_distinguished_cand(dropped_can, r, l, non_manip_rankmaps, strength_order)

		# skip iteration if D is not big enough
		if(len(D) < k-t):
			continue

		# determine optimal supported candidate set for this interation's t
		X = optimal_supported_cand(k, l, t, D, strength_order, utilities, eval_f)

		# determine manipulators satisfaction
		S = get_manip_kegroup(r, k, X, l, non_manip_rankmaps)
		eval_v = eval_f(S, utilities)

		# check if manipulators' satisfaction is maximal
		if(eval_v > max_eval):
			max_eval = eval_v
			max_X = X.copy()
			max_S = S.copy()

	# check if manipulation results in change of kegroup
	replaced = check_manipul(k, max_S, strength_order)

	# if no solution found return nonmanipulative kegroup
	if not max_X:
		return strength_order[:l], eval_f(strength_order[:k], utilities), strength_order[:k], 0

	# return X that maximizes manipulators satisfaction
	return max_X, max_eval, max_S, replaced