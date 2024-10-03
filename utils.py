import os
from typing import Final, List, Dict
from random import randint as ri
from dotenv import load_dotenv
from itertools import permutations
from logger import Logger 

class FileUtils:
    def __init__(self, lang: str="pl", nick_csv: str ="nicknames.csv", gen_csv: str="generated.csv"):
        load_dotenv()
        self.ENV: Final[str]= os.getenv('ENV') or "dev"
        self.ENCODING: Final[str] = 'utf-8'
        self.__NICK_CSV: Final[str] = nick_csv
        self.__GEN_CSV: Final[str] = gen_csv
        self.__LANG: Final[str] = lang
        self.LOGGER = Logger('app')
        self.perm_of_nicks: List[List[str]] = [] 
        self.most_endorsed: Dict[str, List[List[int]]] = {}
        self.__fix_and_permute()
        
        self.LOGGER.write(f"Initialized FileUtils with lang={lang}, nick_csv={nick_csv}, gen_csv={gen_csv}")
    
    def generate_new_nick(self, who: str = "") -> str:
        """Randomly generates a new nickname by selecting two different nicknames 
        from the list of fixed nicknames and combines them to form a new nickname."""
        try:
            random_nick_pair = self.perm_of_nicks[ri(0, len(self.perm_of_nicks) - 1)]
            if who == "zaojoga":
                generated = f"Żao {random_nick_pair[0]} {random_nick_pair[1]}"
                with open(f"zao_{self.__GEN_CSV}", 'a', encoding=self.ENCODING) as f:
                    f.write(f"{generated}\n")
            else:
                generated = f"{random_nick_pair[0]} {random_nick_pair[1]}"
                with open(self.__GEN_CSV, 'a', encoding=self.ENCODING) as f:
                    f.write(f"{generated}\n")
            return generated
        except Exception as e:
            self.LOGGER.write(str(e))
            return "> Error while generating new nickname"
    
    def read_all_sub_nicks(self) -> str:
        """Reads all nicknames and returns them as a list of strings, each within Discord's character limit."""
        try:
            file_content: List[str] = self.__read_csv_file(self.__NICK_CSV)
            all_nicks: str = '\n'.join(file_content)
            return all_nicks
        except Exception as e:
            self.LOGGER.write(str(e))
            return "> Error while reading all nicks"
    
    def write_new_nick_to_file(self, new_n: str) -> str:
        """Appends a new nickname to the specified CSV file, updates the list of fixed nicknames, and regenerates permutations."""
        try:
            if len(new_n) > 30:
                return "> Nickname is too long"
            if new_n == '':
                return "> What am I supposed to do with an empty nickname :)"
            if new_n in self.__read_csv_file(self.__NICK_CSV):
                return f"{new_n} already exists"
            with open(self.__NICK_CSV, 'a', encoding=self.ENCODING) as f:
                f.write(new_n + '\n')
            self.__fix_and_permute()
            return f"> Successfully added {new_n}"
        except Exception as e:
            self.LOGGER.write(str(e))
            return f"> Error while adding {new_n}"

    def delete_nick_from_file(self, n_to_delete: str) -> str:
        """Deletes a nickname from the CSV file, updates the list of fixed nicknames, and regenerates permutations."""
        try:
            if n_to_delete == '':
                return "Umm do I look like I read minds?"
            deleted: bool = False
            with open(self.__NICK_CSV, 'r', encoding=self.ENCODING) as f:
                lines = f.readlines()
            with open(self.__NICK_CSV, 'w', encoding=self.ENCODING) as f:
                for line in lines:
                    if line.strip('\n') != n_to_delete:
                        f.write(line)
                        deleted = True
            self.__fix_and_permute()
            if not deleted:
                return f"{n_to_delete} was not found"
            return f"Successfully deleted {n_to_delete}"
        except Exception as e:
            self.LOGGER.write(str(e))
            return f"Error while deleting {n_to_delete}"

    def last_ten_generated_nicks(self) -> str:
        try:
            """Returns the last ten generated nicknames as a string."""
            generated: List[str] = self.__read_csv_file(self.__GEN_CSV)
            generated.reverse()
            last_10: str = ', '.join(generated[-10:])
            return last_10
        except Exception as e:
            self.LOGGER.write(str(e))
            return "Error while reading last 10 generated nicks"

    #todo
    def read_most_endorsed(self) -> str:
        return "Not implemented yet"

    def __fix_and_permute(self) -> None:
        """Fixes the last letters of all nicknames from the CSV file based on a predefined rule for given language."""
        try:
            match self.__LANG:
                case 'pl':
                    self.perm_of_nicks = self.__fix_pl_nicks(self.__permute())
                case _:
                    self.perm_of_nicks = self.__permute()
        except Exception as e:
            self.LOGGER.write(str(e))
                
    def __permute(self) -> List[List[str]]:
        """Generates all possible permutations of nicknames from the CSV file and returns them as a list of lists."""
        try:
            return [list(p) for p in permutations(self.__read_csv_file(self.__NICK_CSV), 2)] 
        except Exception as e:
            self.LOGGER.write(str(e))
            return [] 

    def __read_csv_file(self, file_name: str) -> List[str]:
        """Reads nicknames from the CSV file and returns them as a list of strings."""
        file_content: List[str] = []
        try:
            with open(file_name, 'r', encoding=self.ENCODING) as f:
                for line in f.readlines():
                    file_content.append(line.strip())
            return file_content
        except Exception as e:
            self.LOGGER.write(str(e))
            return []

    def __fix_pl_nicks(self, nicknames: List[List[str]]) -> List[List[str]]:
        """Fixes the last letters of all nicknames from the CSV file based on a predefined rule for polish language."""
        fixed_nicks_list: List[List[str]] = []
        try:
            for pair in nicknames:
                match pair[0][-1]:
                    case 'a':
                        pair[1] = pair[1].replace('y', 'a')
                    case 'y':
                        pair[0] = pair[0].replace('y', 'a')
                fixed_nicks_list.append([pair[0], pair[1]])
            return fixed_nicks_list
        except Exception as e:
            self.LOGGER.write(str(e))
            return []

# Testing
# test = FileUtils(lang='pl')
# Uncomment the following lines to test various functionalities
# print(test.write_new_sub_nick_to_file('test_nick'))
# print(test.generate_new_nick())
# print(test.read_all_nicks())
# print(test.delete_nick_from_file('test_nick'))
# print(test.perm_of_nicks)
# print(test.last_ten_generated_nicks())
