from pathlib import Path
from PyPDF2 import PdfFileReader
import pandas as pd
import tabula
import re
import argparse
from tqdm import tqdm


def extract_high_salary_df(pdf_path):
    try:
        dfs = dfs_from_last_100_pages(pdf_path)
    except:
        print(f'Problem reading pdf file {pdf_path}')
        return None, None
    selected_df = select_high_salary_df(dfs)
    if selected_df is None:
        print(f'Could not find a table for {pdf_path}')
        return None, None
    money_df = extract_money_column(selected_df)
    if money_df is None or money_df.empty:
        return selected_df, None
    # names_df = extract_names_column(selected_df)

    return selected_df, money_df.nlargest(n=5)


def dfs_from_last_100_pages(pdf_path):
    reader = PdfFileReader(pdf_path)
    end = reader.getNumPages()
    if end < 100:
        start = 1
    else:
        start = end - 100
    dfs = tabula.read_pdf(pdf_path, stream=False, pages=f'{start}-{end}')
    return dfs


def select_high_salary_df(dfs):
    selected_df = None
    for df in dfs:
        if (not df.filter(regex='תגמולים').columns.empty) or ('פרטי מקבל התגמולים' in df.columns) or ('פרטי המקבלים' in df.columns):
            selected_df = df
            break
    if selected_df is None:
        for df in dfs:
            if df.select_dtypes(include='object').apply(lambda col: col.str.contains('תגמולים', na=False), axis=1).any(axis=None):
                selected_df = df
                break
    return selected_df


def extract_money_column(selected_df):
    sum_pattern = re.compile(r'סה.כ')
    sum_matches = list(filter(sum_pattern.match, selected_df.columns))
    if len(sum_matches) > 0:
        money_column_name = sum_matches[0]
    else:
        money_column_name = 'Unnamed: 0'
    if money_column_name not in selected_df.columns:
        print(f'Problem extracting money column with column name {money_column_name}')
        return None
    money_df = selected_df[money_column_name].str.extract(r'((\d{1,2},)?\d{3})')[0]. \
        dropna().apply(lambda x: int(x.replace(',', '')))
    return money_df


def extract_names_column(selected_df):
    names_column_name = 'פרטי מקבל התגמולים'
    return selected_df[names_column_name].str.extract(
        r'(?P<firstname>[\u05D0-\u05EA]+)[^\u05D0-\u05EA]+(?P<lastname>[\u05D0-\u05EA]+)'
    ).dropna()


def extract_high_salaries_from_directory(directory):
    dir_path = Path(directory)
    tables_dir_path = dir_path / 'tables'
    tables_dir_path.mkdir(exist_ok=True)
    stats = pd.DataFrame(columns=['company'] + [f'{a}_{b}' for a in [13, 14, 15, 16, 17, 18, 19] for b in ['max', 'min', 'mean']])
    for pdf_file in tqdm(dir_path.glob('*.pdf')):
        print(f'Starting {pdf_file}')
        whole_df, money_df = extract_high_salary_df(str(pdf_file))
        if whole_df is None or whole_df.empty:
            print(f'Missing whole_df for {pdf_file}')
            continue
        year, company_name = pdf_file.stem.split('_')
        whole_df.to_csv(tables_dir_path / f'{pdf_file.stem}.csv', index=False)
        if money_df is None or money_df.empty:
            print(f'Missing money_df for {pdf_file}')
            continue
        current_stats = money_df.describe()
        if stats[stats.company == company_name].empty:
            stats = stats.append({'company': company_name}, ignore_index=True)
        current_row = stats[stats.company == company_name]
        current_row[f'{year}_mean'] = current_stats['mean']
        current_row[f'{year}_min'] = current_stats['min']
        current_row[f'{year}_max'] = current_stats['max']
        stats[stats.company == company_name] = current_row
    output_path = dir_path / 'output'
    output_path.mkdir()
    stats.to_csv(output_path / 'all_stats.csv', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract high salary data from company PDF files.')
    parser.add_argument('directory', type=str, help='the directory containing the pdfs')
    args = parser.parse_args()
    extract_high_salaries_from_directory(args.directory)
