// graficos.js - Versão com API REST
console.log('===== GRAFICOS.JS CARREGADO =====');

window.onload = function() {
    console.log('1. Window.onload disparou');
    
    setTimeout(function() {
        console.log('2. Timeout executado');
        
        // Verificar se Chart existe
        if (typeof Chart === 'undefined') {
            console.error('ERRO: Chart.js não está disponível!');
            return;
        }
        console.log('3. Chart.js disponível: SIM');
        
        // Buscar canvas
        var canvas1 = document.getElementById('graficoTipo');
        var canvas2 = document.getElementById('graficoStatus');
        
        console.log('4. Canvas1 existe:', canvas1 !== null);
        console.log('5. Canvas2 existe:', canvas2 !== null);
        
        if (!canvas1 || !canvas2) {
            console.error('ERRO: Canvas não encontrados!');
            return;
        }
        
        // Buscar dados da API
        console.log('6. Buscando dados da API...');
        
        // Pegar filtros da URL se existirem
        var urlParams = new URLSearchParams(window.location.search);
        var apiUrl = '/api/dados_graficos';
        if (urlParams.toString()) {
            apiUrl += '?' + urlParams.toString();
        }
        
        fetch(apiUrl)
            .then(function(response) {
                console.log('7. Resposta da API recebida:', response.status);
                if (!response.ok) {
                    throw new Error('Erro na API: ' + response.status);
                }
                return response.json();
            })
            .then(function(dados) {
                console.log('8. Dados JSON parseados com sucesso:');
                console.log('   - Tipos:', dados.tipos);
                console.log('   - Valores:', dados.valores);
                console.log('   - Abertas:', dados.abertas);
                console.log('   - Resolvidas:', dados.resolvidas);
                
                // CRIAR GRÁFICO 1
                try {
                    console.log('9. Criando Gráfico 1...');
                    var ctx1 = canvas1.getContext('2d');
                    new Chart(ctx1, {
                        type: 'bar',
                        data: {
                            labels: dados.tipos,
                            datasets: [{
                                label: 'Quantidade',
                                data: dados.valores,
                                backgroundColor: ['#1976d2', '#dc3545', '#28a745', '#ffc107', '#17a2b8', '#6f42c1', '#fd7e14', '#20c997']
                            }]
                        },
                        options: {
                            responsive: false,
                            plugins: {
                                legend: { display: false }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: { stepSize: 1 }
                                }
                            }
                        }
                    });
                    console.log('10. GRÁFICO 1 CRIADO COM SUCESSO!');
                } catch (e) {
                    console.error('ERRO ao criar Gráfico 1:', e);
                }
                
                // CRIAR GRÁFICO 2
                try {
                    console.log('11. Criando Gráfico 2...');
                    var ctx2 = canvas2.getContext('2d');
                    new Chart(ctx2, {
                        type: 'doughnut',
                        data: {
                            labels: ['Abertas', 'Resolvidas'],
                            datasets: [{
                                data: [dados.abertas, dados.resolvidas],
                                backgroundColor: ['#ffc107', '#28a745']
                            }]
                        },
                        options: {
                            responsive: false,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                }
                            }
                        }
                    });
                    console.log('12. GRÁFICO 2 CRIADO COM SUCESSO!');
                } catch (e) {
                    console.error('ERRO ao criar Gráfico 2:', e);
                }
                
                console.log('===== GRAFICOS CRIADOS COM SUCESSO =====');
            })
            .catch(function(error) {
                console.error('ERRO ao buscar dados:', error);
            });
        
    }, 1500);
};
