// script.js - Traduzido para Português e Atualizado com Limpeza

// Referências aos elementos importantes no DOM
const divPersonagens = document.getElementById('personagens');
const divResposta = document.getElementById('response');
const btnGerarFanfic = document.getElementById('generate-fanfic-btn');
const btnLimparCampos = document.getElementById('clear-personagens-btn');

function atualizarBotoesRemover() {
    const botoesRemover = divPersonagens.querySelectorAll('.personagem-row .btn-danger');
    const linhasPersonagem = divPersonagens.querySelectorAll('.personagem-row');
    const contadorLinhas = linhasPersonagem.length;

    botoesRemover.forEach(botao => {
        botao.disabled = contadorLinhas <= 3;
    });
}

function adicionarPersonagem() {
    const linhaPersonagemDiv = document.createElement('div');
    linhaPersonagemDiv.className = 'personagem-row flex items-center space-x-3';

    const novoInput = document.createElement('input');
    novoInput.type = 'text';
    novoInput.className = 'personagem personagem-input flex-1 p-2.5 border border-gray-300 rounded-md focus:ring-2 focus:ring-teal-400 focus:outline-none text-sm text-gray-700';
    novoInput.placeholder = `Informe um personagem...`;

    const botaoRemover = document.createElement('button');
    botaoRemover.className = 'remove-personagem-btn bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-3 rounded-md text-sm transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed';
    botaoRemover.innerText = 'Remover';
    botaoRemover.addEventListener('click', () => removerPersonagem(botaoRemover));

    linhaPersonagemDiv.appendChild(novoInput);
    linhaPersonagemDiv.appendChild(botaoRemover);
    divPersonagens.appendChild(linhaPersonagemDiv);
    atualizarBotoesRemover();
}

function removerPersonagem(botao) {
    const linhaPersonagem = botao.parentElement;
    if (linhaPersonagem) {
        linhaPersonagem.remove();
    } else {
        console.error('[removerPersonagem] Não foi possível encontrar o elemento pai (personagem-row) para remover.');
    }
    atualizarBotoesRemover();
}

function limparCamposPersonagens() {
    const inputs = divPersonagens.querySelectorAll('.personagem-row .personagem-input');
    inputs.forEach(input => {
        input.value = '';
    });
}

/**
 * @function renderizarFanfic
 * @description Constrói dinamicamente o HTML da fanfic a partir do objeto JSON
 * retornado pela API e o exibe na área de resposta designada.
 * @param {object} dadosFanfic - O objeto JSON contendo os dados da fanfic (titulo, capitulos).
 * Espera a seguinte estrutura:
 * {
 * "titulo": "Título da Fanfic",
 * "capitulos": [
 * {
 * "titulo": "Título do Capítulo 1",
 * "historia": ["Parágrafo 1...", "Parágrafo 2...", "..."]
 * },
 * {
 * "titulo": "Título do Capítulo 2",
 * "historia": ["Parágrafo 1...", "Parágrafo 2...", "..."]
 * },
 * ...
 * ]
 * }
 */
function renderizarFanfic(dadosFanfic) {
    if (!dadosFanfic || typeof dadosFanfic !== 'object' || !dadosFanfic.titulo || !Array.isArray(dadosFanfic.capitulos)) {
        console.error("Erro ao renderizar: Dados da fanfic no formato inesperado.", dadosFanfic);
        divResposta.innerHTML = '<p class="text-red-600 font-semibold">Erro ao renderizar a fanfic recebida.</p>';
        divResposta.className = 'response bg-white p-6 rounded-xl shadow-md border border-gray-200 mt-6 text-left max-w-xl mx-auto text-red-600';
        return;
    }

    let htmlFanfic = `
        <h2 class="text-2xl font-bold mb-4 text-gray-800">${dadosFanfic.titulo}</h2>
    `;

    dadosFanfic.capitulos.forEach((capitulo, index) => {
        htmlFanfic += `
            <div class="mb-6">
                <h3 class="text-xl font-semibold mb-2 text-gray-700">Capítulo ${index + 1}: ${capitulo.titulo}</h3>
                ${capitulo.historia.map(paragrafo => `<p class="text-gray-700 mb-2">${paragrafo}</p>`).join('')}
            </div>
        `;
    });

    divResposta.innerHTML = htmlFanfic;
    divResposta.className = 'response bg-white p-6 rounded-xl shadow-md border border-gray-200 mt-6 text-left max-w-xl mx-auto';
}

