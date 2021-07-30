from flask import (
    Flask, 
    render_template,
    url_for,
    redirect,
    request,
)
import utils
# from utils import (
#     find_potential_allergens,
#     filter_scores,
# )
import random
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
    return render_template('index.html')

@app.route('/results', methods=['GET', 'POST'])
def results():
    if request.method == 'GET':
        redirect(url_for('index'))
    
    bad_prods  = {x for x in request.form.getlist('bad_prods')  if x}
    good_prods = {x for x in request.form.getlist('good_prods') if x}
    consider_prods = {x for x in request.form.getlist('consider_prods') if x}
    
    scores = utils.find_potential_allergens(bad_prods, good_prods)
    n_ingred = len(scores)
    scores = utils.filter_scores(scores, min_score=0, max_n_scores=15)
    #rec_prods = recommend_products(scores)
    #prod_scores = score_products(scores, consider_prods)
    rec_prods = [
        ("Coola Classic Sunscreen Lotion - Guava Mango - SPF 50 - 5 fl oz", 0.95),
        ("DERMA E Sun Defense Mineral Body Sunscreen - SPF 30 - 4oz", 0.87),
    ]
    prod_scores = [(prod, 0.1+0.5*random.random()) for prod in consider_prods]
    prod_scores = sorted(prod_scores, key=lambda x : x[1])

    return render_template('results.html', 
        bad_prods=bad_prods, 
        good_prods=good_prods,
        n_ingred=n_ingred,
        scores=scores,
        rec_prods=rec_prods,
        prod_scores=prod_scores
    )
