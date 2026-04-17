import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

def render_attendance_trends(df):
    """
    Renders a line chart showing attendance trends.
    Expects a DataFrame with at least 'Date' and 'Student ID'.
    """
    if df is None or df.empty:
        return px.line(title="No Data Available")
        
    # Group by Date and count unique students (who are present)
    trend = df.groupby('Date')['Student ID'].nunique().reset_index()
    trend.columns = ['Date', 'Present Count']
    
    fig = px.line(trend, x='Date', y='Present Count', markers=True,
                  title="Daily Attendance Trend")
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Date",
        yaxis_title="Students Present",
        margin=dict(l=0, r=0, t=50, b=0)
    )
    fig.update_traces(line_color='#2e66ff', line_width=3, marker=dict(size=8))
    return fig

def render_department_distribution(df_users, df_attendance):
    """
    Renders a pie chart of attendance by department for a specific set of records.
    """
    if df_users.empty or df_attendance.empty:
        return px.pie(title="No Data Available")
        
    # Merge attendance with users to get department
    merged = pd.merge(df_attendance, df_users, on="Student ID", how="inner")
    
    # Count present per department
    dept_counts = merged.groupby('Department')['Student ID'].nunique().reset_index()
    dept_counts.columns = ['Department', 'Count']
    
    fig = px.pie(dept_counts, names='Department', values='Count', hole=0.4,
                 title="Today's Attendance by Department",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
                 
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=50, b=0)
    )
    return fig
