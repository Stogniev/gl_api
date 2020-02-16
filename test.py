from bottle import request, response, route
from bottle import post, get, put, delete, run
import tx_check_depth_clusters as checktx
from json import dumps


@get('/tx/<tx_id>', METHOD = "GET")
def check_tx(tx_id):
    tx = tx_id
    rv = checktx.tx_back_check(tx)
    response.content_type = 'application/json'
    return dumps(rv)

run(host='localhost', port=8080, debug=True)

#http://localhost:8080/tx/6ea54877fe2fe0f1a5a7c2f368a85ac03833413b45b7005d9cb8365cdf9fe0ac