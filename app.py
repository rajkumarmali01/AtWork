{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "53116ac6-2ef7-4d4e-b6b5-129a9fda4fe1",
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "2025-06-06 11:17:29.903 \n",
      "  \u001b[33m\u001b[1mWarning:\u001b[0m to view this Streamlit app on a browser, run it with the following\n",
      "  command:\n",
      "\n",
      "    streamlit run C:\\Anaconda\\Lib\\site-packages\\ipykernel_launcher.py [ARGUMENTS]\n"
     ]
    }
   ],
   "source": [
    "import streamlit as st\n",
    "import pandas as pd\n",
    "from datetime import datetime\n",
    "\n",
    "# --- Data Processing Function ---\n",
    "def process_data(df):\n",
    "    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])\n",
    "    in_df = df[df['reader in and Out'] == 'In']\n",
    "    out_df = df[df['reader in and Out'] == 'Out']\n",
    "    first_in = in_df.groupby(['employee id', 'employee name', 'date'])['datetime'].min()\n",
    "    last_out = out_df.groupby(['employee id', 'employee name', 'date'])['datetime'].max()\n",
    "    result = pd.concat([first_in, last_out], axis=1).reset_index()\n",
    "    result.columns = ['Employee ID', 'Name', 'Date', 'First In', 'Last Out']\n",
    "    result['Total Time'] = result['Last Out'] - result['First In']\n",
    "    return result\n",
    "\n",
    "# --- Streamlit App Code ---\n",
    "st.title(\"🏢 XYZ Building Time Analyzer\")\n",
    "st.write(\"Upload employee punch data CSV to analyze building occupancy time\")\n",
    "\n",
    "uploaded_file = st.file_uploader(\"Choose CSV file\", type=\"csv\")\n",
    "\n",
    "if uploaded_file:\n",
    "    raw_df = pd.read_csv(uploaded_file)\n",
    "    result_df = process_data(raw_df)\n",
    "    st.subheader(\"Daily Time Analysis\")\n",
    "    st.dataframe(result_df.style.format({\n",
    "        'First In': lambda t: t.strftime(\"%H:%M\"),\n",
    "        'Last Out': lambda t: t.strftime(\"%H:%M\"),\n",
    "        'Total Time': lambda t: str(t).split(\" days \")[-1]\n",
    "    }))\n",
    "    csv = result_df.to_csv(index=False)\n",
    "    st.download_button(\n",
    "        label=\"📥 Download Analysis\",\n",
    "        data=csv,\n",
    "        file_name=f\"time_analysis_{datetime.now().date()}.csv\"\n",
    "    )"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "535f20db-f2ee-4f48-a706-9229ceaf3422",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.4"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
