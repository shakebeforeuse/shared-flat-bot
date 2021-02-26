from enum import Enum
from copy import copy

class Frequency(Enum):
    DAILY, WEEKLY, MONTHLY, YEARLY = range(4)

class Home:
    def __init__(self, name: str):
        self.name = name
        self.rooms = []
        self.members = []
        self.lists = {}
        self.rotations = {}
        self.chat_id = None
    
    def is_member(self, displayname: str):
        for member in self.members:
            if member.displayname == displayname:
                return True
        
        return False
    
    def is_room(self, name: str):
        for room in self.rooms:
            if room.name == name:
                return True
        
        return False
    
    def is_list(self, name: str):
        return name in self.lists.keys()
    
    def is_rotation(self, name: str):
        return name in self.rotations.keys()
    
    def __str__(self):
        return self.name
    
    def __copy__(self):
        cp = type(self)(self.name)
        cp.rooms = [copy(r) for r in self.rooms]
        cp.members = [copy(m) for m in self.members]
        cp.lists = {l_name : copy(l) for l in self.lists.items()}
        
        cp.rotations = {r_name : copy(r) for r in self.rotations}
        for r_name, r in cp.rotations.items():
            r._home = cp
        
        return cp

class Room:
    def __init__(self, name: str):
        self.name = name
    
    def __str__(self):
        return self.name

    def __copy__(self):
        return type(self)(self.name)

class Member:
    def __init__(self, displayname: str):
        self.displayname = displayname
    
    def __str__(self):
        return self.displayname
    
    def __copy__(self):
        return type(self)(self.displayname)

class List:
    def __init__(self, name: str):
        self.name = name
        self.content = []
    
    def __str__(self):
        return self.name + ": " + " ".join(self.content)

class Rotation:
    def __init__(self, name: str, chat_id: int):
        self._chat_id = chat_id
        self.name = name
        self.rooms = []
        self.members = []
        self.frequency = None
        self.offset = 0
        self.completed = []
    
    def __str__(self):
        return "--Rooms: " + " ".join(self.rooms) + "\n--Members: " + " ".join(self.members) + "\n--Frequency: " + self.frequency
    
    