import requests
import json
from pymongo import MongoClient
import address_responce as addr_resp

client = MongoClient("31.202.13.146", 27017)      #('localhost', 27017)
db = client["gl-cluster"]                         #['blockchain_db']

col_blocks = db['blocks']
col_addresses = db['addresses']
col_clusters = db['clusters']

def raw_address_tx_count(address):
    #it will be two tx if address sent change to himself
    raw_tx_count = col_blocks.count_documents({"tx.out.addr":address}) + col_blocks.count_documents({"tx.inputs.prev_out.addr": address})

    return raw_tx_count

def cluster_addresses_count(cluster):
    addr_count = col_addresses.count_documents({"cluster":cluster})
    return addr_count

def get_addr_cluster_info(address):

    addr_cluster_info = {"Cluster":"", "Type":"", "Risk":False, "Entity":"Unknown"}

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

def check_tx(txid):
    tx_req = "https://blkhub.net/api/tx/"
    tx = json.loads(requests.get(tx_req + txid).text)
    return tx

def get_prev_tx(tx):
    prev_tx_inputs = []
    #txid, scriptpubkey_address, value
    for prev_in in tx["vin"]:
        #print(prev_in)

        if prev_in["is_coinbase"] == True:

            input = {"from": "Newly generated coins"}
            prev_tx_inputs.append(input)
            continue

        if "scriptpubkey_address" in prev_in["prevout"]:
            input = {"txid":prev_in["txid"], "from": prev_in["prevout"]["scriptpubkey_address"], "value":prev_in["prevout"]["value"]}
            prev_tx_inputs.append(input)

    return prev_tx_inputs


def tx_back_check(tx_id):
    # params
    max_addr_tx = 50
    max_cluster_addresses = 10

    new_tx_ids = []
    checked_inputs = []
    checked_addresses = []
    known_entities = []
    risky_sources = []
    stop_clusters = []
    initial_inputs = []
    depth = 0

    txid = tx_id

    new_tx_ids.append(txid)

    while True:

        print("Depth: " + str(depth))
        print(new_tx_ids)
        if depth == 20:
            print(checked_inputs)
            break
        if new_tx_ids == []:
            print(checked_inputs)
            break

        tx_ids = new_tx_ids
        new_tx_ids = []

        for id in tx_ids:
            tx_data = check_tx(id)

            #get initial inputs

            #print(tx_data)
            if depth == 0:
                for t in tx_data["vin"]:
                    if "prevout" != None:
                        in_address = t["prevout"]["scriptpubkey_address"]
                        in_inpt = addr_resp.addr_responce(in_address)
                        if in_inpt not in initial_inputs:
                            initial_inputs.append(in_inpt)

            #get previous txs

            prev_tx_inputs = get_prev_tx(tx_data)
            #print(prev_tx_inputs)

            #new_tx_ids.remove(id)

            for p in prev_tx_inputs:
                if p not in checked_inputs:

                    if p["from"] == "Newly generated coins":

                        p["info"] = {}
                        p["info"]["Entity"] = p["from"]
                        known_entities.append(p)
                        checked_inputs.append(p)
                        continue

                    addr = p["from"]

                    p["info"] = (get_addr_cluster_info(addr))
                    checked_inputs.append(p)
                    #print(p)

                    if addr not in checked_addresses:
                        checked_addresses.append(addr)

                        if p["info"]["Risk"] == True:
                            risky_sources.append(p)

                        if p["info"]["Entity"] != "Unknown" and p["info"]["Entity"] != '':
                            known_entities.append(p)
                            continue


                        if raw_address_tx_count(addr) < max_addr_tx:
                            if p["info"]["Cluster"] in stop_clusters:
                                # effectively, if input cluster if big, dont add it to new addresses
                                continue

                        if cluster_addresses_count(p["info"]["Cluster"]) > max_cluster_addresses:
                            stop_clusters.append(p["info"]["Cluster"])
                            continue

                        new_tx_ids.append(p["txid"])

        depth = depth + 1

    risk_bool = False
    if len(risky_sources)>0:
        risk_bool = True

    return {"Original tx": txid, "Risk Identified": risk_bool, "Initial Inputs": initial_inputs, "Risky sources": risky_sources, "Known sources": known_entities, "Checked inputs":checked_inputs}

