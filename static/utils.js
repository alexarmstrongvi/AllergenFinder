function createAttribute(name, value) {
    att = document.createAttribute(name);
    att.value = value;
    return att;  
}

function addProdField(prod_type){
    container = document.getElementById(prod_type);
    n_prod = container.children.length
    
    text_input = document.createElement('input');
    text_input.setAttributeNode(createAttribute('list'       , 'products'));
    text_input.setAttributeNode(createAttribute('name'       , prod_type));
    text_input.setAttributeNode(createAttribute('id'         , prod_type + '_' + (n_prod+1)));
    text_input.setAttributeNode(createAttribute('placeholder', 'Product'));
    
    form_row = document.createElement("div");
    form_row.className = "form-row mb-1";
    form_row.appendChild(text_input);
    
    container.appendChild(form_row);
}

// function update_ing_score_plot(data) {
//     Plotly.newPlot('ingredient_score_plot', data, config={responsive : true});
// }

// function cb(products) {
//     $.getJSON({
//         url  : '/callback',
//         data : {'data' : products},
//         success : function(result) {
//             Plotly.newPlot('ingredient_score_plot', result, config={responsive : true});
//             //update_ingredient_score_plot(result);
//         }
//     });
// }