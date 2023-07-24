# Online Python compiler (interpreter) to run Python online.
# Write Python 3 code in this online
import requests
import json

# M-Pesa API base URL
base_url = 'https://sandbox.safaricom.co.ke/mpesa/'

# M-Pesa API endpoints
oauth_endpoint = 'oauth/v1/generate?grant_type=client_credentials'
lipa_na_mpesa_online_passkey = 'your_passkey'
lipa_na_mpesa_online_shortcode = 'your_shortcode'
b2c_endpoint = 'b2c/v1/paym entrequest'

# Generate OAuth access token
consumer_key = 'your_consumer_key'
consumer_secret = 'your_consumer_secret'
api_credentials = consumer_key + ':' + consumer_secret
import base64

encoded_credentials = base64.b64encode(api_credentials.encode()).decode('utf-8')
headers = {
    'Authorization': 'Basic ' + encoded_credentials,
    'Content-Type': 'application/json'
}
response = requests.get(base_url + oauth_endpoint, headers=headers)
access_token = json.loads(response.text)['access_token']

# Perform B2C transaction
phone_number = 'your_phone_number'
amount = '100'  # Amount to transfer
command_id = 'BusinessPayment'
remarks = 'Test transfer'
queue_timeout_url = 'http://example.com/timeout'
result_url = 'http://example.com/result'

payload = {
    'InitiatorName': 'your_initiator_name',
    'SecurityCredential': 'your_security_credential',
    'CommandID': command_id,
    'Amount': amount,
    'PartyA': lipa_na_mpesa_online_shortcode,
    'PartyB': phone_number,
    'Remarks': remarks,
    'QueueTimeOutURL': queue_timeout_url,
    'ResultURL': result_url
}

headers = {
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache'
}

response = requests.post(base_url + b2c_endpoint, json=payload, headers=headers)
print(response.text)