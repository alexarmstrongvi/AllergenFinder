import json
from functools import reduce
from collections import defaultdict, namedtuple

PRODUCT_DETAILS = json.load(open('data/product_details.json'))

def find_potential_allergens(bad_products, good_products=None):
    bad_ingredients = [get_ingredients(p) for p in bad_products]
    good_ingredients = [get_ingredients(p) for p in good_products]
    scores = score_ingredients(bad_ingredients, good_ingredients)
    return scores

def get_ingredients(product_name):
    prod = PRODUCT_DETAILS.get(product_name, None)
    if prod is None:
        return {}
    ing = set()
    ing.update({x[0] for x in prod.get('Inactive ingredients', [])})
    ing.update({x[0] for x in prod.get('Active ingredients', [])})
    return ing
    
    
def score_ingredients(bad_ingredients, good_ingredients):
    bad_df = product_frequency(bad_ingredients)
    good_df = product_frequency(good_ingredients)
    print("DEBUG :: bad:", bad_ingredients)
    print("DEBUG :: good:", good_ingredients)
    all_ingredients = reduce(lambda x,y : x|y, bad_ingredients + good_ingredients)
    
    scores = {ingr : 100*(bad_df[ingr] - good_df[ingr]) for ingr in all_ingredients}
    
    # Sort by score and group scores to assign rank
    rank = sorted(set(scores.values()), reverse=True)
    scores2 = {}
    for ingr, score in sorted(scores.items(), key=lambda kv : -kv[1]):
        scores2[ingr] = (rank.index(score)+1, score)
    return scores2

def product_frequency(ingredient_sets):
    '''
    Args:
    ingredient_sets : list[set]
    
    Returns:
    defaultdict[word] = freq
    '''
    freq = defaultdict(float)

    increment = 1/len(ingredient_sets) if ingredient_sets else 0
    for product in ingredient_sets:
        for ingredient in product:
            freq[ingredient] += increment
    
    return freq

def filter_scores(scores, min_score = 0, max_n_scores=10):
    scores_filt = {}
    prev_rank = 0
    for ingr, (rank, score) in scores.items():
        if (score >= min_score 
            and (rank == 1 
                 or len(scores_filt) <= max_n_scores 
                 or rank == prev_rank)
           ):
            scores_filt[ingr] = (rank, score)
            prev_rank = rank
    if len(scores_filt) > max_n_scores:
        scores_filt = {k:v for k,v in scores_filt.items() if v[0] < prev_rank}
    return scores_filt