# данный файл создан для более удобного анализа и доработки кода
# путем разбиением функционала на файлы - модули
# в данном файле описан класс для замены персональных данных в тексте

# данная библиотека добавляет удобную работу с регулярными выражениями,
# что здесь используется для создания паттернов номеров машин и аддрессов
import re
# в данном приложении используется для получения названий локаций
# (города и страны) на русском языка
from natasha import Segmenter, NewsEmbedding, NewsNERTagger, Doc


# класс для замены персональных данных в тексте
class Replacer:
    def __init__(self):
        # инициализация компонентов Natasha
        self.segmenter = Segmenter()
        self.embedding = NewsEmbedding()
        self.ner_tagger = NewsNERTagger(self.embedding)

        self.full_name_pattern = re.compile(
            r'\b[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){2}\b',
            re.IGNORECASE
        )
        
        self.passport_pattern = re.compile(
            r'((?:паспорт\s(?:РФ|гражданина)?|серия)\s*:?\s)?'  # Группа 1: "паспорт РФ:", "паспорт гражданина:" или "серия"
            r'(\d{2})\s(\d{2})\s,?\s?№?\s?(\d{6})',             # Группа 2-4: серия и номер
            re.IGNORECASE
        )


        self.phone_pattern = re.compile(
            r'((?:Телефон|тел\.?|мобильный|сотовый|phone|tel\.?)[:\s]*)?'  # контекст
            r'('  # Группа с номером
            r'\+?[78][\s\-]?\(?\d{3,5}\)?[\s\-]?\d{1,3}[\s\-]?\d{2}[\s\-]?\d{2}'  # +7…, 8…
            r'|'
            r'\(?\d{3,5}\)?[\s\-]?\d{1,3}[\s\-]?\d{2}[\s\-]?\d{2}'  # (959…)
            r'|'
            r'\d{3,5}[\s\-]?\d{1,3}[\s\-]?\d{2}[\s\-]?\d{2}'  # 959…
            r')',
            re.IGNORECASE
        )

        # паттерн для ИНН
        self.inn_pattern = re.compile(
            r'\bИНН[:\s]*(\d{10,12})',
            re.IGNORECASE
        )

        # паттерн для СНИЛС
        self.snils_pattern = re.compile(
            r'\bСНИЛС[:\s]*(\d{3}[-]?\d{3}[-]?\d{3}\s?\d{2})',
            re.IGNORECASE
        )

        # добавление недостающих паттерны
        self.passport_date_pattern = re.compile(
            r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4}\b',
            re.IGNORECASE
        )

        self.birth_date_pattern = re.compile(
            r'\b(?:рождения|дата\s*рождения)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})\b',
            re.IGNORECASE
        )

        self.text_date_pattern = re.compile(
            r'\b\d{1,2}\s+[а-яё]+\s+\d{4}\b',
            re.IGNORECASE
        )

        self.zip_pattern = re.compile(
            r'\b\d{6}\b'
        )

        # паттерны для адресов без флагов (флаги будут добавляться при вызове)
        self.street_pattern = r'\b(?:улица|ул\.?)\s+[^,\.;]+'
        self.house_pattern = r'\b(?:дом|д\.?)\s+[^,\.;]+'
        self.apartment_pattern = r'\b(?:квартира|кв\.?)\s+[^,\.;]+'
        self.office_pattern = r'\b(?:офис|оф\.?)\s+[^,\.;]+'

        self.car_number_pattern = re.compile(
            r'\b[А-Я]\d{3}[А-Я]{2}\d{2,3}',
            re.IGNORECASE
        )
        
        self.excluded_words = ['продав', 'покупат']
    

    # замена ИНН    
    def __replace_inn(self, text: str) -> str:
        def inn_repl(m):
            prefix = "ИНН: "
            inn_number = m.group(1)
            return f"{prefix}{inn_number[0]}"

        return self.inn_pattern.sub(inn_repl, text)

    
    def __replace_passport(self, text: str) -> str:
        def repl(m):
            prefix = m.group(1) or ""  # "паспорт РФ: ", "серия ", или пусто
            first_part = m.group(2)    # первые 2 цифры серии
            second_part = m.group(3)   # вторые 2 цифры серии
            number = m.group(4)        # номер паспорта (6 цифр)

            # берем только первые цифры из каждой части
            first_digit = first_part[0] if first_part else ""
            second_digit = second_part[0] if second_part else ""
            number_digit = number[0] if number else ""

            return f"{prefix}{first_digit} {second_digit} {number_digit}"

        return self.passport_pattern.sub(repl, text)

    def __replace_birth_dates(self, text: str) -> str:
        def date_repl(m):
            date_str = m.group()
            normalized = re.sub(r'[\/\-]', '.', date_str)
            parts = normalized.split('.')

            if len(parts) == 3:
                day, month, year = parts
                return f"{day[0]}.{month[0]}.{year[0]}"

            return date_str

        return self.birth_date_pattern.sub(date_repl, text)

    def __replace_text_dates(self, text: str) -> str:
        def text_date_repl(m):
            date_str = m.group()
            parts = date_str.split()
            if len(parts) >= 3:
                day, month, year = parts[0], parts[1], parts[2]
                first_day = day[0] if day else ""
                first_month = month[0] if month else ""
                first_year = year[0] if year else ""
                return f"{first_day} {first_month} {first_year}"
            return date_str

        return self.text_date_pattern.sub(text_date_repl, text)

    def __replace_passport_dates(self, text: str) -> str:
        def date_repl(m):
            date_str = m.group()
            normalized = re.sub(r'[\/\-]', '.', date_str)
            parts = normalized.split('.')

            if len(parts) == 3:
                day, month, year = parts
                return f"{day[0]}.{month[0]}.{year[0]}"

            return date_str

        return self.passport_date_pattern.sub(date_repl, text)

    def __replace_snils(self, text: str) -> str:
        def snils_repl(m):
            prefix = "СНИЛС: "
            snils_number = m.group(1)
            clean_snils = re.sub(r'[^\d]', '', snils_number)
            return f"{prefix}{clean_snils[0]}"

        return self.snils_pattern.sub(snils_repl, text)

    def __replace_phones(self, text: str) -> str:
        def phone_repl(m):
            full_match = m.group(0)

            # если есть контекст (Телефон, тел. и т.д.)
            context_match = m.group(1)
            if context_match:
                # оставляем контекст и добавляем первую цифру/символ номера
                phone_number = m.group(2)
                if phone_number:
                    # ищем первую цифру или символ +
                    first_char = None
                    for char in phone_number:
                        if char.isdigit() or char == '+':
                            first_char = char
                            break

                    if first_char:
                        return f"{context_match.strip()} {first_char}"

            # если контекста нет, обрабатываем просто номер
            phone_number = m.group(2)
            if phone_number:
                # ищем первую цифру или символ +
                for char in phone_number:
                    if char.isdigit() or char == '+':
                        return char

            return "+"  # fallback

        return self.phone_pattern.sub(phone_repl, text)

    def __replace_zip(self, text: str) -> str:
        # замена индекса - оставляем только первую цифру

        def zip_repl(m):
            zip_code = m.group()
            if zip_code and len(zip_code) >= 1:
                return zip_code[0]
            return zip_code

        return self.zip_pattern.sub(zip_repl, text)

    def __repl(self, m: str) -> str:
        # универсальный метод замены для адресов
        full = m.group()
        words = full.split(maxsplit=1)

        if len(words) == 2:
            return words[0] + " " + self.__shorten(words[1])
        else:
            return self.__shorten(full)

    def __shorten(self, text: str) -> str:
        # сокращение текста до первых букв/цифр
        parts = re.split(r"[ \-_/]+", text)
        first_letters = [p[0] for p in parts if p]
        return " ".join(first_letters)

    def __replace_street(self, text: str):
        return re.sub(self.street_pattern, self.__repl, text, flags=re.IGNORECASE)

    def __replace_house(self, text: str):
        return re.sub(self.house_pattern, self.__repl, text, flags=re.IGNORECASE)

    def __replace_apartment(self, text: str):
        return re.sub(self.apartment_pattern, self.__repl, text, flags=re.IGNORECASE)

    def __replace_office(self, text: str):
        return re.sub(self.office_pattern, self.__repl, text, flags=re.IGNORECASE)

    def __replace_car_numbers(self, text: str):
        return re.sub(
            self.car_number_pattern,
            lambda m: self.__shorten(m.group()),
            text
        )

    def __replace_locations(self, text: str, doc: Doc):
        # поиск локации в тексте
        spans = [s for s in doc.spans if s.type == "LOC"]
        spans = sorted(spans, key=lambda s: -len(s.text))

        # укорачиваются все локации до первой буквы
        contains = False
        for span in spans:
            original_span = span.text
            for word in self.excluded_words:
                if word in original_span.lower():
                    contains = True
                    break
            
            if contains:
                contains = False
                continue
            
            text = text.replace(original_span, self.__shorten(span.text))
        
        return text

    def __replace_persons(self, text: str, doc: Doc) -> str:
        # сначала используется Natasha для поиска персон
        spans = [s for s in doc.spans if s.type == "PER"]
        spans = sorted(spans, key=lambda s: -len(s.text))


        # обработка персоны найденные Natasha
        contains = False
        for span in spans:
            original_span = span.text.strip()
            for word in self.excluded_words:
                if word in original_span.lower():
                    contains = True
                    break

            if contains:
                contains = False
                continue    

            # пропуск если это одиночная буква или слишком короткое слово
            if len(original_span) <= 1:
                continue

            # пропускаем если не начинается с большой буквы (не имя собственное)
            if not original_span[0].isupper():
                continue

            # сокращение ФИО до инициалов
            shortened = self.__shorten_person_name(original_span)

            # замена только целые слова (с учетом различных разделителей)
            pattern = r'(?<!\w)' + re.escape(original_span) + r'(?!\w)'
            text = re.sub(pattern, shortened, text)

        # дополнительно обрабатываем ФИО в формате "Фамилия Имя Отчество"
        text = self.__replace_full_names(text)

        return text

    def __shorten_person_name(self, name: str) -> str:
        # иначе сокращаем как обычно
        parts = name.split()
        if len(parts) >= 2:
            initials = [part[0] for part in parts if part]
            return " ".join(initials)
        elif len(parts) == 1:
            return name[0] if name else name
        else:
            return name

    def __replace_full_names(self, text: str) -> str:
        # паттерн для ФИО в формате "Фамилия Имя Отчество"
        def replace_name(m):
            full_name = m.group()
            # дополнительная проверка - все части ФИО должны начинаться с большой буквы
            parts = full_name.split()
            if len(parts) == 3:
                # проверка, что все три слова начинаются с большой буквы
                if all(part[0].isupper() for part in parts):
                    return self.__shorten_person_name(full_name)
            return full_name  # если проверка не пройдена, оставляем как есть

        return self.full_name_pattern.sub(replace_name, text)

    def replace_all(self, text: str):
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_ner(self.ner_tagger)

        # поочередные замены
        text = self.__replace_snils(text)
        text = self.__replace_inn(text)        
        text = self.__replace_phones(text)
        text = self.__replace_passport(text)
        text = self.__replace_birth_dates(text)
        text = self.__replace_text_dates(text)
        text = self.__replace_passport_dates(text)
        text = self.__replace_zip(text)
        text = self.__replace_street(text)
        text = self.__replace_house(text)
        text = self.__replace_apartment(text)
        text = self.__replace_office(text)
        text = self.__replace_car_numbers(text)
        text = self.__replace_persons(text, doc)
        text = self.__replace_locations(text, doc)

        return text