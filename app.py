from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
import os, json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

@app.route("/")
def home():
    return "API funcionando"

# A função criar_fanfic agora aceita uma lista de dicionários de personagens, gênero e cenário
def criar_fanfic(personagens_com_papeis, genero_input=None, cenario_input=None):
    # O mínimo de personagens agora é 1
    if not personagens_com_papeis or len(personagens_com_papeis) < 1:
        return {"error": "É necessário pelo menos 1 personagem."}

    # Constrói a string de personagens com seus papéis definidos pelo usuário
    prompt_personagens = []
    for p in personagens_com_papeis:
        if p.get("papel"):
            prompt_personagens.append(f"{p['papel']}: {p['nome']}")
        else:
            prompt_personagens.append(f"Personagem: {p['nome']}")

    prompt_personagens_str = ", ".join(prompt_personagens)

    prompt_adicionais = ""
    if genero_input:
        prompt_adicionais += f" O gênero da fanfic deve ser: {genero_input}."
    if cenario_input:
        prompt_adicionais += f" O cenário onde a história se passa é: {cenario_input}."


    prompt = f"""
        Crie uma fanfic que tenha como base os seguintes personagens: {prompt_personagens_str}.{prompt_adicionais}
        Caso os personagens, seus papéis, gênero ou cenário inseridos não sejam apropriados, por exemplo, por serem relacionados a conteúdo sexual,
        ódio, qualquer coisa inapropriada ou coisas que não são de boa conduta, ignore-os,
        não gere a fanfic e alerte o usuário sobre o uso responsável da ferramenta de geração de fanfics.
        Caso o nome dos personagens não façam sentido (por exemplo, uma série aleatória de caracteres),
        a fanfic deve ser uma história de como adquirem um nome real.
        O primeiro capítulo deve ser de introdução, o segundo de desenvolvimento e o terceiro sendo a finalização.
        Devolva no seguinte formato JSON:
        {{
            "titulo": "Título da Fanfic",
            "capitulos": [
                {{
                    "titulo": "Título do Capítulo 1",
                    "historia": [
                        "Parágrafo 1 do Capítulo 1.",
                        "Parágrafo 2 do Capítulo 1.",
                        "..."
                    ]
                }},
                {{
                    "titulo": "Título do Capítulo 2",
                    "historia": [
                        "Parágrafo 1 do Capítulo 2.",
                        "Parágrafo 2 do Capítulo 2.",
                        "..."
                    ]
                }},
                {{
                    "titulo": "Título do Capítulo N",
                    "historia": [
                        "Parágrafo 1 do Capítulo N.",
                        "Parágrafo 2 do Capítulo N.",
                        "..."
                    ]
                }}
            ]
        }}
        A fanfic pode ser de qualquer gênero, desde que não seja inapropriada ou explícita.
        Dê preferência para fanfics rápidas de serem lidas.
        """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            }
        )

        if hasattr(response, 'text'):
            response_text = response.text
            try:
                response_json = json.loads(response_text)
                return response_json
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON da resposta da IA: {e}")
                print(f"Texto da resposta da IA: {response_text}")
                return {"error": "Erro ao processar a resposta da IA (JSON inválido)."}
        else:
            print("Resposta da IA não contém atributo 'text' esperado.")
            print(f"Resposta completa da IA: {response}")
            return {"error": "Erro ao receber a resposta da IA."}

    except Exception as e:
        print(f"Erro ao gerar conteúdo com a IA: {e}")
        return {"error": f"Erro ao comunicar com a IA: {str(e)}"}

@app.route('/fanfic', methods=['POST'])
def make_fanfic():
    try:
        dados = request.get_json()

        if not dados or not isinstance(dados, dict):
            return jsonify({'error': 'Requisição JSON inválida. Esperava um dicionário.'}), 400

        # Agora 'personagens' é uma lista de dicionários {'nome': '...', 'papel': '...'}
        personagens_data = dados.get('personagens', [])
        genero = dados.get('genero')
        cenario = dados.get('cenario')

        if not isinstance(personagens_data, list):
            return jsonify({'error': 'O campo "personagens" deve ser uma lista.'}), 400

        # Valida que cada item na lista de personagens é um dicionário e tem 'nome'
        for p in personagens_data:
            if not isinstance(p, dict) or 'nome' not in p:
                return jsonify({'error': 'Cada item na lista de personagens deve ser um dicionário com a chave "nome".'}), 400

        # O mínimo de personagens agora é 1
        if len(personagens_data) < 1:
            return jsonify({'error': 'É necessário pelo menos 1 personagem.'}), 400

        response = criar_fanfic(personagens_data, genero, cenario)
        return jsonify(response), 200

    except Exception as e:
        print(f"Um erro interno ocorreu na API: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)