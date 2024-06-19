import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
#from datetime import time
import sys
from pathlib import Path
import geopandas as gpd
import time
import hmac
import plotly.express as px

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

# Charger vos datasets
@st.cache_data
def load_data_legs():
    # Get the current file's directory
    current_dir = Path(__file__).resolve().parent
    
    # Append parent directory to the system path
    parent_dir = current_dir.parent
    sys.path.append(parent_dir)
    
    # Define paths relative to the current file
    data_dir = current_dir / "data"
    legs_path = data_dir / "legs_nogeometry.pkl"
    
    # Load data using pandas
    legs_nogeometry = pd.read_pickle(legs_path)
    
    return legs_nogeometry

@st.cache_data
def load_data_usrstat():
    # Get the current file's directory
    current_dir = Path(__file__).resolve().parent
    
    # Append parent directory to the system path
    parent_dir = current_dir.parent
    sys.path.append(parent_dir)
    
    # Define paths relative to the current file
    data_dir = current_dir / "data"
    usr_stats_path = data_dir / "usr_stats_nogeometry.pkl"
    
    # Load data using pandas
    usr_stats = pd.read_pickle(usr_stats_path)
    
    return usr_stats

#Compute daily modal distances
def get_daily_modal_distances(df, mode_col):
    
    # Create a copy of the DataFrame to avoid modifying the original
    df = df.copy()
    
    df['length_leg'] = df['length_leg'].astype(float)
    # Group by 'user_id_day', 'previous_mode', and 'previous_leg_id', then sum the distances
    grouped = df.groupby(['user_id_fors', 'user_id_day', mode_col])['length_leg'].sum().reset_index()

    # Pivot the table to have modes as columns
    pivoted = grouped.pivot_table(
        index=['user_id_fors', 'user_id_day'],
        columns=mode_col,
        values='length_leg',
        aggfunc='sum'
    ).reset_index()

    # Resample to include missing days and fill NaNs with different values in different columns
    pivoted['date'] = pd.to_datetime(pivoted['user_id_day'].str[-8:])
    # Create a date range covering the entire date range for each ID
    date_ranges = pivoted.groupby('user_id_fors')['date'].agg(['min', 'max']).reset_index()
    date_ranges['legs_date'] = date_ranges.apply(lambda row: pd.date_range(row['min'], row['max'], freq='D'), axis=1)

    # Create a Cartesian product of IDs and date ranges
    cartesian = date_ranges.explode('legs_date').reset_index(drop=True)

    # Complete the original df with a continuous timeline
    pivoted_filled = pd.merge(pivoted, cartesian[['user_id_fors', 'legs_date']], how='outer', left_on=['user_id_fors', 'date'],
                              right_on=['user_id_fors', 'legs_date'])

    # Create 'days_without_track' column and mark as True for added rows, False otherwise
    pivoted_filled['days_without_track'] = pivoted_filled['date'].isnull().astype(int)
    del pivoted_filled['date']

    # Fill missing values in the user_id_day column
    pivoted_filled['user_id_day'] = pivoted_filled.apply(
        lambda row: row['user_id_day'] if not pd.isnull(row['user_id_day'])
        else row['user_id_fors'] + "_" +
             row['legs_date'].strftime('%Y%m%d'),
        axis=1
    )

    # Fill missing values in the modes columns
    # Get the columns that start with 'Mode::'
    modes_columns = [col for col in pivoted_filled.columns if col.startswith('Mode::')]

    # Fill missing values in the 'modes_columns' with 0
    pivoted_filled[modes_columns] = pivoted_filled[modes_columns].fillna(0)

    # Sort the resulting DataFrame
    pivoted_filled.sort_values(by=['user_id_fors', 'legs_date'], inplace=True)

    return pivoted_filled


