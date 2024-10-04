import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Single Account", layout="wide")

# 读取CSV文件
@st.cache_data
def load_data():
    df = pd.read_csv('data/account.csv')
    df["date"] = pd.to_datetime(df['date'])
    return df

# 处理数据
def process_data(df, main_account_id):
    # 选择main_account的数据
    df_main = df[df['id'] == main_account_id]
    return df_main

# 计算统计指标
def calculate_statistics(df):
    # 计算每日收益率
    daily_returns = df['return']
    
    # 计算总收益率
    total_return = df['accumulated_netvalue'].iloc[-1] / df['accumulated_netvalue'].iloc[0] - 1
    
    # 计算当前回撤
    current_netvalue = df['accumulated_netvalue'].iloc[-1]
    peak_netvalue = df['accumulated_netvalue'].cummax().iloc[-1]
    current_drawdown = (peak_netvalue - current_netvalue) / peak_netvalue
    
    # 计算年化收益率
    annual_return = np.mean(daily_returns) * 250
    
    # 计算夏普比率
    sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(250)
    
    # 计算最大回撤
    cumulative_returns = 1 + daily_returns.cumsum()
    max_drawdown = (cumulative_returns.cummax() - cumulative_returns).max()
    
    # 计算卡玛比率
    calmar_ratio = annual_return / max_drawdown if max_drawdown != 0 else np.inf
    
    # 计算胜率
    win_rate = np.sum(daily_returns > 0) / np.sum(daily_returns != 0)
    
    # 计算盈亏比
    gain_loss_ratio = np.abs(np.mean(daily_returns[daily_returns > 0]) / 
                             np.mean(daily_returns[daily_returns < 0]))
    
    # 格式化统计数据
    stats = {
        '收益率': f'{total_return:.2%}',
        '回撤': f'{current_drawdown:.2%}',
        '年化收益率': f'{annual_return:.2%}',
        '夏普比率': f'{sharpe_ratio:.2f}',
        '卡玛比率': f'{calmar_ratio:.2f}',
        '最大回撤': f'{max_drawdown:.2%}',
        '胜率': f'{win_rate:.2%}',
        '盈亏比': f'{gain_loss_ratio:.2f}'
    }
    
    return stats

# 绘制净值曲线图
def plot_netvalue(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['accumulated_netvalue'], mode='lines', name='净值'))
    fig.update_layout(title='净值曲线图',
                      xaxis_title='日期',
                      yaxis_title='净值')
    return fig

# Streamlit应用
def main():
    st.title('账户净值曲线图')

    # 加载数据
    df = load_data()

    # 获取所有唯一的id
    account_ids = df['id'].unique()

    # 创建一个下拉菜单让用户选择账户id
    selected_id = st.selectbox('选择账户ID', account_ids)

    # 处理选定的账户数据
    df_main = process_data(df, selected_id)

    # 计算统计指标
    stats = calculate_statistics(df_main)
    st.dataframe(pd.DataFrame(stats, index=[selected_id]))

    # 绘制净值曲线图
    fig = plot_netvalue(df_main[['date', 'return', 'accumulated_netvalue']])

    # 显示图表
    st.plotly_chart(fig)

    # 显示数据表格
    st.subheader('数据表格')
    st.dataframe(df_main)

if __name__ == '__main__':
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.warning("😕 Please input Password in Home page")
    else:
        main()