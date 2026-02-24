# Location Vacances - Agent d'extraction depuis les descriptions

## Objectif

L'agent `description_extractor_agent.py` exploite **uniquement** les champs `description_courte` et `description_complete` pour enrichir les listings. Il ne modifie jamais les deux descriptions.

## Champs enrichis

À partir des descriptions, l'agent peut extraire et compléter :

| Champ | Exemple d'extraction |
|-------|---------------------|
| prix, prix_text | "1.750 par mois" → 1750 |
| prix_par_jour | "120 TND/jour" → 120 |
| surface, surface_text | "100 m²" → 100 |
| type_bien | "S2 Meublé" → S2 |
| nombre_pieces | S2 → 2 |
| nombre_chambres | "Deux chambres" → 2 |
| nombre_sdb | "Une salle de bain" → 1 |
| capacite | "4 personnes" → 4 |
| nuits_minimum | "30 nuits minimum" ou "par mois" → 30 |
| etage | "10ème étage", "RDC" |
| residence | "Résidence Les Flamants" |
| ville, quartier | Cité Ennasr 2, Jardin de l'Aouina |
| equipements, amenities_vacances | parking, climatisation, meublé... |
| contact_info (telephone) | "Contact 22 135 639" |
| conditions_location | parking_inclus, syndic_compris |
| informations_supplementaires | meuble |

## Usage

```bash
cd location_vacance

# Mode complement (défaut) : ne remplit que les champs vides
python description_extractor_agent.py -f mubawab_location_vacances_complet_20260201_152000.json

# Fichier de sortie personnalisé
python description_extractor_agent.py -f mubawab_location_vacances_complet_xxx.json -o resultat_enrichi.json

# Mode overwrite : les extraits remplacent les valeurs existantes
python description_extractor_agent.py -f fichier.json --mode overwrite
```

## Modes

- **complement** : Complète uniquement les champs vides (id, url, descriptions inchangés)
- **merge** : Même logique, fusion des listes d'équipements
- **overwrite** : Les valeurs extraites remplacent les existantes

## Sortie

Le fichier enrichi contient :
- Tous les champs originaux (id, titre, url, description_courte, description_complete...)
- Les champs complétés à partir des descriptions
- `description_extracted` : dict des valeurs extraites (traçabilité)
