import pymysql

# Use PyMySQL as a drop-in replacement for MySQLdb (mysqlclient)
# This allows Django to use a pure-Python connector without compiling mysqlclient
pymysql.install_as_MySQLdb()

