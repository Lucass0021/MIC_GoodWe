from flask import Flask, request, jsonify
 
app = Flask(__name__)
 
# Rota para receber dados do ESP32 (Wokwi)
@app.route("/data", methods=["POST"])
def receive_data():
    data = request.get_json()
    print("📩 Dados recebidos:", data)  # aparece no terminal
    return jsonify({"status": "ok", "message": "Dados recebidos com sucesso!"})
 
# Rota para testar se o servidor está ativo
@app.route("/", methods=["GET"])
def home():
    return "Servidor Flask está rodando!"
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
