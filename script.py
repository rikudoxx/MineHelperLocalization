import zipfile
import json
import os
import shutil
import tempfile
import sys


def show_menu():
    """Показывает главное меню программы"""
    print("\n" + "=" * 50)
    print("Велком ту Русификатор!")
    print("=" * 50)
    print("1) Отсортировать JSON-локализацию из JAR-файла")
    print("2) Отсортировать существующий JSON-файл локализации")
    print("0) Выйти из программы")
    print("=" * 50)


def sort_json_from_jar():
    """Сортировка локализации из JAR-файла"""
    # 1. Получаем путь к JAR-файлу
    jar_path = input("Введите путь к файлу мода: ").strip()
    jar_path = os.path.normpath(jar_path)

    if not os.path.exists(jar_path):
        print(f"❌ Ошибка: файл не найден по пути: {jar_path}")
        return

    print(f"✅ Работаем с файлом: {jar_path}")

    # 2. Определяем имя мода и инстанса
    mod_name = os.path.basename(jar_path).replace('.jar', '')
    # Ищем папку "instances" в пути, чтобы получить имя инстанса
    path_parts = jar_path.split(os.sep)
    try:
        instances_index = path_parts.index('.xmcl') + 2  # .xmcl\instances\Имя_инстанса
        instance_name = path_parts[instances_index]
    except (ValueError, IndexError):
        # Если не найдено, используем имя папки, где лежит мод
        instance_name = os.path.basename(os.path.dirname(jar_path))

    print(f"🔍 Инстанс: {instance_name}, Мод: {mod_name}")

    # 3. Распаковываем JAR-файл во временную папку
    temp_dir = tempfile.mkdtemp()
    print(f"📂 Распаковываем в временную папку: {temp_dir}")

    with zipfile.ZipFile(jar_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # 4. ЗАГРУЖАЕМ МАППИНГ ИЗ ВАШЕГО ФАЙЛА (ручной маппинг!)
    mapping_file = 'language_mapping.json'
    if not os.path.exists(mapping_file):
        print(f"❌ Ошибка: файл маппинга {mapping_file} не найден в текущей директории!")
        return

    with open(mapping_file, 'r', encoding='utf-8') as f:
        language_mapping = json.load(f)

    print("\n✅ Маппинг загружен из файла:")
    print(json.dumps(language_mapping, indent=2, ensure_ascii=False))

    # 5. Запрашиваем язык у пользователя
    lang_code = input("\nВведите код языка (например, ru): ").strip()
    if lang_code not in language_mapping:
        print(f"❌ Язык {lang_code} не найден в маппинге!")
        print("Доступные языки:", ", ".join(language_mapping.keys()))
        return

    filename = language_mapping[lang_code]
    print(f"\n➡️ Работаем с файлом: {filename}")

    # 6. Находим все файлы с этим именем в распакованной папке
    found_files = []
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file == filename:
                file_path = os.path.join(root, file)
                found_files.append(file_path)
                print(f"  - Найден: {file_path}")

    if not found_files:
        print(f"❌ Файл {filename} не найден в архиве!")
        return

    # 7. Сортируем каждый найденный файл
    for file_path in found_files:
        print(f"  - Обрабатываю: {file_path}")

        # Читаем JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Сортируем ключи по алфавиту
        sorted_data = dict(sorted(data.items()))

        # Записываем обратно
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, ensure_ascii=False, indent=2)

    # 8. Определяем папку для сохранения (unarchived_mods)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    unarchived_dir = os.path.join(script_dir, 'unarchived_mods')
    os.makedirs(unarchived_dir, exist_ok=True)

    # Создаём структуру: unarchived_mods/Инстанс/mods/Имя_мода/assets/
    target_dir = os.path.join(unarchived_dir, instance_name, 'mods', mod_name, 'assets')
    os.makedirs(target_dir, exist_ok=True)

    # 9. Копируем только папку assets из временной папки в целевую
    assets_source = os.path.join(temp_dir, 'assets')
    if os.path.exists(assets_source):
        print(f"\n💾 Сохраняю в: {target_dir}")
        shutil.copytree(assets_source, target_dir, dirs_exist_ok=True)
        print(f"✅ Готово! Файлы сохранены в {target_dir}")

        # 9.1. ОЧИСТКА: удаляем всё в assets, кроме папки lang и её содержимого
        print("🧹 Очищаю папку assets от лишних файлов...")
        for mod_dir in os.listdir(target_dir):
            mod_path = os.path.join(target_dir, mod_dir)
            if os.path.isdir(mod_path):
                # Пройти по всем элементам в мод-папке
                for item in os.listdir(mod_path):
                    item_path = os.path.join(mod_path, item)
                    # Если это не папка "lang", удаляем
                    if item != 'lang':
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
        print("✅ Лишние файлы удалены. Осталась только структура lang/...")
    else:
        print("❌ Папка assets не найдена в архиве!")

    # 10. Удаляем временную папку
    shutil.rmtree(temp_dir)
    print(f"🧹 Временная папка удалена")


def sort_json_directly():
    """Сортировка существующего JSON-файла локализации"""
    # 1. Получаем путь к файлу JSON
    json_path = input("Введите путь к файлу локализации (например, ru_ru.json): ").strip()
    json_path = os.path.normpath(json_path)

    if not os.path.exists(json_path):
        print(f"❌ Ошибка: файл не найден по пути: {json_path}")
        return

    if not json_path.lower().endswith('.json'):
        print("❌ Ошибка: файл должен иметь расширение .json")
        return

    print(f"✅ Работаем с файлом: {json_path}")

    # 2. Сортируем файл
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Сортируем ключи по алфавиту
        sorted_data = dict(sorted(data.items()))

        # Записываем обратно
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, ensure_ascii=False, indent=2)

        print("✅ Файл успешно отсортирован и сохранен!")
    except Exception as e:
        print(f"❌ Ошибка при обработке файла: {str(e)}")


def main():
    """Главное меню программы"""
    while True:
        show_menu()
        choice = input("Выберите пункт: ").strip()

        if choice == '1':
            sort_json_from_jar()
        elif choice == '2':
            sort_json_directly()
        elif choice == '0':
            print("\nДо свидания! Спасибо за использование Русификатора!")
            break
        else:
            print("❌ Неверный выбор. Пожалуйста, введите 1, 2 или 0.")

        # Добавляем пустую строку для разделения выводов
        print("\n" + "=" * 50)


if __name__ == "__main__":
    main()