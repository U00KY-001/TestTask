from unittest.mock import patch, mock_open

import pytest

from main import try_convert, read_file, Reports


# ─────────────────────────────────────────────────────────────
# try_convert
# ─────────────────────────────────────────────────────────────

class TestTryConvert:

    # --- числа ---

    def test_integer_string_returns_int(self):
        assert try_convert("42") == 42
        assert isinstance(try_convert("42"), int)

    def test_negative_integer_returns_int(self):
        assert try_convert("-10") == -10
        assert isinstance(try_convert("-10"), int)

    def test_zero_returns_int(self):
        assert try_convert("0") == 0
        assert isinstance(try_convert("0"), int)

    def test_float_returns_float(self):
        result = try_convert("18.2")
        assert result == pytest.approx(18.2)
        assert isinstance(result, float)

    def test_whole_float_returns_int(self):
        # "25.0" → is_integer() True → int(25)
        result = try_convert("25.0")
        assert result == 25
        assert isinstance(result, int)

    def test_negative_float_returns_float(self):
        result = try_convert("-3.5")
        assert result == pytest.approx(-3.5)
        assert isinstance(result, float)

    # --- строки ---

    def test_plain_string_returned_unchanged(self):
        assert try_convert("hello") == "hello"

    def test_empty_string_returned_unchanged(self):
        assert try_convert("") == ""

    def test_cyrillic_string_returned_unchanged(self):
        title = "Секрет который скрывают тимлиды"
        assert try_convert(title) == title

    def test_mixed_alphanumeric_returned_unchanged(self):
        assert try_convert("abc123") == "abc123"


# ─────────────────────────────────────────────────────────────
# read_file
# ─────────────────────────────────────────────────────────────

CSV_CONTENT = (
    "title,ctr,retention_rate,views,likes,avg_watch_time\n"
    "Я бросил IT и стал фермером,18.2,35,45200,1240,4.2\n"
    "Секрет который скрывают тимлиды,25.0,22,254000,8900,2.5\n"
    "Рефакторинг выходного дня,8.5,76,28900,780,7.8\n"
)


class TestReadFile:

    def _read(self, content=CSV_CONTENT):
        """Вызывает read_file с замоканным open()."""
        data = []
        with patch("builtins.open", mock_open(read_data=content)):
            read_file("videos.csv", data)
        return data

    def test_correct_number_of_rows(self):
        assert len(self._read()) == 3

    def test_header_is_skipped(self):
        data = self._read()
        for row in data:
            assert row[0] != "title"

    def test_title_is_string(self):
        data = self._read()
        assert data[0][0] == "Я бросил IT и стал фермером"

    def test_float_ctr_parsed_correctly(self):
        data = self._read()
        assert data[0][1] == pytest.approx(18.2)
        assert isinstance(data[0][1], float)

    def test_whole_number_ctr_becomes_int(self):
        # 25.0 → int(25)
        data = self._read()
        assert data[1][1] == 25
        assert isinstance(data[1][1], int)

    def test_retention_rate_parsed(self):
        data = self._read()
        assert data[0][2] == 35

    def test_appends_to_existing_list(self):
        data = [["old", 5, 50, 100, 10, 3.0]]
        with patch("builtins.open", mock_open(read_data=CSV_CONTENT)):
            read_file("videos.csv", data)
        assert len(data) == 4
        assert data[0][0] == "old"

    def test_opens_correct_path(self):
        with patch("builtins.open", mock_open(read_data=CSV_CONTENT)) as m:
            read_file("videos.csv", [])
        m.assert_called_once_with(
            "./Files/videos.csv", "r", newline="", encoding="utf-8"
        )

    def test_empty_csv_returns_empty_list(self):
        header_only = "title,ctr,retention_rate,views,likes,avg_watch_time\n"
        assert self._read(header_only) == []


# ─────────────────────────────────────────────────────────────
# Reports.clickbait
# ─────────────────────────────────────────────────────────────

def row(title="Video", ctr=20.0, retention=30):
    """Вспомогательная фабрика строки данных."""
    return [title, ctr, retention, 10000, 500, 4.0]


