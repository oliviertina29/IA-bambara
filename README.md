# IA Bamanankan na 🇲🇱

Des vidéos courtes pour expliquer la technologie et l'intelligence artificielle **en bambara**, à celles et ceux qui n'y ont pas encore accès.

Chaque épisode est un simple fichier `episodes/<slug>/episode.json`. Dès qu'il arrive dans le dépôt, GitHub Actions :
1. fait parler le texte bambara avec les modèles de [MALIBA-AI](https://github.com/MALIBA-AI/bambara-tts),
2. mixe la voix avec une petite musique,
3. anime les scènes (robot, enfant, animaux, cartes…) et exporte une vidéo verticale MP4 prête pour TikTok.

La vidéo apparaît dans `episodes/<slug>/out/`.

➡️ Tout est expliqué dans [docs/GUIDE.md](docs/GUIDE.md).

Projet éducatif, non commercial. Voix : modèles MALIBA-AI (licences CC BY-NC).
