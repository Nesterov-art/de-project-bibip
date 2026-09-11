from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale
from pathlib import Path
from bisect import bisect_left
from datetime import datetime
from decimal import Decimal

LINE_LEN = 500
ROW_SIZE = LINE_LEN + 1   
SEP = ';'                 


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = Path(root_directory_path)
        self.cars_path = self.root_directory_path / 'cars.txt'
        self.cars_index_path = self.root_directory_path / 'cars_index.txt'
        self.models_path = self.root_directory_path / 'models.txt'
        self.models_index_path = self.root_directory_path / 'models_index.txt'
        self.sales_path = self.root_directory_path / 'sales.txt'
        self.sales_index_path = self.root_directory_path / 'sales_index.txt'
        
        for p in (self.cars_path, self.cars_index_path,
            self.models_path, self.models_index_path,
            self.sales_path, self.sales_index_path):
            p.touch()

    def _read_index(self, path: Path) -> list[list[str]]:
        with open(path, 'r', newline='') as f:
            return [line.strip().split(SEP) for line in f if line.strip()]

    def _write_index(self, path: Path, index: list[list[str]]) -> None:
        with open(path, 'w', newline='') as f:
            for key, row_no in index:
                f.write(f'{key}{SEP}{row_no}'.ljust(LINE_LEN) + '\n')

    def _append_row(self, path: Path, fields: list[str]) -> int:
        line = SEP.join(fields)
        if len(line) > LINE_LEN:
            raise ValueError(f'Строка длиннее {LINE_LEN} — смещения поедут')
        row_no = path.stat().st_size // ROW_SIZE   # размер файла, не readlines()
        with open(path, 'a', newline='') as f:
            f.write(line.ljust(LINE_LEN) + '\n')
        return row_no

    def _find_row(self, index_path: Path, key: str) -> int | None:
        """Номер строки по ключу. Индекс отсортирован - бинарный поиск."""
        index = self._read_index(index_path)
        keys = [pair[0] for pair in index]
        i = bisect_left(keys, key)
        if i < len(keys) and keys[i] == key:
            return int(index[i][1])
        return None

    def _read_row(self, path: Path, row_no: int) -> list[str]:
        """Прыжок к нужной строке без чтения всего файла."""
        with open(path, 'r', newline='') as f:
            f.seek(row_no * ROW_SIZE)
            return f.read(LINE_LEN).strip().split(SEP)

    def _write_row(self, path: Path, row_no: int, fields: list[str]) -> None:
        """Перезапись строки на месте. r+ — читаем и пишем тот же файл."""
        line = SEP.join(fields)
        if len(line) > LINE_LEN:
            raise ValueError(f'Строка длиннее {LINE_LEN} — смещения поедут')
        with open(path, 'r+', newline='') as f:
            f.seek(row_no * ROW_SIZE)
            f.write(line.ljust(LINE_LEN) + '\n')

    def _parse_car(self, fields: list[str]) -> Car:
        """Строка файла -> объект Car. Понадобится в заданиях 3-6."""
        return Car(
            vin=fields[0],
            model=int(fields[1]),
            price=Decimal(fields[2]),
            date_start=datetime.fromisoformat(fields[3]),
            status=CarStatus(fields[4]),
        )

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        fields = [str(model.id), model.name, model.brand]

        row_no = self._append_row(self.models_path, fields)

        index = self._read_index(self.models_index_path)
        index.append([str(model.id), str(row_no)])
        index.sort(key=lambda pair: int(pair[0]))   
        self._write_index(self.models_index_path, index)

        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        fields = [
            car.vin,
            str(car.model),
            str(car.price),
            car.date_start.isoformat(),
            car.status.value,
        ]

        row_no = self._append_row(self.cars_path, fields)

        index = self._read_index(self.cars_index_path)
        index.append([car.vin, str(row_no)])
        index.sort()
        self._write_index(self.cars_index_path, index)

        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        fields = [
            sale.sales_number,
            sale.car_vin,
            sale.sales_date.isoformat(),
            str(sale.cost),
        ]
        
        row_no = self._append_row(self.sales_path, fields)

        index = self._read_index(self.sales_index_path)
        index.append([sale.car_vin, str(row_no)])
        index.sort()
        self._write_index(self.sales_index_path, index)
        
        car_row = self._find_row(self.cars_index_path, sale.car_vin)
        car_fields = self._read_row(self.cars_path, car_row)
        car_fields[4] = CarStatus.sold.value
        self._write_row(self.cars_path, car_row, car_fields)

        return self._parse_car(car_fields)

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        raise NotImplementedError

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        raise NotImplementedError

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        raise NotImplementedError

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        raise NotImplementedError

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        raise NotImplementedError