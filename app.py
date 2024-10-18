import time
import requests
from web3 import Web3
import config

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(config.INFURA_URL))
account = web3.eth.account.from_key(config.PRIVATE_KEY)
address = account.address

def monitor_mempool():
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={config.UNISWAP_POOL_ADDRESS}&startblock=0&endblock=99999999&sort=asc&apikey={config.ETHERSCAN_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('result', [])
    else:
        print(f"Error fetching mempool data: {response.status_code}")
        return []

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
    if response.status_code == 200:
        return response.json().get('data', {}).get('swaps', [])
    else:
        print(f"Error fetching large orders: {response.status_code}")
        return []

def place_transaction(to_address, value):
    tx = {
        'nonce': web3.eth.get_transaction_count(address),
        'to': to_address,
        'value': value,
        'gas': 2000000,
        'gasPrice': web3.to_wei(config.GAS_PRICE, 'gwei'),
    }
    signed_tx = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return web3.to_hex(tx_hash)

def limit_trade_size(amount):
    max_trade_size = web3.to_wei(config.MAX_TRADE_SIZE, 'ether')
    return min(amount, max_trade_size)

def main():
    print("Starting  bot...")
    while True:
        try:
            # Monitor mempool
            pending_transactions = monitor_mempool()
            for tx in pending_transactions:
                print(f"Pending Transaction: {tx['hash']}, Value: {web3.from_wei(int(tx['value']), 'ether')} ETH, Gas Price: {web3.from_wei(int(tx['gasPrice']), 'gwei')} Gwei")

            # Identify large orders
            large_orders = identify_large_orders()
            for order in large_orders:
                print(f"Large Order: {order['id']}, Token Pair: {order['pair']['token0']['symbol']}/{order['pair']['token1']['symbol']}, Value: {order['amountUSD']} USD")

                # If a large order is found, place a  transaction
                if float(order['amountUSD']) > config.LARGE_ORDER_THRESHOLD:
                    to_address = config.UNISWAP_POOL_ADDRESS
                    value = limit_trade_size(web3.to_wei(1, 'ether'))  # Example value

                    tx_hash = place_transaction(to_address, value)
                    print(f"Placed  transaction: {tx_hash}")

            time.sleep(10)  # Wait for 10 seconds before next iteration
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(30)  # Wait longer if an error occurs

if __name__ == "__main__":
    main()
