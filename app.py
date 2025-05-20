from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
import os, json, re
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
    if not personagens_com_papeis:
        return {"error": "É necessário pelo menos 1 personagem."}

    prompt_personagens = []
    for p in personagens_com_papeis:
        prompt_personagens.append(f"{p.get('papel', 'Personagem')}: {p['nome']}")
    prompt_personagens_str = ", ".join(prompt_personagens)

    prompt_adicionais = ""
    if genero_input:
        prompt_adicionais += f" O gênero da fanfic deve ser: {genero_input}."
    if cenario_input:
        prompt_adicionais += f" O cenário onde a história se passa é: {cenario_input}."
    if idioma_input:
        prompt_adicionais += f" O idioma da fanfic deve ser: {idioma_input}."

    prompt = f"""
        Crie uma fanfic que tenha como base os seguintes personagens: {prompt_personagens_str}.{prompt_adicionais}
        Os capítulos devem ser numerados sequencialmente. Você NÃO deve adicionar nenhum prefixo como 'Capítulo 1:', 'Chapter 1:', '章 1:', '第 1 章:', '장 1:' ou similar ao título do capítulo. Apenas retorne o título do capítulo em si.
        O título que você gerar NÃO DEVE conter a palavra 'Capítulo', 'Chapter', '章', 'Fase', 'Parte' ou qualquer variação de "capítulo" EM NENHUM IDIOMA (incluindo português, inglês, japonês, coreano, grego, etc.). O título do capítulo DEVE ser APENAS o nome do capítulo, no idioma principal da fanfic.

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
                    "titulo": "Título do Capítulo 1 (apenas o título, no idioma da fanfic, sem prefixos de capítulo)",
                    "historia": [
                        "Parágrafo 1 do Capítulo 1.",
                        "Parágrafo 2 do Capítulo 1.",
                        "..."
                    ]
                }},
                {{
                    "titulo": "Título do Capítulo 2 (apenas o título, no idioma da fanfic, sem prefixos de capítulo)",
                    "historia": [
                        "Parágrafo 1 do Capítulo 2.",
                        "Parágrafo 2 do Capítulo 2.",
                        "..."
                    ]
                }},
                {{
                    "titulo": "Título do Capítulo N (apenas o título, no idioma da fanfic, sem prefixos de capítulo)",
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

        if not hasattr(response, 'text'):
            return {"error": "Resposta da IA não contém conteúdo textual."}

        response_text = response.text
        
        try:
            fanfic_data = json.loads(response_text)

            mapa_prefixo_capitulo = {
                "Português": "Capítulo {numero}:", "Inglês": "Chapter {numero}:",
                "Espanhol": "Capítulo {numero}:", "Francês": "Chapitre {numero}:",
                "Alemão": "Kapitel {numero}:", "Japonês": "章 {numero}:",
                "Chinês (Simplificado)": "第 {numero} 章:", "Hindi": "अध्याय {numero}:",
                "Árabe": "الفصل {numero}:", "Russo": "Глава {numero}:",
                "Italiano": "Capitolo {numero}:", "Coreano": "장 {numero}:",
                "Holandês": "Hoofdstuk {numero}:", "Sueco": "Kapitel {numero}:",
                "Norueguês": "Kapittel {numero}:", "Dinamarquês": "Kapitel {numero}:",
                "Finlandês": "Luku {numero}:", "Polonês": "Rozdział {numero}:",
                "Turco": "Bölüm {numero}:", "Vietnamita": "Chương {numero}:",
                "Tailandês": "บทที่ {numero}:", "Indonésio": "Bab {numero}:",
                "Grego": "Κεφάλαιο {numero}:", "Hebraico": "פרק {numero}:",
                "Búlgaro": "Глава {numero}:", "Checo": "Kapitola {numero}:",
                "Húngaro": "Fejezet {numero}:", "Romeno": "Capitolul {numero}:",
                "Português (Portugal)": "Capítulo {numero}:"
            }

            formato_prefixo_capitulo = mapa_prefixo_capitulo.get(idioma_input, mapa_prefixo_capitulo["Português"])

            regex_patterns_to_remove = [
                r"^\s*(?:Capítulo|Chapter|Chapitre|Kapitel|章|अध्याय|فصل|Глава|Luku|Rozdział|Bölüm|Chương|บทที่|Bab|Κεφάλαιο|פרק|Kapitola|Fejezet|Capitolul|Fase|Parte|Part|Section|Seção|Vol\.|Volume|Volumen)\s*\d*\s*[:\-\.]*\s*",
                r"^\s*\d+\s*[:\-\.]*\s*",
                r"^\s*[:\-\.]*\s*"
            ]

            if "capitulos" in fanfic_data and isinstance(fanfic_data["capitulos"], list):
                for i, capitulo in enumerate(fanfic_data["capitulos"]):
                    if "titulo" in capitulo:
                        original_title = capitulo["titulo"].strip()
                        cleaned_title = original_title
                        for pattern in regex_patterns_to_remove:
                            cleaned_title = re.sub(pattern, "", cleaned_title, flags=re.IGNORECASE).strip()
                            original_title = cleaned_title 

                        original_title = original_title.lstrip(":- ").strip()

                        if original_title.lower().startswith("título do capítulo"):
                            original_title = ""

                        capitulo["titulo"] = formato_prefixo_capitulo.format(numero=i + 1) + " " + original_title

            return fanfic_data
        except json.JSONDecodeError:
            return {"error": "Erro ao processar a resposta da IA (JSON inválido)."}
    except Exception as e:
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

        if not isinstance(personagens_data, list) or not personagens_data:
            return jsonify({'error': 'É necessário pelo menos 1 personagem.'}), 400

        for p in personagens_data:
            if not isinstance(p, dict) or 'nome' not in p:
                return jsonify({'error': 'Cada item na lista de personagens deve ser um dicionário com a chave "nome".'}), 400

        response = criar_fanfic(personagens_data, genero, cenario, idioma)
        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False) # Mudei para False para produção, pode voltar para True para depuração