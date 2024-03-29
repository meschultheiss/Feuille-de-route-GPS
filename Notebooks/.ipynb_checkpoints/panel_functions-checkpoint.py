from shapely import wkb
import binascii
import pandas as pd
import geopandas as gpd
from shapely.geometry import JOIN_STYLE, Polygon, MultiPolygon


def get_user_activity_stats(count_act):
    # Convert 'started_at' column to datetime
    count_act['started_at'] = pd.to_datetime(count_act['started_at'])

    # Extract only the date part
    count_act['date'] = count_act['started_at'].dt.date

    # Group by 'user_id', then find the min and max dates
    user_stats = count_act.groupby('user_id')['date'].agg(['min', 'max']).reset_index()

    # Calculate the total days in the range for each user
    user_stats['days_in_range'] = (pd.to_datetime(user_stats['max']) - pd.to_datetime(user_stats['min'])).dt.days + 1

    # Create a date range covering the entire date range for each user
    date_ranges = user_stats.apply(lambda row: pd.date_range(row['min'], row['max'], freq='D'), axis=1)
    user_stats['date_range'] = date_ranges

   # Group by 'user_id' and count the unique dates
    user_unique_dates = count_act.groupby(['user_id'])['date'].nunique().reset_index()

    # Merge with user_unique_dates to get active_days_count
    user_stats = pd.merge(user_stats, user_unique_dates, on='user_id', how='left')
    user_stats.rename(columns={'date': 'active_days_count'}, inplace=True)

    # Calculate the number of missing days within the range for each user
    user_stats['missing_days'] = user_stats['days_in_range'] - user_stats['date_range'].apply(len)

    # Drop unnecessary columns
    user_stats.drop(columns=['date_range'], inplace=True)

    # Rename the min/may columns
    user_stats.rename(columns={'min':'first_activity_date','max':'last_activity_da'}, inplace=True)

    return user_stats

# Fonction pour convertir une chaîne EWKB en objet shapely
def parse_ewkb(hex_str):
    # Convertit la chaîne hexadécimale en binaire
    binary_data = binascii.unhexlify(hex_str)
    # Utilise wkb.loads pour obtenir l'objet shapely à partir des données binaires
    geometry = wkb.loads(binary_data)
    return geometry

# Fonction pour boucher les trous dans un shape (e.g. les lacs)
def close_holes(poly: Polygon) -> Polygon:
        """
        Close polygon holes by limitation to the exterior ring.
        Args:
            poly: Input shapely Polygon
        Example:
            df.geometry.apply(lambda p: close_holes(p))
        """
        if poly.interiors:
            return Polygon(list(poly.exterior.coords))
        else:
            return poly