import oracledb


try:
    # Establish connection
    connection = oracledb.connect(
        user=username,
        password=password,
        dsn=connection_string
    )
    print("Successfully connected to Oracle Database!")

    # Close connection when done
    connection.close()

except Exception as e:
    print(f"Connection failed: {e}")
