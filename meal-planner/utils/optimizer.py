from pulp import LpProblem, LpMinimize, LpVariable, LpStatus, lpSum, value


def optimize_meal_plan(foods, daily_requirements, meal_plan, mix_ratios=None, constraint_rules=None):
    if not foods or not daily_requirements or not meal_plan:
        return None

    meals = meal_plan.get("meals", [])
    if not meals:
        return None

    if mix_ratios is None:
        mix_ratios = {}
    if constraint_rules is None:
        constraint_rules = {}

    nutrients = list(daily_requirements.keys())

    fixed_meals = [m for m in meals if m.get("is_fixed")]
    normal_meals = [m for m in meals if not m.get("is_fixed")]

    fixed_nutrient_total = {nid: 0 for nid in nutrients}
    for meal in fixed_meals:
        fixed_nutrients = meal.get("fixed_nutrients", {})
        for nid, val in fixed_nutrients.items():
            if nid in fixed_nutrient_total:
                fixed_nutrient_total[nid] += val

    if not normal_meals:
        result = {
            "status": "optimal",
            "meal_plan_name": meal_plan.get("name", ""),
            "meals": [],
            "daily_total": {},
            "daily_target": {}
        }
        for meal in fixed_meals:
            result["meals"].append({
                "name": meal.get("name", ""),
                "time": meal.get("time", ""),
                "is_fixed": True,
                "foods": [],
                "nutrients": meal.get("fixed_nutrients", {})
            })
        for nid in nutrients:
            result["daily_total"][nid] = round(fixed_nutrient_total.get(nid, 0), 1)
            result["daily_target"][nid] = daily_requirements.get(nid, {}).get("min", 0) or 0
        return result

    prob = LpProblem("MealPlanOptimizer", LpMinimize)

    food_vars = {}
    for meal in normal_meals:
        meal_id = meal["id"]
        food_vars[meal_id] = {}
        for food in foods:
            food_id = food["id"]
            food_vars[meal_id][food_id] = LpVariable(f"meal_{meal_id}_food_{food_id}", lowBound=0, cat='Continuous')

    # 将固定值+浮动转换为min/max，并创建松弛变量
    exceed_slack = {}
    reduce_slack = {}
    for meal in normal_meals:
        meal_id = meal["id"]
        exceed_slack[meal_id] = {}
        reduce_slack[meal_id] = {}
        meal_constraints = meal.get("constraints", {})
        for nutrient_id in nutrients:
            if nutrient_id in meal_constraints:
                c = meal_constraints[nutrient_id]
                rule = constraint_rules.get(nutrient_id, {})
                hard_exceed = rule.get("hard_exceed", False)
                hard_reduce = rule.get("hard_reduce", False)

                # 计算min/max
                base_value = c.get("value", 0)
                up_percent = c.get("up", 0)
                down_percent = c.get("down", 0)

                min_val = base_value * (1 - down_percent / 100) if base_value and down_percent else None
                max_val = base_value * (1 + up_percent / 100) if base_value and up_percent else None

                # 创建松弛变量
                if not hard_exceed and max_val is not None:
                    exceed_slack[meal_id][nutrient_id] = LpVariable(f"exceed_{meal_id}_{nutrient_id}", lowBound=0, cat='Continuous')

                if not hard_reduce and min_val is not None:
                    reduce_slack[meal_id][nutrient_id] = LpVariable(f"reduce_{meal_id}_{nutrient_id}", lowBound=0, cat='Continuous')

    # 目标函数
    objective = []

    # 总食品量（权重1）
    for meal_id in food_vars:
        for food_id in food_vars[meal_id]:
            objective.append(food_vars[meal_id][food_id])

    # 超出量惩罚
    for meal_id in exceed_slack:
        for nutrient_id, slack_var in exceed_slack[meal_id].items():
            rule = constraint_rules.get(nutrient_id, {})
            priority = rule.get("exceed_priority", 100)
            weight = (101 - priority) * 10
            objective.append(slack_var * weight)

    # 不足量惩罚
    for meal_id in reduce_slack:
        for nutrient_id, slack_var in reduce_slack[meal_id].items():
            rule = constraint_rules.get(nutrient_id, {})
            priority = rule.get("reduce_priority", 100)
            weight = (101 - priority) * 5
            objective.append(slack_var * weight)

    prob += lpSum(objective), "Objective"

    # 每餐营养约束（使用转换后的min/max）
    for meal in normal_meals:
        meal_id = meal["id"]
        meal_constraints = meal.get("constraints", {})

        for nutrient_id in nutrients:
            if nutrient_id not in meal_constraints:
                continue

            c = meal_constraints[nutrient_id]
            base_value = c.get("value", 0)
            up_percent = c.get("up", 0)
            down_percent = c.get("down", 0)

            min_val = base_value * (1 - down_percent / 100) if base_value and down_percent else None
            max_val = base_value * (1 + up_percent / 100) if base_value and up_percent else None

            rule = constraint_rules.get(nutrient_id, {})
            hard_exceed = rule.get("hard_exceed", False)
            hard_reduce = rule.get("hard_reduce", False)

            nutrient_sum = []
            for food in foods:
                amount = food_vars[meal_id][food["id"]]
                nutrient_value = food["nutrition_per_100g"].get(nutrient_id, 0)
                if nutrient_value > 0:
                    nutrient_sum.append(amount * nutrient_value)

            if not nutrient_sum:
                continue

            # 处理最小值约束
            if min_val is not None and min_val > 0:
                if hard_reduce:
                    prob += lpSum(nutrient_sum) >= min_val
                elif nutrient_id in reduce_slack.get(meal_id, {}):
                    prob += lpSum(nutrient_sum) + reduce_slack[meal_id][nutrient_id] >= min_val

            # 处理最大值约束
            if max_val is not None and max_val > 0:
                if hard_exceed:
                    prob += lpSum(nutrient_sum) <= max_val
                elif nutrient_id in exceed_slack.get(meal_id, {}):
                    prob += lpSum(nutrient_sum) - exceed_slack[meal_id][nutrient_id] <= max_val

    # 每日总营养约束
    for nutrient_id in nutrients:
        daily_min = daily_requirements.get(nutrient_id, {}).get("min", 0)
        if not daily_min or daily_min <= 0:
            continue

        daily_sum = []
        for meal_id in food_vars:
            for food_id in food_vars[meal_id]:
                amount = food_vars[meal_id][food_id]
                for food in foods:
                    if food["id"] == food_id:
                        nutrient_value = food["nutrition_per_100g"].get(nutrient_id, 0)
                        if nutrient_value > 0:
                            daily_sum.append(amount * nutrient_value)
                        break

        remaining = daily_min - fixed_nutrient_total.get(nutrient_id, 0)
        if remaining > 0 and daily_sum:
            prob += lpSum(daily_sum) >= remaining

    prob.solve()

    if LpStatus[prob.status] != "Optimal":
        message = "无法找到满足所有约束条件的配比方案。"
        message += "\n\n建议：\n1. 放宽浮动范围\n2. 增加可用食品\n3. 调整约束规则"
        return {"status": "infeasible", "message": message}

    # 构建结果
    result = {"status": "optimal", "meal_plan_name": meal_plan.get("name", ""), "meals": [], "constraint_rules": constraint_rules}

    for meal in fixed_meals:
        result["meals"].append({
            "name": meal.get("name", ""),
            "time": meal.get("time", ""),
            "is_fixed": True,
            "foods": [],
            "nutrients": meal.get("fixed_nutrients", {})
        })

    for meal in normal_meals:
        meal_id = meal["id"]
        meal_result = {"name": meal.get("name", ""), "time": meal.get("time", ""), "is_fixed": False, "foods": [], "nutrients": {}}
        for nutrient_id in nutrients:
            meal_result["nutrients"][nutrient_id] = 0

        for food in foods:
            amount = value(food_vars[meal_id][food["id"]])
            if amount and amount > 0.01:
                amount_grams = round(amount * 100)
                meal_result["foods"].append({
                    "id": food["id"],
                    "name": food["name"],
                    "category": food.get("category", ""),
                    "priority": food.get("priority", 1),
                    "amount_grams": amount_grams
                })
                for nutrient_id in nutrients:
                    nutrient_value = food["nutrition_per_100g"].get(nutrient_id, 0)
                    meal_result["nutrients"][nutrient_id] += amount * nutrient_value

        for nutrient_id in meal_result["nutrients"]:
            meal_result["nutrients"][nutrient_id] = round(meal_result["nutrients"][nutrient_id], 1)
        result["meals"].append(meal_result)

    result["daily_total"] = {}
    result["daily_target"] = {}
    result["daily_diff"] = {}
    for nutrient_id in nutrients:
        total = fixed_nutrient_total.get(nutrient_id, 0)
        for meal in result["meals"]:
            if not meal.get("is_fixed"):
                total += meal["nutrients"].get(nutrient_id, 0)
        result["daily_total"][nutrient_id] = round(total, 1)
        target = daily_requirements.get(nutrient_id, {}).get("min", 0)
        result["daily_target"][nutrient_id] = target or 0
        result["daily_diff"][nutrient_id] = round(total - (target or 0), 1)

    return result


def getNutrientName(nid):
    name_map = {"protein": "蛋白质", "carbs": "碳水化合物", "fat": "脂肪", "fiber": "膳食纤维"}
    return name_map.get(nid, nid)