class TestClickbait:

    @pytest.fixture
    def report(self):
        return Reports()

    def test_first_row_is_header(self, report):
        result = report.clickbait([row()])
        assert result[0] == ["title", "ctr", "retention_rate"]

    def test_video_passes_filter(self, report):
        result = report.clickbait([row("Good", ctr=20.0, retention=30)])
        assert len(result) == 2  # заголовок + 1 видео
        assert result[1][0] == "Good"

    def test_low_ctr_excluded(self, report):
        result = report.clickbait([row(ctr=10.0, retention=30)])
        assert len(result) == 1  # только заголовок

    def test_ctr_exactly_15_excluded(self, report):
        # условие строгое: ctr > 15
        result = report.clickbait([row(ctr=15.0, retention=30)])
        assert len(result) == 1

    def test_high_retention_excluded(self, report):
        result = report.clickbait([row(ctr=20.0, retention=60)])
        assert len(result) == 1

    def test_retention_exactly_40_excluded(self, report):
        # условие строгое: retention_rate < 40
        result = report.clickbait([row(ctr=20.0, retention=40)])
        assert len(result) == 1

    def test_sorted_by_ctr_descending(self, report):
        rows = [
            row("A", ctr=16.0, retention=30),
            row("B", ctr=25.0, retention=20),
            row("C", ctr=20.0, retention=35),
        ]
        result = report.clickbait(rows)
        ctrs = [r[1] for r in result[1:]]
        assert ctrs == sorted(ctrs, reverse=True)

    def test_empty_input_returns_only_header(self, report):
        assert report.clickbait([]) == [["title", "ctr", "retention_rate"]]

    def test_result_columns_are_title_ctr_retention(self, report):
        result = report.clickbait([row("X", ctr=20.0, retention=30)])
        assert result[1] == ["X", 20.0, 30]

    def test_real_data_sample(self, report):
        rows = [
            ["Я бросил IT и стал фермером",              18.2, 35, 45200,  1240, 4.2],
            ["Как я спал по 4 часа и ничего не понял",   22.5, 28, 128700, 3150, 3.1],
            ["Почему сеньоры не носят галстуки",          9.5, 82, 31500,   890, 8.9],
            ["Секрет который скрывают тимлиды",          25.0, 22, 254000, 8900, 2.5],
            ["Купил джуну макбук и он уволился",         19.0, 38, 87600,  2100, 4.5],
            ["Честный обзор на печеньки в офисе",         6.0, 91, 12300,   450, 10.2],
            ["Как я задолжал ревьюеру 1000 строк кода",  21.0, 35, 67300,  1890, 4.0],
            ["Рефакторинг выходного дня",                 8.5, 76, 28900,   780, 7.8],
            ["Почему я не использую ChatGPT на собесах", 16.5, 42, 54100,  1320, 4.8],
            ["Я переписал всё на Go и пожалел",          14.2, 68, 43800,  1150, 6.5],
        ]
        result = report.clickbait(rows)
        titles = [r[0] for r in result[1:]]

        assert "Секрет который скрывают тимлиды" in titles
        assert "Как я спал по 4 часа и ничего не понял" in titles
        assert "Как я задолжал ревьюеру 1000 строк кода" in titles
        assert "Купил джуну макбук и он уволился" in titles
        assert "Я бросил IT и стал фермером" in titles

        assert "Почему я не использую ChatGPT на собесах" not in titles  # retention=42
        assert "Я переписал всё на Go и пожалел" not in titles           # ctr=14.2
        assert "Почему сеньоры не носят галстуки" not in titles          # ctr=9.5

        assert titles[0] == "Секрет который скрывают тимлиды"  # наибольший CTR первый


# ─────────────────────────────────────────────────────────────
# Reports.choice_method
# ─────────────────────────────────────────────────────────────

class TestChoiceMethod:

    @pytest.fixture
    def report(self):
        return Reports()

    def test_clickbait_dispatches_correctly(self, report):
        result = report.choice_method("clickbait", [row()])
        assert isinstance(result, list)
        assert result[0] == ["title", "ctr", "retention_rate"]

    def test_unknown_method_returns_error_string(self, report):
        assert report.choice_method("unknown", []) == "Метода не существует"

    def test_empty_method_name_returns_error_string(self, report):
        assert report.choice_method("", []) == "Метода не существует"

    def test_choice_method_matches_direct_call(self, report):
        rows = [row("A", ctr=25.0, retention=20), row("B", ctr=5.0, retention=80)]
        assert report.choice_method("clickbait", rows) == report.clickbait(rows)
