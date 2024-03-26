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