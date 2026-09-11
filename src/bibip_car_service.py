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

    def _scan(self, path: Path):
        """Полный проход по файлу, по одной строке за раз (Seq Scan)."""
        with open(path, 'r', newline='') as f:
            while chunk := f.read(ROW_SIZE):
                stripped = chunk.strip()
                if stripped:
                    yield stripped.split(SEP)
    
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
            '0',
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
        result = []
        for fields in self._scan(self.cars_path):
            if fields[4] == status.value:
                result.append(self._parse_car(fields))
        return result

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        car_row = self._find_row(self.cars_index_path, vin)
        if car_row is None:
            return None
        car_fields = self._read_row(self.cars_path, car_row)

        model_row = self._find_row(self.models_index_path, car_fields[1])
        model_fields = self._read_row(self.models_path, model_row)

        sales_date = None
        sales_cost = None
        if car_fields[4] == CarStatus.sold.value:
            sale_row = self._find_row(self.sales_index_path, vin)
            if sale_row is not None:
                sale_fields = self._read_row(self.sales_path, sale_row)
                if sale_fields[4] == '0':          # продажа не отменена
                    sales_date = datetime.fromisoformat(sale_fields[2])
                    sales_cost = Decimal(sale_fields[3])

        return CarFullInfo(
            vin=car_fields[0],
            car_model_name=model_fields[1],
            car_model_brand=model_fields[2],
            price=Decimal(car_fields[2]),
            date_start=datetime.fromisoformat(car_fields[3]),
            status=CarStatus(car_fields[4]),
            sales_date=sales_date,
            sales_cost=sales_cost,
        )

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        row_no = self._find_row(self.cars_index_path, vin)
        if row_no is None:
            raise ValueError(f'Автомобиль с VIN {vin} не найден')

        car_fields = self._read_row(self.cars_path, row_no)
        car_fields[0] = new_vin
        self._write_row(self.cars_path, row_no, car_fields)

        index = self._read_index(self.cars_index_path)
        index = [pair for pair in index if pair[0] != vin]
        index.append([new_vin, str(row_no)])
        index.sort()
        self._write_index(self.cars_index_path, index)

        return self._parse_car(car_fields)

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        vin = sales_number.split('#')[1]

        sale_row = self._find_row(self.sales_index_path, vin)
        if sale_row is None:
            raise ValueError(f'Продажа с номером {sales_number} не найдена')

        sale_fields = self._read_row(self.sales_path, sale_row)
        sale_fields[4] = '1'
        self._write_row(self.sales_path, sale_row, sale_fields)

        car_row = self._find_row(self.cars_index_path, vin)
        car_fields = self._read_row(self.cars_path, car_row)
        car_fields[4] = CarStatus.available.value
        self._write_row(self.cars_path, car_row, car_fields)

        return self._parse_car(car_fields)

    # Задание 7. Самые продаваемые модели
        # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        # Считаем продажи по моделям. В sales нет model_id — идём за ним в cars по VIN.
        counts: dict[str, int] = {}
        max_cost: dict[str, Decimal] = {}

        for sale_fields in self._scan(self.sales_path):
            if sale_fields[4] == '1':          # отменённые не считаем
                continue
            vin = sale_fields[1]
            car_row = self._find_row(self.cars_index_path, vin)
            if car_row is None:
                continue
            model_id = self._read_row(self.cars_path, car_row)[1]
            cost = Decimal(sale_fields[3])

            counts[model_id] = counts.get(model_id, 0) + 1
            max_cost[model_id] = max(max_cost.get(model_id, cost), cost)

        # Сортировка: сначала по числу продаж, при равенстве — по цене. Обе по убыванию.
        top = sorted(counts, key=lambda mid: (counts[mid], max_cost[mid]), reverse=True)[:3]

        result = []
        for model_id in top:
            model_row = self._find_row(self.models_index_path, model_id)
            name, brand = self._read_row(self.models_path, model_row)[1:3]
            result.append(ModelSaleStats(
                car_model_name=name,
                brand=brand,
                sales_number=counts[model_id],
            ))
        return result