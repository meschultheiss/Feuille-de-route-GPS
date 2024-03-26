import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import time
import sys
from pathlib import Path
import geopandas as gpd

# Charger vos datasets
@st.cache_data
# def load_data():
#     # Get the current file's directory
#     current_dir = Path(__file__).resolve().parent
    
#     # Append parent directory to the system path
#     parent_dir = current_dir.parent
#     sys.path.append(parent_dir)
    
#     # Define paths relative to the current file
#     data_dir = current_dir / "data"
#     legs_path = data_dir / "legs_nogeometry.pkl"
#     usr_stats_path = data_dir / "gps_user_statistics.pkl"
    
#     # Load data using pandas
#     legs_nogeometry = pd.read_pickle(legs_path)
#     usr_stats = pd.read_pickle(usr_stats_path)
    
#     return legs_nogeometry, usr_stats
def load_data():
    dir = path.Path(__file__).abspath()
    sys.path.append(dir.parent.parent)
    # Charger vos datasets ici
    legs_nogeometry = pd.read_pickle('Streamlit/data/legs_nogeometry.pkl')
    usr_stats = pd.read_pickle('Streamlit/data/gps_user_statistics.pkl')
    return legs_nogeometry, usr_stats

# Fonction pour calculer les distances par user et mode

#Compute daily modal distances
def get_daily_modal_distances(df):
    
    # Create a copy of the DataFrame to avoid modifying the original
    df = df.copy()
    
    df['length'] = df['length'].astype(float)
    # Group by 'user_id_day', 'previous_mode', and 'previous_leg_id', then sum the distances
    grouped = df.groupby(['user_id_fors', 'user_id_day', 'mode'])['length'].sum().reset_index()

    # Pivot the table to have modes as columns
    pivoted = grouped.pivot_table(
        index=['user_id_fors', 'user_id_day'],
        columns='mode',
        values='length',
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
def calculate_dmd(legs_nogeom, usr_stats, KT, weight, period_of_tracking, visitors, airplane, incl_signal_loss):

    legs_nogeometry = legs_nogeom.copy()
    # Filter Airplane if needed
    if not airplane:
        legs_nogeometry = legs_nogeometry[legs_nogeometry['mode'] != 'Mode::Airplane'].copy()

    # Filter tracks with signal loss
    if not incl_signal_loss:
        legs_nogeometry = legs_nogeometry[legs_nogeometry['low_quality_legs_1'] == 0].copy()
        
        
    # Creating a dictionary mapping user IDs to their corresponding weight values
    # If weight is 'Aucun', map each user ID to the value 1
    if weight == 'Aucun':
        weight_mapping = usr_stats.set_index('user_id_fors').apply(lambda x: 1, axis=1).to_dict()
    else:
        weight_mapping = usr_stats.set_index('user_id_fors')[weight].to_dict()
    
    # Creating a dictionary mapping user IDs to their corresponding period of tracking values
    active_days_mapping = usr_stats.set_index('user_id_fors')[period_of_tracking].to_dict()
    
    # Setting the condition based on the value of KT
    # If KT is not 'Tous', filter data based on the condition KT_home_survey == KT
    # If KT is 'Tous', include all data (no filtering based on KT)
    if KT != 'Tous':
        KT_condition = (legs_nogeometry.KT_home_survey == KT)
    else:
        KT_condition = True

    if visitors == True:
        visit_condition = (legs_nogeometry.activity_in_KT == KT)
        dmd = get_daily_modal_distances(legs_nogeometry.loc[KT_condition | visit_condition])
    else:
        dmd = get_daily_modal_distances(legs_nogeometry.loc[KT_condition])
    
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
                'Voiture conducteur': ['Mode::Car', 'Mode::Carsharing','Mode::Ecar','Mode::TaxiUber'],
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