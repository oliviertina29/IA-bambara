---
name: video-bambara
description: Produire une vidéo TikTok éducative en bambara (tech, IA, science) de bout en bout avec l'équipe d'agents et le dépôt oliviertina29/IA-bambara. Utiliser quand Olivier demande une vidéo en bambara ou tape /video-bambara <sujet>.
---

# /video-bambara <sujet>

Projet éducatif d'Olivier : expliquer la technologie et l'IA **en bambara parlé** à des personnes qui ne lisent pas forcément.
Le dépôt `oliviertina29/IA-bambara` contient le moteur d'animation, le pipeline et `docs/GUIDE.md` (catalogue des scènes, format JSON). **Tout se fait gratuitement** : Claude (abonnement) pour le texte, GitHub Actions pour la voix et le rendu.

## 0. Préparer (silencieux)
1. `add_repo` owner `oliviertina29`, repo `IA-bambara`, access `push`, puis clone. Lire `docs/GUIDE.md` en entier.
2. Numéro d'épisode = dernier dossier `episodes/NNN-*` + 1. Slug = `NNN-mots-cles-du-sujet` (minuscules, tirets, sans accents).
3. Créer une liste de tâches : Recherche → Script → Bambara → Réalisation → Contrôle → Validation → Production → Livraison.

## 1. L'équipe d'agents (outil Agent, en série, chacun reçoit la sortie du précédent + le GUIDE)
- **Chercheur** (general-purpose) : faits vérifiés sur le sujet, 3–5 idées très simples, 2–3 exemples tirés de la vie malienne, sources. Pas de jargon.
- **Scénariste** : script français, 5–7 scènes (accroche → idée → exemple concret → usages → appel à suivre), 90–120 mots, 35–60 s. Ton chaleureux, comme un grand frère qui explique au grin.
- **Traducteur bambara** : pour chaque scène, 1–3 répliques en bambara parlé naturel, ≤ 8 mots, orthographe standard (ɛ ɔ ɲ ŋ), nombres en toutes lettres, mots-clés entre [crochets]. Signaler en liste séparée tout terme dont il n'est pas sûr, avec 1–2 alternatives.
- **Réalisateur** : écrit `episode.json` selon le GUIDE : un type de scène par idée, icônes existantes uniquement, `intro` en premier et `outro` en dernier, `cards` = autant de répliques que de cartes.
- **Contrôleur** (toi-même) : JSON valide, types/icônes du catalogue, lancer `python pipeline/preview.py episodes/<slug>` (installer `playwright` et chromium si besoin) et **regarder** les images : rien ne déborde, textes lisibles. Corriger puis relancer.

## 2. Validation d'Olivier
Sauf s'il a dit « valide automatiquement », montrer avec AskUserQuestion : le titre, chaque scène en bambara + français, et les termes douteux du traducteur. Options : « Valider », « Je corrige » (appliquer ses corrections), « Changer le sujet ». Olivier est locuteur natif : ses corrections font foi.

## 3. Production (GitHub Actions)
1. Supprimer `episodes/<slug>/out` s'il existe, commit `Épisode NNN : <titre>` sur `main`, push. Le workflow « Produire la vidéo » démarre seul.
2. Attendre : suivre la course GitHub Actions (API publique), puis `git pull` et vérifier `episodes/<slug>/out/status.json` (boucle Bash avec timeout ≤ 10 min, répétée ; maximum ~60 min).
3. `status.ok = true` → la vidéo est `episodes/<slug>/out/<slug>.mp4`.
   `status.ok = false` → lire `error`, `trace` et `out/log.txt`, corriger (épisode ou pipeline), re-push.
   Rien après 60 min → dire à Olivier de vérifier l'onglet Actions (secret `HF_TOKEN`, quota).

## 4. Livraison
Envoyer le MP4 avec SendUserFile. Réponse courte : titre, durée, voix utilisée (`timing.json → engine`), et une suggestion de légende TikTok en bambara + français avec 3–5 hashtags (#bamanankan #IA #Mali …).

## Règles
- Ne jamais inventer de fait : le Chercheur cite ses sources.
- Le bambara doit sonner parlé, pas traduit mot à mot. En cas de doute, demander à Olivier.
- Si un visuel manque vraiment, ajouter une icône ou un type de scène dans `engine/index.html`, le documenter dans `docs/GUIDE.md`, et le tester avec `preview.py`.
- Mon environnement ne joint pas Hugging Face : la voix se fait **uniquement** sur GitHub Actions.
- Voix par défaut : `"voice": {"engine": "spark", "speaker": "Moussa"}` (Spark MALIBA-AI via GGUF public, choisie par Olivier). Repli automatique sur VITS.
- La production prend ~5–6 min ; suivre la course via `https://api.github.com/repos/oliviertina29/IA-bambara/actions/runs?per_page=3` (champ head_sha du commit poussé).
