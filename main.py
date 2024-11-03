import concurrent.futures
from solana.keypair import Keypair
from base58 import b58encode
import multiprocessing
from datetime import datetime
import time


# ========================= CONFIG =========================

# В солана можно использовать буквы и цифры, но не каждая комбинация может быть найдена.
# Я сам не проверял, что может быть, а что нет, но вот что ответил ChatGPT:
# С некоторыми исключениями: не используются символы, которые могут быть легко спутаны,
# такие как 0 (ноль) и O (буква O), а также I (буква I) и l (маленькая буква L)

config = {
    "address_start": "12",  # Начало адреса (оставьте пустым, если не важно)
    "address_end": "",  # Конец адреса (оставьте пустым, если не важно)
    "num_processes": multiprocessing.cpu_count() - 2,  # Количество процессоров компа для параллельной работы
    "show_log": True,  # Логировать прогресс или нет
    "log_count": 5000    # Логировать каждые N генераций
}

# ========================= CONFIG =========================


def matches_address(address: str, start: str, end: str) -> bool:
    """Проверяет, соответствует ли адрес заданному началу и/или концу (игнорируя регистр)."""
    address1 = str(address)  # Приводим адрес к строке
    address = address1.lower()  # Приводим адрес к строке
    start = start.lower()  # Приводим начало к нижнему регистру
    end = end.lower()  # Приводим конец к нижнему регистру
    return (start == "" or address.startswith(start)) and (end == "" or address.endswith(end))


def generate_wallet() -> dict:
    """Генерирует кошелек и возвращает приватный ключ и адрес."""
    keypair = Keypair.generate()
    public_key = str(keypair.public_key)
    secret_key = keypair.secret_key
    secret_key_base58 = b58encode(secret_key).decode('utf-8')

    return {
        "public_key": public_key,
        "secret_key": secret_key_base58
    }


def log_progress(process_id, attempts):
    """Логирование прогресса генераций каждых 50 попыток."""
    if config["show_log"] and attempts % config["log_count"] == 0:
        print(f"Процесс {process_id}: {attempts} попыток генераций")


def save_wallet_to_file(wallet, address_start):
    """Сохраняет информацию о найденном кошельке в файл."""
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{address_start}.txt"
    with open(filename, "w", encoding='utf-8') as f:
        f.write(f"Адрес: {wallet['public_key']}\n")
        f.write(f"Секретный ключ (в Base58): {wallet['secret_key']}\n")
    print(f"Информация записана в файл: {filename}")


def wallet_search(process_id: int, stop_event) -> dict:
    """Функция для параллельного поиска нужного адреса."""
    attempts = 0

    while not stop_event.is_set():  # Проверяем флаг остановки
        wallet = generate_wallet()
        attempts += 1

        # Логирование прогресса
        log_progress(process_id, attempts)

        if matches_address(wallet["public_key"], config["address_start"], config["address_end"]):
            stop_event.set()  # Устанавливаем флаг остановки для других процессов
            save_wallet_to_file(wallet, config["address_start"])
            return wallet  # Возвращаем найденный кошелек


def main():
    print(f'Генерируем адресс: {config["address_start"]}...{config["address_end"]} на {config["num_processes"]} ядрах.')
    input(f'Нажмите Enter для старта')
    start_time = time.time()  # Засекаем время начала
    with multiprocessing.Manager() as manager:
        stop_event = manager.Event()  # Создаем общий флаг остановки

        with concurrent.futures.ProcessPoolExecutor(max_workers=config["num_processes"]) as executor:
            # Запуск параллельных задач с передачей номера процесса и флага остановки
            futures = [executor.submit(wallet_search, process_id=i + 1, stop_event=stop_event) for i in
                       range(config["num_processes"])]

            for future in concurrent.futures.as_completed(futures):
                # Как только один из процессов найдет нужный кошелек, завершаем программу
                wallet = future.result()
                if wallet:
                    print(f"Найден кошелек!")
                    print(f"Адрес: {wallet['public_key']}")
                    print(f"Секретный ключ: {wallet['secret_key']}")
                    elapsed_time = time.time() - start_time  # Вычисляем время окончания
                    print(f"Время выполнения: {elapsed_time:.2f} секунд")

                    break


art = '''

███╗   ██╗██╗ ██████╗███████╗    ███████╗ ██████╗ ██╗      █████╗ ███╗   ██╗ █████╗ 
████╗  ██║██║██╔════╝██╔════╝    ██╔════╝██╔═══██╗██║     ██╔══██╗████╗  ██║██╔══██╗
██╔██╗ ██║██║██║     █████╗      ███████╗██║   ██║██║     ███████║██╔██╗ ██║███████║
██║╚██╗██║██║██║     ██╔══╝      ╚════██║██║   ██║██║     ██╔══██║██║╚██╗██║██╔══██║
██║ ╚████║██║╚██████╗███████╗    ███████║╚██████╔╝███████╗██║  ██║██║ ╚████║██║  ██║
╚═╝  ╚═══╝╚═╝ ╚═════╝╚══════╝    ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
                                                                                    
Telegram: @vPoiskahGema
'''

if __name__ == "__main__":
    print(art)
    main()