async function enviarFormulario() {
    console.log('[enviarFormulario] Processando e enviando formulário...');
    btnGerarFanfic.disabled = true;
    btnGerarFanfic.innerHTML = 'Gerando...';
    divResposta.innerHTML = 'Carregando...';
    divResposta.classList.remove('hidden');

    const inputsPersonagem = divPersonagens.querySelectorAll('.personagem-row .personagem-input');
    const personagens = [];
    inputsPersonagem.forEach(input => {
        const valor = input.value.trim();
        if (valor) {
            personagens.push(valor);
        }
    });

    console.log('[enviarFormulario] Personagens coletados:', personagens);

    if (personagens.length < 3) {
        alert('Por favor, preencha pelo menos três campos de personagem para gerar uma fanfic!');
        console.warn('[enviarFormulario] Validação falhou: Menos de 3 personagens.');
        divResposta.classList.add('hidden');
        btnGerarFanfic.disabled = false;
        btnGerarFanfic.innerHTML = 'Gerar Fanfic';
        return;
    }

    const dados = {
        personagens: personagens
    };
    console.log('[enviarFormulario] Dados preparados para API:', dados);

    try {
        console.log('[enviarFormulario] Enviando requisição para API...');
        const resposta = await fetch('http://localhost:5000/fanfic', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dados)
        });

        console.log('[enviarFormulario] Resposta da API recebida (Status: ' + resposta.status + ').');

        const resultado = await resposta.json();
        console.log('[enviarFormulario] Resposta JSON parseada:', resultado);

        if (resultado && typeof resultado === 'object' && resultado.titulo && Array.isArray(resultado.capitulos)) {
            console.log('[enviarFormulario] Objeto de fanfic válido encontrado. Renderizando.');
            renderizarFanfic(resultado);
            limparCamposPersonagens();
            divResposta.className = 'response bg-white p-6 rounded-xl shadow-md border border-gray-200 mt-6 text-left max-w-xl mx-auto';
        } else if (resultado && typeof resultado === 'object' && resultado.error) {
            console.error('[enviarFormulario] API retornou objeto de erro:', resultado.error);
            divResposta.innerHTML = `<p class="text-red-600 font-semibold">Erro da API: ${resultado.error}</p>`;
            divResposta.className = 'response bg-white p-6 rounded-xl shadow-md border border-gray-200 mt-6 text-left max-w-xl mx-auto text-red-600';
        } else {
            console.error('[enviarFormulario] API retornou formato inesperado:', resultado);
            divResposta.innerHTML = '<p class="text-red-600 font-semibold">Erro: Formato de resposta inesperado da API.</p>';
            divResposta.className = 'response bg-white p-6 rounded-xl shadow-md border border-gray-200 mt-6 text-left max-w-xl mx-auto text-red-600';
        }

        divResposta.classList.remove('hidden');

    } catch (error) {
        console.error('[enviarFormulario] Erro no Fetch ou parsing JSON:', error);
        divResposta.innerHTML = `<p class="text-red-600 font-semibold">Ocorreu um erro ao tentar comunicar com o servidor: ${error.message}</p>`;
        divResposta.className = 'response bg-white p-6 rounded-xl shadow-md border border-gray-200 mt-6 text-left max-w-xl mx-auto text-red-600';
        divResposta.classList.remove('hidden');

    } finally {
        btnGerarFanfic.disabled = false;
        btnGerarFanfic.innerHTML = 'Gerar Fanfic';
        console.log('[enviarFormulario] Finalizado.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM completamente carregado.');

    const btnAdicionarPersonagem = document.getElementById('add-personagem-btn');
    btnAdicionarPersonagem.addEventListener('click', adicionarPersonagem);
    console.log('Event listener adicionado ao botão "Adicionar Personagem".');

    btnGerarFanfic.addEventListener('click', enviarFormulario);
    console.log('Event listener adicionado ao botão "Gerar Fanfic".');

    btnLimparCampos.addEventListener('click', limparCamposPersonagens);
    console.log('Event listener adicionado ao botão "Limpar Campos".');

    const botoesRemoverIniciais = divPersonagens.querySelectorAll('.personagem-row .btn-danger');
    botoesRemoverIniciais.forEach(botao => {
        botao.addEventListener('click', () => removerPersonagem(botao));
    });
    console.log('Event listeners adicionados aos botões "Excluir" iniciais.');

    atualizarBotoesRemover();
    console.log('atualizarBotoesRemover chamado na inicialização.');
});