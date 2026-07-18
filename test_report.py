import sys
import os
sys.path.insert(0, 'D:/meal-planner')
os.chdir('D:/meal-planner')

from utils.data_manager import get_nutrients, get_daily_requirements, get_meal_plans, get_foods
from utils.optimizer import optimize_meal_plan

# 获取数据
nutrients = get_nutrients()
daily_req = get_daily_requirements()
meal_plans = get_meal_plans()
foods = get_foods()

print('=' * 60)
print('备餐系统测试报告')
print('=' * 60)

# 显示营养物质
print('\n【营养物质】')
for n in nutrients:
    print(f'  {n["name"]} ({n["unit"]})')

# 显示每日需求
print('\n【每日需求】')
for nid, req in daily_req.items():
    print(f'  {nid}: 基础值={req.get("min", 0)}, 上浮={req.get("up", 0)}%, 下浮={req.get("down", 0)}%')

# 测试5组配比方案
print('\n' + '=' * 60)
print('测试5组配比方案')
print('=' * 60)

for i, plan in enumerate(meal_plans[:3], 1):
    print(f'\n【方案{i}: {plan["name"]}】')
    print(f'  餐数: {len(plan["meals"])}餐')
    
    # 运行优化
    result = optimize_meal_plan(foods, daily_req, plan)
    
    if result and result.get('status') == 'optimal':
        print(f'\n  每餐配比结果:')
        for meal in result.get('meals', []):
            if meal.get('is_fixed'):
                print(f'    {meal["name"]} (固定餐):')
                for nid, val in meal.get('nutrients', {}).items():
                    print(f'      {nid}: {val}g')
            else:
                print(f'    {meal["name"]}:')
                for food in meal.get('foods', []):
                    print(f'      - {food["name"]}: {food["amount_grams"]}g')
                print(f'    营养摄入:')
                for nid, val in meal.get('nutrients', {}).items():
                    print(f'      {nid}: {val}g')
        
        print(f'\n  每日总计与标准值对比:')
        for n in nutrients:
            nid = n['id']
            total = result.get('daily_total', {}).get(nid, 0)
            target = daily_req.get(nid, {}).get('min', 0)
            diff = total - target
            status = '达标' if diff >= 0 else '不足'
            print(f'    {n["name"]}: 实际={total}g, 标准={target}g, 差值={diff:+.1f}g [{status}]')
    else:
        print(f'  生成失败: {result.get("message", "未知错误")}')
    
    print()
