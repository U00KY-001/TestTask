import argparse
import csv
from tabulate import tabulate


# Преобразовние строкового элемента списка в числовой
def try_convert(val):
    try:
        # Пытаемся преобразовать в float, затем int, если это целое
        f = float(val)
        return int(f) if f.is_integer() else f
    except ValueError:
        # Если не число, возвращаем исходное значение
        return val


# Парсинг введенной команды
def pars():
    parser = argparse.ArgumentParser(description='description')
    # Получаем список файлов
    parser.add_argument(
        '--files',
        nargs='+',
        dest='file_names',
        help='Обрабатываемые файлы',
        # Обязательное поле
        required=True
    )
    # Получаем вид отчета
    parser.add_argument(
        '--report',
        dest='reports',
        help='Обрабатываемые файлы',
        # Обязательное поле
        required=True
    )
    args = parser.parse_args()
    return args


# Чтение файла
def read_file(file_name, data):
    with open(f'./Files/{file_name}', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        # Заголовок с которым можно работать
        headers = next(reader)
        for row in reader:
            # Записываем строки в список
            new_row = [try_convert(val) for val in row]
            data.append(new_row)


# Класс содержащий --report (можно добавить метод)
class Reports:
    def clickbait(self, data):
        data = sorted(data, key=lambda ctr: ctr[1], reverse=True)
        report_data=[]
        # Заголовок который нужен в отчете
        report_data.append(['title', 'ctr', 'retention_rate'])
        # Формирование массива отчета
        for i in range(len(data)):
            if data[i][1] > 15 and data[i][2] < 40:
                report_data.append([data[i][0], data[i][1], data[i][2]])
        return report_data

    # Выбираем каким методом необходимо сформировать отчет
    def choice_method(self, operator, data):
        methods = {
            "clickbait": self.clickbait
        }

        method = methods.get(operator)
        if method:
            return method(data)
        return 'Метода не существует'


# Основное тело программы
if __name__ == '__main__':
    db = []
    args = pars()
    print(args.file_names, args.reports)

    for i in range(len(args.file_names)):
        read_file(args.file_names[i], db)

    report = Reports()
    ans = report.choice_method(args.reports, db)
    print(tabulate(ans, headers='firstrow', tablefmt='grid'))