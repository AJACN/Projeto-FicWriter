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

def criar_fanfic(personagens_input):
    if not personagens_input or len(personagens_input) < 3:
        return {"error": "São necessários pelo menos 3 personagens."}

    protagonista = personagens_input[0]
    co_protagonista = personagens_input[1]
    antagonista = personagens_input[2]
    outros_personagens = personagens_input[3:]

    prompt_personagens = f"Protagonista: {protagonista}, Co-protagonista: {co_protagonista}, Antagonista: {antagonista}"
    if outros_personagens:
        prompt_personagens += f", Outros personagens: {', '.join(outros_personagens)}"

    prompt = f"""
        Crie uma fanfic que tenha como base os seguintes personagens: {prompt_personagens}.
        Em caso de personagens que não sejam apropriados ou não existam, por exemplo, orgãos sexuais,
        objetos, ignore-os, não gere a fanfic e alerte o usuário sobre o uso responsável
        da ferramenta de geração de fanfics.
        da fanfic.
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

        personagens = dados.get('personagens', [])

        if not isinstance(personagens, list):
            return jsonify({'error': 'O campo \"personagens\" deve ser uma lista.'}), 400

        if len(personagens) < 3:
            return jsonify({'error': 'São necessários pelo menos 3 personagens.'}), 400

        response = criar_fanfic(personagens)
        return jsonify(response), 200

    except Exception as e:
        print(f"Um erro interno ocorreu na API: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)