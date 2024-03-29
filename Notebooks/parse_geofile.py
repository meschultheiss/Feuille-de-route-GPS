import geopandas as gpd
import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser(description="Geopandas Operations")
    parser.add_argument("input_pickle", help="Input pickle file path")
    parser.add_argument("--read-crs", action="store_true", help="Read and display CRS information")
    parser.add_argument("--change-crs", help="Change CRS and save as GeoJSON")
    parser.add_argument("--copy-geojson", help="Create a copy in GeoJSON format")
    parser.add_argument("--copy-shapefile", help="Create a copy in Shapefile format")

    args = parser.parse_args()

    try:
        # Load the DataFrame from the input pickle file using pandas
        df = pd.read_pickle(args.input_pickle)

        if isinstance(df, gpd.geodataframe.GeoDataFrame):
            if args.read_crs:
                if df.crs:
                    print("Current CRS:", df.crs)
                else:
                    print("Your GeoDataFrame has no CRS set.")
                    set_crs = input("Would you like to set the CRS to EPSG:4326 (WGS 84) and overwrite your pickle? (y/n): ").strip().lower()
                    if set_crs == 'y':
                        df = df.to_crs('EPSG:4326')
                        df.to_pickle(args.input_pickle)

            if args.change_crs:
                df = df.to_crs(args.change_crs)
                df.to_file(args.change_crs + ".geojson", driver="GeoJSON")

            if args.copy_geojson:
                df.to_file(args.copy_geojson, driver="GeoJSON")

            if args.copy_shapefile:
                df.to_file(args.copy_shapefile, driver="ESRI Shapefile")

        elif isinstance(df, pd.DataFrame):
            if 'geometry' in df.columns:
                set_geometry = input("Would you like to set 'geometry' column as the geometry? (y/n): ").strip().lower()
                if set_geometry == 'y':
                    df = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
                    print("You just parsed your DataFrame to a GeoDataFrame with CRS:", df.crs)
                    set_crs = input("Would you like to overwrite your pickle with this new gdf ? (y/n): ").strip().lower()
                    if set_crs == 'y':
                        df.to_pickle(args.input_pickle)
                else:
                    print("No CRS information, and 'geometry' column not set as geometry.")
            else:
                print("Input is a DataFrame but lacks a 'geometry' column.")

        else:
            print("Input is not a DataFrame or GeoDataFrame.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
