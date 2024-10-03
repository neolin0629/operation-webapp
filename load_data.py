import os
import pandas as pd
from datetime import datetime

product_file = os.path.join('data', 'product.csv')
product = pd.read_csv(product_file, encoding='utf-8')

# 获取今天的日期
today_date = datetime.today().strftime('%Y%m%d')

# 构建今天的csv文件路径
data_folder = 'data'
csv_files = [f"{today_date}_{i}.csv" for i in range(2)]  # 有两个文件，分别为0和1
file_paths = [os.path.join(data_folder, csv_file) for csv_file in csv_files]

result = pd.DataFrame(columns=['date', 'id', 'amount', 'in', 'out', 'diviend'])
# 读取并展示今天的csv文件
for file_path in file_paths:
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='gbk')
        
        if "_0" in file_path:
            df = df.loc[:, ['账户', '动态权益']].rename(columns={'账户': 'account', '动态权益': 'amount'})
            df = df.reindex(columns=['account', 'amount', 'in', 'out', 'diviend'])
        else:
            df = df.loc[:, ['account', 'amount', 'in', 'out', 'diviend']]

        df['date'] = pd.to_datetime(today_date)
        merged_df = pd.merge(df, product[['account', 'id']], on='account').loc[:, ['date', 'id', 'amount', 'in', 'out', 'diviend']].fillna(0)
        result = pd.concat([result, merged_df], axis=0, ignore_index=True)
    else:
        print(f"文件 {file_path} 不存在")

# 读取account文件
account_file = os.path.join('data', 'account.csv')
account = pd.read_csv(account_file, encoding='utf-8').fillna(0)
account['date'] = pd.to_datetime(account['date'])

# 获取前一天的数据
previous_date = account['date'].max()
previous_data = (account.loc[
    account['date'] == previous_date, ['id', 'amount', 'netvalue', 'accumulated_netvalue']]
    .rename(columns={'amount': 'amount_prev', 'netvalue': 'netvalue_prev', 'accumulated_netvalue': 'accumulated_netvalue_prev'}))

# 合并最新一天和前一天的数据
merged_data = pd.merge(result, previous_data, on='id').sort_values(by='id')

# 计算最新一天的指标
merged_data['return'] = (merged_data['amount'] - merged_data['amount_prev'] - merged_data['in'] + merged_data['out']) / merged_data['amount_prev']
merged_data['netvalue'] = (merged_data['netvalue_prev'] + merged_data['return']) - (merged_data['diviend'] / merged_data['amount_prev'])
merged_data['accumulated_netvalue'] = merged_data['accumulated_netvalue_prev'] + merged_data['return']

# 计算max_drawdown
max_accumulated_netvalue = account.groupby('id')['accumulated_netvalue'].max()
max_accumulated_netvalue = max_accumulated_netvalue.rename("max_accumulated_netvalue")  # 重命名Series以便合并
merged_data = pd.merge(merged_data, max_accumulated_netvalue, on='id')
merged_data['max_drawdown'] = merged_data.apply(
    lambda row: 0 if row['accumulated_netvalue'] >= row['max_accumulated_netvalue'] 
    else row['accumulated_netvalue'] - row['max_accumulated_netvalue'], axis=1)

# 将result拼接到account中
account = pd.concat([account, merged_data[['date', 'id', 'amount', 'in', 'out', 'diviend', 'netvalue', 'accumulated_netvalue', 'return', 'max_drawdown']]], ignore_index=True)

# 打印出combined_df中最后一天的数据
print(account[account['date'] == account['date'].max()].sort_values(by='id'))

# 如果需要，可以将结果保存到新的CSV文件
account.to_csv('./data/account.csv', index=False)

# 重命名data文件夹下的文件
for file_path in file_paths:
    if os.path.exists(file_path):
        next_date = (pd.to_datetime(today_date) + pd.Timedelta(days=1)).strftime('%Y%m%d')
        new_file_path = file_path.replace(today_date, next_date)
        os.rename(file_path, new_file_path)