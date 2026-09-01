---
name: fitness-nutrition
description: "Workout planning, macros, and body metrics via wger/USDA."
platforms: [linux, macos, windows]
version: 1.0.0
author: Hailey Marshall (haileymarshall), Hermes Agent
authors:
  - haileymarshall
license: MIT
metadata:
  hermes:
    tags: [health, fitness, nutrition, gym, workout, diet, exercise]
    category: health
    prerequisites:
      commands: [curl, python]
required_environment_variables:
  - name: USDA_API_KEY
    prompt: "USDA FoodData Central API key (free)"
    help: "Get one free at https://fdc.nal.usda.gov/api-key-signup/ — or skip to use DEMO_KEY with lower rate limits"
    required_for: "higher rate limits on food/nutrition lookups (DEMO_KEY works without signup)"
    optional: true
---

# Fitness & Nutrition

role: fitness and sports-nutrition information operator
do: query wger/USDA; run offline calculators; explain metrics; scale portions; sanity-check estimates
inputs: exercise/muscle/category/equipment query; food/FDC ID; body metrics; training goal; optional `USDA_API_KEY`
outputs: exercise details; per-100g nutrition; BMI/TDEE/1RM/macros/body-fat estimates; cited source context
¬: present estimates as diagnosis; hide uncertainty; treat BMI as body composition; omit units/portion basis; expose API keys

Use two free data sources and offline stdlib calculators:

- wger: https://wger.de/api/v2/, 690+ exercises with muscles, equipment, images; public endpoints need no authentication
- USDA FoodData Central: https://api.nal.usda.gov/fdc/v1/, 380,000+ foods; `DEMO_KEY` works instantly, free signup gives higher limits
- calculators: BMI, TDEE (Mifflin-St Jeor), 1RM (Epley/Brzycki/Lombardi), macro splits, body-fat % (US Navy)

## When to Use

- exercises, workouts, gym routines, muscle groups, workout splits
- food macros, calories, protein, meal planning, calorie counting
- BMI, body fat, TDEE, caloric surplus/deficit
- 1RM estimates, training percentages, progressive overload
- cutting, bulking, or maintenance macro ratios

## Prerequisites

- `curl` and Python; no pip dependencies for the API path/calculators
- optional `USDA_API_KEY`; otherwise `DEMO_KEY`
- USDA signup: https://fdc.nal.usda.gov/api-key-signup/

## Procedure

### 1. Exercise lookup via wger

Public endpoints return JSON with no auth. Add `format=json` and `language=2`
(English) to exercise queries. Select endpoint by intent:

- muscle: `/api/v2/exercise/?muscles={id}&language=2&status=2&format=json`
- category: `/api/v2/exercise/?category={id}&language=2&status=2&format=json`
- equipment: `/api/v2/exercise/?equipment={id}&language=2&status=2&format=json`
- name: `/api/v2/exercise/search/?term={query}&language=english&format=json`
- details: `/api/v2/exerciseinfo/{exercise_id}/?format=json`

Reference IDs:

| ID | Category |
|----|-------------|
| 8 | Arms |
| 9 | Legs |
| 10 | Abs |
| 11 | Chest |
| 12 | Back |
| 13 | Shoulders |
| 14 | Calves |
| 15 | Cardio |

| ID | Muscle | ID | Muscle |
|----|---------------------------|----|-------------------------|
| 1 | Biceps brachii | 2 | Anterior deltoid |
| 3 | Serratus anterior | 4 | Pectoralis major |
| 5 | Obliquus externus | 6 | Gastrocnemius |
| 7 | Rectus abdominis | 8 | Gluteus maximus |
| 9 | Trapezius | 10 | Quadriceps femoris |
| 11 | Biceps femoris | 12 | Latissimus dorsi |
| 13 | Brachialis | 14 | Triceps brachii |
| 15 | Soleus | | |

| ID | Equipment |
|----|----------------|
| 1 | Barbell |
| 3 | Dumbbell |
| 4 | Gym mat |
| 5 | Swiss Ball |
| 6 | Pull-up bar |
| 7 | none (bodyweight) |
| 8 | Bench |
| 9 | Incline bench |
| 10 | Kettlebell |

Name search:

```bash
# Search exercises by name
QUERY="$1"
ENCODED=$(python -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$QUERY")
curl -s "https://wger.de/api/v2/exercise/search/?term=${ENCODED}&language=english&format=json" \
  | python -c "
import json,sys
data=json.load(sys.stdin)
for s in data.get('suggestions',[])[:10]:
    d=s.get('data',{})
    print(f\"  ID {d.get('id','?'):>4} | {d.get('name','N/A'):<35} | Category: {d.get('category','N/A')}\")
"
```

Details:

```bash
# Get full details for a specific exercise
EXERCISE_ID="$1"
curl -s "https://wger.de/api/v2/exerciseinfo/${EXERCISE_ID}/?format=json" \
  | python -c "
import json,sys,html,re
data=json.load(sys.stdin)
trans=[t for t in data.get('translations',[]) if t.get('language')==2]
t=trans[0] if trans else data.get('translations',[{}])[0]
desc=re.sub('<[^>]+>','',html.unescape(t.get('description','N/A')))
print(f\"Exercise  : {t.get('name','N/A')}\")
print(f\"Category  : {data.get('category',{}).get('name','N/A')}\")
print(f\"Primary   : {', '.join(m.get('name_en','') for m in data.get('muscles',[])) or 'N/A'}\")
print(f\"Secondary : {', '.join(m.get('name_en','') for m in data.get('muscles_secondary',[])) or 'none'}\")
print(f\"Equipment : {', '.join(e.get('name','') for e in data.get('equipment',[])) or 'bodyweight'}\")
print(f\"How to    : {desc[:500]}\")
imgs=data.get('images',[])
if imgs: print(f\"Image     : {imgs[0].get('image','')}\")
"
```

