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

def criar_fanfic(personagens_com_papeis, genero_input=None, cenario_input=None, idioma_input=None):
    if not personagens_com_papeis or len(personagens_com_papeis) < 1:
        return {"error": "É necessário pelo menos 1 personagem."}

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
    if idioma_input:
        prompt_adicionais += f" O idioma da fanfic deve ser: {idioma_input}."

    # A IA não será mais responsável por adicionar "Capítulo X:".
    # Pediremos apenas o título do capítulo e a história.
    prompt = f"""
        Crie uma fanfic que tenha como base os seguintes personagens: {prompt_personagens_str}.{prompt_adicionais}
        Os capítulos devem ser numerados sequencialmente, mas você NÃO precisa adicionar o prefixo 'Capítulo N:', 'Chapter N:', '章 N:' ou similar ao título do capítulo. Apenas retorne o título do capítulo em si.

        Caso os personagens, seus papéis, gênero, cenário ou idioma inseridos não sejam apropriados, por exemplo, por serem relacionados a conteúdo sexual,
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
                    "titulo": "Título do Capítulo 1 (sem o prefixo de capítulo)",
                    "historia": [
                        "Parágrafo 1 do Capítulo 1.",
                        "Parágrafo 2 do Capítulo 1.",
                        "..."
                    ]
                }},
                {{
                    "titulo": "Título do Capítulo 2 (sem o prefixo de capítulo)",
                    "historia": [
                        "Parágrafo 1 do Capítulo 2.",
                        "Parágrafo 2 do Capítulo 2.",
                        "..."
                    ]
                }},
                {{
                    "titulo": "Título do Capítulo N (sem o prefixo de capítulo)",
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
                fanfic_data = json.loads(response_text)

                # --- PÓS-PROCESSAMENTO AQUI ---
                # Mapeamento para a palavra "Capítulo" e sua formatação no idioma
                mapa_prefixo_capitulo = {
                    "Português": "Capítulo {numero}:",
                    "Inglês": "Chapter {numero}:",
                    "Espanhol": "Capítulo {numero}:",
                    "Francês": "Chapitre {numero}:",
                    "Alemão": "Kapitel {numero}:",
                    "Japonês": "章 {numero}:",
                    "Chinês (Simplificado)": "第 {numero} 章:",
                    "Hindi": "अध्याय {numero}:",
                    "Árabe": "الفصل {numero}:",
                    "Russo": "Глава {numero}:",
                    "Italiano": "Capitolo {numero}:",
                    "Coreano": "장 {numero}:",
                    "Holandês": "Hoofdstuk {numero}:",
                    "Sueco": "Kapitel {numero}:",
                    "Norueguês": "Kapittel {numero}:",
                    "Dinamarquês": "Kapitel {numero}:",
                    "Finlandês": "Luku {numero}:",
                    "Polonês": "Rozdział {numero}:",
                    "Turco": "Bölüm {numero}:",
                    "Vietnamita": "Chương {numero}:",
                    "Tailandês": "บทที่ {numero}:",
                    "Indonésio": "Bab {numero}:",
                    "Grego": "Κεφάλαιο {numero}:",
                    "Hebraico": "פרק {numero}:",
                    "Búlgaro": "Глава {numero}:",
                    "Checo": "Kapitola {numero}:",
                    "Húngaro": "Fejezet {numero}:",
                    "Romeno": "Capitolul {numero}:",
                    "Português (Portugal)": "Capítulo {numero}:"
                }

                # Pega o formato do prefixo do capítulo para o idioma selecionado
                formato_prefixo_capitulo = mapa_prefixo_capitulo.get(idioma_input, mapa_prefixo_capitulo["Português"])

                # Adiciona o prefixo aos títulos dos capítulos
                if "capitulos" in fanfic_data and isinstance(fanfic_data["capitulos"], list):
                    for i, capitulo in enumerate(fanfic_data["capitulos"]):
                        if "titulo" in capitulo:
                            # Remove qualquer prefixo de capítulo existente gerado pela IA
                            # Ex: "Capítulo 1: ", "Chapter 1: ", "章 1: "
                            # Isso é uma tentativa de limpeza, pode não ser 100% à prova de falhas se a IA for muito criativa
                            original_title = capitulo["titulo"].strip()
                            for prefix in mapa_prefixo_capitulo.values():
                                for num in range(1, 4): # Tenta remover para os primeiros 3 capítulos
                                    formatted_prefix = prefix.format(numero=num)
                                    if original_title.startswith(formatted_prefix):
                                        original_title = original_title[len(formatted_prefix):].strip()
                                        break # Sai do loop interno se encontrou e removeu

                            capitulo["titulo"] = formato_prefixo_capitulo.format(numero=i + 1) + " " + original_title.lstrip(":") # Adiciona o prefixo correto

                return fanfic_data
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

        personagens_data = dados.get('personagens', [])
        genero = dados.get('genero')
        cenario = dados.get('cenario')
        idioma = dados.get('idioma')

        if not isinstance(personagens_data, list):
            return jsonify({'error': 'O campo "personagens" deve ser uma lista.'}), 400

        for p in personagens_data:
            if not isinstance(p, dict) or 'nome' not in p:
                return jsonify({'error': 'Cada item na lista de personagens deve ser um dicionário com a chave "nome".'}), 400

        if len(personagens_data) < 1:
            return jsonify({'error': 'É necessário pelo menos 1 personagem.'}), 400

        response = criar_fanfic(personagens_data, genero, cenario, idioma)
        return jsonify(response), 200

    except Exception as e:
        print(f"Um erro interno ocorreu na API: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)