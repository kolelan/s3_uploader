import os
import sys
import platform
import argparse
import ctypes
from typing import List


def is_admin_windows():
    """Проверяет права администратора в Windows"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def is_symlink(path: str) -> bool:
    """Проверьте, является ли path символической ссылкой (включая WSL-ссылки в Windows)."""
    if platform.system() == "Windows":
        try:
            # Стандартная проверка символических ссылок
            if os.path.islink(path):
                return True
            # Дополнительная проверка для WSL
            if os.path.isfile(path):
                with open(path, 'rb') as f:
                    header = f.read(10)
                    return header.startswith((b'lxsf', b'wsl$'))
            # Проверка точки соединения
            return bool(ctypes.windll.kernel32.GetFileAttributesW(os.path.abspath(path)) & 0x400)
        except:
            return False
    return os.path.islink(path)

def create_symlink(source: str, link_name: str, silent: bool = False) -> bool:
    """Create a symbolic link from source to link_name.

    Args:
        source: Path to the target file/directory.
        link_name: Path to the symbolic link to be created.
        silent: If True, suppresses all output messages.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(source):
        if not silent:
            print(f"Ошибка: Источник '{source}' не существует")
        return False
    try:
        if platform.system() == "Windows" and not is_admin_windows():
            print("Ошибка: Требуются права администратора в Windows")
            return False

        if os.path.exists(link_name):
            print(f"Ошибка: '{link_name}' уже существует")
            return False

        if platform.system() == "Windows":
            target_is_dir = os.path.isdir(source)
            os.symlink(source, link_name, target_is_directory=target_is_dir)
        else:
            os.symlink(source, link_name)

        print(f"Создано: {link_name} → {source}")
        return True
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        return False


def find_symlinks(directory: str = ".", recursive: bool = True) -> List[str]:
    """Finds all symbolic links in the directory (files and directories).

    Args:
        directory: Path to search in (default: current directory).
        recursive: If True, searches recursively.

    Returns:
        List of paths to symbolic links.
    """
    symlinks = []
    for root, dirs, files in os.walk(directory):  # Fixed: added dirs
        for name in files + dirs:
            path = os.path.join(root, name)
            if is_symlink(path):
                symlinks.append(path)
        if not recursive:
            break
    return symlinks


def delete_symlink(link_path: str, silent: bool = False) -> bool:
    """Удаляет символическую ссылку с улучшенной обработкой ошибок"""
    try:
        if not is_symlink(link_path):
            if not silent:
                print(f"⚠️ '{link_path}' не является символической ссылкой!")
            return False

        # Особенности удаления в Windows
        if platform.system() == "Windows":
            if os.path.isdir(link_path):
                os.rmdir(link_path)  # Для junction и симлинков на папки
            else:
                os.unlink(link_path)  # Для симлинков на файлы
        else:
            os.unlink(link_path)

        if not silent:
            print(f"🗑️ Удалено: {link_path}")
        return True

    except Exception as e:
        if not silent:
            print(f"❌ Ошибка при удалении {link_path}: {str(e)}")
        return False

def recursive_delete(path: str, silent: bool = False) -> bool:
    """Рекурсивное удаление всех ссылок в папке"""
    success = True
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files + dirs:
            item_path = os.path.join(root, name)
            if is_symlink(item_path):
                if not delete_symlink(item_path, silent):
                    success = False
    return success

def main():
    parser = argparse.ArgumentParser(description="Менеджер символических ссылок")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Парсер для создания ссылки
    parser_create = subparsers.add_parser('create', help='Создать символическую ссылку')
    parser_create.add_argument('--silent', action='store_true', help='Suppress output messages')
    parser_create.add_argument('source', help='Исходный файл/папка')
    parser_create.add_argument('link_name', help='Имя ссылки')

    # Парсер для поиска ссылок
    parser_list = subparsers.add_parser('list', help='Найти все символические ссылки')
    parser_list.add_argument('--directory', default='.', help='Директория для поиска')
    parser_list.add_argument('--no-recursive', action='store_true', help='Не искать рекурсивно')

    # Парсер для удаления ссылок
    parser_delete = subparsers.add_parser('delete', help='Удалить символическую ссылку')
    parser_delete.add_argument('path', help='Путь к ссылке')
    parser_delete.add_argument('--recursive', action='store_true', help='Рекурсивное удаление')
    parser_delete.add_argument('--silent', action='store_true', help='Suppress output messages')

    args = parser.parse_args()

    if args.command == 'create':
        if not create_symlink(args.source, args.link_name):
            sys.exit(1)
    elif args.command == 'list':
        symlinks = find_symlinks(args.directory, not args.no_recursive)
        if symlinks:
            print("Найдены символические ссылки:")
            for link in symlinks:
                try:
                    target = os.readlink(link)
                except:
                    target = "???"
                print(f"{link} → {target}")
        else:
            print("Ссылок не найдено")
    elif args.command == 'delete':
        if args.recursive and os.path.isdir(args.path):
            if not recursive_delete(args.path, args.silent):
                sys.exit(1)
        else:
            if not delete_symlink(args.path, args.silent):
                sys.exit(1)


if __name__ == "__main__":
    if platform.system() == "Windows" and not is_admin_windows():
        print("Внимание: Для работы с символическими ссылками в Windows требуются права администратора!")
    main()