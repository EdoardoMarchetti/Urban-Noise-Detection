#Replicate the coinbase.http in python language
import requests
import argparse as ap


parser = ap.ArgumentParser()
parser.add_argument(
    '--currency',
    type=str,
    help='Currency code.',
    default='EUR'
)

args = parser.parse_args()

host = 'https://api.coinbase.com/v2'
currency = args.currency

buy_endpoint = f'/prices/BTC-{currency}/buy'
sell_endpoint = f'/prices/BTC-{currency}/sell'

#Get request
response = requests.get(host+buy_endpoint) #equivalent of 
                                           #GET {{host}}/prices/BTC-EUR/buy 
                                           #in http
#Check repsonse status
code = response.status_code
print(f'Status code: {code}')
if response.status_code == 200:
    buy_dict = response.json()
    buy_price = buy_dict['data']['amount']
    print(f'Buy price in {currency} is: {buy_price}')
elif response.status_code == 400:
    print(f'ERROR: {currency} is invalid') 