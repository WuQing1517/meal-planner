from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SECRET_KEY, DEBUG, DATA_DIR
from utils.data_manager import (
    get_nutrients, add_nutrient, update_nutrient, delete_nutrient,
    get_daily_requirements, save_daily_requirements,
    get_constraint_rules, save_constraint_rules,
    get_meal_plans, add_meal_plan, update_meal_plan, delete_meal_plan,
    get_foods, add_food, update_food, delete_food,
    get_plans, save_plan
)
from utils.optimizer import optimize_meal_plan

app = Flask(__name__)
app.secret_key = SECRET_KEY


ADMIN_USERNAME = 'wuqing'
ADMIN_PASSWORD = 'HZBLOVEJYH'

@app.route('/')
def index():
    return render_template('index.html')


# 后台管理
@app.route('/admin')
def admin():
    # 检查是否已登录
    if request.args.get('logout'):
        return render_template('admin_login.html')
    if 'admin_logged_in' not in session:
        return render_template('admin_login.html')
    return render_template('admin.html')


@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return redirect(url_for('admin'))
    return render_template('admin_login.html', error='用户名或密码错误')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))


@app.route('/api/prizes')
def get_prizes():
    prizes_file = os.path.join(DATA_DIR, 'prizes.json')
    if os.path.exists(prizes_file):
        with open(prizes_file, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    # 默认奖品
    default_prizes = [
        {"name": "蛋白质补给卡", "desc": "额外获得20g蛋白质配额！", "icon": "💪"},
        {"name": "碳水狂欢券", "desc": "今天碳水可以多吃50g！", "icon": "🍞"},
        {"name": "脂肪赦免令", "desc": "今天脂肪摄入不计入总量！", "icon": "🥑"},
        {"name": "营养师咨询", "desc": "获得一次专业营养建议！", "icon": "👨‍⚕️"},
        {"name": "健身会员卡", "desc": "获得一周免费健身！", "icon": "🏋️"},
        {"name": "美食优惠券", "desc": "下周可以吃一顿大餐！", "icon": "🍔"}
    ]
    return jsonify(default_prizes)


@app.route('/api/prizes/save', methods=['POST'])
def save_prizes():
    data = request.get_json()
    prizes_file = os.path.join(DATA_DIR, 'prizes.json')
    with open(prizes_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'奖品已保存: {len(data)}个')
    return jsonify({'status': 'ok'})


# 许愿记录管理API
@app.route('/api/wishes')
def get_wishes():
    wishes_file = os.path.join(DATA_DIR, 'wishes.json')
    if os.path.exists(wishes_file):
        with open(wishes_file, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify([])


@app.route('/api/wishes/delete', methods=['POST'])
def delete_wish():
    data = request.get_json()
    index = data.get('index')
    wishes_file = os.path.join(DATA_DIR, 'wishes.json')
    if os.path.exists(wishes_file):
        with open(wishes_file, 'r', encoding='utf-8') as f:
            wishes = json.load(f)
        if 0 <= index < len(wishes):
            wishes.pop(index)
            with open(wishes_file, 'w', encoding='utf-8') as f:
                json.dump(wishes, f, ensure_ascii=False, indent=2)
            return jsonify({'status': 'ok'})
    return jsonify({'error': '删除失败'}), 400


@app.route('/api/wishes/clear', methods=['POST'])
def clear_wishes():
    wishes_file = os.path.join(DATA_DIR, 'wishes.json')
    with open(wishes_file, 'w', encoding='utf-8') as f:
        json.dump([], f)
    return jsonify({'status': 'ok'})


# 重置许愿（清空许愿记录和触发记录）
@app.route('/api/reset-wishes', methods=['POST'])
def reset_wishes():
    # 清空许愿记录
    wishes_file = os.path.join(DATA_DIR, 'wishes.json')
    with open(wishes_file, 'w', encoding='utf-8') as f:
        json.dump([], f)
    
    # 保存重置时间
    import time
    reset_time_file = os.path.join(DATA_DIR, 'reset_time.txt')
    with open(reset_time_file, 'w') as f:
        f.write(str(time.time()))
    
    return jsonify({'status': 'ok', 'message': '许愿已重置，所有用户可以重新许愿'})


# 获取重置标记
@app.route('/api/reset-flag')
def get_reset_flag():
    reset_time_file = os.path.join(DATA_DIR, 'reset_time.txt')
    reset_time = "0"
    if os.path.exists(reset_time_file):
        with open(reset_time_file, 'r') as f:
            reset_time = f.read().strip()
    return jsonify({'reset_time': reset_time})


# 清空彩蛋触发历史
@app.route('/api/secret-wishes/clear', methods=['POST'])
def clear_secret_wishes():
    # 这个在前端localStorage中，通过返回特殊标志让前端清除
    return jsonify({'status': 'ok', 'clear_localStorage': True})


# 许愿记录
@app.route('/api/submit-wish', methods=['POST'])
def submit_wish():
    data = request.get_json()
    time_str = data.get('time', '')
    wish = data.get('wish', '')

    # 保存到本地文件
    wishes_file = os.path.join(DATA_DIR, 'wishes.json')
    wishes = []
    if os.path.exists(wishes_file):
        with open(wishes_file, 'r', encoding='utf-8') as f:
            wishes = json.load(f)

    wishes.append({
        'time': time_str,
        'wish': wish
    })

    with open(wishes_file, 'w', encoding='utf-8') as f:
        json.dump(wishes, f, ensure_ascii=False, indent=2)

    return jsonify({'status': 'ok'})


# 魔搭API获取许愿反馈
@app.route('/api/wish-feedback', methods=['POST'])
def wish_feedback():
    data = request.get_json()
    wish = data.get('wish', '')
    print(f'收到许愿: {wish}')

    if not wish:
        return jsonify({'feedback': '祝你今天一切顺利！'})

    # 根据许愿内容生成个性化的祝福语
    feedbacks = {
        '减肥': ['坚持就是胜利，每一步都在靠近目标！', '健康减重，你一定可以的！', '管住嘴迈开腿，好身材在等你！'],
        '学习': ['知识改变命运，加油学习！', '每天进步一点点，成功就在眼前！', '学海无涯，但你已经很棒了！'],
        '工作': ['努力工作，未来可期！', '你的付出终将得到回报！', '职场之路，步步高升！'],
        '健康': ['身体健康是最大的财富！', '愿你永远健康快乐！', '健康生活，从今天开始！'],
        '爱情': ['愿你遇到对的人！', '爱情会来的，耐心等待！', '你值得被爱！'],
        '财富': ['财源广进，日进斗金！', '努力工作，财富自然来！', '愿你财运亨通！'],
        '考试': ['金榜题名，马到成功！', '你已经准备好了，相信自己！', '考试顺利，旗开得胜！']
    }

    # 根据关键词匹配祝福语
    import random
    for keyword, msgs in feedbacks.items():
        if keyword in wish:
            return jsonify({'feedback': random.choice(msgs)})

    # 默认祝福语
    default_feedbacks = [
        '愿你的梦想都能实现！加油！',
        '祝你心想事成，万事如意！',
        '相信自己，你一定可以的！',
        '每一天都是新的开始，加油！',
        '愿你前程似锦，未来可期！'
    ]
    return jsonify({'feedback': random.choice(default_feedbacks)})


@app.route('/wishes')
def wishes_list():
    wishes_file = os.path.join(DATA_DIR, 'wishes.json')
    wishes = []
    if os.path.exists(wishes_file):
        with open(wishes_file, 'r', encoding='utf-8') as f:
            wishes = json.load(f)
    wishes.reverse()  # 最新的在前面
    return render_template('wishes.html', wishes=wishes)


# 背景图片设置
@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/settings/upload-bg', methods=['POST'])
def upload_bg():
    if 'background' in request.files:
        file = request.files['background']
        if file.filename:
            # 保存到static目录
            bg_path = os.path.join(app.static_folder, 'background.jpg')
            file.save(bg_path)
    return redirect(url_for('settings'))


@app.route('/settings/reset-bg', methods=['POST'])
def reset_bg():
    # 删除自定义背景
    bg_path = os.path.join(app.static_folder, 'background.jpg')
    if os.path.exists(bg_path):
        os.remove(bg_path)
    return redirect(url_for('settings'))


@app.route('/static/background.jpg')
def serve_bg():
    return send_from_directory(app.static_folder, 'background.jpg')


# 营养物质管理
@app.route('/nutrients')
def nutrients_list():
    nutrients = get_nutrients()
    return render_template('nutrients.html', nutrients=nutrients)


@app.route('/nutrients/add', methods=['POST'])
def nutrients_add():
    name = request.form.get('name')
    unit = request.form.get('unit', 'g')
    description = request.form.get('description', '')
    if name:
        add_nutrient(name, unit, description)
    return redirect(url_for('nutrients_list'))


@app.route('/nutrients/edit/<nutrient_id>', methods=['POST'])
def nutrients_edit(nutrient_id):
    name = request.form.get('name')
    unit = request.form.get('unit', 'g')
    description = request.form.get('description', '')
    if name:
        update_nutrient(nutrient_id, name, unit, description)
    return redirect(url_for('nutrients_list'))


@app.route('/nutrients/delete/<nutrient_id>', methods=['POST'])
def nutrients_delete(nutrient_id):
    delete_nutrient(nutrient_id)
    return redirect(url_for('nutrients_list'))


# 每日需求配置
@app.route('/daily-requirements')
def daily_requirements():
    nutrients = get_nutrients()
    requirements = get_daily_requirements()
    return render_template('daily_req.html', nutrients=nutrients, requirements=requirements)


@app.route('/daily-requirements/save', methods=['POST'])
def daily_requirements_save():
    nutrients = get_nutrients()
    requirements = {}
    for nutrient in nutrients:
        nid = nutrient['id']
        min_val = request.form.get(f'{nid}_min')
        requirements[nid] = {
            "min": float(min_val) if min_val else None
        }
    save_daily_requirements(requirements)
    return redirect(url_for('daily_requirements'))


# 约束规则配置
@app.route('/constraint-rules')
def constraint_rules():
    nutrients = get_nutrients()
    rules = get_constraint_rules()
    return render_template('constraint_rules.html', nutrients=nutrients, rules=rules)


@app.route('/constraint-rules/save', methods=['POST'])
def constraint_rules_save():
    nutrients = get_nutrients()
    rules = {}
    for nutrient in nutrients:
        nid = nutrient['id']
        exceed_priority = request.form.get(f'{nid}_exceed_priority')
        reduce_priority = request.form.get(f'{nid}_reduce_priority')
        hard_exceed = request.form.get(f'{nid}_hard_exceed') == '1'
        hard_reduce = request.form.get(f'{nid}_hard_reduce') == '1'
        rules[nid] = {
            "hard_exceed": hard_exceed,
            "hard_reduce": hard_reduce,
            "exceed_priority": int(exceed_priority) if exceed_priority else 1,
            "reduce_priority": int(reduce_priority) if reduce_priority else 1
        }
    save_constraint_rules(rules)
    return redirect(url_for('constraint_rules'))


# 餐数配置
@app.route('/meals')
def meals_list():
    plans = get_meal_plans()
    nutrients = get_nutrients()
    nutrient_names = {n['id']: n['name'] for n in nutrients}
    return render_template('meals.html', plans=plans, nutrients=nutrients, nutrient_names=nutrient_names)


@app.route('/meals/add', methods=['POST'])
def meals_add():
    name = request.form.get('name')
    meals_count = int(request.form.get('meals_count', 3))
    nutrients = get_nutrients()

    meals = []
    for i in range(meals_count):
        meal_name = request.form.get(f'meal_{i}_name', f'第{i+1}餐')
        meal_time = request.form.get(f'meal_{i}_time', '')
        is_fixed = request.form.get(f'meal_{i}_is_fixed') == '1'

        if is_fixed:
            fixed_nutrients = {}
            for nutrient in nutrients:
                nid = nutrient['id']
                fixed_val = request.form.get(f'meal_{i}_nutrient_{nid}_fixed')
                if fixed_val:
                    fixed_nutrients[nid] = float(fixed_val)

            meals.append({
                "id": f"meal_{i+1}",
                "name": meal_name,
                "time": meal_time,
                "is_fixed": True,
                "fixed_nutrients": fixed_nutrients,
                "constraints": {}
            })
        else:
            constraints = {}
            for nutrient in nutrients:
                nid = nutrient['id']
                value = request.form.get(f'meal_{i}_nutrient_{nid}_value')
                up = request.form.get(f'meal_{i}_nutrient_{nid}_up', '0')
                down = request.form.get(f'meal_{i}_nutrient_{nid}_down', '0')

                if value:
                    constraint = {
                        'value': float(value),
                        'up': int(up),
                        'down': int(down)
                    }
                    constraints[nid] = constraint

            meals.append({
                "id": f"meal_{i+1}",
                "name": meal_name,
                "time": meal_time,
                "is_fixed": False,
                "constraints": constraints
            })

    if name:
        add_meal_plan(name, meals)
    return redirect(url_for('meals_list'))


@app.route('/meals/edit/<plan_id>', methods=['POST'])
def meals_edit(plan_id):
    name = request.form.get('name')
    nutrients = get_nutrients()

    meals = []
    i = 0
    while True:
        meal_name = request.form.get(f'edit_{i}_name')
        if meal_name is None:
            break

        meal_time = request.form.get(f'edit_{i}_time', '')
        is_fixed = request.form.get(f'edit_{i}_is_fixed') == '1'

        if is_fixed:
            fixed_nutrients = {}
            for nutrient in nutrients:
                nid = nutrient['id']
                fixed_val = request.form.get(f'edit_{i}_nutrient_{nid}_fixed')
                if fixed_val:
                    fixed_nutrients[nid] = float(fixed_val)

            meals.append({
                "id": f"meal_{i+1}",
                "name": meal_name,
                "time": meal_time,
                "is_fixed": True,
                "fixed_nutrients": fixed_nutrients,
                "constraints": {}
            })
        else:
            constraints = {}
            for nutrient in nutrients:
                nid = nutrient['id']
                value = request.form.get(f'edit_{i}_nutrient_{nid}_value')
                up = request.form.get(f'edit_{i}_nutrient_{nid}_up', '0')
                down = request.form.get(f'edit_{i}_nutrient_{nid}_down', '0')

                if value:
                    constraint = {
                        'value': float(value),
                        'up': int(up),
                        'down': int(down)
                    }
                    constraints[nid] = constraint

            meals.append({
                "id": f"meal_{i+1}",
                "name": meal_name,
                "time": meal_time,
                "is_fixed": False,
                "constraints": constraints
            })

        i += 1

    if name:
        update_meal_plan(plan_id, name, meals)
    return redirect(url_for('meals_list'))


@app.route('/meals/delete/<plan_id>', methods=['POST'])
def meals_delete(plan_id):
    delete_meal_plan(plan_id)
    return redirect(url_for('meals_list'))


# 食品管理
@app.route('/foods')
def foods_list():
    foods = get_foods()
    nutrients = get_nutrients()
    categories = list(set(f.get('category', '') for f in foods))
    return render_template('foods.html', foods=foods, nutrients=nutrients, categories=categories)


def auto_categorize_food(nutrition_per_100g):
    """根据营养成分自动判断食品分类"""
    if not nutrition_per_100g:
        return "其他"
    
    # 计算总热量（卡路里估算）
    protein = nutrition_per_100g.get('protein', 0) or 0
    carbs = nutrition_per_100g.get('carbs', 0) or 0
    fat = nutrition_per_100g.get('fat', 0) or 0
    
    # 各营养物质的热量贡献
    protein_cal = protein * 4
    carbs_cal = carbs * 4
    fat_cal = fat * 9
    
    # 找出最高热量贡献的营养物质
    max_cal = max(protein_cal, carbs_cal, fat_cal)
    
    if max_cal == 0:
        return "其他"
    
    # 按优先级判断分类
    if protein_cal == max_cal and protein > 0:
        return "蛋白质类"
    elif carbs_cal == max_cal and carbs > 0:
        return "碳水类"
    elif fat_cal == max_cal and fat > 0:
        return "脂肪类"
    else:
        return "其他"


@app.route('/foods/add', methods=['POST'])
def foods_add():
    name = request.form.get('name')
    priority = int(request.form.get('priority', 1))
    category = request.form.get('category', '')
    nutrients = get_nutrients()

    nutrition_per_100g = {}
    for nutrient in nutrients:
        value = request.form.get(f'nutrition_{nutrient["id"]}')
        if value:
            nutrition_per_100g[nutrient["id"]] = float(value)

    # 如果没有选择分类，使用自动分类
    if not category:
        category = auto_categorize_food(nutrition_per_100g)

    if name:
        add_food(name, category, nutrition_per_100g, priority)
    return redirect(url_for('foods_list'))


@app.route('/foods/edit/<food_id>', methods=['POST'])
def foods_edit(food_id):
    name = request.form.get('name')
    priority = int(request.form.get('priority', 1))
    category = request.form.get('category', '')
    nutrients = get_nutrients()

    nutrition_per_100g = {}
    for nutrient in nutrients:
        value = request.form.get(f'nutrition_{nutrient["id"]}')
        if value:
            nutrition_per_100g[nutrient["id"]] = float(value)

    # 如果没有选择分类，使用自动分类
    if not category:
        category = auto_categorize_food(nutrition_per_100g)

    if name:
        update_food(food_id, name, category, nutrition_per_100g, priority)
    return redirect(url_for('foods_list'))


@app.route('/foods/delete/<food_id>', methods=['POST'])
def foods_delete(food_id):
    delete_food(food_id)
    return redirect(url_for('foods_list'))


# 配比生成
@app.route('/plan')
def plan_page():
    nutrients = get_nutrients()
    requirements = get_daily_requirements()
    meal_plans = get_meal_plans()
    foods = get_foods()
    saved_plans = get_plans()
    # 创建营养物质ID到中文名称的映射
    nutrient_names = {n['id']: n['name'] for n in nutrients}
    return render_template('plan.html',
                         nutrients=nutrients,
                         requirements=requirements,
                         meal_plans=meal_plans,
                         foods=foods,
                         saved_plans=saved_plans,
                         nutrient_names=nutrient_names)


@app.route('/plan/generate', methods=['POST'])
def plan_generate():
    data = request.get_json()

    meal_plan_id = data.get('meal_plan_id')
    selected_food_ids = data.get('selected_foods', [])
    mix_ratios = data.get('mix_ratios', {})

    # 获取数据
    foods = get_foods()
    requirements = get_daily_requirements()
    meal_plans = get_meal_plans()
    constraint_rules = get_constraint_rules()

    # 找到选中的餐数方案
    selected_plan = None
    for plan in meal_plans:
        if plan['id'] == meal_plan_id:
            selected_plan = plan
            break

    if not selected_plan:
        return jsonify({"error": "未找到餐数方案"}), 400
    
    # 过滤选中的食品
    selected_foods = [f for f in foods if f['id'] in selected_food_ids]
    
    if not selected_foods:
        return jsonify({"error": "请选择至少一种食品"}), 400
    
    # 按优先级排序选中的食品
    selected_foods.sort(key=lambda x: x.get('priority', 1))
    
    # 运行优化
    result = optimize_meal_plan(selected_foods, requirements, selected_plan, mix_ratios, constraint_rules)
    
    if result and result.get('status') == 'optimal':
        # 保存方案
        plan_data = {
            "meal_plan_name": selected_plan['name'],
            "result": result,
            "selected_foods": selected_food_ids,
            "mix_ratios": mix_ratios
        }
        save_plan(plan_data)
    
    return jsonify(result)


@app.route('/plan/history')
def plan_history():
    saved_plans = get_plans()
    nutrients = get_nutrients()
    nutrient_names = {n['id']: n['name'] for n in nutrients}
    return render_template('plan_history.html', plans=saved_plans, nutrients=nutrients, nutrient_names=nutrient_names)


# Vercel部署适配
app.config['STATIC_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=DEBUG, host='0.0.0.0', port=port)
