"""
Email Analytics Visualization for SecondBrain application.
Provides enhanced chart generation and visualization capabilities.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from wordcloud import WordCloud
import base64
from io import BytesIO
from scipy import stats
import calendar
from collections import Counter

logger = logging.getLogger(__name__)

class ChartType:
    """Enhanced types of charts for visualization."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    NETWORK = "network"
    WORDCLOUD = "wordcloud"
    BOX = "box"
    VIOLIN = "violin"
    RADAR = "radar"
    SUNBURST = "sunburst"
    TREEMAP = "treemap"
    SANKEY = "sankey"
    CALENDAR = "calendar"
    SCATTER3D = "scatter3d"
    SURFACE3D = "surface3d"
    BUBBLE = "bubble"
    FUNNEL = "funnel"
    POLAR = "polar"
    CANDLESTICK = "candlestick"
    AREA = "area"
    WATERFALL = "waterfall"
    GAUGE = "gauge"
    ERRORBAR = "errorbar"
    CUSTOM = "custom"

@dataclass
class ChartConfig:
    """Enhanced configuration for chart generation."""
    name: str
    type: str
    title: str
    x_label: str = None
    y_label: str = None
    width: int = 800
    height: int = 600
    theme: str = "plotly"
    color_scheme: str = "default"
    animation: bool = False
    interactive: bool = True
    metadata: Dict[str, Any] = None

