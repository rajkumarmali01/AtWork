import streamlit as st
import pandas as pd
from datetime import datetime

# --- Data Processing Function ---
def process_data(df):
    # Combine date and time into a single datetime column
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    
    # Separate In and Out records
    in_df = df[df['reader in and Out'].str.lower() == 'in']
    out_df = df[df['reader in and Out'].str.lower() == 'out']
    
    # Get the earliest In and latest Out for each employee per day
    first_in = in_df.groupby(['employee id', 'employee name', 'date'])['datetime'].min()
    last_out = out_df.groupby(['employee id', 'employee name', 'date'])['datetime'].max()
    
    # Combine results into a single DataFrame
    result = pd.concat([first_in, last_out], axis=1).reset_index()
    result.columns = ['Employee ID', 'Name', 'Date', 'First In', 'Last Out']
    
    # Calculate total time spent in the building
    result['Total Time'] = result['Last Out'] - result['First In']
    
    return result

# --- Streamlit App Interface ---
st.title("🏢 XYZ Building Time Analyzer")
st.write("Upload your employee punch data CSV to analyze building occupancy time.")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    try:
        raw_df = pd.read_csv(uploaded_file)
        # Check required columns
        required_cols = {'employee id', 'employee name', 'date', 'time', 'reader in and Out'}
        if not required_cols.issubset(set(raw_df.columns)):
            st.error(f"CSV must contain columns: {', '.join(required_cols)}")
        else:
            result_df = process_data(raw_df)
            st.subheader("Daily Time Analysis")
            st.dataframe(result_df.style.format({
                'First In': lambda t: t.strftime("%H:%M") if pd.notnull(t) else "",
                'Last Out': lambda t: t.strftime("%H:%M") if pd.notnull(t) else "",
                'Total Time': lambda t: str(t).split(" days ")[-1] if pd.notnull(t) else ""
            }))
            # Download button
            csv = result_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Analysis CSV",
                data=csv,
                file_name=f"time_analysis_{datetime.now().date()}.csv"
            )
    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Awaiting CSV file upload.")

st.markdown("---")
st.markdown("*Sample CSV columns:* employee id, employee name, date, time, reader in and Out")