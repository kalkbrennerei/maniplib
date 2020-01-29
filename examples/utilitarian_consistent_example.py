from maniplib import data_preparation as dp
from maniplib import manipulation_utils as mu
from maniplib import consistent_manipulation as cm

if __name__ == '__main__':
	
	sf_12 = "http://www.preflib.org/data/election/sf/ED-00021-00000014.toc" # san fransisco 2012 election dataset
	candmap, rankmaps, numvoters = dp.dataset_from_url(sf_12) # download and read election data

	r = 40 # specify the number of manipulators
	numcandidates = len(candmap)
	utilities = dp.utilities_borda_random(rankmaps, r, numcandidates)

	l = 6 # specify parameter of l-Bloc rule
	k = 5 # specify number of winning candidates
	non_manip = dp.get_nonmanipulative_votes(rankmaps, utilities) # removing manipulative votes from the rankmaps
	candidates_to_approve, eval_value, candidates_winning, num_candidates_replaced = cm.consistent_manipulation(l, k, non_manip, utilities, mu.utilitarian)

	# iterate over candidates_to_approve to obtain the name by using candmap
	names_to_approve = []
	for cand in candidates_to_approve:
		names_to_approve.append(candmap[cand])

	print(names_to_approve)