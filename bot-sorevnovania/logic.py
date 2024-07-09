import sqlite3
from config import *


class DB_Manager():
    def __init__(self, database):
        self.database = database

    def create_questions_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    question_id INTEGER PRIMARY KEY,
                    question_text TEXT,
                    answer TEXT,
                    score INTEGER,
                    level INTEGER,
                    key TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS answers (
                    question_id INTEGER,
                    team_id INTEGER,
                    FOREIGN KEY (question_id) REFERENCES questions (question_id),
                    FOREIGN KEY (team_id) REFERENCES teams (team_id)
                    
                )
            ''')
            conn.commit()

    def insert_questions(self, data):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()

            cursor.executemany('INSERT OR IGNORE INTO questions (question_text, answer, score, level, key) VALUES (?, ?, ?, ?,?)', data)
            conn.commit() 
    
    def update_questions_key(self, key, question_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE questions SET key = ? WHERE question_id = ?', (key, question_id))
            conn.commit() 

    def create_users_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    team_id INTEGER,
                    question_id INTEGER DEFAULT 1,        
                    FOREIGN KEY (team_id) REFERENCES teams (team_id),
                    FOREIGN KEY (question_id) REFERENCES questions (question_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    team_id INTEGER PRIMARY KEY,
                    name TEXT,
                    score INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1   
                )
            ''')
            conn.commit()


    def insert_user(self, user_id, team_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()

            cursor.execute('INSERT OR IGNORE INTO users (user_id, team_id) VALUES (?, ?)', (user_id, team_id))
            conn.commit()
        

    def insert_team(self, team_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO teams (name) VALUES (?)', (team_name,))
            conn.commit()
            cursor.execute('SELECT team_id FROM teams WHERE name = ?', (team_name, ))
            return cursor.fetchone()[0]

    def get_rating(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute('SELECT name, score FROM teams ORDER BY score DESC')
        return cursor.fetchall()
        
    def get_question(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()

            cursor.execute('''SELECT questions.question_id, questions.question_text, answer FROM users
    INNER JOIN questions ON users.question_id = questions.question_id
    WHERE user_id = ?''', (user_id,))
            
            return cursor.fetchone()

    def get_answers(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()

            cursor.execute('''SELECT answers.question_id FROM answers
    INNER JOIN users ON users.team_id = answers.team_id
    WHERE user_id = ?''', (user_id,))
            
            return [x[0] for x in cursor.fetchall()]

    def get_teams_name(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()

            cursor.execute('''SELECT team_id, name FROM teams''')
            return cursor.fetchall()
            

    def check_answer(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()

            cursor.execute('''SELECT answers.question_id FROM answers
    INNER JOIN users ON users.team_id = answers.team_id
    WHERE user_id = ? AND answers.question_id = users.question_id''', (user_id,))
            
            return cursor.fetchall()


    def update_question_id(self, user_id, question_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''UPDATE users SET question_id = ?
    WHERE user_id = ?''', (question_id, user_id))


    def get_key_by_id(self, question_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT key FROM questions
    WHERE question_id = ?''', (question_id,))
            return  cursor.fetchone()[0]

         
    def add_bonus(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT users.team_id, teams.level FROM users
    INNER JOIN teams ON users.team_id = teams.team_id
    WHERE user_id = ?''', (user_id,))
            
            team_id, level = cursor.fetchone()
            score = QUESTIONS_INFO[level-1]['bonus']
            cursor.execute(f'''UPDATE teams set score = score+{score}
                            WHERE team_id = ?''', (team_id,))   
            conn.commit()

            
    
    def add_points(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()

            cursor.execute('''SELECT questions.score, questions.question_id, users.team_id FROM users
    INNER JOIN questions ON users.question_id = questions.question_id
    WHERE user_id = ?''', (user_id,))
            
            score, question_id, team_id = cursor.fetchone()
            cursor.execute("INSERT OR IGNORE INTO answers values(?,?)", (question_id, team_id))
            cursor.execute(f'''UPDATE teams set score = score+{score}
                            WHERE team_id = ?''', (team_id,))   
            conn.commit()

            return self.check_finish_level(user_id)
        

    def get_level(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT teams.level FROM users
    INNER JOIN teams ON users.team_id = teams.team_id
    WHERE users.user_id = ?''', (user_id,))
            return cursor.fetchone()[0]


    def check_access(self, question_id, user_id):
        level = self.get_level(user_id)
        last_question = QUESTIONS_INFO[level-1]['list'][-1]
        if question_id <= last_question:
            return 1
        else:
            return 0
        
    def update_level(self, user_id):
        level = self.get_level(user_id)
        if level == len(QUESTIONS_INFO):
            return 1
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT teams.team_id FROM users
INNER JOIN teams ON users.team_id = teams.team_id
WHERE users.user_id = ?''', (user_id,))
            team_id = cursor.fetchone()[0]
            cursor.execute('''UPDATE teams
SET level = level+1
WHERE team_id = ?''', (team_id,))
            return 0

    def get_level_key(self, user_id):
        level = self.get_level(user_id)
        return QUESTIONS_INFO[level-1]['key']


    def check_finish_level(self, user_id):
        answers = self.get_answers(user_id)
        level = self.get_level(user_id)
        list_ans = []
        for lvl in QUESTIONS_INFO[:level]:
            list_ans += lvl['list']
        if set( list_ans ).issubset(answers):
            return 1
        else:
            return 0
        

if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.create_questions_tables()
    manager.create_users_table()
    questions = [
        ("Какая столица у Самоа?", "Апиа", 5, 1, ""),
        ("Сколько всего континентов в Базе данных?", "6", 5, 1, ''),
        ("Как называется столбец, который отвечает за площадь?", "area", 5, 1, ""),
        ("Какой ключевое значение связывает таблицы со странами и информацией о них?", "country_id", 5, 1, ''),

        ("Найди самую маленькую по площади страну", "Ватикан", 10, 2, ''),
        ("У какой страны самая большая плотность населения?", "Монако", 10, 2, ''),
        ("На каком континенте находится страна со столицей Бастер?", "Северная Америка", 10, 2, ''),
        ("Сколько стран в Африке?", "53", 10, 2, ''),

        ("Какая столица у страны с численностью населения 1500001 человек?", "Манама", 20, 2, ''),
        ("Какая страна самая густонаселенная среди тех, у кого численность больше 10 миллионов человек и площадь меньше 8 миллионов квадратных киллометров?", "Бангладеш", 20, 2, ''),
        ("Сколько стран имеют столицы, начинающиеся на букву Б?", "24", 20, 2, ''),
        ("На каком континенте самая маленькая средняя плотность населения?", "Южная Америка", 20, 2, ''),

        ("Какая общая площадь всех стран Австралии и Океании?", "8490640.4", 30, 3, ""),
        ("В таблице info есть несколько стран, с процентом численности населения относительно численности Земли равным нулю. Определи среди этих стран ту, у которой самое длинное название столицы, в ответ напиши численность населения этой страны.", "81588", 30, 3, ""),
        ("Какая страна заканчивается на 'ия', находится в Океании и имеет минимальную численность?", "Микронезия", 30, 3, ""),
        ("Задание со звездочкой: Определи среднюю численность населения в первых 10 странах Европы, отсортированных по плотности населения (по возрастанию). В ответ напиши целое число.", "17045185", 30, 3, "")
        
        ]
    manager.insert_questions(questions)
    
    for i, key in enumerate(ANSWER_LIST):
        manager.update_questions_key(key, i+1)



