"""
ICenter module
@Dev Jason
"""
from flask import request, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.functions.database.models import db
import logging

def delete_data(model, **filters):
    """
    根据条件删除指定模型的数据
    :param model: 数据库模型类
    :param filters: 过滤条件，键值对形式
    """
    # 查询要删除的记录
    record_to_delete = db.session.query(model).filter_by(**filters).first()

    if record_to_delete:
        # 删除记录
        db.session.delete(record_to_delete)
        db.session.commit()
        logging.info(f"Record {filters} in {model.__name__} has been deleted.")
    else:
        logging.error(f"No record found with {filters} in {model.__name__}.")


def execute_sql_statement(sql):
    """
    执行SQL指令
    :param sql: SQL语句
    :return: 包含执行结果的字典
    """
    try:
        with db.engine.connect() as connection:
            # 执行SQL语句
            result = connection.execute(text(sql))

            # 判断是否为DML操作（INSERT/UPDATE/DELETE）
            is_dml = result.rowcount >= 0 and not result.returns_rows

            # 自动提交事务（针对DML和DDL语句）
            if is_dml or sql.strip().lower().startswith(('insert', 'update', 'delete', 'alter', 'create', 'drop')):
                connection.commit()

            # 处理返回结果
            response = {
                "success": True,
                "message": "执行成功",
                "rowcount": result.rowcount
            }

            # 添加查询结果数据
            if result.returns_rows:
                response["data"] = [dict(row._mapping) for row in result]

            return response

    except SQLAlchemyError as e:
        connection.rollback()
        error_msg = f"SQL执行错误: {str(e)}"
        logging.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        logging.error(f"未知错误: {str(e)}")
        return {
            "success": False,
            "message": f"系统错误: {str(e)}",
            "error": str(e)
        }

def add_column_to_table(table_name, column_name, column_type):
    """
    向表中添加列
    :param table_name: 表名
    :param column_name: 列名
    :param column_type: 列类型（如 db.String(50)）
    :return: 成功返回 True，失败返回 False
    """
    try:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        db.engine.execute(sql)
        logging.info(f"Column {column_name} added to table {table_name}.")
        return True
    except Exception as e:
        logging.error(f"Error adding column {column_name} to table {table_name}: {e}")
        return False

def execute_sql_logic():
    """
    二次封装
    主功能实现还是在 execute_sql_statement
    :return: any
    """
    sql_statement = request.json.get('sql')

    if not sql_statement:
        return jsonify({
            "success": False,
            "message": "未提供SQL语句"
        }), 400

    # 执行并获取结果
    result = execute_sql_statement(sql_statement)

    # 返回标准JSON响应
    status_code = 200 if result['success'] else 500
    return jsonify(result), status_code
