import inspect
class WorkspaceService:

    def create_workspace():
        print(f"Function called: {inspect.currentframe().f_code.co_name}")

    def rename_workspace():
        print(f"Function called: {inspect.currentframe().f_code.co_name}")

    def archive_workspace():
        print(f"Function called: {inspect.currentframe().f_code.co_name}")

    def delete_workspace():
        print(f"Function called: {inspect.currentframe().f_code.co_name}")

    def open_workspace():
        print(f"Function called: {inspect.currentframe().f_code.co_name}")

    def list_workspaces():
        print(f"Function called: {inspect.currentframe().f_code.co_name}")