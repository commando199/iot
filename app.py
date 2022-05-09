import requests
from flask import Flask, render_template, request
from Product import Store

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def order():
    productList = Store()
    if request.method == 'POST':
        item = request.form['pizza_name']
        quantity = int(request.form['quantity'])
        price = productList.getPrize(item)
        amount = price * quantity
        print(amount)

        # Create a new resource
        # REPLACE WITH YOUR SERVER HERE
        response = requests.post(
            'https://siddhix.bpmcep.ics.unisg.ch/engine-rest/process-definition/key/payment-retrieval/start',
            json={
                "variables": {
                    "amount": {
                        "value": amount,
                        "type": "long"
                    },
                    "item": {
                        "value": item,
                        "type": "string"
                    }
                }
            })

        print(response.content)
        if response.status_code == 200:
            jsonResponse = response.json()
            instanceID = jsonResponse.get("id")
        else:
            instanceID = "null"

        return render_template('response.html', item=item, amount=amount, quantity=quantity,code=response.status_code, instanceID=instanceID,message=response.content)
    return render_template('order.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
