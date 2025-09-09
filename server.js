import express from "express";

const app = express();
const PORT = 3000;

// URL base com os CSV de 10 minutos
const LIST_URL = "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/10min/";

async function getLatestCsvUrl() {
  const html = await fetch(LIST_URL).then(r => r.text());

  // procura por arquivos CSV no HTML
  const matches = [...html.matchAll(/href="(focos_10min_\d{8}_\d{4}\.csv)"/g)].map(m => m[1]);

  if (!matches.length) throw new Error("Nenhum CSV encontrado no diretório do INPE.");

  // pega o último (mais recente) arquivo listado
  const latestFile = matches[matches.length - 1];
  return new URL(latestFile, LIST_URL).toString();
}

app.get("/fires/recents", async (req, res) => {
  try {
    const url = await getLatestCsvUrl();
    const csv = await fetch(url).then(r => r.text());

    // transforma em JSON (opcional)
    const rows = csv.split("\n").map(line => line.split(";"));
    const headers = rows.shift();
    const json = rows
      .filter(r => r.length === headers.length) // garante que não entre linha vazia
      .map(row =>
        Object.fromEntries(row.map((val, i) => [headers[i], val]))
      );

    res.json({
      fonte: "INPE - Queimadas (últimos 10 min)",
      arquivo: url,
      total_registros: json.length,
      dados: json,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Falha ao buscar CSV do INPE" });
  }
});

app.listen(PORT, () => {
  console.log(`✅ Servidor rodando em http://localhost:${PORT}`);
});
