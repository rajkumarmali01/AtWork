import streamlit as st
import pandas as pd
from datetime import datetime

def format_timedelta_to_hhmm(t):
    if pd.isnull(t):
        return ""
    total_minutes = int(t.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"

def process_data(df):
    # Combine date and time into a single datetime column
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    # Robust cleaning of 'reader in and out' column (handles NaN and blanks)
    df['reader in and out'] = df['reader in and out'].apply(
        lambda x: str(x).strip().lower() if pd.notnull(x) else ""
    )
    # Mark entries as 'in' or 'out' only if x is a string
    def get_entry_type(x):
        if isinstance(x, str):
            if 'in' in x:
                return 'in'
            elif 'out' in x:
                return 'out'
        return None
    df['entry_type'] = df['reader in and out'].apply(get_entry_type)
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
    # Flag missing punches
    def missing_punch(row):
        if pd.isnull(row['First In']) and pd.isnull(row['Last Out']):
            return "Both Missing"
        elif pd.isnull(row['First In']):
            return "Punch In Missing"
        elif pd.isnull(row['Last Out']):
            return "Punch Out Missing"
        else:
            return ""
    result['Missing Punch'] = result.apply(missing_punch, axis=1)
    return result

st.title("🏢 Atwork Employee Daily Time Analysis")
st.write("Upload your employee punch data in CSV format to analyze Timing of employee")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    try:
        raw_df = pd.read_csv(uploaded_file)
        required_cols = {'employee id', 'employee name', 'date', 'time', 'reader in and out'}
        if not required_cols.issubset(set(raw_df.columns)):
            st.error(f"CSV must contain columns: {', '.join(required_cols)}")
        else:
            result_df = process_data(raw_df)

            # ---- Main Daily Time Analysis Table ----
            st.subheader("Daily Time Analysis")
            st.dataframe(result_df.style.format({
                'First In': lambda t: t.strftime("%H:%M") if pd.notnull(t) else "",
                'Last Out': lambda t: t.strftime("%H:%M") if pd.notnull(t) else "",
                'Total Time': format_timedelta_to_hhmm,
                'Missing Punch': lambda x: x if x else ""
            }))

            # ---- Download: Main Table with HH:MM "Total Time" ----
            result_df_export = result_df.copy()
            result_df_export['First In'] = result_df_export['First In'].dt.strftime("%H:%M")
            result_df_export['Last Out'] = result_df_export['Last Out'].dt.strftime("%H:%M")
            result_df_export['Total Time'] = result_df_export['Total Time'].apply(format_timedelta_to_hhmm)
            csv = result_df_export.to_csv(index=False)
            st.download_button(
                label="📥 Download Analysis CSV",
                data=csv,
                file_name=f"time_analysis_{datetime.now().date()}.csv"
            )

            # ---- Employees with less than 9 hours in a day ----
            less_than_9_hours = result_df[result_df['Total Time'] < pd.Timedelta(hours=9)][
                ['Employee ID', 'Name', 'Date', 'Total Time']
            ]
            st.subheader("Employees Who Stayed Less Than 9 Hours (Daily)")
            st.dataframe(less_than_9_hours.style.format({
                'Total Time': format_timedelta_to_hhmm
            }))
            # Download: Less Than 9 Hours Table
            less_than_9_hours_export = less_than_9_hours.copy()
            less_than_9_hours_export['Total Time'] = less_than_9_hours_export['Total Time'].apply(format_timedelta_to_hhmm)
            csv_lt9 = less_than_9_hours_export.to_csv(index=False)
            st.download_button(
                label="📥 Download Less Than 9 Hours CSV",
                data=csv_lt9,
                file_name=f"less_than_9_hours_{datetime.now().date()}.csv"
            )

            # ---- Weekly Analysis: Less than 49 hours ----
            result_df['Date'] = pd.to_datetime(result_df['Date'])
            start_date = result_df['Date'].min()
            result_df['Week'] = ((result_df['Date'] - start_date).dt.days // 7) + 1

            weekly_hours = result_df.groupby(['Employee ID', 'Name', 'Week'])['Total Time'].sum().reset_index()
            weekly_below_49 = weekly_hours[weekly_hours['Total Time'] < pd.Timedelta(hours=49)]
            weekly_below_49['Total Time'] = weekly_below_49['Total Time'].apply(format_timedelta_to_hhmm)

            st.subheader("Employees With Weekly Total Less Than 49 Hours")
            st.dataframe(weekly_below_49[['Employee ID', 'Name', 'Week', 'Total Time']])
            csv_lt49 = weekly_below_49[['Employee ID', 'Name', 'Week', 'Total Time']].to_csv(index=False)
            st.download_button(
                label="📥 Download Weekly Less Than 49 Hours CSV",
                data=csv_lt49,
                file_name=f"weekly_less_than_49_hours_{datetime.now().date()}.csv"
            )

            # ---- Missing Punches Output ----
            missing_punches = result_df[result_df['Missing Punch'] != ""]
            st.subheader("⚠️ Employees With Missing Punches")
            if not missing_punches.empty:
                st.dataframe(missing_punches[['Employee ID', 'Name', 'Date', 'Missing Punch']])
                csv_missing = missing_punches[['Employee ID', 'Name', 'Date', 'Missing Punch']].to_csv(index=False)
                st.download_button(
                    label="📥 Download Missing Punches CSV",
                    data=csv_missing,
                    file_name=f"missing_punches_{datetime.now().date()}.csv"
                )
            else:
                st.success("No missing punches found!")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Awaiting CSV file upload.")

st.markdown("---")
st.markdown("*Sample CSV columns:* employee name, date, employee id, time, reader in and out Created By :- Rajkumar Mali Intern")
