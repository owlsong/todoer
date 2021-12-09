from .model import Task
import datetime as dt


class TestDatabaseException(Exception):
    pass


class TestDatabase:
    def __init__(self):
        self.data = []
        self.next_id = 0

        def create_task(i):
            return Task(
                id=i,
                summary=f"Summary for task {i}",
                description=f"Desc for task {i}",
                status="Backlog",
                assignee="todd",
                created=dt.datetime.now(),
            )

        for i in range(3):
            # self.data.append(create_task(i))
            self.add(create_task(i))

    def _get_index(self, task_id):
        offsets = [i for i, task in enumerate(self.data) if task.id == task_id]
        if len(offsets) != 1:
            raise TestDatabaseException(
                f"Error tried to delete task {task_id} but did not have 1 occurance"
            )
        return offsets[0]

    def get(self, task_id: int):
        return list(filter(lambda x: task_id == x.id, self.data))

    def add(self, task: Task):
        task.id = self.next_id
        self.next_id += 1
        self.data.append(task)
        return task

    def delete(self, task_id: int):
        return self.data.pop(self._get_index(task_id))

    def update(self, task: Task):
        self.data[self._get_index(task.id)] = task
        return task

    def __str__(self) -> str:
        strs = [str(x) for x in self.data]
        rslt = "data => [" + ",".join(strs) + "]"
        return rslt
