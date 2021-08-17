import json
from functools import reduce
from math import copysign, sin

PRODUCT_DETAILS = json.load(open('data/product_details.json'))
BRANDS = json.load(open('data/brands.json'))

def get_all_product_names():
    return sorted(PRODUCT_DETAILS.keys())

def get_ingredients(product_name):
    global PRODUCT_DETAILS
    prod = PRODUCT_DETAILS.get(product_name, None)
    if prod is not None:
        ing = set()
        ing.update({x[0] for x in prod.get('Inactive ingredients', {})})
        ing.update({x[0] for x in prod.get('Active ingredients', {})})
        return ing
    return {}

def get_brand(product_name):
    global BRANDS
    for brand in BRANDS:
        if brand in product_name:
            return brand

def get_doc_freq(ingredient_sets):
    '''
    Args:
    ingredient_sets : list[set]
    
    Returns:
    dict[word] = freq
    '''
    freq = {}
    increment = 1/len(ingredient_sets) if ingredient_sets else 0
    for product in ingredient_sets:
        for ingr in product:
            freq[ingr] = freq.get(ingr, 0) + increment
    
    return freq

class Scorer():
    def __init__(self, impute_val=None):
        self.impute_val = impute_val
    
    def fit(self, bad_products, good_products=None):
        if good_products is None:
            good_products = []

        # Get ingredients
        bad_ingredients  = [get_ingredients(p) for p in bad_products]
        good_ingredients = [get_ingredients(p) for p in good_products]
        all_ingredients = reduce(lambda x,y : x|y, bad_ingredients + good_ingredients)        
        
        # Calculate frequency of ingredients per product group
        bad_df  = get_doc_freq(bad_ingredients)
        good_df = get_doc_freq(good_ingredients)
        
        # Score all ingredients
        scores = {}
        for ingr in all_ingredients:
            scores[ingr] = bad_df.get(ingr,0) - good_df.get(ingr,0)
        self.ingredient_scores_ = dict(sorted(scores.items(), key=lambda kv : (kv[1], -len(kv[0])), reverse=True))

        # Impute mean score to any unseen ingredients
        if self.impute_val is None:
            self.impute_val = sum(self.ingredient_scores_.values())/len(all_ingredients)
            #self.impute_val = median(self.scores_.values())

        # Score all products
        self.product_scores_ = {}
        scores = {p : self.score_product(p) for p in PRODUCT_DETAILS}
        self.product_scores_ = dict(sorted(scores.items(), key=lambda kv : kv[1], reverse=True))

        # Rank all unique ingredient scores
        self.ranked_scores_ = sorted(set(self.ingredient_scores_.values()), reverse=True)
        

        
        return self

    def score_ingredient(self, ingredient):
        return self.ingredient_scores_.get(ingredient, self.impute_val)

    def rank_ingredient(self, ingredient):
        rank = self.ranked_scores_.index(ingredient)
        return rank+1 if rank != -1 else -1

    def score_product(self, product):
        if product in self.product_scores_:
            return self.product_scores_[product]

        ingr = get_ingredients(product)
        if not ingr:
            score = self.impute_val
        else:
            f = lambda s : -copysign(1,s) * abs(s)**0.5
            #f = lambda s : -sin(s)
            scores = [f(self.score_ingredient(i)) for i in ingr]
            score = sum(scores)/len(scores)
        return score
        
    def filtered_scores(self, min_score = 0, max_n_scores=10):
        scores_filt = {}
        prev_rank = 0
        for ingr, score in self.ingredient_scores_.items():
            rank = self.rank_ingredient(score)
            
            score_pass = score >= min_score 
            rank_pass  = (rank == 1) or (rank == prev_rank)
            len_pass   = len(scores_filt) <= max_n_scores
            if score_pass and (rank_pass or len_pass):
                scores_filt[ingr] = (rank, score)
                prev_rank = rank
                
        # Trim off last rank if too many entries
        if len(scores_filt) > max_n_scores:
            scores_filt = {k:v for k,v in scores_filt.items() if v[0] < prev_rank}
        
        # Remove rank
        return {k:v[1] for k,v in scores_filt.items()}