#Compute daily modal distances
def calculate_dmd(legs_nogeom, usr_stats, KT, weight, period_of_tracking, bad_users, visitors, airplane, incl_signal_loss, outliers, mode_col):

    # SUBSET USERS
    
    # Filter on bad users
    bad_users_condition = (usr_stats['usr_w_constant_bad_signal'] == 0) if not bad_users else np.full(len(usr_stats), True)
    
    usr_stats_sub_list = usr_stats.loc[bad_users_condition, 'user_id_fors'].to_list()
    
    # Creating a dictionary mapping user IDs to their corresponding period of tracking values
    active_days_mapping = usr_stats.set_index('user_id_fors').loc[usr_stats_sub_list, period_of_tracking].to_dict()
    
    # Creating a dictionary mapping user IDs to their corresponding weight values
    # If weight is 'Aucun', map each user ID to the value 1
    if weight == 'Aucun':
        weight_mapping = usr_stats.set_index('user_id_fors').loc[usr_stats_sub_list].apply(lambda x: 1, axis=1).to_dict()
    else:
        weight_mapping = usr_stats.set_index('user_id_fors').loc[usr_stats_sub_list, weight].to_dict()
    
    # SUBSET LEGS
    legs_sub = legs_nogeom[legs_nogeom.user_id_fors.isin(usr_stats_sub_list)].copy()
    
    # Filter Airplane if needed
    airplane_condition = (legs_sub[mode_col] != 'Mode::Airplane') if not airplane else pd.Series(np.full(len(legs_sub), True))
    
    
    # Filter on residents and visitors
    resid_condition = (legs_sub['KT_home_survey'] == KT) if KT != 'Tous' else pd.Series(np.full(len(legs_sub), True))
    visit_condition = (legs_sub['activity_in_KT'] == KT) if visitors else pd.Series(np.full(len(legs_sub), True))
    if visitors:
        resident_visit_condition = resid_condition | visit_condition
    else:
        resident_visit_condition = resid_condition
    
    # Filter tracks with signal loss
    # Handle selection
    if incl_signal_loss == "0.05 de perte":
        signal_loss_threshold = 'low_quality_legs_1'
    elif incl_signal_loss == "0.07 de perte":
        signal_loss_threshold = 'low_quality_legs_2'
    
    signal_loss_condition = (legs_sub[signal_loss_threshold] == 0) if incl_signal_loss != "Non" else pd.Series(np.full(len(legs_sub), True))
    
    # Filter outliers if needed
    # Handle selection
    if outliers == "Quantile95":
        outlier_threshold = f"extreme95_length_{mode_col}"
    elif outliers == "Quantile98":
        outlier_threshold = f"extreme98_length_{mode_col}"
    elif outliers == "Quantile99":
        outlier_threshold = f"extreme99_length_{mode_col}"
    
    outliers_condition = (~legs_sub[outlier_threshold]) if outliers != "Aucune" else pd.Series(np.full(len(legs_sub), True))
    
    # Combine all conditions
    def check_boolean_series(condition, name):
        if not isinstance(condition, pd.Series) or condition.dtype != 'bool':
            raise ValueError(f"{name} is not a boolean series.")
    
    check_boolean_series(airplane_condition, 'airplane_condition')
    check_boolean_series(resident_visit_condition, 'resident_visit_condition')
    check_boolean_series(signal_loss_condition, 'signal_loss_condition')
    check_boolean_series(outliers_condition, 'outliers_condition')
    
    combined_dmd_condition = airplane_condition & resident_visit_condition & signal_loss_condition & outliers_condition
    
    dmd = get_daily_modal_distances(legs_sub[combined_dmd_condition], mode_col)
    
    # Filtering columns that start with 'Mode::' for further calculations
    mode_columns = dmd.filter(like='Mode::')
    
    # Calculating the sum for each 'Mode::' column for each user_id
    sum_mode_per_user = mode_columns.groupby(dmd['user_id_fors']).apply(lambda x: x.sum())
    
    # Weighting the sum of each 'Mode::' column based on user weights and active days
    sum_mode_per_user_w = sum_mode_per_user.mul(sum_mode_per_user.index.map(weight_mapping), axis=0).div(sum_mode_per_user.index.map(active_days_mapping), axis=0).dropna()

    return sum_mode_per_user_w.astype(int)


