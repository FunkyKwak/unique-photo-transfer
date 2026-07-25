const { GoogleGenAI } = require("@google/genai");
const fs = require("fs");

async function run() {
  const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
  const readmeContent = fs.readFileSync("readme.md", "utf8");

  const prompt = `Tu es un traducteur technique expert. Traduis le document Markdown suivant de l'anglais vers le français pour un fichier readme.fr.md.

Règles strictes :
1. Ne traduis PAS les blocs de code (\`\`\`), ni le code en ligne (\`code\`), ni les variables, ni les commandes terminal.
2. Garde les liens Markdown [texte](url) intacts (traduis le texte de l'ancrage uniquement si nécessaire, conserve les URLs strictes).
3. Conserve la syntaxe Markdown à l'identique (titres, listes, tableaux, émojis).
4. Ne traduis pas les termes techniques consacrés si leur traduction française est inhabituelle pour un développeur (ex: "commit", "push", "pull request", "build", "framework").
5. Renvoie UNIQUEMENT le contenu Markdown traduit, sans aucun commentaire d'introduction ou de conclusion.

Voici le contenu à traduire :

${readmeContent}`;

  const response = await ai.models.generateContent({
    model: "gemini-1.5-flash",
    contents: prompt,
  });

  fs.writeFileSync("README.fr.md", response.text);
  console.log("Traduction terminée avec succès dans readme.fr.md !");
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
