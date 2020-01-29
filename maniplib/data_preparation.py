from maniplib.preflibtools import PreflibUtils as pu
import requests
import io
import random

def merge_rankmap_counts(rankmaps, rankmapcounts):
	'''
	merge rankmaps and it's count into one list where duplicates are allowed

	:param rankmaps: candidate to rank mapping per voter, duplicates removed (list of dicts)
	:param rankmapcounts: keeping track of duplicates

	:returns: merged rankmaps and rankmapcounts in preflib data format
	:rtype: list
	'''
	new_rankmaps = []

	for r, c in zip(rankmaps, rankmapcounts):
		for i in range(c):
			new_rankmaps.append(r)

	return new_rankmaps

def dataset_from_url(url):
	'''
	read a dataset from an url

	:param url: adress of the data ressource conforming to the specified format (str)

	:returns:
		* **candmap** – mapping from candidate indices to candidate names (dict)
		* **rankmaps** – candidate to rank mapping per voter, duplicates removed (list of dicts)
		* **numvoters** – number of voters (int)
	:rtype: tuple (candmap, rankmaps, rankmapcounts)
	'''	
	req = requests.get(url)
	dataset = io.StringIO(req.text)

	candmap, rankmaps, rankmapcounts, numvoters = pu.read_election_file(dataset)

	new_rankmaps = merge_rankmap_counts(rankmaps, rankmapcounts)
	return candmap, new_rankmaps, numvoters

def dataset_from_file(path):
	'''
	read a dataset from a file

	:param path: path to the data ressource file confroming to the specified format (str)

	:returns:
		* **candmap** – mapping from candidate indices to candidate names (dict)
		* **rankmaps** – candidate to rank mapping per voter, duplicates removed (list of dicts)
		* **numvoters** – number of voters (int)
	:rtype: tuple (candmap, rankmaps, numvoters)
	'''
	f = open(path, "r")
	dataset = io.StringIO(f.read())

	candmap, rankmaps, rankmapcounts, numvoters = pu.read_election_file(dataset)

	new_rankmaps = merge_rankmap_counts(rankmaps, rankmapcounts)
	return candmap, new_rankmaps, numvoters

def utilities_borda(rankmaps, r, numcandidates):
	'''
	select the first r voters from the rankmap as manipulators and extract their utilities by borda rule
	voter_index is relative to rankmaps

	:param rankmaps: candidate to rank mapping per voter (list of dicts)
	:param r: number of manipulators (int)
	:param numcandidates: number of candidates (int))

	:returns: manipulators utilities {manipulator_index:utility}
	:rtype: list
	'''
	# check if number of manipulators feasible
	if r > len(rankmaps):
		return []

	utilities = [{} for i in range(numcandidates)]

	# determine max rank that is given to a candidate
	max_utility = max([max(i.values()) for i in rankmaps])

	# add utilities for the selected voters
	for i in range(r):

		# initialize utility by zero
		for utility in utilities:
			utility[i] = 0

		# update utility if manipulators ranked the candidate
		for cand, rank in rankmaps[i].items():
			# borda rule depends on rank (e.g. 1 rank gives max utility)
			utilities[cand-1][i] = max_utility-rank+1 

	return(utilities)

def utilities_borda_random(rankmaps, r, numcandidates):
	'''
	select the r random voters from the rankmap as manipulators and extract their utilities by borda rule
	voter_index is relative to rankmaps

	:param rankmaps: candidate to rank mapping per voter (list of dicts)
	:param r: number of manipulators (int)
	:param numcandidates: number of candidates (int)

	:returns: manipulators utilities {manipulator_index:utility}
	:rtype: list
	'''	
	# check if number of manipulators is feasible
	if r > len(rankmaps):
		return -1
		
	utilities = [{} for i in range(numcandidates)]
	# determine max rank that is given to a candidate
	max_utility = max([max(i.values()) for i in rankmaps])

	# add utilities for the randomly selected voters
	for i in random.sample(range(len(rankmaps)), r):

		# initialize utility by zero
		for utility in utilities:
			utility[i] = 0

		# update utility if manipulators ranked the candidate
		for cand, rank in rankmaps[i].items():
			# borda rule depends on rank (e.g. 1 rank gives max utility)
			utilities[cand-1][i] = max_utility-rank+1	

	return(utilities)

def utilities_borda_random_udiff(rankmaps, r, numcandidates, udiff):
	'''
	select the r random voters from the rankmap as manipulators and extract their utilities by borda rule using udiff different utility values
	voter_index is relative to rankmaps

	:param rankmaps: candidate to rank mapping per voter (list of dicts)
	:param r: number of manipulators (int)
	:param numcandidates: number of candidates (int)
	:param udiff: number of different utility values (int)

	:returns: manipulators utilities {manipulator_index:utility}
	:rtype: list
	'''	
	# check if number of manipulators is feasible
	if r > len(rankmaps):
		return -1

	# check if udiff is feasible
	if udiff > numcandidates:
		return -1
		
	utilities = [{} for i in range(numcandidates)]
	# determine max rank that is given to a candidate
	max_utility = max([max(i.values()) for i in rankmaps])

	# add utilities for the randomly selected voters
	for i in random.sample(range(len(rankmaps)), r):

		# initialize utility by zero
		for utility in utilities:
			utility[i] = 0

		# update utility if manipulators ranked the candidate
		for cand, rank in rankmaps[i].items():
			# ranks higher than udiff are utility zero to enforce using udiff values only (including 0)
			if rank >= udiff:
				utilities[cand-1][i] = 0
			else:
				# borda rule depends on rank (e.g. 1 rank gives max utility)
				utilities[cand-1][i] = max_utility-rank+1	

	return(utilities)

def get_nonmanipulative_votes(rankmaps, utilities):
	'''
	removes manipulative votes from manipulator's utilities from rankmaps

	:param rankmaps: candidate to rank mapping per voter (list of dicts)
	:param utilities: manipulators utilities {manipulator_index:utility} (list)

	:returns: candidate to rank mapping per voter without manipulators
	:rtype: list of dicts
	'''
	nonmanip_rankmaps = []

	# get manipulators indices to filter out
	manip_idx = utilities[0].keys()

	# copy only nonmanipulative votes
	for i in range(len(rankmaps)):
		if i not in manip_idx:
			nonmanip_rankmaps.append(rankmaps[i])

	return nonmanip_rankmaps