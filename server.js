const express = require("express");

const app = express();
const PORT = 3000;

// URL base da API Flask do INPE
// Docs: http://queimadas.dgi.inpe.br/queimadas/dados-abertos/
const INPE_API = "https://queimadas.dgi.inpe.br/api/focos";

// Rota para buscar focos ativos no Brasil
app.get("/fires/brasil", async (req, res) => {
  try {
    // Exemplo: pegar os focos ativos das últimas 48h
    // (há parâmetros como: pais, bioma, estado, satélite etc.)
    const url = `${INPE_API}?pais=BRASIL&horas=48`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Erro na API do INPE: ${response.status}`);
    }

    const data = await response.json();

    // Retorna direto o JSON para o app mobile
    res.json({
      fonte: "INPE - BDQueimadas",
      total_focos: data.length,
      focos: data,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: `Erro ao buscar dados do INPE: ${err}`  });
  }
});

app.listen(PORT, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}`);
});
