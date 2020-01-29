import math

def get_score_map(l, rankmaps):
	'''
	calculates scores for all candidates according to l-bloc rule and votes casted in rankmaps

	:param l: paramenter of l-bloc-rule (int)
	:param rankmaps: preflib data structure for voters preferences (list of dicts)

	:returns: candidates and their scores
	:rtype: dict
	'''
	# init scoremap
	scoremap = {}
	for voter in rankmaps:
		for can in voter:
			scoremap[can] = 0

	# sum up every candidate's score
	for voter in rankmaps:
		for can in voter:
			# check if candidate is in voters l highest preferences
			if voter[can] <= l:
				scoremap[can] += 1

	return scoremap

def get_strength_order_lex(scoremap):
	'''
	sort candidates according to voters preferences and lex_tb

	:param scoremap: mapping from candidates to scores (dict)

	:returns: candidate indices, strongest candidates in the front
	:rtype: list
	'''
	strength_order = []

	# sort scores descending
	scores = list(set(scoremap.values()))
	scores.sort(reverse=True)

	# check how many candidates with the same score exist
	for score in scores:
		same_score = list(filter(lambda xy : xy[1]==score, scoremap.items()))
		if len(same_score)==1:
			strength_order.append(same_score[0][0])
		else:
			# perform tie-breaking for more than one candidate with the same score
			# sort by index for lexicographic tie-breaking
			tb = sorted([x[0] for x in same_score])
			strength_order.extend(tb)

	return strength_order

def utilitarian(S, utilities):
	'''
	evaluates elected kegroup for manipulators by utilitarian function

	:param S: choice of candidates in kegroup (list)
	:param utilities: manipulators utilities {manipulator_index:utility} (list)

	:returns: utilitarian value
	:rtype: int
	'''
	result = 0

	# sum up all manipulator's utility values for candidates in S
	for can in S:
		utility = utilities[can-1]
		for manip in utility:
			result+= utility[manip]

	return result

def candegal(S, utilities):
	'''
	evaluates elected kegroup for manipulators by candidate-wise egalitarian function

	:param S: choice of candidates in kegroup (list)
	:param utilities: manipulators utilities {manipulator_index:utility} (list)

	:returns: utilitarian value
	:rtype: int
	'''
	result = 0

	# scan utilities for manipulator that gains least utility from a candidate
	for can in S:
		utility = utilities[can-1]
		min_ut = math.inf
		for manip in utility:
			if utility[manip] < min_ut:
				min_ut = utility[manip]
		# sum up minimum utilities
		result+= min_ut

	return result

def egalitarian(S, utilities, r):
	'''
	evaluates elected kegroup for manipulators by egalitarian function

	:param S: choice of candidates in kegroup (list)
	:param utilities: manipulators utilities {manipulator_index:utility} (list)
	:param r: number of manipulators

	:returns: utilitarian value
	:rtype: int
	'''
	ut = []
	# compute manipulators utilities
	for can in S:
		utility = utilities[can-1]
		for manip in utility:
			ut.append(utility[manip])

	# determine least satisfied manipulator
	return min(ut)

def check_manipul(k, max_S, strength_order):
	'''
	counts how many candidates get exchanged after manipulation

	:param k: winning egroup size (int)
	:param max_S: winning kegroup that maximizes manipulator's satisfaction
	:param strength_order: ordering of the candidates according to nonmanipulative votes (list)

	:returns: number of candidates exchanged
	:rtype: int
	'''
	exchanged = 0

	# find differences between manipulative winners and nonmanipulative winners
	for can in max_S:
		if can not in strength_order[:k]:
			exchanged += 1

	return exchanged

def get_types(utilities):
	'''
	get type data structures needed for tie breaking algorithm

	:param utilities: manipulators utilities {manipulator_index:utility} (list)

	:returns: 
		* **T** – types, tuples of utility values (list)
		* **T_count** – for every type in T T_count has the number of candidates
		* **candidates** – list of each candidate's type
	:rtype: tuple (T, T_count, candidates)
	'''
	# determine possible type vectors by removing duplicates
	candidates = [tuple(d.values()) for d in utilities]
	T = list(set(candidates))

	# T_count[i] denotes the count of candidates of type T[i] in utilities
	T_count = [candidates.count(type) for type in T]

	return T, T_count, candidates