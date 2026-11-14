# Calibration du juge de fidélité (20 cas annotés)

Protocole : un LLM (Claude) a pré-annoté chaque cas avec une justification (data/pre_annotations.jsonl), sans connaître le verdict du juge ; un humain a relu ces justifications face aux extraits et les a validées (data/annotations.jsonl). Les cas n0-doc-06 et n0-doc-15 sont des cas limites, tranchés en « non fidèle » en appliquant la règle à la lettre.

- Accord avec l'annotation humaine : 95%
- Réponses non fidèles selon l'humain : 10, dont repérées par le juge : 9
- Réponses fidèles selon l'humain : 10, dont reconnues par le juge : 10

Désaccords :

- n0-doc-06 : humain non fidèle, juge fidèle. 
