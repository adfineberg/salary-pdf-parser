from pathlib import Path
from PyPDF2 import PdfFileReader
import pandas as pd
import tabula
import re
import argparse


def extract_high_salary_df(pdf_path):
    dfs = dfs_from_last_100_pages(pdf_path)
    selected_df = select_high_salary_df(dfs)
    money_df = extract_money_column(selected_df)
    # names_df = extract_names_column(selected_df)

    return selected_df, money_df.head(5)


def dfs_from_last_100_pages(pdf_path):
    reader = PdfFileReader(pdf_path)
    end = reader.getNumPages()
    if end < 100:
        start = 0
    else:
        start = end - 100
    dfs = tabula.read_pdf(pdf_path, stream=False, pages=f'{start}-{end}')
    return dfs


def select_high_salary_df(dfs):
    selected_df = None
    for df in dfs:
        if ('פרטי מקבל התגמולים' in df.columns) or ('פרטי המקבלים' in df.columns):
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
    tables_dir_path.mkdir()
    stats = pd.DataFrame(columns=['company'] + [f'{a}_{b}' for a in [13, 14, 18, 19] for b in ['max', 'min', 'mean']])
    for pdf_file in dir_path.glob('*.pdf'):
        whole_df, money_df = extract_high_salary_df(str(pdf_file))
        year, company_name = pdf_file.stem.split('-')
        whole_df.to_csv(tables_dir_path / f'{pdf_file.stem}.csv', index=False)
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
