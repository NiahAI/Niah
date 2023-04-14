import openai
import os
from twilio.rest import Client
import json
import airtable
from airtable import Airtable
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
client = Client()

# set up Airtable API
AIRTABLE_API_KEY = os.environ.get('key7eNQstIOkZ2A2h')
base_key = os.environ.get('AIRTABLE_BASE_KEY')
symptoms_table = Airtable(base_key, 'Symptoms', api_key=AIRTABLE_API_KEY)

# set up OpenAI API
openai.api_key = os.environ.get('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')

# set up Twilio API
TWILIO_ACCOUNT_SID = os.environ.get('SK040235c9391a07d93f134115ca56638e')
TWILIO_AUTH_TOKEN = os.environ.get('Ddvk46PNlLYAI9SzldxHYpxt9JOlMv16')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# create function to get symptom data from Airtable
def get_symptom_info(symptom):
    records = symptoms_table.search('Name', symptom)
    if len(records) > 0:
        description = records[0]['fields']['Description']
        causes = records[0]['fields']['Possible Causes']
        treatments = records[0]['fields']['Treatments']
        return {'description': description, 'causes': causes, 'treatments': treatments}
    else:
        return None

# create function to get GPT-3 response
def get_gpt_response(message):
    prompt = f"Symptom checker: {message}"
    response = openai.Completion.create(
      engine="text-davinci-002",
      prompt=prompt,
      temperature=0.7,
      max_tokens=1024,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    return response.choices[0].text.strip()

# create function to send response to user via WhatsApp
def send_whatsapp_message(to, body):
    message = client.messages.create(
        body=body,
        from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
        to=f'whatsapp:{to}'
    )
    return message.sid

# create route to receive WhatsApp messages
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").lower()
    resp = MessagingResponse()
    response_text = ""

    # get symptom information from Airtable
    symptom_info = get_symptom_info(incoming_msg)

    if symptom_info is not None:
        # if symptom is found, return symptom information
        response_text = f"{symptom_info['description']}\n\nPossible causes:\n{symptom_info['causes']}\n\nTreatments:\n{symptom_info['treatments']}"
    else:
        # if symptom is not found, use GPT-3 to generate response
        gpt_response = get_gpt_response(incoming_msg)
        response_text = gpt_response

    # send response to user via WhatsApp
    send_whatsapp_message(request.values.get("From"), response_text)

    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
