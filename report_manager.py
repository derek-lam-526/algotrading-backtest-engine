import os
import pandas as pd

class ReportGenerator:
    @staticmethod
    def save_report(backtest_instance, stats, filename, strategy_class=None):
        # ... (Keep steps 1, 2, 3 the same as you have now) ...

        # --- INSERT NEW LOGIC HERE (After step 3) ---
        # 3b. Extract Strategy Info
        desc = "No description."
        params_html = "<p>No parameters.</p>"
        
        if strategy_class:
            # Get Description
            if strategy_class.__doc__:
                desc = strategy_class.__doc__.strip().replace("\n", "<br>")
            
            # Get Parameters (int/float/str variables only)
            params = {k: v for k, v in strategy_class.__dict__.items() 
                    if not k.startswith('_') and isinstance(v, (int, float, str))}
            
            if params:
                # Convert dict to simple HTML table rows
                rows = "".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in params.items()])
                params_html = f"<table class='metrics-table'>{rows}</table>"
        """
        Generates a split-screen HTML report:
        Left: Interactive Chart
        Right: Performance Metrics Table
        """
        # 1. Generate the standard Bokeh plot to a temporary file
        temp_file = "temp_plot.html"
        backtest_instance.plot(filename=temp_file, open_browser=False)
        
        # 2. Read the generated HTML content
        with open(temp_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # 3. Clean up the Stats (Filter out heavy dataframes like 'Equity Curve')
        # We only want the summary metrics (scalars)
        metrics = stats[stats.apply(lambda x: not isinstance(x, (pd.DataFrame, pd.Series, list)))]
        metrics_df = pd.DataFrame(metrics).reset_index()
        metrics_df.columns = ["Metric", "Value"]
        
        # Format numbers (optional cleanup)
        metrics_df["Value"] = metrics_df["Value"].apply(lambda x: str(round(x, 4)) if isinstance(x, float) else str(x))
        
        # Convert to HTML Table
        table_html = metrics_df.to_html(index=False, classes="metrics-table", border=0)

        # 4. Define CSS Grid Layout
        custom_css = """
        <style>
            /* GRID SETUP */
            body { 
                display: grid !important; 
                grid-template-columns: 1fr 350px !important; /* Left: Auto, Right: Fixed */
                grid-template-rows: 1fr 250px !important;    /* Top: Auto, Bottom: Fixed */
                height: 100vh !important; 
                margin: 0 !important; 
                font-family: 'Segoe UI', sans-serif;
                overflow: hidden !important;
            }
            
            /* TOP LEFT: Chart */
            .bk-root { 
                grid-column: 1 / 2 !important;
                grid-row: 1 / 2 !important;
                width: 100% !important;
                height: 100% !important;
                border-bottom: 2px solid #ccc;
            }
            
            /* BOTTOM LEFT: Strategy Info (New) */
            .strategy-panel {
                grid-column: 1 / 2 !important;
                grid-row: 2 / 3 !important;
                padding: 20px;
                overflow-y: auto;
                display: flex; gap: 30px; /* Split description and params */
            }

            /* RIGHT: Metrics (Spans full height) */
            .side-panel { 
                grid-column: 2 / 3 !important;
                grid-row: 1 / 3 !important;
                background: #f8f9fa; 
                border-left: 2px solid #ccc; 
                padding: 20px; 
                overflow-y: auto;
            }

            /* Table Styling (Reused) */
            .metrics-table { width: 100%; border-collapse: collapse; font-size: 13px; }
            .metrics-table td, th { padding: 8px; border-bottom: 1px solid #eee; }
            h2 { margin-top: 0; font-size: 18px; border-bottom: 2px solid #007bff; display: inline-block;}
        </style>
        """

        # 5. Define HTML for BOTH panels
        # New Bottom-Left Panel
        strategy_html = f"""
        <div class="strategy-panel">
            <div style="flex: 2;"> <h2>Logic</h2> <p>{desc}</p> </div>
            <div style="flex: 1;"> <h2>Settings</h2> {params_html} </div>
        </div>
        """
        
        # Existing Right Panel
        side_panel_html = f"""
        <div class="side-panel">
            <h2>Results</h2>
            {table_html}
        </div>
        """

        # 6. Inject CSS and BOTH HTML Panels
        html_content = html_content.replace("</head>", f"{custom_css}</head>")
        # Append both panels to the end of the body
        html_content = html_content.replace("</body>", f"{strategy_html}{side_panel_html}</body>")
        
        # Inject Side Panel before </body>
        html_content = html_content.replace("</body>", f"{side_panel_html}</body>")

        # 7. Save Final Report
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Cleanup temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        print(f"Advanced report saved to: {filename}")
