# Feuille de route GPS

Ce repository contient la préparation de la base GPS en vue de constituer un base de travail commune aux partenaires du Panel Lémanique

## Contexte : Panel Lémanique
Dans le cadre de l’enquête du Panel Lémanique, un suivi gps a été réalisé du 24 avril au 5 juin 2023 auprès de 2806 personnes résidentes de la zone d’étude. Ces données ont été collectées par MotionTag, puis livrées (base brute) sous la forme de géodonnées de deux types : legs et staypoints. Les géodonnées de type legs se rapprochent de l’étape1 de déplacement, tel que renseigné dans le mrmt. Les staypoints se rapprochent des “activités” ou transbordements.

En l’état, les données ne sont que partiellement exploitables pour en faire des analyses de mobilité, notamment pour les raisons suivantes :

- Perte de signal : certaines traces présentent des anomalies dans leur géocodage ce qui peut notamment mener à une sous-évaluation des calculs de distance ;
- Etapes, déplacements et boucles : la base brute est une base fine à l’étape de déplacement renseignées par un leg_id, mais aucun identifiant ne permet de reconstituer une base déplacement – utile notamment dans les analyses de motifs de déplacement ou de l’intermodalité
- Jour sans observation : en l’état, il ne semble pas simple de distinguer les jours non- déplacés des jours non-détectés
- Inférence modale : en majorité, les modes de déplacement sont inférés de manière automatique dans la base brute. Cela conduit notamment à confondre certains modes tels que les mode bus et les vélos
- Modes et motifs : les catégories proposées dans la base brute ne sont pas entièrement compatibles avec le mrmt
- Période de suivi variable : les dates de début et de fin – et a fortiori la durée du suivi gps – sont variables d’un·e répondant·e à l’autre

## Objectifs de la feuille de route
L'objectif de notre plan d'analyse est de créer une base de travail commune pour les partenaires du Panel Lémanique à partir des données brutes – en vue de mener des analyses quantitatives sur les données. Cela implique de formuler une série d'hypothèses et de faire des choix structurants pour les analyses à venir. Nous chercherons à optimiser la correspondance entre la base du panel GPS et les bases mrmt passées et futures, tout en proposant des niveaux d'agrégation cohérents avec les pratiques opérationnelles des cantons, sans perdre la richesse des données, y compris la variabilité journalière des pratiques de mobilité. Nous procéderons à un nettoyage, un filtrage, une transformation et une normalisation des données GPS brutes.

Les objectifs principaux de la présente feuille de route sont les suivants :
1. Constituer une base de travail gps
2. Identifier les parts modales représentatives de la base par territoire
3. Définir un plan d’analyses futures

## Difficultés
Aux vues de l’originalité des données et de leur structure complexe (timeseries géolocalisées), la feuille de route se veut partiellement exploratoire. Une méthode de travail pas-à-pas en concertation avec les partenaires du Panel permettra d’atteindre les objectifs i.e. constituer une base de travail des données gps satisfaisante. La littérature est encore lacunaire et éparse concernant le traitement opérationnel de données de type gps pour des analyses fines de mobilité.
Le poids des données – notamment de trajectoires (legs) – rend la manipulation de la base brute difficile et des compétences avancées en gestion et stockage et compression des données et parallélisation des scripts et algorithmes de transformation.
La sensibilité des données implique une manipulation soignée et pseudonymisée des données brutes sur des serveurs sécurisés.

## Données d’entrée
Les tâches de cette feuille de route seront réalisées à partir de trois fichiers de données :
• La base « étape » GPS
• Les statistiques des usagers
• La base de correspondance aux transports publics

## Taxonomie des analyses
| Modules | Sources de données | Données d'entrée | Notebooks | Données de sortie | Description |
|---------|--------------------|------------------|-----------|-------------------|-------------|
| Module 0 | motiontag | storyline | module0_parsestoryline.ipynb | legs.pkl, staypoints.pkl | "séparer les pistes et les séjours, convertir la géométrie de EWKB en objet shapely et formater certaines variables, convertir les chaînes de plusieurs lignes en chaînes de lignes simples" |