Filters:

```bash
# List exercises filtering by muscle, category, or equipment
# Combine filters as needed: ?muscles=4&equipment=1&language=2&status=2
FILTER="$1"  # e.g. "muscles=4" or "category=11" or "equipment=3"
curl -s "https://wger.de/api/v2/exercise/?${FILTER}&language=2&status=2&limit=20&format=json" \
  | python -c "
import json,sys
data=json.load(sys.stdin)
print(f'Found {data.get(\"count\",0)} exercises.')
for ex in data.get('results',[]):
    print(f\"  ID {ex['id']:>4} | muscles: {ex.get('muscles',[])} | equipment: {ex.get('equipment',[])}\")
"
```

### 2. Nutrition lookup via USDA

Use `USDA_API_KEY` when set; otherwise `DEMO_KEY`. Limits: `DEMO_KEY` 30
requests/hour; free signup key 1,000 requests/hour.

```bash
# Search foods by name
FOOD="$1"
API_KEY="${USDA_API_KEY:-DEMO_KEY}"
ENCODED=$(python -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$FOOD")
curl -s "https://api.nal.usda.gov/fdc/v1/foods/search?api_key=${API_KEY}&query=${ENCODED}&pageSize=5&dataType=Foundation,SR%20Legacy" \
  | python -c "
import json,sys
data=json.load(sys.stdin)
foods=data.get('foods',[])
if not foods: print('No foods found.'); sys.exit()
for f in foods:
    n={x['nutrientName']:x.get('value','?') for x in f.get('foodNutrients',[])}
    cal=n.get('Energy','?'); prot=n.get('Protein','?')
    fat=n.get('Total lipid (fat)','?'); carb=n.get('Carbohydrate, by difference','?')
    print(f\"{f.get('description','N/A')}\")
    print(f\"  Per 100g: {cal} kcal | {prot}g protein | {fat}g fat | {carb}g carbs\")
    print(f\"  FDC ID: {f.get('fdcId','N/A')}\")
    print()
"
```

```bash
# Detailed nutrient profile by FDC ID
FDC_ID="$1"
API_KEY="${USDA_API_KEY:-DEMO_KEY}"
curl -s "https://api.nal.usda.gov/fdc/v1/food/${FDC_ID}?api_key=${API_KEY}" \
  | python -c "
import json,sys
d=json.load(sys.stdin)
print(f\"Food: {d.get('description','N/A')}\")
print(f\"{'Nutrient':<40} {'Amount':>8} {'Unit'}\")
print('-'*56)
for x in sorted(d.get('foodNutrients',[]),key=lambda x:x.get('nutrient',{}).get('rank',9999)):
    nut=x.get('nutrient',{}); amt=x.get('amount',0)
    if amt and float(amt)>0:
        print(f\"  {nut.get('name',''):<38} {amt:>8} {nut.get('unitName','')}\")
"
```

### 3. Offline calculators

Use helper scripts for batches or these commands for single calculations:

- `python scripts/body_calc.py bmi <weight_kg> <height_cm>`
- `python scripts/body_calc.py tdee <weight_kg> <height_cm> <age> <M|F> <activity 1-5>`
- `python scripts/body_calc.py 1rm <weight> <reps>`
- `python scripts/body_calc.py macros <tdee_kcal> <cut|maintain|bulk>`
- `python scripts/body_calc.py bodyfat <M|F> <neck_cm> <waist_cm> [hip_cm] <height_cm>`

Formula rationale: `references/FORMULAS.md`.

## Pitfalls

- wger returns all languages by default; add `language=2` for English.
- wger includes unverified submissions; add `status=2` for approved exercises.
- USDA `DEMO_KEY` allows 30 req/hour; add `sleep 2` between batches or obtain a free key.
- USDA values are per 100g; scale to actual portion size.
- BMI does not distinguish muscle from fat; muscular high BMI is not necessarily unhealthy.
- Body-fat formulas estimate ±3-5%; recommend DEXA for precision.
- 1RM formulas lose accuracy above 10 reps; sets of 3-5 are best estimates.
- wger `exercise/search` uses `term`, not `query`.

## Verification

- exercise search results include exercise names, muscle groups, and equipment
- nutrition lookup returns per-100g kcal, protein, fat, and carbohydrate
- calculator results have units and pass sanity checks; typical adult TDEE is 1500-3500

## Quick Reference

| Task | Source | Endpoint |
|------|--------|----------|
| Search exercises by name | wger | `GET /api/v2/exercise/search/?term=&language=english` |
| Exercise details | wger | `GET /api/v2/exerciseinfo/{id}/` |
| Filter by muscle | wger | `GET /api/v2/exercise/?muscles={id}&language=2&status=2` |
| Filter by equipment | wger | `GET /api/v2/exercise/?equipment={id}&language=2&status=2` |
| List categories | wger | `GET /api/v2/exercisecategory/` |
| List muscles | wger | `GET /api/v2/muscle/` |
| Search foods | USDA | `GET /fdc/v1/foods/search?query=&dataType=Foundation,SR Legacy` |
| Food details | USDA | `GET /fdc/v1/food/{fdcId}` |
| BMI / TDEE / 1RM / macros | offline | `python scripts/body_calc.py` |