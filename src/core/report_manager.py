import os
import pandas as pd
import json
import csv
from datetime import datetime 

class ReportGenerator:
    @staticmethod
    def save_report(backtest_instance, stats, symbol, timeframe, strategy_class=None, output_dir="output"):
        """
        Generates a Dashboard HTML report:
        - Top Left: Interactive Chart
        - Right: Performance Metrics
        - Bottom: Tabbed Panel (Strategy Info | Trade History)
        """
        strat_instance = stats._strategy
        strat_name = strat_instance.__class__.__name__
        strat_doc = strat_instance.__class__.__doc__

        output_folder = os.path.join(output_dir, strat_name, symbol)
        os.makedirs(output_folder, exist_ok=True)

        start_date = stats["Start"].strftime("%Y%m%d")
        end_date = stats["End"].strftime("%Y%m%d")

        def safe_val(val): 
            return val if (val and str(val) != 'nan') else 0.0
        
        return_pct = round(stats['Return [%]'], 2)
        sharpe = safe_val(stats['Sharpe Ratio'])
        sharpe_str = f"{sharpe:.2f}"

        filename = f"{strat_name}_{symbol}_{timeframe.value}_{start_date}-{end_date}_Ret{return_pct}_Shrp{sharpe_str}.html"
        full_path = os.path.join(output_folder, filename)
        
        # 1. Generate the standard Bokeh plot to a temporary file
        temp_file = "temp_plot.html"
        backtest_instance.plot(filename=temp_file, open_browser=False)
        
        # 2. Read the generated HTML content
        with open(temp_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        report_title = os.path.basename(filename)
        html_content = html_content.replace("<title>temp_plot.html</title>", f"<title>{report_title}</title>")
        
        # --- PROCESS METRICS ---
        metrics = stats[stats.apply(lambda x: not isinstance(x, (pd.DataFrame, pd.Series, list)))]
        metrics_df = pd.DataFrame(metrics).reset_index()
        metrics_df.columns = ["Metric", "Value"]
        metrics_df["Value"] = metrics_df["Value"].apply(lambda x: str(round(x, 4)) if isinstance(x, float) else str(x))
        metrics_html = metrics_df.to_html(index=False, classes="metrics-table", border=0)

        # --- PROCESS TRADE HISTORY ---
        trades = stats['_trades']
        trades_count = len(trades)
        trades_html = "<p style='color: #666; padding: 20px;'>No trades executed.</p>"
        
        if not trades.empty:
            t_df = trades.copy()
            # Round floats
            numeric_cols = t_df.select_dtypes(include=['float']).columns
            t_df[numeric_cols] = t_df[numeric_cols].round(4)
            # Format Dates
            date_cols = t_df.select_dtypes(include=['datetime']).columns
            for col in date_cols:
                t_df[col] = t_df[col].dt.strftime('%Y-%m-%d %H:%M')
            
            # Create Table
            trades_html = t_df.to_html(index=False, classes="metrics-table trade-table", border=0)

        # --- PROCESS STRATEGY INFO ---
        desc = "No description available."
        if strat_doc:
            desc = strat_doc.strip().replace("\n", "<br>")

        params_html = "<p>No parameters.</p>"

        params = {}
        BLACKLIST = {
            'broker', 'data', 'orders', 'position', 'trades', 'closed_trades', 
            'equity', 'cash', 'commission', 'margin', 'trade_on_close', 'hedging'
        }
        
        for name in dir(strat_instance):
            if name.startswith('_') or name in BLACKLIST: continue
            try:
                val = getattr(strat_instance, name)
                # Only keep simple types (numbers/strings)
                if isinstance(val, (int, float, str, bool)):
                    params[name] = val
            except: continue

        if params:
            rows = "".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in params.items()])
            params_html = f"<table class='metrics-table' style='width: auto;'>{rows}</table>"

        custom_css = ReportGenerator._get_css()
        tab_script = ReportGenerator._get_js()

        # --- HTML STRUCTURE ---
        
        # 1. Right Panel
        side_panel_html = f"""
        <div class="panel side-panel">
            <div class="content-wrapper" style="flex-shrink: 0;">
                <h2>Performance Metrics</h2>
            </div>
            <div class="side-content">
                {metrics_html}
            </div>
        </div>
        """

        # 2. Bottom Panel
        bottom_panel_html = f"""
        <div class="panel bottom-panel">
            <div class="tab-header">
                <button class="tab-btn active" onclick="openTab(event, 'TabStrategy')">Strategy Info</button>
                <button class="tab-btn" onclick="openTab(event, 'TabTrades')">Trade History ({trades_count})</button>
            </div>

            <div id="TabStrategy" class="tab-content active">
                <div class="content-wrapper" style="display: flex; gap: 40px;">
                    <div style="flex: 2; border-right: 1px solid #eee; padding-right: 20px;"> 
                        <h2>Logic</h2> 
                        <p style="line-height: 1.6; color: #333;">{desc}</p> 
                    </div>
                    <div style="flex: 1;"> 
                        <h2>Settings</h2> 
                        {params_html} 
                    </div>
                </div>
            </div>

            <div id="TabTrades" class="tab-content">
                {trades_html}
            </div>
        </div>
        """

        # --- INJECTION ---
        html_content = html_content.replace("</head>", f"{custom_css}{tab_script}</head>")
        html_content = html_content.replace("</body>", f"{bottom_panel_html}{side_panel_html}</body>")

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            print(f"\nPlot saved to: {full_path}")
        
        if os.path.exists(temp_file):
            os.remove(temp_file)

        log_file = os.path.join(output_dir, strat_name, "summary_log.csv")
        ReportGenerator._append_to_log(log_file, stats, symbol, timeframe, full_path)

    @staticmethod
    def _append_to_log(filepath, stats, symbol, timeframe, html_path):
        """Appends a single row of metrics to a CSV file."""
        file_exists = os.path.isfile(filepath)

        strat_obj = stats._strategy
        params = {}
        strat_name = strat_obj.__class__.__name__

        BLACKLIST = {
            'broker', 'data', 'orders', 'position', 'trades', 'closed_trades', 
            'equity', 'cash', 'commission', 'margin', 'trade_on_close', 'hedging'
        }

        # Scan the instance attributes, not the class dictionary
        for name in dir(strat_obj):
            if name.startswith('_') or name in BLACKLIST: continue
            try:
                val = getattr(strat_obj, name)
                if isinstance(val, (int, float, bool, str)):
                    params[name] = val
            except: continue

        param_str = " | ".join([f"{k}:{v}" for k,v in params.items()])

        fieldnames = [
            'Run_Time', 'Symbol', 'Timeframe', 'Strategy',
            'Start', 'End', 
            'Return_Pct', 'Sharpe_Ratio', 'Max_DD', 'Win_Rate', '#_Trades',
            'Parameters', 
            'Report_Path'
        ]
        
        def safe_round(val):
            try: return round(float(val), 2)
            except: return 0.0

        data = {
            'Run_Time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'Strategy': strat_name,
            'Symbol': symbol,
            'Timeframe': timeframe,
            'Start': stats['Start'].strftime('%Y-%m-%d'),
            'End': stats['End'].strftime('%Y-%m-%d'),
            'Return_Pct': safe_round(stats['Return [%]']),
            'Sharpe_Ratio': safe_round(stats['Sharpe Ratio']),
            'Max_DD': safe_round(stats['Max. Drawdown [%]']),
            'Win_Rate': safe_round(stats['Win Rate [%]']),
            '#_Trades': stats['# Trades'],
            'Parameters': param_str,
            'Report_Path': html_path
        }
        
        try:
            with open(filepath, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists: writer.writeheader()
                writer.writerow(data)
            print(f"Stats logged to: {filepath}")
        except Exception as e:
            print(f"CSV Log Error: {e}")

    @staticmethod
    def _get_css():
        return """
        <style>
            /* GRID SETUP */
            body { 
                display: grid !important; 
                /* minmax(0, 1fr) prevents the chart/table from forcing page width expansion */
                grid-template-columns: minmax(0, 1fr) 340px !important; 
                
                /* CHANGED: Reduced bottom row height from 350px to 280px (shorter containers) */
                grid-template-rows: 1fr 280px !important;    
                
                height: 100vh !important; 
                min-height: 800px !important; 
                
                /* CHANGED: Disable main page horizontal scroll, keep vertical */
                overflow-x: hidden !important;
                overflow-y: auto !important;  
                
                margin: 0 !important; 
                padding: 15px !important;
                box-sizing: border-box !important;
                gap: 15px !important;
                font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
                background-color: #eef2f5;
            }
            
            /* PANELS */
            .panel {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                display: flex; flex-direction: column;
                overflow: hidden;
                position: relative;
            }

            /* TOP LEFT: Chart */
            .bk-root { 
                grid-column: 1 / 2 !important;
                grid-row: 1 / 2 !important;
                width: 100% !important; height: 100% !important;
                background: white; border-radius: 8px;
                min-height: 400px;
            }
            
            /* RIGHT: Metrics */
            .side-panel { 
                grid-column: 2 / 3 !important;
                grid-row: 1 / 3 !important; 
                padding: 0; 
            }
            
            /* SCROLLABLE CONTENT AREAS */
            .side-content, .tab-content {
                flex: 1;
                min-height: 0; 
                
                /* Vertical Scroll for long lists */
                overflow-y: auto;
                
                /* CHANGED: Horizontal Scroll for wide tables (PRESERVED) */
                overflow-x: auto; 
            }

            /* BOTTOM LEFT: Tabs */
            .bottom-panel {
                grid-column: 1 / 2 !important;
                grid-row: 2 / 3 !important;
            }

            /* TAB STYLING */
            .tab-header {
                display: flex;
                background-color: #f8f9fa;
                border-bottom: 1px solid #d1d5db;
                flex-shrink: 0; 
            }
            .tab-btn {
                padding: 12px 20px;
                cursor: pointer;
                background: transparent;
                border: none;
                font-size: 14px;
                font-weight: 600;
                color: #555;
                outline: none;
                transition: 0.2s;
            }
            .tab-btn:hover { background-color: #e9ecef; }
            .tab-btn.active {
                background-color: white;
                color: #007bff;
                border-bottom: 3px solid #007bff;
            }
            
            /* TAB CONTENT */
            .tab-content {
                display: none; 
                padding: 0; 
                background: white;
            }
            .tab-content.active { display: block; }
            
            .content-wrapper { padding: 20px; } 

            /* TABLE STYLING */
            .metrics-table { 
                width: 100%; 
                border-collapse: separate; 
                border-spacing: 0;
                font-size: 13px; 
            }
            
            /* Sticky Header */
            .metrics-table th { 
                position: sticky; 
                top: 0; 
                z-index: 50; 
                background-color: #f1f3f5; 
                color: #333;
                text-align: left; 
                font-weight: 600; 
                padding: 10px;
                border-bottom: 2px solid #ddd;
                box-shadow: 0 2px 2px -1px rgba(0,0,0,0.1); 
            }
            
            .metrics-table td { 
                padding: 8px 10px; 
                border-bottom: 1px solid #eee; 
                background-color: white; 
                white-space: nowrap;     
            }
            
            /* Fix last row padding */
            .metrics-table tr:last-child td {
                border-bottom: none;
                padding-bottom: 20px;
            }

            .metrics-table tr:hover td { background-color: #f8f9fa; }
            
            h2 { font-size: 16px; margin: 0 0 10px 0; border-bottom: 2px solid #007bff; display: inline-block; padding-bottom: 4px; }
            
            /* Custom Scrollbar Styling */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: #f1f1f1; }
            ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }
            ::-webkit-scrollbar-thumb:hover { background: #bbb; }
        </style>
        """
    
    @staticmethod
    def _get_js():
        return """
        <script>
            function openTab(evt, tabName) {
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].className = tabcontent[i].className.replace(" active", "");
                    if(tabcontent[i].id !== tabName) tabcontent[i].style.display = "none";
                }
                tablinks = document.getElementsByClassName("tab-btn");
                for (i = 0; i < tablinks.length; i++) {
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }
                var activeTab = document.getElementById(tabName);
                activeTab.style.display = "block";
                activeTab.className += " active";
                evt.currentTarget.className += " active";
            }
        </script>
        """
