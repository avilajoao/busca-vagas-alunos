# 🎯 Buscador de Vagas Remotas LATAM

Script de automação diária para buscar e categorizar de 3 a 4 vagas por tecnologia/stack para alunos do programa.

## 🛠️ O que os arquivos fazem:
- `buscador_vagas.py`: O script em Python que consulta as APIs, filtra por LATAM e inglês, e gera o relatório `VAGAS_DO_DIA.md`.
- `requirements.txt`: Lista de dependências Python necessárias para rodar o script.
- `.github/workflows/vagas-diarias.yml`: Arquivo de automação para o GitHub Actions rodar a busca todos os dias automaticamente.

## 🚀 Como rodar localmente no seu computador:

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute o buscador:
```bash
python buscador_vagas.py
```

3. Abra o arquivo `VAGAS_DO_DIA.md` gerado na pasta para ver as vagas recolhidas!
