# NMR 2D Peak Picker — morfologia experimental v2.0

## Execução
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Selecione HSQC, COSY ou HMBC. O visualizador existente permanece disponível; abaixo dele, a nova seção **Reconhecimento morfológico experimental** permite alterar raios em ppm, SNR, persistência e política de fase, comparar hipóteses multilóbulos e exportar CSV.

## Arquitetura
`morphology.py` é o motor reutilizável de agrupamento de máximos. Entrada: DataFrame com `H_ppm`, `C_ppm`, `smoothed_intensity`, `snr_proxy`, `scales_detected` e `polarity` opcional. Saída: tabela de grupos e tabela de máximos com IDs de grupos. O motor não depende do Streamlit.

## Limitações
- Os visualizadores e listas de máximos são de experimentos já processados. Ainda não há importação/reprocessamento automático de um novo ZIP Bruker.
- O módulo é uma **proposta geométrica de reconhecimento morfológico**, com orientação, espaçamento e padrão de polaridade. Não lê os perfis de intensidade pixel a pixel, não executa ajuste de linhas, não identifica fisicamente a alternância de fase e **não comprova que máximos agrupados pertencem à mesma correlação**.
- O modo `alternating` só combina máximos de polaridades opostas, sem garantir um padrão físico de fase. COSY foi importado com polaridade positiva porque a lista anterior não inclui sinal.
- Os limites de agrupamento são heurísticos, ajustáveis e devem ser calibrados com anotações manuais.


## Atualização v2.1
O visualizador HMBC incorpora o controle de SNR de 5 a 30. A interface de reconhecimento morfológico do Streamlit permanece disponível abaixo do visualizador. O corte SNR do HTML é aplicado aos candidatos previamente processados (SNR >= 5), sem refazer a detecção.

### Windows (duplo clique)
Execute `INICIAR_STREAMLIT.bat`; o script cria `.venv` e instala as dependências na primeira execução. Requer Python instalado e disponível via `py` ou `python`.