class EmailVisualizer:
    """Enhanced visualizations for email analytics."""
    
    def __init__(self, config_dir: str = "config/email"):
        """Initialize the email visualizer.
        
        Args:
            config_dir: Directory to store configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self._setup_themes()
        self._setup_color_schemes()
    
    def _setup_logging(self):
        """Set up logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_configs(self):
        """Load configurations."""
        try:
            config_file = self.config_dir / "visualization.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = json.load(f)
            else:
                self.configs = {}
                self._save_configs()
        except Exception as e:
            logger.error(f"Failed to load configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save configurations."""
        try:
            config_file = self.config_dir / "visualization.json"
            with open(config_file, 'w') as f:
                json.dump(self.configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save configurations: {str(e)}")
    
    def _setup_themes(self):
        """Set up visualization themes."""
        # Plotly themes
        self.themes = {
            "plotly": "plotly",
            "dark": "plotly_dark",
            "white": "plotly_white",
            "seaborn": "seaborn",
            "ggplot2": "ggplot2"
        }
        
        # Matplotlib styles
        plt.style.use("seaborn")
    
    def _setup_color_schemes(self):
        """Set up color schemes for visualizations."""
        self.color_schemes = {
            "default": px.colors.qualitative.Plotly,
            "dark": px.colors.qualitative.Dark24,
            "light": px.colors.qualitative.Light24,
            "pastel": px.colors.qualitative.Pastel,
            "bold": px.colors.qualitative.Bold,
            "vivid": px.colors.qualitative.Vivid,
            "safe": px.colors.qualitative.Safe,
            "set1": px.colors.qualitative.Set1,
            "set2": px.colors.qualitative.Set2,
            "set3": px.colors.qualitative.Set3
        }
    
    def create_time_series(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create time series chart.
        
        Args:
            data: DataFrame with time series data
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure()
            
            for column in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data[column],
                    name=column,
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title=config.title,
                xaxis_title=config.x_label,
                yaxis_title=config.y_label,
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create time series: {str(e)}")
            return None
    
    def create_bar_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create bar chart.
        
        Args:
            data: DataFrame with categorical data
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure()
            
            for column in data.columns:
                fig.add_trace(go.Bar(
                    x=data.index,
                    y=data[column],
                    name=column
                ))
            
            fig.update_layout(
                title=config.title,
                xaxis_title=config.x_label,
                yaxis_title=config.y_label,
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create bar chart: {str(e)}")
            return None
    
    def create_pie_chart(self, data: pd.Series, config: ChartConfig) -> go.Figure:
        """Create pie chart.
        
        Args:
            data: Series with categorical data
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure(data=[go.Pie(
                labels=data.index,
                values=data.values,
                hole=.3
            )])
            
            fig.update_layout(
                title=config.title,
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create pie chart: {str(e)}")
            return None
    
    def create_heatmap(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create heatmap.
        
        Args:
            data: DataFrame with correlation data
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure(data=go.Heatmap(
                z=data.values,
                x=data.columns,
                y=data.index,
                colorscale='RdBu'
            ))
            
            fig.update_layout(
                title=config.title,
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create heatmap: {str(e)}")
            return None
    
    def create_network_graph(self, G: nx.Graph, config: ChartConfig) -> go.Figure:
        """Create network graph.
        
        Args:
            G: NetworkX graph object
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            pos = nx.spring_layout(G)
            
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines'
            )
            
            node_x = []
            node_y = []
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers',
                hoverinfo='text',
                marker=dict(
                    showscale=True,
                    colorscale='YlGnBu',
                    size=10
                )
            )
            
            fig = go.Figure(data=[edge_trace, node_trace],
                          layout=go.Layout(
                              title=config.title,
                              width=config.width,
                              height=config.height,
                              template=self.themes.get(config.theme, "plotly")
                          ))
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create network graph: {str(e)}")
            return None
    
    def create_wordcloud(self, text: str, config: ChartConfig) -> plt.Figure:
        """Create word cloud.
        
        Args:
            text: Text data
            config: Chart configuration
            
        Returns:
            Matplotlib figure object
        """
        try:
            wordcloud = WordCloud(
                width=config.width,
                height=config.height,
                background_color='white'
            ).generate(text)
            
            fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title(config.title)
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create word cloud: {str(e)}")
            return None
    
    def create_box_plot(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create box plot.
        
        Args:
            data: DataFrame with numerical data
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure()
            
            for column in data.columns:
                fig.add_trace(go.Box(
                    y=data[column],
                    name=column,
                    boxpoints='all',
                    jitter=0.3,
                    pointpos=-1.8
                ))
            
            fig.update_layout(
                title=config.title,
                xaxis_title=config.x_label,
                yaxis_title=config.y_label,
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create box plot: {str(e)}")
            return None
    
    def create_violin_plot(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create violin plot.
        
        Args:
            data: DataFrame with numerical data
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure()
            
            for column in data.columns:
                fig.add_trace(go.Violin(
                    y=data[column],
                    name=column,
                    box_visible=True,
                    meanline_visible=True
                ))
            
            fig.update_layout(
                title=config.title,
                xaxis_title=config.x_label,
                yaxis_title=config.y_label,
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create violin plot: {str(e)}")
            return None
    
    def create_radar_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create radar chart.
        
        Args:
            data: DataFrame with categorical data
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure()
            
            for column in data.columns:
                fig.add_trace(go.Scatterpolar(
                    r=data[column],
                    theta=data.index,
                    name=column,
                    fill='toself'
                ))
            
            fig.update_layout(
                title=config.title,
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, data.max().max()]
                    )
                ),
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create radar chart: {str(e)}")
            return None
    
    def create_calendar_heatmap(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create calendar heatmap.
        
        Args:
            data: DataFrame with date index and value column
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            # Create calendar matrix
            cal_matrix = np.zeros((7, 53))
            dates = pd.date_range(start=data.index.min(), end=data.index.max())
            
            for date in dates:
                if date in data.index:
                    week = date.isocalendar()[1]
                    day = date.weekday()
                    cal_matrix[day, week-1] = data.loc[date].iloc[0]
            
            fig = go.Figure(data=go.Heatmap(
                z=cal_matrix,
                x=list(range(1, 54)),
                y=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                colorscale='Viridis'
            ))
            
            fig.update_layout(
                title=config.title,
                xaxis_title="Week",
                yaxis_title="Day",
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create calendar heatmap: {str(e)}")
            return None
    
    def create_scatter3d(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create 3D scatter plot.
        
        Args:
            data: DataFrame with x, y, z coordinates and optional color/size
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure(data=[go.Scatter3d(
                x=data['x'],
                y=data['y'],
                z=data['z'],
                mode='markers',
                marker=dict(
                    size=data.get('size', 12),
                    color=data.get('color', None),
                    opacity=0.8
                )
            )])
            
            fig.update_layout(
                title=config.title,
                scene=dict(
                    xaxis_title=config.x_label,
                    yaxis_title=config.y_label,
                    zaxis_title=config.z_label
                ),
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create 3D scatter plot: {str(e)}")
            return None
    
    def create_surface3d(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create 3D surface plot.
        
        Args:
            data: DataFrame with x, y coordinates and z values
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure(data=[go.Surface(
                x=data['x'],
                y=data['y'],
                z=data['z'],
                colorscale='Viridis'
            )])
            
            fig.update_layout(
                title=config.title,
                scene=dict(
                    xaxis_title=config.x_label,
                    yaxis_title=config.y_label,
                    zaxis_title=config.z_label
                ),
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create 3D surface plot: {str(e)}")
            return None
    
    def create_bubble_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create bubble chart.
        
        Args:
            data: DataFrame with x, y coordinates and size values
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure()
            
            for category in data['category'].unique():
                category_data = data[data['category'] == category]
                fig.add_trace(go.Scatter(
                    x=category_data['x'],
                    y=category_data['y'],
                    mode='markers',
                    name=category,
                    marker=dict(
                        size=category_data['size'],
                        sizemode='area',
                        sizeref=2.*max(category_data['size'])/(40.**2),
                        sizemin=4
                    )
                ))
            
            fig.update_layout(
                title=config.title,
                xaxis_title=config.x_label,
                yaxis_title=config.y_label,
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create bubble chart: {str(e)}")
            return None
    
    def create_funnel_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create funnel chart.
        
        Args:
            data: DataFrame with stages and values
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure(go.Funnel(
                y=data['stage'],
                x=data['value'],
                textinfo="value+percent initial"
            ))
            
            fig.update_layout(
                title=config.title,
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create funnel chart: {str(e)}")
            return None
    
    def create_polar_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create polar chart.
        
        Args:
            data: DataFrame with angle and radius values
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure()
            
            for column in data.columns:
                fig.add_trace(go.Scatterpolar(
                    r=data[column],
                    theta=data.index,
                    name=column,
                    fill='toself'
                ))
            
            fig.update_layout(
                title=config.title,
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, data.max().max()]
                    )
                ),
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create polar chart: {str(e)}")
            return None
    
    def create_candlestick_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create candlestick chart.
        
        Args:
            data: DataFrame with OHLC data
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close']
            )])
            
            fig.update_layout(
                title=config.title,
                xaxis_title=config.x_label,
                yaxis_title=config.y_label,
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create candlestick chart: {str(e)}")
            return None
    
    def create_area_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create area chart.
        
        Args:
            data: DataFrame with time series data
            config: Chart configuration
            
        Returns:
            Plotly figure object
        """
        try:
            fig = go.Figure()
            
            for column in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data[column],
                    name=column,
                    fill='tonexty'
                ))
            
            fig.update_layout(
                title=config.title,
                xaxis_title=config.x_label,
                yaxis_title=config.y_label,
                width=config.width,
                height=config.height,
                template=self.themes.get(config.theme, "plotly")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create area chart: {str(e)}")
            return None
    
    def save_chart(self, fig: Union[go.Figure, plt.Figure], 
                  filename: str, format: str = 'html') -> str:
        """Save chart to file.
        
        Args:
            fig: Figure object
            filename: Output filename
            format: Output format (html, png, etc.)
            
        Returns:
            Path to saved file
        """
        try:
            output_path = self.config_dir / f"{filename}.{format}"
            
            if isinstance(fig, go.Figure):
                if format == 'html':
                    fig.write_html(str(output_path))
                else:
                    fig.write_image(str(output_path))
            else:
                fig.savefig(str(output_path))
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save chart: {str(e)}")
            return None
    
    def get_chart_base64(self, fig: Union[go.Figure, plt.Figure], 
                        format: str = 'png') -> str:
        """Get base64 encoded chart.
        
        Args:
            fig: Figure object
            format: Output format
            
        Returns:
            Base64 encoded string
        """
        try:
            if isinstance(fig, go.Figure):
                img_bytes = fig.to_image(format=format)
            else:
                buf = BytesIO()
                fig.savefig(buf, format=format)
                img_bytes = buf.getvalue()
            
            return base64.b64encode(img_bytes).decode()
            
        except Exception as e:
            logger.error(f"Failed to get chart base64: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    visualizer = EmailVisualizer()
    
    # Sample data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    data = pd.DataFrame({
        'Emails': np.random.randint(10, 100, size=len(dates)),
        'Responses': np.random.randint(5, 50, size=len(dates))
    }, index=dates)
    
    # Create time series chart
    config = ChartConfig(
        name="email_volume",
        type=ChartType.LINE,
        title="Email Volume Over Time",
        x_label="Date",
        y_label="Count"
    )
    
    fig = visualizer.create_time_series(data, config)
    visualizer.save_chart(fig, "email_volume") 