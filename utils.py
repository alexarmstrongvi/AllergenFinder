import json
from functools import reduce
from plotly import graph_objects as go
from plotly.utils import PlotlyJSONEncoder

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
        self.bad_products_ = bad_products
        self.good_products_ = good_products

        # Get ingredients
        bad_ingredients  = [get_ingredients(p) for p in bad_products]
        good_ingredients = [get_ingredients(p) for p in good_products]
        all_ingredients = reduce(lambda x,y : x|y, bad_ingredients + good_ingredients)        
        
        # Calculate frequency of ingredients per product group
        bad_df  = get_doc_freq(bad_ingredients)
        good_df = get_doc_freq(good_ingredients)
        
        # Score all ingredients
        scores = {}
        weights = {}
        for ingr in all_ingredients:
            scores[ingr] = bad_df.get(ingr,0) - good_df.get(ingr,0)
            weights[ingr] = scores[ingr]
        self.ingredient_scores_ = dict(sorted(scores.items(), key=lambda kv : (kv[1], -len(kv[0])), reverse=True))

        # Impute mean score to any unseen ingredients
        if self.impute_val is None:
            self.impute_val = sum(self.ingredient_scores_.values())/len(all_ingredients)
            #self.impute_val = median(self.scores_.values())


        # Score all products
        self.weights_ = {}
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
            return self.impute_val
        scores = list(map(self.score_ingredient, ingr))
        if not any(scores):
            return  self.impute_val
            
        weight_f = lambda score: abs(score)**2 if score > 0 else 0.5 * abs(score)**2
        weights = list(map(weight_f, scores))
        weighted_mean = sum(w*s for w,s in zip(weights, scores))/sum(weights)
        return weighted_mean
        
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

def to_plotly_json(figure):
    return json.dumps(figure, cls=PlotlyJSONEncoder) if figure else None

def ingredient_score_binwidth(scorer):
    uniq = sorted(set(scorer.ingredient_scores_.values()))
    binwidth = min(uniq[i+1]-uniq[i] for i in range(len(uniq)-1))

def plot_ingredient_scores(scorer):    
    scores = list(scorer.ingredient_scores_.values())
    uniq = sorted(set(scores))
    binwidth = min(uniq[i+1]-uniq[i] for i in range(len(uniq)-1))
    data = go.Histogram(
        x = scores, 
        xbins_size  = binwidth,
        xbins_start = -1 - binwidth/2,
        xbins_end   =  1 + binwidth/2,
        autobinx = False)
    
    fig  = go.Figure(data=data)
    n_prods = len(scorer.bad_products_ | scorer.good_products_)
    tickvals = sorted(set(uniq + [-1, 0, 1]))
    fig.update_layout(
        title_text  = f'Scores for {len(scores)} ingredients over {n_prods} products', 
        xaxis_title = "Ingredient Score",
        yaxis_title = "Ingredient Count",
        xaxis_tickmode = 'array',
        xaxis_tickvals = tickvals,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        bargap=0.1,
    )
    fig.update_xaxes(range=(-1 - binwidth/2,1 + binwidth/2))
    return fig

def plot_product_scores(scorer):
    scores = list(scorer.product_scores_.values())
    data = go.Histogram(x=scores)
    fig  = go.Figure(data=data)
    fig.update_layout(
        title_text  = f'Scores for {len(scores)} products', 
        xaxis_title = "Product Score",
        yaxis_title = "Product Count",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        bargap=0.05,
    )
    fig.update_xaxes(range=(-1,1))
    return fig

def plot_top_product_ingredient_scores(scorer):
    scores = list(scorer.ingredient_scores_.values())
    uniq = sorted(set(scores))
    binwidth = min(uniq[i+1]-uniq[i] for i in range(len(uniq)-1))
    bins = dict(
        size  = binwidth,
        start = uniq[0]  - binwidth/2, 
        end   = uniq[-1] + binwidth/2, 
    )

    prod_scores = sorted(scorer.product_scores_.items(), key=lambda kv : kv[1], reverse=True)
    scores = [v for _, v in prod_scores]
    fig  = go.Figure()

    #for order, (prod, score) in enumerate(prod_scores[:topn]+prod_scores[-topn:]):
    for order in [0, 1, len(prod_scores)-2, len(prod_scores)-1]:
        prod, score = prod_scores[order]
        name = f'({order+1}) {score:+.3f} - {prod}' 
        x = list(map(scorer.score_ingredient, get_ingredients(prod)))
        fig.add_histogram(name = name, x=x, xbins=bins, autobinx=False)

    fig.update_layout(
        title_text  = f'Ingredient scores for top 2 and bottom 2 scoring products',
        title_y = 1,
        xaxis_title = "Ingredient Score",
        yaxis_title = "Ingredient Count",
        legend_yanchor='top',
        legend_xanchor='left',
        legend_y = 1.4,
        legend_x = 0,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        bargap=0.1,
    )
    fig.update_xaxes(range=(-1-binwidth/2,1+binwidth/2))
    return fig