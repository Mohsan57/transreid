import requests

url = "https://send.api.mailtrap.io/api/send"

payload = "{\"from\":{\"email\":\"mailtrap@ec2-3-81-224-99.compute-1.amazonaws.com\",\"name\":\"Mailtrap Test\"},\"to\":[{\"email\":\"campus.surveillance.system@gmail.com\"}],\"subject\":\"You are awesome!\",\"text\":\"Congrats for sending test email with Mailtrap!\",\"category\":\"Integration Test\"}"
headers = {
  "Authorization": "Bearer 445cf04fa3293fc3a84730d44d8cad0f",
  "Content-Type": "application/json"
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)