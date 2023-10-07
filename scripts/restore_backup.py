import os
import io
import sys
import json
import argparse
import time
import shutil
import getpass
import subprocess
import psycopg2
from psycopg2 import sql
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def exec_command(command, command_dir=None, stdout=None, **kwargs):
    capture_output = True if not stdout else False
    result = subprocess.run(
        [command],
        cwd=command_dir,
        shell=True,
        stdout=stdout,
        capture_output=capture_output,
        **kwargs,
    )
    if stdout:
        return None
    return result.stdout, result.stderr


def exec_command_with_password(command, command_dir=None, stdout=None, **kwargs):
    password = getpass.getpass("Enter your sudo password: ")
    command_with_password = f"echo '{password}' | sudo -S {command}"
    return exec_command(command_with_password, command_dir, stdout, **kwargs)


def get_sql_filename(backup_dir_path):
    for f in os.listdir(backup_dir_path):
        if f.endswith(".sql"):
            return os.path.join(backup_dir_path, f)
    raise Exception("Database dump file does not exist.")


# Generator function to filter lines
def filter_lines(input_text, keyword):
    for line in input_text.splitlines():
        if keyword not in line:
            yield line


def main():

    argParser = argparse.ArgumentParser(
        prog="sudo python restore_backup.py",
        description="This script restores a backup for a project based on Lava.",
        # epilog='Text at the bottom of help'
    )
    argParser.add_argument(
        "-f",
        "--backup-file",
        help="Path to the zipped backup file.",
        required=True,
    )

    args = argParser.parse_args()

    backup_filename = args.backup_file

    # if os.geteuid() != 0:
    #     print(
    #         "\n\nPlease run this script using sudo command.\n\n"
    #     )
    #     raise SystemExit(1)

    # if not backup_filename.startswith("/"):
    #     print("\n\nPlease provide an absolute path for the backup file.")
    #     raise SystemExit(1)

    restore_backup(backup_filename)


