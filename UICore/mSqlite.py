# -*- coding: utf-8 -*-

from sqlite3 import connect


class Sqlite:
    def __init__(self, db):
        self.db = db
        self.connection = None
        self.row_factory = None

    def _connect(self):
        self.connection = connect(self.db)
        # self.connection.text_factory = str
        self.row_factory = self.connection.row_factory
        # print(f"连接Sqlite数据库：{self.db}成功！")

    def connect(self):
        try:
            if self.connection:
                pass
                # print(f"已存在数据库连接：{self.db}")
            else:
                self._connect()
        except Exception as e:
            print(f"连接Sqlite数据库：{self.db}失败！异常信息：{e.args[0]}")
            raise

    def execute(self, sql, values=(), bFetch=False, row_factory=None):
        self.connect()
        row = []
        try:
            self.connection.row_factory = row_factory
            cur = self.connection.cursor()
            cur.execute(sql, values)
            if bFetch:
                row = cur.fetchall()
            self.connection.commit()
            # print(f"执行sql语句成功：{sql}")
            cur.close()
        except Exception as e:
            print(f"执行sql语句失败：{sql}！异常信息：{e.args[0]}")
            self.connection.rollback()
            raise
        # return row
        finally:
            self.connection.row_factory = self.row_factory   # 还原返回值数据结构
            self.close()
            return row

    def executemany(self, sql, values=()):
        """根据序列重复执行 SQL 语句"""
        self.connect()
        try:
            cur = self.connection.cursor()
            cur.executemany(sql, values)
            self.connection.commit()
            # print(f"执行sql语句成功：{sql}")
            cur.close()
        except Exception as e:
            print(f"执行sql语句失败：{sql}！异常信息：{e.args[0]}")
            raise
        finally:
            self.close()

    def executescript(self, script):
        """执行 SQL 脚本"""
        self.connect()
        try:
            cur = self.connection.cursor()
            cur.executescript(script)
            self.connection.commit()
            # print(f"执行sql语句成功：{script}")
            cur.close()
        except Exception as e:
            print(f"执行sql脚本失败：{script}！异常信息：{e.args[0]}")
            raise
        finally:
            self.close()

    @staticmethod
    def _dict_factory(cursor, row):
        return dict([(col[0], row[idx]) for idx, col in enumerate(cursor.description)])
        # d = {}
        # for index, col in enumerate(cursor.description):
        #     d[col[0]] = row[index]
        # return d

    def execute_dict(self, sql, values=()):
        self.connect()
        row = {}
        try:
            self.connection.row_factory = self._dict_factory
            # self.connection.text_factory = lambda x: x.encode('utf-8')
            cur = self.connection.cursor()
            cur.execute(sql, values)
            row = cur.fetchall()
            # print(f"执行sql语句成功：{sql}")
            cur.close()
        except Exception as e:
            print(f"执行sql语句失败：{sql}！异常信息：{e.args[0]}")
            raise
        # return row
        finally:
            self.connection.row_factory = self.row_factory   # 还原返回值数据结构
            self.close()
            return row

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            # print(f"关闭Sqlite数据库：{self.db}成功！")