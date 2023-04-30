from flask import Flask, jsonify, render_template, request, redirect, url_for, Response
from datahandler import PersistentDataHandler
from structures import Company, Player
import mimetypes
app = Flask(__name__)

handler = PersistentDataHandler("somefile.json")

# Initialize company data - FOR 14 Companies = 14 Sponsors
import random
[handler.add_company(f"Company {i}", '/static/logos/bitmato100.png' , random.randint(0, 5000), random.randint(0, 2500)) for i in range(0, 14)]

@app.route('/') #authored by: @pshroff 
def index():
    user_id = request.cookies.get("user_id", None)
    player = handler.get_player(user_id)
    sorted_companies = sorted(handler.data[0].values(), key=lambda x: x.value, reverse=True)

    # Calculate the total value of shares for each holding
    holdings_with_value = []
    
    if player:
        for company_name, shares in player.holdings.items():
            company = handler.get_company(company_name)
            total_value = shares * company.value
            holdings_with_value.append((company_name, shares, total_value))

    return render_template('index.html', companies=sorted_companies, player=player.dict() if player else Player("None", 0, 0), holdings_with_value=holdings_with_value)

def update_vote_count(company_name):
    # Find the company with the matching name
    company = handler.get_company(company_name)
    if company:
        # Increment the vote count for the company
        company.clicks += 1
        # Return the updated vote count
        return company.clicks
    return None

@app.route('/static/<static_type>/<filename>')
def get_static(static_type:str, filename:str):
    print(f"static/{static_type}/{filename}")
    with open(f"./static/{static_type}/{filename}", 'rb') as reader:
        data = reader.read()
    
    mimeType = mimetypes.guess_type(filename)[0]
    
    return Response(data, 200, mimetype=mimeType)

@app.route("/login/<wallet>", methods=["POST"])
def login(wallet:str):
    handler.create_player(wallet)
    return "SUCCESS!"

@app.route("/player/<wallet>")
def get_player(wallet:str):
    ply = handler.get_player(wallet)
    return jsonify(ply.dict())

@app.route('/vote', methods=['POST']) #authored by: @pshroff 
def vote():
    company_name = request.form['company']
    # Update the vote count for the company
    updated_vote_count = update_vote_count(company_name)
    if updated_vote_count is not None:
        return jsonify({'vote_count': updated_vote_count})
    else:
        return jsonify({'error': 'Company not found'}), 404

@app.route('/gamestate')
def getGameState():
    return jsonify(
            {name: c.dict() for name, c in handler.data[0].items()}
        )

@app.route('/trade/<player_id>/<mode>/<shares>/<company_name>', methods=['POST']) #authored by: @pshroff 
def trade(player_id:str, mode:str, shares:float, company_name:str):
    player = handler.get_player(player_id)
    
    if not player:
        return jsonify(
            {name: c.dict() for name, c in handler.data[0].items()}
        )
    
    shares = float(shares)

    company = handler.get_company(company_name)

    if mode == "buy":
        cost = company.value * shares
        if player.cash >= cost and company.total_shares >= shares:
            handler.new_holdings(player.name, company.name, shares, cost)
            
    elif mode == "sell":
        current_shares = player.holdings.get(company_name, None)
        if current_shares >= shares:
            handler.sell_holdings(player.name, company_name, shares)

    return jsonify(
            {name: c.dict() for name, c in handler.data[0].items()}
        )

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        handler.write()
