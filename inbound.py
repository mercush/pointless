import os
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
import sys 
import backend
from twilio.rest import Client
import csv

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]

client = Client(account_sid, auth_token)

app = Flask(__name__)

@app.route("/sms", methods=['GET', 'POST'])
def sms():
    if backend.SIGN_IN:
        backend.USERS[request.form['From']] = request.form['Body']
        backend.POINTS[request.form['From']] = 0
        resp = MessagingResponse()
        resp.message("Thank you for signing up for Pointless, {}.".format(request.form['Body']))
    else:
        backend.USER_ANSWERS[request.form['From']] = request.form['Body']
        if request.form['Body'] in backend.ANSWERS:
            backend.ANSWERS[request.form['Body']] += 1
        else:
            backend.ANSWERS[request.form['Body']] = 1
        resp = MessagingResponse()
        resp.message("Your answer has been recorded. If you want to change it, just send another text before the time runs out.")
    return str(resp)

@app.route("/start_signin", methods=['POST'])
def sign_in():
    backend.SIGN_IN = True
    return "SIGN_IN set to True\n"

@app.route("/start_question/<int:question_number>", methods=['POST'])
def question_start(question_number):
    backend.SIGN_IN = False
    backend.ANSWER_INTERVAL = True
    for number in backend.USERS.keys():
        client.messages.create(
            to=number,
            from_="+16572543034",
            body="Question {} has started. You have 100 seconds to give an answer".format(question_number)
        )
    return ""
@app.route("/end_question", methods=['POST'])
def question_end():
    backend.ANSWER_INTERVAL = False
    for number in backend.USERS.keys():
        client.messages.create(
            to=number,
            from_="+16572543034",
            body="Time's up!"
        )
    for user in backend.USER_ANSWERS:
        if user in backend.POINTS:
            backend.POINTS[user] += backend.ANSWERS[backend.USER_ANSWERS[user]]
    with open('answers.csv','w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for answer in backend.ANSWERS:
            writer.writerow([answer, backend.ANSWERS[answer]])
    with open('points.csv','w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for user in backend.POINTS:
            writer.writerow([backend.USERS[user], backend.POINTS[user]])
    return ""
if __name__ == "__main__":
    app.run(debug=True)