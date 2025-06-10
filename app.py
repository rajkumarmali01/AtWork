import streamlit as st
import pandas as pd
from datetime import datetime

# --- Data Processing Function ---
def process_data(df):
    # Combine date and time into a single datetime column
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    
    # Clean up the 'reader in and out' column (strip spaces, lowercase)
    df['reader in and out'] = df['reader in and out'].str.strip().str.lower()
    
    # Mark entries as 'in' or 'out' if they contain those words
    df['entry_type'] = df['reader in and out'].apply(
        lambda x: 'in' if 'in' in x else ('out' if 'out' in x else None)
    )
    
    # Separate In and Out records
    in_df = df[df['entry_type'] == 'in']
    out_df = df[df['entry_type'] == 'out']
    
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
st.title("🏢 Employee Time Analyzer")
st.write("Upload your employee punch data in CSV format to analyze building occupancy time.")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    try:
        raw_df = pd.read_csv(uploaded_file)
        # Check required columns -- all lowercase!
        required_cols = {'employee id', 'employee name', 'date', 'time', 'reader in and out'}
        if not required_cols.issubset(set(raw_df.columns)):
            st.error(f"CSV must contain columns: {', '.join(required_cols)}")
        else:
            result_df = process_data(raw_df)
            st.subheader("Daily Time Analysis")
            st.dataframe(result_df.style.format({
                'First In': lambda t: t.strftime("%H:%M") if pd.notnull(t) else "",
                'Last Out': lambda t: t.strftime("%H:%M") if pd.notnull(t) else "",
                'Total Time': lambda t: (
                    f"{int(t.total_seconds()//3600):02d}:{int((t.total_seconds()%3600)//60):02d}"
                    if pd.notnull(t) else ""
                )
            }))
            # Download button for full analysis
            csv = result_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Analysis CSV",
                data=csv,
                file_name=f"time_analysis_{datetime.now().date()}.csv"
            )

            # --- Employees with less than 9 hours in a day ---
            less_than_9_hours = result_df[result_df['Total Time'] < pd.Timedelta(hours=9)][
                ['Employee ID', 'Name', 'Date', 'Total Time']
            ]
            st.subheader("Employees Who Stayed Less Than 9 Hours (Daily)")
            if not less_than_9_hours.empty:
                st.dataframe(less_than_9_hours.style.format({
                    'Total Time': lambda t: (
                        f"{int(t.total_seconds()//3600):02d}:{int((t.total_seconds()%3600)//60):02d}"
                        if pd.notnull(t) else ""
                    )
                }))
                csv_lt9 = less_than_9_hours.to_csv(index=False)
                st.download_button(
                    label="📥 Download Less Than 9 Hours CSV",
                    data=csv_lt9,
                    file_name=f"less_than_9_hours_{datetime.now().date()}.csv"
                )
            else:
                st.info("No employees found who stayed less than 9 hours in a day.")

            # --- Weekly Analysis: Less than 49 hours ---
            result_df['Week'] = pd.to_datetime(result_df['Date']).dt.isocalendar().week
            result_df['Year'] = pd.to_datetime(result_df['Date']).dt.isocalendar().year
            weekly_hours = result_df.groupby(['Employee ID', 'Name', 'Year', 'Week'])['Total Time'].sum().reset_index()
            weekly_below_49 = weekly_hours[weekly_hours['Total Time'] < pd.Timedelta(hours=49)]
            st.subheader("Employees With Weekly Total Less Than 49 Hours")
            if not weekly_below_49.empty:
                weekly_below_49['Total Time'] = weekly_below_49['Total Time'].apply(
                    lambda t: f"{int(t.total_seconds()//3600):02d}:{int((t.total_seconds()%3600)//60):02d}"
                    if pd.notnull(t) else ""
                )
                st.dataframe(weekly_below_49[['Employee ID', 'Name', 'Year', 'Week', 'Total Time']])
                csv_lt49 = weekly_below_49.to_csv(index=False)
                st.download_button(
                    label="📥 Download Weekly Less Than 49 Hours CSV",
                    data=csv_lt49,
                    file_name=f"weekly_less_than_49_hours_{datetime.now().date()}.csv"
                )
            else:
                st.info("No employees found with weekly total less than 49 hours.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Awaiting CSV file upload.")

st.markdown("---")
st.markdown("*Sample CSV columns:* employee name, date, employee id, time, reader in and out")
