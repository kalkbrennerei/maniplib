# ManipLib

This tool solves the coalitional manipulation problem for the *l-Bloc* voting rule, an extension of [Single Non-Transferable Vote](https://en.wikipedia.org/wiki/Single_non-transferable_vote), a multiwinner voting rule.

There are different ways of decing on a possible goal of manipulation by aggregating manipulators' utilities ([utilitarian](https://en.wikipedia.org/wiki/Social_welfare_function#Cardinal_social_welfare_functions), candidate-wise egalitarian and egalitarian evaluation) We provide an implementation of the following variants:
- Utilitarian and Candidate-wise egalitarian variant,
- Utilitarian and Candidate-wise egalitarian variant with consistent manipulators,
- Egalitarian variant, and
- Egalitarian Tie-Breaking.

As part of my [Bachelor thesis](https://fpt.akt.tu-berlin.de/publications/theses/BA-lydia-kalkbrenner.pdf) I implemented the algorithms proposed by [R. Bredereck, A. Kaczmarczyk, and R. Niedermeier](https://arxiv.org/abs/1806.10460).

## Usage
The egalitarian variant of manipulation and tie-breaking use the [Gurobi Optimizer](https://www.gurobi.com/) which requires a license (free for academic use).

This library uses election data in [PrefLib](http://www.preflib.org/) data format, for example [San Fransisco City Council Election 2012](http://www.preflib.org/data/election/sf/). Input data can be read directly from a file or url as shown:
```python
from maniplib import data_preparation as dp

sf_12 = "http://www.preflib.org/data/election/sf/ED-00021-00000014.toc" # san fransisco 2012 election dataset
candmap, rankmaps, numvoters = dp.dataset_from_url(sf_12) # download and read election data
```
The algorithms use utility functions to aggregate manipulators' utilities. Utility functions can be generated by choosing random candidates as manipulators from the rankmaps and compute their utility functions by [Borda scores](https://en.wikipedia.org/wiki/Borda_count#Starting_at_0).
```python
r = 40 # specify the number of manipulators
numcandidates = len(candmap)
utilities = dp.utilities_borda_random(rankmaps, r, numcandidates)
```

A result for a utilitarian manipulation with consistent manipulators can be obtained as follows:
```python
from maniplib import manipulation_utils as mu
from maniplib import consistent_manipulation as cm

l = 6 # specify parameter of l-Bloc rule
k = 5 # specify number of winning candidates
non_manip = dp.get_nonmanipulative_votes(rankmaps, utilities) # removing manipulative votes from the rankmaps
candidates_to_approve, eval_value, candidates_winning, num_candidates_replaced = cm.consistent_manipulation(l, k, non_manip, utilities, mu.utilitarian)
```
For candidate-wise evaluation, ```python mu.utilitarian``` can be exchanged by ```python mu.candegal```.

The candidate map can be used to output the names of the candidates to support in a manipulation:
```python
names_to_approve = []
for cand in candidates_to_approve:
	names_to_approve.append(candmap[cand])
```

A result for a utilitarian manipulation (which doesn't require consistentcy) can be obtained as follows:
```python
from maniplib import manipulation_utils as mu
from maniplib import consistent_manipulation as cm

l = 6 # specify parameter of l-Bloc rule
k = 5 # specify number of winning candidates
non_manip = dp.get_nonmanipulative_votes(rankmaps, utilities) # removing manipulative votes from the rankmaps
candidates_to_approve, eval_value, candidates_winning, num_candidates_replaced = cm.consistent_manipulation(l, k, non_manip, utilities, mu.utilitarian)
```

Documentation available [here](https://kalkbrennerei.github.io/maniplib/).

## License
The code is copyright Lu Kalkbrenner 2020 under the [Apache License 2.0](LICENSE).
