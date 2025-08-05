import json
import os
import glob
import argparse

def compact_json_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

        try:
            data = json.loads(content)

            with open(output_file, 'w', encoding='utf-8') as out:
                if isinstance(data, list):
                    out.write('[\n')
                    for i, item in enumerate(data):
                        if i > 0:
                            out.write(',\n')
                        json.dump(item, out, ensure_ascii=False, separators=(',', ':'))
                    out.write('\n]')
                else:
                    json.dump(data, out, ensure_ascii=False, separators=(',', ':'))

        except json.JSONDecodeError:
            # Обработка случая, когда файл содержит несколько JSON объектов подряд
            with open(output_file, 'w', encoding='utf-8') as out:
                start = 0
                brace_count = 0
                in_string = False
                escape = False
                first_obj = True

                for i, char in enumerate(content):
                    if char == '"' and not escape:
                        in_string = not in_string
                    if char == '\\':
                        escape = not escape
                    else:
                        escape = False

                    if not in_string:
                        if char == '{':
                            if brace_count == 0:
                                start = i
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                try:
                                    obj_str = content[start:i+1]
                                    obj = json.loads(obj_str)
                                    if not first_obj:
                                        out.write('\n')
                                    json.dump(obj, out, ensure_ascii=False, separators=(',', ':'))
                                    first_obj = False
                                except json.JSONDecodeError:
                                    pass

def process_directory(directory):
    for json_file in glob.glob(os.path.join(directory, '*.json')):
        print(f"Обрабатываю файл: {json_file}")
        temp_file = json_file + '.temp'
        compact_json_file(json_file, temp_file)
        os.replace(temp_file, json_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Компактификация JSON файлов')
    parser.add_argument('--default', action='store_true', help='Использовать директорию из конфигурационной переменной')
    args = parser.parse_args()

    if args.default:
        # Получаем директорию из конфигурационной переменной (можно заменить на вашу конкретную переменную)
        directory = os.getenv('JSON_COMPACT_DIR', '')
        if not directory:
            print("Конфигурационная переменная JSON_COMPACT_DIR не установлена")
            exit(1)
    else:
        directory = input("Введите путь к папке с JSON файлами: ")

    if os.path.isdir(directory):
        process_directory(directory)
        print("Все файлы успешно обработаны!")
    else:
        print("Указанная папка не существует.")