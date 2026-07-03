import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# JSON数据文件路径
NUTRIENTS_FILE = os.path.join(DATA_DIR, 'nutrients.json')
DAILY_REQUIREMENTS_FILE = os.path.join(DATA_DIR, 'daily_requirements.json')
MEALS_FILE = os.path.join(DATA_DIR, 'meals.json')
FOODS_FILE = os.path.join(DATA_DIR, 'foods.json')
PLANS_FILE = os.path.join(DATA_DIR, 'plans.json')

# Flask配置
SECRET_KEY = 'meal-planner-secret-key'
DEBUG = True
