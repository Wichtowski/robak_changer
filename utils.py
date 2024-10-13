import os
import logging
from typing import Final, List, Dict
from random import choice, randint as ri
from dotenv import load_dotenv
from itertools import permutations

class FileUtils:
    def __init__(self):
        load_dotenv()
        self.ENV: Final[str]= os.getenv('ENV') or "dev"
        self.ENCODING: Final[str] = 'utf-8'
        self.__NICK_CSV: Final[str] = "nicknames.csv"
        self.__GEN_CSV: Final[str] = "generated.csv"
        self.__LANG: Final[str] = "lang.csv"
        # self.perm_of_nicks: List[List[str]] = [] 
        # self.most_endorsed: Dict[str, List[List[int]]] = {}
        # self.__fix_and_permute()
            
    def generate_new_nick(self, guild_id:int, who: str = "") -> str:
        """Randomly generates a new nickname by selecting two different nicknames 
        from the list of fixed nicknames and combines them to form a new nickname."""
        try:
            guild_nicks = self.__read_csv_file(f"{str(guild_id)}/{self.__NICK_CSV}")
            indexes = [ri(0, len(guild_nicks) - 1), ri(0, len(guild_nicks) - 1)]
            while indexes[0] == indexes[1]:
                indexes[1] = ri(0, len(guild_nicks) - 1)
            n1, n2 = guild_nicks[indexes[0]], guild_nicks[indexes[1]]
            fixed_nick = self.__fix_lang(guild_id, n1, n2)
            if who == "zaojoga":
                generated = f"Żao {fixed_nick}"
                with open(f"{str(guild_id)}/zao_{self.__GEN_CSV}", 'a', encoding=self.ENCODING) as f:
                    f.write(f"{generated}\n")
            else:
                generated = f"{fixed_nick}"
                with open(f"{str(guild_id)}/{self.__GEN_CSV}", 'a', encoding=self.ENCODING) as f:
                    f.write(f"{generated}\n")
            return generated
        except Exception as e:
            raise Exception("> Error while generating new nickname")
    
    def read_all_sub_nicks(self, guild_id:int) -> str:
        """Reads all nicknames and returns them as a list of strings, each within Discord's character limit."""
        try:
            file_content: List[str] = self.__read_csv_file(f"{str(guild_id)}/{self.__NICK_CSV}")
            all_nicks: str = '\n'.join(file_content)
            return all_nicks
        except Exception as e:
            raise Exception("> Error while reading all nicks")
    
    def write_new_nick_to_file(self, guild_id: int, new_n: str) -> str:
        """Appends a new nickname to the specified CSV file, updates the list of fixed nicknames, and regenerates permutations."""
        try:
            if len(new_n) > 30:
                return "> Nickname is too long"
            if new_n == '':
                return "> What am I supposed to do with an empty nickname :)"
            if new_n in self.__read_csv_file(f"{str(guild_id)}/{self.__NICK_CSV}"):
                return f"{new_n} already exists"
            with open(f"{str(guild_id)}/{self.__NICK_CSV}", 'a', encoding=self.ENCODING) as f:
                f.write(new_n + '\n')
            return f"> Successfully added {new_n}"
        except Exception as e:
            raise Exception(f"> Error while adding {new_n}")

    def delete_nick_from_file(self, guild_id: int, n_to_delete: str) -> str:
        """Deletes a nickname from the CSV file, updates the list of fixed nicknames, and regenerates permutations."""
        try:
            if n_to_delete == '':
                return "Umm do I look like I read minds?"
            deleted: bool = False
            with open(f"{str(guild_id)}/{self.__NICK_CSV}", 'r', encoding=self.ENCODING) as f:
                lines = f.readlines()
            with open(f"{str(guild_id)}/{self.__NICK_CSV}", 'w', encoding=self.ENCODING) as f:
                for line in lines:
                    if line.strip('\n') != n_to_delete:
                        f.write(line)
                    else:
                        deleted = True
            if not deleted:
                return f"{n_to_delete} was not found"
            return f"Successfully deleted {n_to_delete}"
        except Exception as e:
            raise Exception(f"Error while deleting {n_to_delete}")

    def last_ten_generated_nicks(self, guild_id: int) -> str:
        try:
            """Returns the last ten generated nicknames as a string."""
            generated: List[str] = self.__read_csv_file(f"{str(guild_id)}/{self.__GEN_CSV}")
            generated.reverse()
            last_10: str = ', '.join(generated[-10:])
            return last_10
        except Exception as e:
            raise Exception("Error while reading last 10 generated nicks")

    #todo
    def read_most_endorsed(self, guild_id) -> str:
        return "Not implemented yet"

    def set_lang(self, guild_id: int, lang: str) -> str:
        """Sets the language for the given guild."""
        try:
            with open(f"{str(guild_id)}/{self.__LANG}", 'w', encoding=self.ENCODING) as f:
                f.write(lang)
            return f"Language set to {lang}"
        except Exception as e:
            raise Exception(f"Error while setting language to {lang}")

    def get_lang(self, guild_id: int) -> str:
        """Returns the language for the given guild."""
        try:
            lang = self.__read_csv_file(f"{str(guild_id)}/{self.__LANG}")
            return lang[0]
        except Exception as e:
            raise Exception("Error while getting language")

    def sanitize_lang(self, lang) -> str:
        try:
            match lang:
                case 'pl':
                # Allow alphanumeric characters, Polish special chars, and some punctuation
                    sanitized = re.sub(r'[^a-zA-Z\s\-_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', '', user_input)
                case 'en' | _:
                    sanitized = re.sub(r'[^a-zA-Z\s\-_]', '', user_input)
            return sanitized
        except Exception as e:
            raise Exception("Error while sanitizing language")

    def __fix_lang(self, guild_id: int, n1, n2) -> str:
        """Fixes the last letters of all nicknames from the CSV file based on a predefined rule for given language."""
        try:
            guild_lang = self.__read_csv_file(f"{str(guild_id)}/{self.__LANG}").read().strip()
            match guild_lang:
                case 'pl':
                    return self.__fix_pl_nicks(n1, n2)
                case 'en' | _:
                    return f"{n1} {n2}"
            return f"{n1} {n2}"
        except Exception as e:
            return f"{n1} {n2}"
        
    def __read_csv_file(self, file_path: str) -> List[str]:
        """Reads nicknames from the CSV file and returns them as a list of strings."""
        file_content: List[str] = []
        try:
            with open(file_path, 'r', encoding=self.ENCODING) as f:
                for line in f.readlines():
                    file_content.append(line.strip())
            return file_content
        except Exception as e:
            return []

    def __fix_pl_nicks(self, n1: str, n2: str) -> str:
        """Fixes the last letters of nicknames based on a predefined rule for Polish language."""
        try:
            if n1[-1] == 'a':
                if n2[-1] == 'y':
                    n2 = n2[:-1] + 'a'
            elif n2[-1] == 'y':
                n2 = n2[:-1] + 'a'
            return f"{n1} {n2}"
        except Exception as e:
            return ""

# Testing
# test = FileUtils()
# Uncomment the following lines to test various functionalities
# print(test.write_new_sub_nick_to_file('test_nick'))
# print(test.generate_new_nick(495677065027387392))
# print(test.read_all_sub_nicks(495677065027387392))
# print(test.delete_nick_from_file(495677065027387392, 'test_nick'))
# print(test.last_ten_generated_nicks(495677065027387392))

# def __permute(self) -> List[List[str]]:
    #     """Generates all possible permutations of nicknames from the CSV file and returns them as a list of lists."""
    #     try:
    #         return [list(p) for p in permutations(self.__read_csv_file(self.__NICK_CSV), 2)] 
    #     except Exception as e:
    #         self.LOGGER.write(str(e))
    #         return [] 