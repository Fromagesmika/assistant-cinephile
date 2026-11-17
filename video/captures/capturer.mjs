// Capture les vrais écrans de l'interface (streamlit run app.py doit tourner sur le port 8501).
// Usage : node video/captures/capturer.mjs <chemin vers puppeteer-core>
// Chaque scène charge une nouvelle session, choisit un niveau, pose une question et photographie
// la page en 2880 x 1620 (1920 x 1080 à l'échelle 1,5), pour pouvoir zoomer dans la vidéo.
import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";

const ici = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const puppeteer = require(process.argv[2]);
const URL = "http://localhost:8501";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";

const navigateur = await puppeteer.launch({ executablePath: CHROME, headless: "new", protocolTimeout: 600000 });
const attendreTexte = (page, texte, delai = 120000) =>
  page.waitForFunction((t) => document.body.innerText.toLowerCase().includes(t.toLowerCase()), { timeout: delai }, texte);
const pause = (ms) => new Promise((r) => setTimeout(r, ms));

async function nouvellePage() {
  const page = await navigateur.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1.5 });
  await page.goto(URL, { waitUntil: "networkidle2" });
  await attendreTexte(page, "Une question de cinéma");
  await pause(1500);
  return page;
}

async function choisirNiveau(page, n) {
  const libelles = { 0: "Niveau 0 · LLM seul", 1: "Niveau 1 · RAG", 2: "Niveau 2 · Agent", 3: "Niveau 3 · Agent + RAG" };
  await page.click(`::-p-text(${libelles[n]})`);
  await pause(1500);
}

async function poser(page, question) {
  await page.click('input[aria-label="Question"]');
  await page.keyboard.type(question, { delay: 5 });
  await page.keyboard.press("Enter");
}

async function photo(page, nom) {
  // Streamlit redessine la page après chaque réponse : on attend qu'il n'y ait plus
  // d'éléments « périmés » (affichés en transparence) avant de photographier.
  await page.waitForFunction(() => !document.querySelector('[data-stale="true"]'), { timeout: 60000 });
  await pause(2500);
  await page.screenshot({ path: path.join(ici, `${nom}.png`) });
  console.log("capturé", nom);
}

// Photographie un élément seul, en entier (la dernière occurrence du sélecteur).
async function photoElement(page, selecteur, nom) {
  await page.waitForFunction(() => !document.querySelector('[data-stale="true"]'), { timeout: 60000 });
  await pause(1500);
  const elements = await page.$$(selecteur);
  await elements[elements.length - 1].screenshot({ path: path.join(ici, `${nom}.png`) });
  console.log("capturé", nom);
}

async function amenerEnHaut(page, selecteur) {
  await page.evaluate((s) => {
    const el = [...document.querySelectorAll(s)].pop();
    if (el) el.scrollIntoView({ block: "start" });
  }, selecteur);
  await pause(800);
}

async function ouvrirOnglet(page, debut) {
  await page.click(`::-p-text(${debut})`);
  await pause(1200);
}

const FLOW = "Quel est le budget du film d'animation Flow de Gints Zilbalodis ?";

// 1. Accueil, niveau 0 choisi
{
  const page = await nouvellePage();
  await photo(page, "00_accueil");
  await page.close();
}

// 2. La même question aux quatre niveaux
for (const n of [0, 1, 2, 3]) {
  const page = await nouvellePage();
  await choisirNiveau(page, n);
  if (n === 0) await photo(page, "01_accueil_niveau0");
  await poser(page, FLOW);
  await attendreTexte(page, "Coût de la requête", 240000);
  await amenerEnHaut(page, '[data-testid="stChatMessage"]');
  await photo(page, `1${n}_flow_niveau${n}`);
  await photoElement(page, '[data-testid="stChatMessage"]', `c1${n}_carte_flow_niveau${n}`);
  if (n === 3) {
    await ouvrirOnglet(page, "Trace (");
    await amenerEnHaut(page, '[data-testid="stTabs"]');
    await photo(page, "13b_flow_niveau3_trace");
    await photoElement(page, '[data-testid="stTabs"]', "c13_trace_flow");
    await ouvrirOnglet(page, "Sources citées (");
    await photo(page, "13c_flow_niveau3_sources");
  }
  await page.close();
}

// 3. Une abstention : un film qui n'existe pas
{
  const page = await nouvellePage();
  await choisirNiveau(page, 1);
  await poser(page, "Qui a réalisé le film Les Horloges de Valparaíso, sorti en 2019 ?");
  await attendreTexte(page, "Coût de la requête", 240000);
  await amenerEnHaut(page, '[data-testid="stChatMessage"]');
  await photo(page, "20_abstention");
  await photoElement(page, '[data-testid="stChatMessage"]', "c20_carte_abstention");
  await page.close();
}

// 4. Une tâche en plusieurs étapes, avec confirmation et trace
{
  const page = await nouvellePage();
  await choisirNiveau(page, 3);
  await poser(page, "Ajoute Grave et Titane, les deux films de Julia Ducournau, à la liste à voir.");
  await attendreTexte(page, "Action à confirmer", 240000);
  await photo(page, "30_confirmation_grave");
  await photoElement(page, '.st-key-confirmation', "c30_confirmation_grave");
  await page.click("::-p-text(Accepter)");
  await page.waitForFunction(() => document.body.innerText.includes("Titane » (2021)"), { timeout: 240000 });
  await photo(page, "31_confirmation_titane");
  await photoElement(page, '.st-key-confirmation', "c31_confirmation_titane");
  await page.click("::-p-text(Accepter)");
  await attendreTexte(page, "Coût de la requête", 240000);
  await amenerEnHaut(page, '[data-testid="stChatMessage"]');
  await photo(page, "32_liste_modifiee");
  await photoElement(page, '[data-testid="stChatMessage"]', "c32_carte_liste_modifiee");
  await ouvrirOnglet(page, "Trace (");
  await amenerEnHaut(page, '[data-testid="stTabs"]');
  await photo(page, "33_trace_tache");
  await photoElement(page, '[data-testid="stTabs"]', "c33_trace_tache");
  await page.evaluate(() => window.scrollTo(0, 0));
  await amenerEnHaut(page, '[data-testid="stMainBlockContainer"]');
  await page.click("::-p-text(Liste à voir ·)");
  await pause(1500);
  await photo(page, "34_liste_ouverte");
  await page.close();
}

await navigateur.close();
