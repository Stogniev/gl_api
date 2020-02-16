from pymongo import MongoClient

client = MongoClient("31.202.13.146", 27017)      #('localhost', 27017)
db = client["gl-cluster"]                         #['blockchain_db']


col_blocks = db['blocks']
col_addresses = db['addresses']
col_clusters = db['clusters']


def get_recieved_tx(address):

    outputs = col_blocks.find({"tx.out.addr": address}, {"tx.$": 1, "_id": 0})
    #need to return as array of tx
    recieved_array = []
    for doc in outputs:
        for tx in doc["tx"]:
            recieved_array.append(tx)

    return recieved_array

def get_sent_tx(address):
    inputs = col_blocks.find({"tx.inputs.prev_out.addr": address}, {"tx.$": 1, "_id": 0})
    # need to return as array of tx
    recieved_array = []
    for doc in inputs:
        for tx in doc["tx"]:
            recieved_array.append(tx)

    return recieved_array

def get_addr_cluster_info(address):

    addr_cluster_info = {"Address": address, "Cluster":"", "Type":"", "Risk":False, "Entity":"Unknown"}

    addr_clustr = col_addresses.find_one({"address": address})
    if addr_clustr != None:
        cluster_data = col_clusters.find_one({"cluster": addr_clustr["cluster"]})
        if cluster_data != None:
            addr_cluster_info["Cluster"] = cluster_data["cluster"]
            addr_cluster_info["Type"] = cluster_data["type"]
            addr_cluster_info["Entity"] = cluster_data["entity"]
            addr_cluster_info["Risk"] = cluster_data["risk"]
            #load it into json or dict

    return  addr_cluster_info

def calculate_sent(sent_array, test_addr):
    sent_amount = 0
    for sent_tx in sent_array:
        for inpt in sent_tx["inputs"]:
            if test_addr == inpt["prev_out"]["addr"]:
                sent_amount = sent_amount + inpt["prev_out"]["value"]

    return sent_amount

def calculate_recieved(recieved_array, test_addr):
    recieved_amount = 0
    for rcvd_tx in recieved_array:
        for outpt in rcvd_tx["out"]:
            if "addr" in outpt:
                if test_addr == outpt["addr"]:
                    recieved_amount = recieved_amount + outpt["value"]

    return recieved_amount

def unique_txs(sent, recieved):
    unique_tx_arr = []
    for s in sent:
        if s not in unique_tx_arr:
            unique_tx_arr.append(s)

    for r in recieved:
        if r not in unique_tx_arr:
            unique_tx_arr.append(r)

    return unique_tx_arr

#-------------------------------------------------------------------------------------------

def addr_responce(addr):

    test_addr = addr
    api_responce = {"Address": "",
                    "Wallet": "",
                    "Entity": "",
                    "Balance": "",
                    "Number of transactions": "",
                    "Sent": "",
                    "Recieved": "",
                    }

    addr_info = get_addr_cluster_info(test_addr)

    api_responce["Address"] = addr_info["Address"]
    api_responce["Wallet"] = addr_info["Cluster"]
    api_responce["Entity"] = addr_info["Entity"]

    sent = get_sent_tx(test_addr)
    rcvd = get_recieved_tx(test_addr)
    all_tx = unique_txs(sent, rcvd)

    api_responce["Sent"] = calculate_sent(sent, test_addr)
    api_responce["Recieved"] = calculate_recieved(rcvd, test_addr)

    api_responce["Balance"] = api_responce["Recieved"] - api_responce["Sent"]

    api_responce["Number of transactions"] = len(all_tx)

    return api_responce


