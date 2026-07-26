const OpenAI = require("openai");
const fs = require("fs");
const path = require("path");

async function run() {
  // Initialisation de la bibliothèque OpenAI pointée sur l'API Groq
  const openai = new OpenAI({
    apiKey: process.env.GROQ_API_KEY,
    baseURL: "https://api.groq.com/openai/v1",
  });

  // Résolution propre des chemins par rapport à la racine du projet
  const readmePath = path.resolve(__dirname, "../README.md");
  const readmeFrPath = path.resolve(__dirname, "../docs/README.fr.md");

  if (!fs.existsSync(readmePath)) {
    console.error(`Fichier introuvable : ${readmePath}`);
    process.exit(1);
  }

  const readmeContent = fs.readFileSync(readmePath, "utf8");

  const prompt = `Tu es un traducteur technique expert. Traduis le document Markdown suivant de l'anglais vers le français pour un fichier README.fr.md.

Règles strictes :
1. Ne traduis PAS les blocs de code (\`\`\`), ni le code en ligne (\`code\`), ni les variables, ni les commandes terminal. Sauf pour les blocs de code de type mermaid (\`\`\`mermaid:)
2. Garde les liens Markdown [texte](url) intacts (traduis le texte de l'ancrage uniquement si nécessaire, conserve les URLs strictes).
3. Conserve la syntaxe Markdown à l'identique (titres, listes, tableaux, émojis).
4. Ne traduis pas les termes techniques consacrés si leur traduction française est inhabituelle pour un développeur (ex: "commit", "push", "pull request", "build", "framework"), ainsi que les termes liés au projet (ex: "Unique Photo Transfer").
5. Renvoie UNIQUEMENT le contenu Markdown traduit, sans aucun commentaire d'introduction ou de conclusion.
6. Remplace sans traduire "🇬🇧 **English** | 🇫🇷 [Français](docs/README.fr.md)" par "🇬🇧 [English](../README.md) | 🇫🇷**Français**"

Voici le contenu à traduire :

${readmeContent}`;

  const response = await openai.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [
      { role: "user", content: prompt }
    ],
    temperature: 0.3, // Faible température pour une traduction fidèle et constante
  });

  fs.writeFileSync(readmeFrPath, response.choices[0].message.content);
  console.log("Traduction terminée avec succès dans README.fr.md via Groq !");
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
