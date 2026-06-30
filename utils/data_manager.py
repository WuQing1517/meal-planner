import json
import os
import uuid
from config import DATA_DIR, NUTRIENTS_FILE, DAILY_REQUIREMENTS_FILE, MEALS_FILE, FOODS_FILE, PLANS_FILE

CONSTRAINT_RULES_FILE = os.path.join(DATA_DIR, 'constraint_rules.json')


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_json(file_path, default=None):
    ensure_data_dir()
    if not os.path.exists(file_path):
        return default if default is not None else {}
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(file_path, data):
    ensure_data_dir()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_id():
    return str(uuid.uuid4())[:8]


# 营养物质操作
def get_nutrients():
    data = load_json(NUTRIENTS_FILE, {"nutrients": []})
    return data.get("nutrients", [])


def add_nutrient(name, unit, description=""):
    nutrients = get_nutrients()
    nutrient = {
        "id": generate_id(),
        "name": name,
        "unit": unit,
        "description": description
    }
    nutrients.append(nutrient)
    save_json(NUTRIENTS_FILE, {"nutrients": nutrients})
    return nutrient


def update_nutrient(nutrient_id, name, unit, description=""):
    nutrients = get_nutrients()
    for n in nutrients:
        if n["id"] == nutrient_id:
            n["name"] = name
            n["unit"] = unit
            n["description"] = description
            save_json(NUTRIENTS_FILE, {"nutrients": nutrients})
            return n
    return None


def delete_nutrient(nutrient_id):
    nutrients = get_nutrients()
    nutrients = [n for n in nutrients if n["id"] != nutrient_id]
    save_json(NUTRIENTS_FILE, {"nutrients": nutrients})


# 每日需求操作
def get_daily_requirements():
    data = load_json(DAILY_REQUIREMENTS_FILE, {"daily_requirements": {}})
    return data.get("daily_requirements", {})


def save_daily_requirements(requirements):
    save_json(DAILY_REQUIREMENTS_FILE, {"daily_requirements": requirements})


# 约束规则操作
def get_constraint_rules():
    data = load_json(CONSTRAINT_RULES_FILE, {"rules": {}})
    return data.get("rules", {})


def save_constraint_rules(rules):
    save_json(CONSTRAINT_RULES_FILE, {"rules": rules})


# 餐数配置操作
def get_meal_plans():
    data = load_json(MEALS_FILE, {"meal_plans": []})
    return data.get("meal_plans", [])


def add_meal_plan(name, meals):
    plans = get_meal_plans()
    plan = {
        "id": generate_id(),
        "name": name,
        "meals": meals
    }
    plans.append(plan)
    save_json(MEALS_FILE, {"meal_plans": plans})
    return plan


def update_meal_plan(plan_id, name, meals):
    plans = get_meal_plans()
    for p in plans:
        if p["id"] == plan_id:
            p["name"] = name
            p["meals"] = meals
            save_json(MEALS_FILE, {"meal_plans": plans})
            return p
    return None


def delete_meal_plan(plan_id):
    plans = get_meal_plans()
    plans = [p for p in plans if p["id"] != plan_id]
    save_json(MEALS_FILE, {"meal_plans": plans})


# 食品操作
def get_foods():
    data = load_json(FOODS_FILE, {"foods": []})
    return data.get("foods", [])


def add_food(name, category, nutrition_per_100g, priority=1):
    foods = get_foods()
    food = {
        "id": generate_id(),
        "name": name,
        "category": category,
        "unit": "g",
        "priority": priority,
        "nutrition_per_100g": nutrition_per_100g
    }
    foods.append(food)
    save_json(FOODS_FILE, {"foods": foods})
    return food


def update_food(food_id, name, category, nutrition_per_100g, priority=1):
    foods = get_foods()
    for f in foods:
        if f["id"] == food_id:
            f["name"] = name
            f["category"] = category
            f["nutrition_per_100g"] = nutrition_per_100g
            f["priority"] = priority
            save_json(FOODS_FILE, {"foods": foods})
            return f
    return None


def delete_food(food_id):
    foods = get_foods()
    foods = [f for f in foods if f["id"] != food_id]
    save_json(FOODS_FILE, {"foods": foods})


# 配比方案操作
def get_plans():
    data = load_json(PLANS_FILE, {"plans": []})
    return data.get("plans", [])


def save_plan(plan_data):
    plans = get_plans()
    plan_data["id"] = generate_id()
    plans.append(plan_data)
    save_json(PLANS_FILE, {"plans": plans})
    return plan_data