def restore_backup(backup_filename):

    restore_in_progress_flag = ".db_restoration_in_progress"
    if os.path.exists(os.path.join(BASE_DIR, restore_in_progress_flag)):
        print(
            "Another backup restoration is running. Please wait until it finishes before starting a new one."
        )
        return

    # Create restore_on_progress flag
    print("Creating `db_restoration_in_progress` flag.")
    open(os.path.join(BASE_DIR, restore_in_progress_flag), "w").close()

    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", 5432)  # Default PostgreSQL port

    psql_dbname = os.getenv("ADMIN_DB_NAME", "postgres")
    psql_username = os.getenv("ADMIN_USER", db_user)
    psql_password = os.getenv("ADMIN_PASSWORD", db_password)

    if not db_name or not db_user or not psql_username or not psql_password:
        print(
            (
                "Please make sure that the following environment variables are correctly setup:\n"
            )
            + ("    - DB_NAME\n" if not db_name else "")
            + ("    - DB_USER\n" if not db_user else "")
            + ("    - DB_PASSWORD\n" if not db_password else "")
            + (
                "    - ADMIN_DB_NAME (If emmited, DB_NAME will be used instead.)\n"
                if not psql_dbname
                else ""
            )
            + (
                "    - ADMIN_USER (If emmited, DB_USER will be used instead.)\n"
                if not psql_username
                else ""
            )
            + (
                "    - ADMIN_PASSWORD (If emmited, DB_USER_PWD will be used instead.)\n"
                if not psql_password
                else ""
            )
        )
        raise SystemExit(1)

    # Unzip files
    print("Unzip files")
    backup_dir_name, _ext = os.path.splitext(os.path.basename(backup_filename))
    backup_dir_path = os.path.join(BASE_DIR, backup_dir_name)
    unzip_out, unzip_err = exec_command(
        (f"unzip {backup_filename} -d {backup_dir_path}")
    )
    if unzip_err:
        raise Exception(unzip_err.decode())

    # Restore database
    print("Running backup commands.")

    rollback_db_rename = False
    rollback_db_create = False
    rollback_checkout = False
    rollback_requirements = False
    create_db_backup = True

    connection = None

    try:
        try:
            connection = psycopg2.connect(
                host=host, port=port, dbname=db_name, user=db_user, password=db_password
            )
        except psycopg2.OperationalError as e:
            does_not_exist_message = f'database "{db_name}" does not exist'
            if does_not_exist_message in str(e):
                print("Database does not exist. No backup will be created.")
                create_db_backup = False
            else:
                raise e

        try:
            connection = psycopg2.connect(
                host=host,
                port=port,
                dbname=psql_dbname,
                user=psql_username,
                password=psql_password,
            )
        except psycopg2.OperationalError as e:
            raise e

        if create_db_backup:
            try:
                print("Creating db backup...")
                cursor = connection.cursor()
                cursor.execute(f"ALTER DATABASE {db_name} RENAME TO {db_name}_tmp;")
                connection.commit()
                print("Database renamed successfully")
                rollback_db_rename = True
            except psycopg2.Error as e:
                raise e
            finally:
                cursor.close()

        try:
            print("Creating new database...")
            connection.set_isolation_level(
                psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
            )
            cursor = connection.cursor()
            create_db_query = sql.SQL("CREATE DATABASE {} OWNER {} ENCODING {}").format(
                sql.Identifier(db_name), sql.Identifier(db_user), sql.Identifier("UTF8")
            )
            cursor.execute(create_db_query)
            connection.commit()
            print("Database created successfully")
        except psycopg2.Error as e:
            raise e
        finally:
            cursor.close()

        rollback_db_create = True

        sql_dump_file = get_sql_filename(backup_dir_path)
        keyword_to_remove = "OWNER TO "
        sed_command = rf"sed -i '/OWNER TO /d' {sql_dump_file}"
        try:
            # Execute the sed command
            exec_command(sed_command, check=True)
            print("Lines containing 'OWNER TO ' removed successfully.")
        except subprocess.CalledProcessError as e:
            raise e

        try:
            # Build the psql command to restore the dump into the database
            command = [
                f"PGPASSWORD='{db_password}' psql",
                f"-h {host}",
                f"-p {port}",
                f"-d {db_name}",
                f"-U {db_user}",
                f"-f {sql_dump_file}",
            ]

            # If a password is set, add it to the command
            # if db_password:
            #     command.append(f"-W {db_password}")

            # Execute the psql command
            # subprocess.run(command, check=True)
            out, err = exec_command(" ".join(command))
            if err:
                raise Exception(err.decode())

            print(f"Dump file '{sql_dump_file}' successfully loaded into '{db_name}'.")

        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

        # Remove media and static folders
        print("Removing media and static folders")
        if os.path.exists(os.path.join(BASE_DIR, "media")):
            os.rename(
                os.path.join(BASE_DIR, "media"), os.path.join(BASE_DIR, "media.bak")
            )
        if os.path.exists(os.path.join(BASE_DIR, "static")):
            os.rename(
                os.path.join(BASE_DIR, "static"), os.path.join(BASE_DIR, "static.bak")
            )

        # Copy media from backup folder to the root directory
        print("Copy media from backup folder to the root directory")
        shutil.copytree(
            os.path.join(backup_dir_path, "media"), os.path.join(BASE_DIR, "media")
        )

        # Checkout repositories
        print("Checkout repos")
        repositories_file = os.path.join(backup_dir_path, "repositories.json")
        with open(repositories_file, "r") as f:
            data = json.load(f)
            for repo in data.keys():
                branch = data[repo]["branch"]
                commit = data[repo]["commit"]

                command_dir = BASE_DIR
                if repo != "main":
                    command_dir = os.path.join(BASE_DIR, repo)

                print(f"Checking out to {branch} - {commit}")
                print(f"command_dir: {command_dir}")

                out, err = exec_command(
                    (f"git checkout {branch} && " f"git checkout {commit}"),
                    command_dir=command_dir,
                )
                if err:
                    error_str = err.decode()
                    print("Git Checkout error message:", error_str)

        rollback_checkout = True

        # Generate static files
        print("Collecting static files")
        out, err = exec_command(
            (f"venv/bin/python manage.py collectstatic --no-input"),
            command_dir=BASE_DIR,
        )
        if err and "WARNING" not in err.decode():
            raise Exception(err.decode())

        # Install all requirements
        print("Installing requirements")
        out, err = exec_command(
            (f"venv/bin/pip install -r {backup_dir_path}/all_requirements.txt"),
            command_dir=BASE_DIR,
        )

        rollback_requirements = True

        shutil.rmtree(backup_dir_path)

        os.remove(restore_in_progress_flag)

        if os.path.exists(os.path.join(BASE_DIR, "media.bak")):
            shutil.rmtree(os.path.join(BASE_DIR, "media.bak"))
        if os.path.exists(os.path.join(BASE_DIR, "static.bak")):
            shutil.rmtree(os.path.join(BASE_DIR, "static.bak"))

        _out, db_err = exec_command(
            (
                # Drop tmp database
                f"sudo PGPASSWORD='{psql_password}' dropdb "
                f"-U {psql_username} -h {host} -p {port} {db_name}_tmp; "
            ),
        )
    except Exception as e:
        print("\n\nException encountered... starting rollback.")
        os.remove(restore_in_progress_flag)
        if os.path.exists(os.path.join(BASE_DIR, "media.bak")) and os.path.exists(
            os.path.join(BASE_DIR, "media")
        ):
            shutil.rmtree(os.path.join(BASE_DIR, "media"))
            os.rename(
                os.path.join(BASE_DIR, "media.bak"), os.path.join(BASE_DIR, "media")
            )

        if os.path.exists(os.path.join(BASE_DIR, "static.bak")) and os.path.exists(
            os.path.join(BASE_DIR, "static")
        ):
            shutil.rmtree(os.path.join(BASE_DIR, "static"))
            os.rename(
                os.path.join(BASE_DIR, "static.bak"), os.path.join(BASE_DIR, "static")
            )

        if os.path.exists(os.path.join(backup_dir_path)):
            shutil.rmtree(backup_dir_path)

        if rollback_db_create:
            try:
                connection.set_isolation_level(
                    psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
                )
                print("Dropping the new database...")
                cursor = connection.cursor()
                cursor.execute(f"DROP DATABASE {db_name};")
                connection.commit()
                print("Database dropped successfully")
            except psycopg2.Error as e:
                print("Error dropping the database:", e)
            finally:
                cursor.close()

        if rollback_db_rename:
            try:
                print("Restoring db backup...")
                cursor = connection.cursor()
                cursor.execute(f"ALTER DATABASE {db_name}_tmp RENAME TO {db_name};")
                connection.commit()
                print("Database renamed successfully")
            except psycopg2.Error as e:
                raise e
            finally:
                cursor.close()

        if rollback_checkout:
            # TODO: Revert git checkouts
            pass

        if rollback_requirements:
            # TODO: Revert install requirements
            pass

        print("\n\n")
        raise e

    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    start = datetime.now()
    main()

    # Print report
    finish = datetime.now()
    print(f"\n\nScript finished after {(finish - start).total_seconds()} seconds.\n\n")
