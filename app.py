from flask import (
    Flask, 
    render_template,
    url_for,
    redirect,
    request,
)
import utils
import plotly.graph_objects as go
################################################################################
# Configure
################################################################################
app = Flask(__name__, instance_relative_config=True)

################################################################################
# Views
################################################################################
@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    return render_template('index.html', all_products=utils.get_all_product_names())

@app.route('/results', methods=['GET', 'POST'])
def results():
    if request.method == 'GET':
        redirect(url_for('index'))
    
    bad_prods  = {x for x in request.form.getlist('bad_prods')  if x and x in utils.PRODUCT_DETAILS}
    good_prods = {x for x in request.form.getlist('good_prods') if x and x in utils.PRODUCT_DETAILS}
    consider_prods = {x for x in request.form.getlist('consider_prods') if x and x in utils.PRODUCT_DETAILS}
    
    scorer = utils.Scorer().fit(bad_prods, good_prods)
    n_ingred = len(scorer.ingredient_scores_)
    
    ingr_scores = scorer.filtered_scores(min_score=0, max_n_scores=100)
    ingr_scores = {ingr : (scorer.rank_ingredient(s), int(round(s*100))) for ingr, s in ingr_scores.items()}
    #HACK while most ingredients are meaningless
    ingr_scores = {k:v for i, (k,v) in enumerate(ingr_scores.items()) if i < 5}

    prod_scores = {p : scorer.score_product(p) for p in consider_prods}
    prod_scores = dict(sorted(prod_scores.items(), key=lambda kv:-kv[1]))
    
    top_n = 5 # Recommend top n ingredients
    seen_brands = set()
    
    rec_prods = {}
    for p, s in scorer.product_scores_.items():
        brand = utils.get_brand(p)
        if p in consider_prods or brand in seen_brands:
            continue
        if len(rec_prods) >= top_n:
            break
        seen_brands.add(brand)
        rec_prods[p] = s

    return render_template('results.html', 
        bad_prods   = bad_prods, 
        good_prods  = good_prods,
        n_ingred    = n_ingred,
        scores      = ingr_scores,
        prod_scores = prod_scores,
        rec_prods   = rec_prods,
    )

@app.route('/under-the-hood', methods=['GET', 'POST'])
def under_the_hood():
    if request.method == 'GET':
        # defaults
        bad_prods = {
            'Banana Boat Ultra Sport Sunscreen Lotion - 8 fl oz',
            'Coppertone Pure & Simple Sunscreen Lotion - SPF 50 - 6 fl oz',
            'Sport Sunscreen Lotion - SPF 30 - 3oz - up & up™',
            'Cetaphil Sheer Mineral Sunscreen - SPF 50 - 3 fl oz'
        } 
        good_prods = {
            'Neutrogena Sensitive Skin Sunscreen Broad Spectrum - SPF 60+ - 3 fl oz',
            'La Roche-Posay Anthelios Melt in Milk Sunscreen Lotion - SPF 100 - 3.0 fl oz',
            'Sun Bum Original Sunscreen Lotion',
            'CeraVe Hydrating Sunscreen Body Lotion - SPF 50 - 5 fl oz',
        }
    if request.method == 'POST':
        bad_prods  = {x for x in request.form.getlist('bad_prods')  if x}
        good_prods = {x for x in request.form.getlist('good_prods') if x}

    scorer = utils.Scorer().fit(bad_prods, good_prods)
    fig_ingred_score = utils.plot_ingredient_scores(scorer)
    fig_product_score = utils.plot_product_scores(scorer)
    fig_top_ingred_scores = utils.plot_top_product_ingredient_scores(scorer)

    return render_template('under_the_hood.html',
        all_products = utils.get_all_product_names(),
        good_prods = good_prods,
        bad_prods = bad_prods,
        IngredientScoreGraphJSON     = utils.to_plotly_json(fig_ingred_score),
        ProductScoreGraphJSON        = utils.to_plotly_json(fig_product_score),
        TopProdIngredScoreGraphJSON  = utils.to_plotly_json(fig_top_ingred_scores))

@app.route('/about-me')
def about_me():
    return render_template('about_me.html')

# @app.route('/callback', methods=['GET', 'POST'])
# def callback():
#     data = request.args.get('data')
#     print(data)
#     fig = utils.plot_ingredient_scores()
#     return utils.to_plotly_json(fig)