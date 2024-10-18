import requests
import time
from web3 import Web3
import config

# Use configuration values
etherscan_api_key = config.ETHERSCAN_API_KEY
infura_url = config.INFURA_URL
private_key = config.PRIVATE_KEY
uniswap_pool_address = config.UNISWAP_POOL_ADDRESS

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(INFURA_URL))
account = web3.eth.account.from_key(PRIVATE_KEY)
address = account.address

def monitor_mempool():
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={UNISWAP_POOL_ADDRESS}&startblock=0&endblock=99999999&sort=asc&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    return response.json()['result']

def identify_large_orders():
    url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    query = """
    {
      swaps(first: 10, orderBy: amountUSD, orderDirection: desc) {
        id
        pair {
          token0 { symbol }
          token1 { symbol }
        }
        amountUSD
      }
    }
    """
    response = requests.post(url, json={'query': query})
    return response.json()['data']['swaps']

def place_transaction(to_address, value, gas_price):
    tx = {
        'nonce': web3.eth.getTransactionCount(address),
        'to': to_address,
        'value': value,
        'gas': 2000000,
        'gasPrice': gas_price,
    }
    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    return web3.toHex(tx_hash)

def limit_trade_size(amount):
    max_trade_size = config.MAX_TRADE_SIZE * 10**18 
    return min(amount, max_trade_size)

def main():
    while True:
        try:
            # Monitor mempool
            pending_transactions = monitor_mempool()
            for tx in pending_transactions:
                print(f"Pending Transaction: {tx['hash']}, Value: {int(tx['value']) / 10**18} ETH, Gas Price: {tx['gasPrice']}")

            # Identify large orders
            large_orders = identify_large_orders()
            for order in large_orders:
                print(f"Large Order: {order['id']}, Token Pair: {order['pair']['token0']['symbol']}/{order['pair']['token1']['symbol']}, Value: {order['amountUSD']} USD")

                # If a large order is found, place a  transaction
                if float(order['amountUSD']) > config.LARGE_ORDER_THRESHOLD:
                    to_address = UNISWAP_POOL_ADDRESS
                    value = limit_trade_size(web3.toWei(1, 'ether'))  # Example value
                    gas_price = web3.toWei(str(config.GAS_PRICE), 'gwei')  # Higher gas price for 

                    tx_hash = place_transaction(to_address, value, gas_price)
                    print(f"Placed  transaction: {tx_hash}")

            time.sleep(10)  # Wait for 10 seconds before next iteration
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(30)  # Wait longer if an error occurs

if __name__ == "__main__":
    main()
