import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import hmac

st.set_page_config(layout="wide")

# 用户输入的处理
def password_entered():
    if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
        st.session_state["password_correct"] = True
        del st.session_state["password"]  # 不再存储密码
    else:
        st.session_state["password_correct"] = False

# 读取CSV文件
@st.cache_data
def load_data():
    account = pd.read_csv('data/account.csv', encoding='utf-8')
    account['date'] = pd.to_datetime(account['date'])
    product = pd.read_csv('data/product.csv', encoding='utf-8',
                          dtype={'original_fund': float, 'diviend_ratio': float, 'dividend_nv': float, 'min_retained_nv': float})
    return account, product

# 处理数据
def process_data(df, main_account_ids):
    df_main = df[df['id'].isin(main_account_ids)]
    df_main['date'] = pd.to_datetime(df_main['date'])
    return df_main

# 计算统计指标
def calculate_statistics(df):
    stats = []
    for account_id in df['id'].unique():
        df_account = df[df['id'] == account_id]
        daily_returns = df_account['return']
        
        total_return = df_account['accumulated_netvalue'].iloc[-1] / df_account['accumulated_netvalue'].iloc[0] - 1
        # 计算当前回撤
        current_netvalue = df_account['accumulated_netvalue'].iloc[-1]
        peak_netvalue = df_account['accumulated_netvalue'].cummax().iloc[-1]
        current_drawdown = current_netvalue- peak_netvalue

        annual_return = np.mean(daily_returns) * 250
        sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(250)
        
        cumulative_returns = 1 + daily_returns.cumsum()
        max_drawdown = (cumulative_returns.cummax() - cumulative_returns).max()
        
        # 计算卡玛比率
        calmar_ratio = annual_return / max_drawdown if max_drawdown != 0 else np.inf
        
        win_rate = np.sum(daily_returns > 0) / np.sum(daily_returns != 0)
        
        gain_loss_ratio = np.abs(np.mean(daily_returns[daily_returns > 0]) / 
                                 np.mean(daily_returns[daily_returns < 0]))
        
        # 格式化统计数据
        stats_formatted = {
            'ID': account_id,
            '收益率': f'{total_return:.2%}',
            '回撤': f'{current_drawdown:.2%}',
            '年化收益率': f'{annual_return:.2%}',
            '夏普': f'{sharpe_ratio:.2f}',
            '卡玛': f'{calmar_ratio:.2f}',
            '最大回撤': f'{max_drawdown:.2%}',
            '胜率': f'{win_rate:.2%}',
            '盈亏比': f'{gain_loss_ratio:.2f}'
        }
        stats.append(stats_formatted)
    return pd.DataFrame(stats)

# 绘制净值曲线图
def plot_netvalue(df):
    fig = go.Figure()
    for account_id in df['id'].unique():
        df_account = df[df['id'] == account_id]
        fig.add_trace(go.Scatter(x=df_account['date'], y=df_account['accumulated_netvalue'], mode='lines', name=f'账户 {account_id}'))
    
    fig.update_layout(title='多账户净值曲线图',
                      xaxis_title='日期',
                      yaxis_title='净值',
                      legend_title='账户ID')
    return fig

# 计算分红
def calculate_dividend(df, product):
    def calculate_single_dividend(row, product_info):
        if product_info['diviend_ratio'] == 0:
            return 0, 0
        
        current_amount = row['amount']
        original_fund = product_info['original_fund']
        dividend_ratio = product_info['diviend_ratio']
        dividend_nv = product_info.get('dividend_nv', 1)  # 如果没有设置dividend_nv，默认为1
        min_retained_nv = product_info.get('min_retained_nv', 1)  # 如果没有设置min_retained_nv，默认为1
        current_nv = row['netvalue']
        
        if current_nv > dividend_nv:
            receivable_dividend = (current_amount - original_fund) * dividend_ratio
            distributable_dividend = (current_amount - min_retained_nv * original_fund) * dividend_ratio
            return max(0, receivable_dividend), max(0, distributable_dividend)
        else:
            return 0, 0

    # 从df中获取最后一天的记录
    df_last_day = df[df['date'] == df['date'].max()]
    result = []
    for _, row in df_last_day.iterrows():
        product_info = product[product['id'] == row['id']].iloc[0]
        receivable, distributable = calculate_single_dividend(row, product_info)
        if receivable > 0 or distributable > 0:
            result.append({
                'id': row['id'],
                'receivable_dividend': f'{receivable:.0f}',
                'distributable_dividend': f'{distributable:.0f}'
            })
    
    return pd.DataFrame(result)


# Streamlit应用
def main():
    st.title('多账户净值曲线图和统计指标')

    # 加载数据
    df, product = load_data()

    # 获取所有唯一的id
    account_ids = sorted(df['id'].unique())

    # 设置默认账户
    default_accounts = [3, 16]
    default_accounts = [id for id in default_accounts if id in account_ids]

    # 创建一个列布局
    col1, col2 = st.columns([3, 1])

    with col1:
        # 创建一个多选框让用户选择多个账户id，设置默认值
        selected_ids = st.multiselect('选择账户ID', account_ids, default=default_accounts)

    with col2:
        # 添加"选择所有账户"按钮
        if st.checkbox('选择所有账户'):
            selected_ids = account_ids

    # 如果用户没有选择任何账户，使用默认账户
    if not selected_ids:
        selected_ids = default_accounts
        st.info(f'未选择账户，显示默认账户: {default_accounts}')

    # 处理选定的账户数据
    df_main = process_data(df, selected_ids)

    # 计算统计指标
    stats_df = calculate_statistics(df_main)
    st.dataframe(stats_df)

    # 绘制净值曲线图和统计表格
    fig = plot_netvalue(df_main)

    # 显示图表
    st.plotly_chart(fig, use_container_width=True)

    # 计算分红
    dividend_df = calculate_dividend(df_main, product)
    if not dividend_df.empty:
        st.dataframe(dividend_df)
        
        # 统计可分红账户信息
        dividend_count = len(dividend_df)
        total_receivable = dividend_df['receivable_dividend'].astype(float).sum()
        total_distributable = dividend_df['distributable_dividend'].astype(float).sum()
        
        st.info(f'当前选中 {len(selected_ids)} 个账户，可分红账户数量：{dividend_count}，总应收金额：{total_receivable:.2f}，总可得金额：{total_distributable:.2f}')
    else:
        st.info(f'当前选中 {len(selected_ids)} 个账户，无可分红账户')   


if __name__ == '__main__':
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        # 显示密码输入框
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.warning("😕 Check Password")
    else:
        main()