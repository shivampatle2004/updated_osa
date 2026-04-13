import sys
import os

# Add the current directory to sys.path to import modules
sys.path.append(os.getcwd())

import pandas as pd
import numpy as np
from services.graph_engine import GraphEngine

def test_aggregation():
    print("Testing GraphEngine aggregation...")
    df = pd.DataFrame({
        'A': ['cat1', 'cat2', 'cat1', 'cat3'],
        'B': [10, 20, 30, 40],
        'C': [1.1, 2.2, 3.3, 4.4]
    })
    
    chart_types = ["bar", "pie", "line", "area", "donut", "radar", "treemap", "composed", "funnel", "radialBar", "kpiCard", "heatmap", "sunburst", "boxPlot", "waterfall", "polarArea", "bubble", "bullet"]
    
    for ct in chart_types:
        try:
            print(f"Testing {ct}...")
            res = GraphEngine.get_aggregated_data(df, ct, 'A', 'B', 'sum')
            # print(f"  Result: {res}")
            
            # Test with NaN
            df_nan = df.copy()
            df_nan.loc[0, 'B'] = np.nan
            res_nan = GraphEngine.get_aggregated_data(df_nan, ct, 'A', 'B', 'sum')
            # print(f"  Result with NaN: {res_nan}")
            
        except Exception as e:
            print(f"FAILED {ct}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_aggregation()
