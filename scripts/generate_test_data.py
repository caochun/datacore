#!/usr/bin/env python3
"""
生成高速公路收费中心测试数据
"""
import duckdb
import random
from datetime import datetime, timedelta
import os

# 确保scripts目录存在
os.makedirs('scripts', exist_ok=True)

# 连接DuckDB
conn = duckdb.connect('datacore.duckdb')

# 收费站数据
toll_stations = [
    ('S001', '京沪高速-北京收费站', '北京', 'G2', '主线收费站', '2020-01-01'),
    ('S002', '京沪高速-天津收费站', '天津', 'G2', '主线收费站', '2020-01-01'),
    ('S003', '京沪高速-济南收费站', '济南', 'G2', '主线收费站', '2020-01-01'),
    ('S004', '京沪高速-南京收费站', '南京', 'G2', '主线收费站', '2020-01-01'),
    ('S005', '京沪高速-上海收费站', '上海', 'G2', '主线收费站', '2020-01-01'),
    ('S101', '京沪高速-廊坊匝道收费站', '廊坊', 'G2', '匝道收费站', '2020-01-01'),
    ('S102', '京沪高速-沧州匝道收费站', '沧州', 'G2', '匝道收费站', '2020-01-01'),
    ('S103', '京沪高速-德州匝道收费站', '德州', 'G2', '匝道收费站', '2020-01-01'),
    ('S104', '京沪高速-泰安匝道收费站', '泰安', 'G2', '匝道收费站', '2020-01-01'),
    ('S105', '京沪高速-苏州匝道收费站', '苏州', 'G2', '匝道收费站', '2020-01-01'),
]

# 车型分类
vehicle_types = [
    ('V01', '一类车', '7座及以下客车', 0.5),
    ('V02', '二类车', '8-19座客车', 1.0),
    ('V03', '三类车', '20-39座客车', 1.5),
    ('V04', '四类车', '40座及以上客车', 2.0),
    ('V05', '一类货车', '2轴货车', 1.0),
    ('V06', '二类货车', '3轴货车', 1.5),
    ('V07', '三类货车', '4轴货车', 2.0),
    ('V08', '四类货车', '5轴货车', 2.5),
    ('V09', '五类货车', '6轴及以上货车', 3.0),
]

# 支付方式
payment_methods = [
    ('P01', 'ETC', '电子不停车收费'),
    ('P02', '现金', '现金支付'),
    ('P03', '移动支付', '微信/支付宝'),
    ('P04', '银行卡', '银行卡支付'),
]

# 创建原始数据表
conn.execute("""
    CREATE SCHEMA IF NOT EXISTS raw;
""")

# 创建收费站表
conn.execute("""
    CREATE TABLE IF NOT EXISTS raw.toll_station (
        station_id VARCHAR(10) PRIMARY KEY,
        station_name VARCHAR(100),
        city VARCHAR(50),
        highway_code VARCHAR(10),
        station_type VARCHAR(20),
        open_date DATE
    );
""")

# 创建车型字典表
conn.execute("""
    CREATE TABLE IF NOT EXISTS raw.vehicle_type_dict (
        vehicle_type_code VARCHAR(10) PRIMARY KEY,
        vehicle_type_name VARCHAR(50),
        vehicle_type_desc VARCHAR(100),
        toll_rate_multiplier DECIMAL(3,1)
    );
""")

# 创建支付方式字典表
conn.execute("""
    CREATE TABLE IF NOT EXISTS raw.payment_method_dict (
        payment_method_code VARCHAR(10) PRIMARY KEY,
        payment_method_name VARCHAR(50),
        payment_method_desc VARCHAR(100)
    );
""")

# 创建收费交易原始表
conn.execute("""
    CREATE TABLE IF NOT EXISTS raw.toll_transaction (
        transaction_id VARCHAR(50) PRIMARY KEY,
        station_id VARCHAR(10),
        lane_id VARCHAR(10),
        vehicle_plate VARCHAR(20),
        vehicle_type_code VARCHAR(10),
        entry_station_id VARCHAR(10),
        entry_time TIMESTAMP,
        exit_time TIMESTAMP,
        payment_method_code VARCHAR(10),
        toll_amount DECIMAL(10,2),
        actual_amount DECIMAL(10,2),
        discount_amount DECIMAL(10,2),
        transaction_status VARCHAR(20),
        create_time TIMESTAMP,
        update_time TIMESTAMP
    );
""")

# 插入收费站数据
conn.executemany("""
    INSERT INTO raw.toll_station 
    (station_id, station_name, city, highway_code, station_type, open_date)
    VALUES (?, ?, ?, ?, ?, ?)
""", toll_stations)

