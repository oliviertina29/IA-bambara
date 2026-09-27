# Guide de production — IA Bamanankan na

Vidéos éducatives courtes (TikTok, 9:16, 35–60 s) qui expliquent la technologie et l'IA **en bambara parlé**,
pour des personnes qui ne lisent pas forcément. La **voix** porte le message ; l'image l'illustre ; le texte à l'écran est un bonus.

## L'équipe d'agents

| Agent | Rôle | Sortie |
|---|---|---|
| Chercheur | Comprend le sujet, vérifie les faits, trouve 3–5 idées simples et des exemples de la vie malienne (marché, champ, bétail, téléphone, Orange Money, grin, école…) | notes courtes + sources |
| Scénariste | Écrit le script en français : accroche → idée clé → exemple concret → à quoi ça sert → appel à suivre. 5–7 scènes, ~90–120 mots au total | script français par scène |
| Traducteur bambara | Adapte en bambara parlé naturel, phrases courtes (≤ 8 mots par réplique), orthographe officielle (ɛ ɔ ɲ ŋ), nombres écrits en lettres, pas de mélange français/bambara sauf mots courants (ordinatɛri, telefɔni, internɛti) | répliques `bm` |
| Réalisateur | Choisit un type de scène par idée dans le catalogue ci-dessous, avec les icônes | `episode.json` |
| Contrôleur | Vérifie le JSON, la longueur, les icônes, lance `pipeline/preview.py` et regarde les images | feu vert |
| ✋ Olivier | Relit et corrige le bambara (optionnel) | validation |
| Voix + Monteur (GitHub Actions) | `pipeline/produce.py` : voix MALIBA-AI → mixage → rendu MP4 | `episodes/<slug>/out/<slug>.mp4` |

## Format `episodes/<slug>/episode.json`

```json
{
  "slug": "002-c-est-quoi-internet",       // = nom du dossier
  "title": "C'est quoi Internet ?",
  "lesson": 2,                              // "Kalan 2" affiché en haut
  "tag": "IA · Bamanankan na",
  "voice": {"engine": "auto", "speaker": "Seydou", "speed": 1.0},
  "pronounce": {"IA": "i a"},              // remplacements pour la voix seulement
  "music_volume": 0.4,
  "scenes": [
    {"type": "intro", "params": {"title": "WEB"},
     "bm": ["Réplique 1?", "Réplique 2?"],   // chaque réplique = un morceau de voix ; [crochets] = mot surligné
     "fr": "Traduction française courte (sous-titre secondaire)"}
  ]
}
```

Règles : 5 à 7 scènes ; 1 à 3 répliques par scène ; toujours commencer par `intro` et finir par `outro`.

## Catalogue des scènes

| type | Ce qu'on voit | params |
|---|---|---|
| `intro` | Le robot tombe du ciel, gros titre lettre par lettre, points d'interrogation | `title` (1–5 lettres, ex. "IA", "WEB", "5G"), `questions` (true/false) |
| `concept` | Un grand écran où une icône se dessine en néon + circuits ; option : 3 personnes qui la fabriquent | `icon` ∈ brain, globe, wifi, chip, phone, cloud, bulb, eye, network ; `people` (bool) ; `label` (texte court sous l'icône) |
| `learn` | Un enfant regarde passer des animaux devant un baobab, un compteur monte, puis il comprend (bulle) | `animal` ∈ cow (vaches animées) ou toute icône (goat, chicken, fish…) ; `word` (mot bambara) ; `count` (1–6) |
| `data` | Le robot avale des centaines d'images, un compteur explose | `to` (nombre final), `label`, `icons` (liste d'icônes) |
| `cards` | 1 à 3 cartes qui arrivent chacune au moment où sa réplique est dite | `cards`: [{`title` (bambara), `sub` (français), `icon`, `color`}] — mettre autant de répliques que de cartes |
| `robot_says` | Le robot parle, une bulle montre une grande icône et un mot | `icon`, `label` |
| `compare` | Deux choses côte à côte avec un signe au milieu (→, =, ≠, +, vs) | `left` {icon,label,color}, `right` {icon,label,color}, `sign` — la 2e réplique fait apparaître la droite |
| `outro` | Le robot salue, confettis, bouton « s'abonner » | `cta` (ex. "Aw ye an tugu!") |

Couleurs : teal, orange, red, green, blue, purple.

Icônes : cow, goat, chicken, sun, tree, house, fish, millet, phone, globe, wifi, chat, question, health, book, money, bulb,
computer, camera, people, farmer, water, bolt, satellite, brain, robot, check, cross, warning, lock, school, car, medicine, mosquito, image.

Pour un nouveau besoin visuel récurrent, on ajoute un type de scène ou une icône dans `engine/index.html` (une seule fois),
puis on le documente ici.

## Voix

- `engine: "auto"` essaie **Spark** (MALIBA-AI/bambara-tts, 10 voix : Adama, Moussa, Bourama, Modibo, Seydou, Amadou, Bakary, Ngolo, Ibrahima, Amara), puis **VITS** (MALIBA-AI/malian-tts).
- Modèles à accès restreint : secret GitHub `HF_TOKEN` requis. Licences non commerciales (CC BY-NC) → usage éducatif uniquement.
- Test des voix : onglet Actions → « Tester les voix bambara » → échantillons dans `voice-tests/`.

## Commandes

```bash
python pipeline/preview.py episodes/<slug>   # images de contrôle sans voix
python pipeline/produce.py episodes/<slug>   # voix + mixage + vidéo (a besoin de Hugging Face)
```