# Aggregate modes in dmd
def dmd_aggreg_modes(dmd, level):
    df = dmd.copy()

    if level == "Motiontag":
        return df
    else:
        if level == "MRMT":
            # First level of mode mapping
            mode_mapping = {
                'Voiture conducteur': ['Mode::Car', 'Mode::Carsharing','Mode::Ecar'],
                'Taxi': ['Mode::TaxiUber'],
                '2RM': ['Mode::KickScooter','Mode::Motorbike'],
                'Train': ['Mode::RegionalTrain','Mode::Train'],
                'Bus': ['Mode::Bus'],
                'Tram/Métro': ['Mode::LightRail','Mode::Subway','Mode::Tram'],
                'Bateau': ['Mode::Boat'],
                'Marche': ['Mode::Walk'],
                'Vélo conventionnel': ['Mode::Bicycle', 'Mode::Bikesharing'],
                'Vélo électrique': ['Mode::Ebicycle'],
                'Engins assimilés à des véhicules': ['Mode::Other'],
                'Avion': ['Mode::Airplane']
            }
    
        elif level == "Niveau 1":
            # Second level of mode mapping
            mode_mapping = {
                'Voiture': ['Mode::Car', 'Mode::Carsharing','Mode::Ecar','Mode::TaxiUber'],
                '2RM': ['Mode::KickScooter', 'Mode::Motorbike'],
                'Train': ['Mode::Train','Mode::RegionalTrain'],
                'Autre TP': ['Mode::Bus','Mode::LightRail','Mode::Subway','Mode::Tram','Mode::Boat'],
                'Marche': ['Mode::Walk'],
                'Vélo': ['Mode::Bicycle', 'Mode::Bikesharing','Mode::Ebicycle'],
                'Autre': ['Mode::Other'],
                'Avion': ['Mode::Airplane']
            }
    
        elif level == "Niveau 2":
            # Third level of mode mapping
            mode_mapping = {
                'TIM': ['Mode::Car', 'Mode::Carsharing','Mode::Ecar', 'Mode::KickScooter','Mode::Motorbike','Mode::TaxiUber'],
                'TP': ['Mode::Boat','Mode::Bus','Mode::LightRail','Mode::RegionalTrain', 'Mode::Subway','Mode::Train', 'Mode::Tram'],
                'MD': ['Mode::Bicycle', 'Mode::Bikesharing','Mode::Ebicycle', 'Mode::Walk'],
                'Avion': ['Mode::Airplane'],
                'Autre': ['Mode::Other']
            }
        
        else:
            raise ValueError("Invalid level. Please choose Motiontag, MRMT, Niveau 1 or Niveau 2 for the desired level.")
        
        # Create new columns based on the mapping
        for new_column, modes in mode_mapping.items():
            # Check if modes exist in columns before summing
            valid_modes = [mode for mode in modes if mode in df.columns]
            df[new_column] = df[valid_modes].sum(axis=1, min_count=1)
        
        # Create a new DataFrame with the new columns
        new_dmd = df[list(mode_mapping.keys())].copy()
        
        # Check if 'Avion' column is full of NaN, then drop it
        if 'Avion' in new_dmd.columns and new_dmd['Avion'].isnull().all():
            new_dmd.drop(columns=['Avion'], inplace=True)
    
        return new_dmd

# Fonction pour ploter l'histogramme et le pie chart
def plot_charts(modal_share):
    # Plot du pie chart avec des couleurs distinctes et une légende
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0','#ffb3e6','#ff6666']
    fig_pie, ax_pie = plt.subplots()
    ax_pie.pie(modal_share, labels=modal_share.index, colors=colors, autopct='%1.1f%%', startangle=90)
    ax_pie.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax_pie.set_title('Parts Modales')

    # Ajouter une légende
    ax_pie.legend(loc='upper right', labels=modal_share.index)
    
    return fig_pie