# 插入车型字典数据
conn.executemany("""
    INSERT INTO raw.vehicle_type_dict 
    (vehicle_type_code, vehicle_type_name, vehicle_type_desc, toll_rate_multiplier)
    VALUES (?, ?, ?, ?)
""", vehicle_types)

# 插入支付方式字典数据
conn.executemany("""
    INSERT INTO raw.payment_method_dict 
    (payment_method_code, payment_method_name, payment_method_desc)
    VALUES (?, ?, ?)
""", payment_methods)

# 生成收费交易数据
def generate_plate():
    """生成车牌号"""
    provinces = ['京', '津', '冀', '鲁', '苏', '沪', '浙', '皖', '豫', '鄂']
    letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    numbers = '0123456789'
    
    province = random.choice(provinces)
    city_letter = random.choice(letters)
    plate_number = ''.join(random.choices(numbers, k=5))
    return f"{province}{city_letter}{plate_number}"

def generate_transaction_id(date, index):
    """生成交易ID"""
    return f"TXN{date.strftime('%Y%m%d')}{str(index).zfill(8)}"

# 生成最近30天的交易数据
base_date = datetime.now() - timedelta(days=30)
transactions = []

for day in range(30):
    current_date = base_date + timedelta(days=day)
    # 每天生成1000-5000条交易
    num_transactions = random.randint(1000, 5000)
    
    for i in range(num_transactions):
        # 随机选择收费站
        station = random.choice(toll_stations)
        entry_station = random.choice(toll_stations)
        
        # 生成通行时间（在同一天内）
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        entry_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 出口时间比入口时间晚1-6小时
        exit_time = entry_time + timedelta(hours=random.randint(1, 6))
        
        # 如果出口时间超过当天，调整到当天23:59
        if exit_time.date() > current_date.date():
            exit_time = current_date.replace(hour=23, minute=59, second=0, microsecond=0)
        
        # 选择车型和支付方式
        vehicle_type = random.choice(vehicle_types)
        payment_method = random.choice(payment_methods)
        
        # 计算收费金额（基础费率 * 车型系数 * 距离系数）
        base_rate = 0.5  # 每公里基础费率
        distance = random.randint(10, 500)  # 距离10-500公里
        toll_amount = round(base_rate * distance * vehicle_type[3], 2)
        
        # 折扣（ETC 95折，其他无折扣）
        if payment_method[0] == 'P01':
            discount_amount = round(toll_amount * 0.05, 2)
        else:
            discount_amount = 0.0
        
        actual_amount = toll_amount - discount_amount
        
        # 交易状态（95%正常，5%异常）
        if random.random() < 0.95:
            status = '正常'
        else:
            status = random.choice(['异常', '逃费', '设备故障', '数据缺失'])
            # 异常情况下可能金额为0或NULL
            if status in ['逃费', '设备故障']:
                actual_amount = 0.0
        
        transaction_id = generate_transaction_id(current_date, i)
        lane_id = f"L{random.randint(1, 8):02d}"
        
        transactions.append((
            transaction_id,
            station[0],  # station_id
            lane_id,
            generate_plate(),
            vehicle_type[0],  # vehicle_type_code
            entry_station[0],  # entry_station_id
            entry_time,
            exit_time,
            payment_method[0],  # payment_method_code
            toll_amount,
            actual_amount,
            discount_amount,
            status,
            current_date,
            current_date
        ))

# 批量插入交易数据
print(f"正在插入 {len(transactions)} 条交易数据...")
conn.executemany("""
    INSERT INTO raw.toll_transaction 
    (transaction_id, station_id, lane_id, vehicle_plate, vehicle_type_code,
     entry_station_id, entry_time, exit_time, payment_method_code,
     toll_amount, actual_amount, discount_amount, transaction_status,
     create_time, update_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", transactions)

# 创建索引
conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_toll_transaction_station 
    ON raw.toll_transaction(station_id);
""")

conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_toll_transaction_time 
    ON raw.toll_transaction(exit_time);
""")

conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_toll_transaction_plate 
    ON raw.toll_transaction(vehicle_plate);
""")

# 统计信息
stats = conn.execute("""
    SELECT 
        COUNT(*) as total_transactions,
        COUNT(DISTINCT station_id) as total_stations,
        COUNT(DISTINCT vehicle_plate) as total_vehicles,
        SUM(actual_amount) as total_revenue,
        MIN(exit_time) as earliest_time,
        MAX(exit_time) as latest_time
    FROM raw.toll_transaction
""").fetchone()

print("\n数据生成完成！")
print(f"总交易数: {stats[0]}")
print(f"收费站数: {stats[1]}")
print(f"车辆数: {stats[2]}")
print(f"总收入: {stats[3]:,.2f} 元")
print(f"时间范围: {stats[4]} 至 {stats[5]}")

conn.close()
print("\n数据库文件已保存: datacore.duckdb")

